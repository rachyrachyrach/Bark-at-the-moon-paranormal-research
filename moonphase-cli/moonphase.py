#!/usr/bin/env python3
import os
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
ZIP_COUNTY_API = "https://public.opendatasoft.com/api/records/1.0/search/?dataset=us-zip-code-latitude-and-longitude&q={zip}"
FBI_BASE_URL = "https://api.usa.gov/crime/fbi/sapi/api"

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
    place = data["places"][0]
    lat = float(place["latitude"])
    lon = float(place["longitude"])
    loc = f"{place['place name']}, {place['state abbreviation']}"
    return lat, lon, loc, place["state abbreviation"]


def get_county_from_zip(zip_code):
    res = requests.get(ZIP_COUNTY_API.format(zip=zip_code))
    res.raise_for_status()
    records = res.json().get("records", [])
    if records:
        fields = records[0].get("fields", {})
        return fields.get("county", "Unknown County")
    return "Unknown County"


def fetch_fbi_crime_data(state_abbr, county_name, api_key):
    """Fetch recent violent crime summary for the given state/county."""
    county_clean = county_name.replace(" County", "").upper()
    headers = {"x-api-key": api_key}
    url = f"{FBI_BASE_URL}/summarized/state/{state_abbr.lower()}/violent-crime/2021/2022"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        results = res.json().get("results", [])
        total = sum(item.get("actual", 0) for item in results)
        return total, results
    except Exception as e:
        return None, str(e)


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


def generate_html_single(date, name, illum, rise, sett, location, emoji, art, crime_text, filename):
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
  .crime {{ margin-top: 20px; color: #f1fa8c; }}
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
  <div class="crime">{crime_text}</div>
</div>
</body>
</html>"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    console.print(f"[green]Saved HTML report to [bold]{filename}[/bold][/green]")


def print_single(date, lat, lon, location, ask_html, html_filename, crime_text):
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
            f"[bold yellow]{art}[/bold yellow]\n\n"
            f"{crime_text}",
            border_style="purple",
            title="🌙 Moonphase Report",
            subtitle="🦇",
        )
    )

    if ask_html:
        generate_html_single(date.strftime("%Y-%m-%d"), name, illum, rise, sett, location, emoji, art, crime_text, html_filename)


@click.command()
@click.option("--date", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--zip", "zip_code", default=None, help="US ZIP code for location")
@click.option("--days", default=None, type=int, help="Number of days (1 or 7)")
@click.option("--html", "html_file", default=None, help="Optional filename to save as HTML")
def main(date, zip_code, days, html_file):
    # Prompt for date/ZIP if not provided
    if date is None:
        date = inquirer.text("Enter date (YYYY-MM-DD):", default=datetime.date.today().isoformat()).execute()
    if zip_code is None:
        while True:
            zip_code = inquirer.text("Enter ZIP code (5 digits):").execute()
            if zip_code.isdigit() and len(zip_code) == 5:
                break
            console.print("[red]Invalid ZIP code. Please enter 5 digits.[/red]")

    start_date = dt.fromisoformat(date)
    lat, lon, location, state_abbr = get_coords(zip_code)

    # Crime stats
    crime_text = ""
    crime_choice = inquirer.confirm("Would you like to fetch FBI crime stats for this ZIP's county?", default=False).execute()
    if crime_choice:
        api_key = os.getenv("FBI_API_KEY")
        if not api_key:
            api_key = inquirer.text("Enter your FBI API key (leave blank to skip):", default="").execute()
        if api_key:
            county = get_county_from_zip(zip_code)
            total, details = fetch_fbi_crime_data(state_abbr, county, api_key)
            if total:
                crime_text = f"[bold magenta]FBI Crime Stats[/bold magenta]: ~[yellow]{total}[/yellow] violent crimes (2021-2022) in {county}, {state_abbr}"
            else:
                crime_text = f"[red]Could not fetch FBI data: {details}[/red]"

    # Prompt for days if not specified
    if days is None:
        console.print("\n[bold purple]🦇 Bark at the Moon - Paranormal Research[/bold purple]")
        console.print("[dim]Use arrow keys or Tab to select, Enter to confirm[/dim]\n")
        console.print(Panel.fit("[bold magenta]Select your moon report:[/bold magenta]", border_style="purple", title="🌙 Moonphase CLI", subtitle="🦇"))
        choice = inquirer.select(
            message="Choose a report:",
            choices=[{"name": "🌙  1 Day (Today)", "value": 1}, {"name": "📅  7 Days (Weekly Calendar)", "value": 7}],
            default=1,
            pointer="👉",
        ).execute()
        days = int(choice)

    # Prompt for HTML save
    if html_file is None:
        save_choice = inquirer.confirm("Would you like to save this as HTML?", default=True).execute()
        if save_choice:
            html_file = inquirer.text("Enter filename:", default="moonphase_report.html").execute()

    ask_html = bool(html_file)

    if days > 1:
        # For now, only single-day has crime data integrated
        console.print("[yellow]Crime data currently only shown for single-day reports.[/yellow]")
    print_single(start_date, lat, lon, location, ask_html, html_file or "moonphase_report.html", crime_text)


if __name__ == "__main__":
    main()