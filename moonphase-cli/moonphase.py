#!/usr/bin/env python3
import requests
import datetime
from datetime import datetime as dt, timedelta
import click
import ephem
from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

ZIP_COORDS_API = "http://api.zippopotam.us/us/{zip}"

PHASE_EMOJI = {
    "New Moon": "🌑",
    "Waxing Crescent": "🌒",
    "First Quarter": "🌓",
    "Waxing Gibbous": "🌔",
    "Full Moon": "🌕",
    "Waning Gibbous": "🌖",
    "Last Quarter": "🌗",
    "Waning Crescent": "🌘",
}

ASCII_MOONS = {
    "New Moon": "   ●   ",
    "Waxing Crescent": "  🌘   ",
    "First Quarter": "  ◐    ",
    "Waxing Gibbous": "  🌖   ",
    "Full Moon": "   ○   ",
    "Waning Gibbous": "  🌕   ",
    "Last Quarter": "  ◑    ",
    "Waning Crescent": "  🌒   ",
}


def get_coords(zip_code):
    res = requests.get(ZIP_COORDS_API.format(zip=zip_code))
    res.raise_for_status()
    data = res.json()
    place = data['places'][0]
    lat = float(place['latitude'])
    lon = float(place['longitude'])
    loc = f"{place['place name']}, {place['state abbreviation']}"
    return lat, lon, loc


def phase_name_and_illumination(date):
    moon = ephem.Moon(date)
    illum = moon.phase
    prev_new = ephem.previous_new_moon(date)
    lunation_days = (date - prev_new.datetime()).days + (date - prev_new.datetime()).seconds / 86400
    fraction = lunation_days / 29.53

    if illum < 1:
        name = "New Moon"
    elif 0 < fraction < 0.25:
        name = "Waxing Crescent"
    elif abs(fraction - 0.25) < 0.02:
        name = "First Quarter"
    elif 0.25 < fraction < 0.5:
        name = "Waxing Gibbous"
    elif abs(fraction - 0.5) < 0.02:
        name = "Full Moon"
    elif 0.5 < fraction < 0.75:
        name = "Waning Gibbous"
    elif abs(fraction - 0.75) < 0.02:
        name = "Last Quarter"
    else:
        name = "Waning Crescent"

    return name, round(illum, 1)


def moonrise_moonset(date, lat, lon):
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = date
    moon = ephem.Moon(observer)
    try:
        rise = observer.next_rising(moon).datetime().strftime("%H:%M")
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        rise = "N/A"
    try:
        sett = observer.next_setting(moon).datetime().strftime("%H:%M")
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        sett = "N/A"
    return rise, sett


def generate_html_single(date, name, illum, rise, sett, location, emoji, art, filename):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Moonphase Report - {date}</title>
<style>
  body {{ background-color: #1e1e2e; color: #f8f8f2; font-family: Arial, sans-serif; padding: 20px; }}
  h1 {{ color: #bd93f9; }}
  h2 {{ color: #50fa7b; }}
  .card {{ background-color: #282a36; border: 1px solid #bd93f9; padding: 20px; max-width: 400px; margin: auto; text-align: center; }}
  .moon {{ font-size: 4rem; }}
  .bat {{ font-size: 2rem; color: #ff79c6; float: right; }}
</style>
</head>
<body>
<h1>🦇 Moonphase Report</h1>
<div class="card">
  <div class="moon">{emoji}</div>
  <h2>{name}</h2>
  <p>Date: {date}</p>
  <p>Location: {location}</p>
  <p>Illumination: {illum}%</p>
  <p>Moonrise: {rise} — Moonset: {sett}</p>
  <pre>{art}</pre>
</div>
</body>
</html>"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    console.print(f"[green]Saved HTML report to [bold]{filename}[/bold][/green]")

def generate_html_week(start_date, days, rows, location, filename):
    html_rows = ""
    for row in rows:
        html_rows += f"<tr><td>{row['date']}</td><td>{row['phase']}</td><td>{row['illum']}</td><td>{row['rise']}</td><td>{row['set']}</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Moonphase Forecast</title>
<style>
  body {{ background-color: #1e1e2e; color: #f8f8f2; font-family: Arial, sans-serif; padding: 20px; }}
  h1 {{ color: #bd93f9; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
  th, td {{ border: 1px solid #6272a4; padding: 8px; text-align: center; }}
  th {{ background-color: #44475a; color: #f1fa8c; }}
  tr:nth-child(even) {{ background-color: #282a36; }}
</style>
</head>
<body>
<h1>🦇 Moon Phases for {location}</h1>
<table>
<tr><th>Date</th><th>Phase</th><th>Illum</th><th>Rise</th><th>Set</th></tr>
{html_rows}
</table>
</body>
</html>"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    console.print(f"[green]Saved HTML report to [bold]{filename}[/bold][/green]")


def print_single(date, lat, lon, location, ask_html, html_filename):
    name, illum = phase_name_and_illumination(date)
    rise, sett = moonrise_moonset(date, lat, lon)
    emoji = PHASE_EMOJI.get(name, "🌙")
    art = ASCII_MOONS.get(name, "")

    console.print(
        Panel.fit(
            f"{emoji} [bold cyan]{name}[/bold cyan]\n"
            f"Date: [bold]{date.strftime('%Y-%m-%d')}[/bold]\n"
            f"Location: [bold]{location}[/bold]\n\n"
            f"Illumination: [yellow]{illum}%[/yellow]\n"
            f"Moonrise: [green]{rise}[/green]  Moonset: [red]{sett}[/red]\n\n"
            f"[bold yellow]{art}[/bold yellow]",
            border_style="purple",
            title="🌙 Moonphase Report",
            subtitle="🦇",
        )
    )

    if ask_html:
        generate_html_single(date.strftime("%Y-%m-%d"), name, illum, rise, sett, location, emoji, art, html_filename)


def print_week(start_date, days, lat, lon, location, ask_html, html_filename):
    table = Table(title=f"🦇 Moon Phases for {location}", title_style="bold magenta")
    table.add_column("Date", style="cyan", justify="center")
    table.add_column("Phase", style="magenta", justify="left")
    table.add_column("Illum", style="yellow", justify="center")
    table.add_column("Rise", style="green", justify="center")
    table.add_column("Set", style="red", justify="center")

    html_rows = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        name, illum = phase_name_and_illumination(day)
        rise, sett = moonrise_moonset(day, lat, lon)
        emoji = PHASE_EMOJI.get(name, "🌙")
        table.add_row(day.strftime("%Y-%m-%d"), f"{emoji} {name}", f"{illum:.1f}%", rise, sett)
        html_rows.append({
            "date": day.strftime("%Y-%m-%d"),
            "phase": f"{emoji} {name}",
            "illum": f"{illum:.1f}%",
            "rise": rise,
            "set": sett,
        })

    console.print(table)

    if ask_html:
        generate_html_week(start_date, days, html_rows, location, html_filename)


@click.command()
@click.option("--date", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--zip", "zip_code", default=None, help="US ZIP code for location")
@click.option("--days", default=None, type=int, help="Number of days (if skipped, interactive menu)")
@click.option("--html", "html_file", default=None, help="Optional filename to save as HTML (auto skips prompt)")
def main(date, zip_code, days, html_file):
    # Prompt for date if not provided
    if date is None:
        date = inquirer.text(
            message="Enter date (YYYY-MM-DD):",
            default=datetime.date.today().isoformat(),
        ).execute()

    # Prompt for ZIP if not provided
    if zip_code is None:
        while True:
            zip_code = inquirer.text(message="Enter ZIP code (5 digits):").execute()
            if zip_code.isdigit() and len(zip_code) == 5:
                break
            console.print("[red]Invalid ZIP code. Please enter 5 digits.[/red]")

    start_date = dt.fromisoformat(date)
    lat, lon, location = get_coords(zip_code)

    # Interactive choice for number of days (if not provided)
    if days is None:
        console.print("\n[bold purple]🦇 Bark at the Moon - Paranormal Research[/bold purple]")
        console.print("[dim]Use arrow keys or Tab to select, Enter to confirm[/dim]\n")
        console.print(Panel.fit(
            "[bold magenta]Select your moon report:[/bold magenta]",
            border_style="purple", title="🌙 Moonphase CLI", subtitle="🦇"
        ))

        choice = inquirer.select(
            message="Choose a report:",
            choices=[
                {"name": "🌙  1 Day (Today)", "value": 1},
                {"name": "📅  7 Days (Weekly Calendar)", "value": 7},
            ],
            default=1,
            pointer="👉",
        ).execute()
        days = int(choice)

    # Prompt for HTML save if not specified
    if html_file is None:
        save_choice = inquirer.confirm(message="Would you like to save this as HTML?", default=True).execute()
        if save_choice:
            html_file = inquirer.text(
                message="Enter filename (default: moonphase_report.html):",
                default="moonphase_report.html"
            ).execute()

    ask_html = bool(html_file)
    if days > 1:
        print_week(start_date, days, lat, lon, location, ask_html, html_file or "moonphase_report.html")
    else:
        print_single(start_date, lat, lon, location, ask_html, html_file or "moonphase_report.html")


if __name__ == "__main__":
    main()