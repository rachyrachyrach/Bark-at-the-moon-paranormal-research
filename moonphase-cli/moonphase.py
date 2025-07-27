#!/usr/bin/env python3
import os
import json
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

ZIP_DB = os.path.join(os.path.dirname(__file__), "USCities.json")
ZIP_CACHE = os.path.join(os.path.dirname(__file__), ".zipcache.json")
FBI_BASE_URL = "https://api.usa.gov/crime/fbi/cde"


OFFENSE_CODES = {
    "violent-crime": "V",
    "property-crime": "P",
    "homicide": "HOM",
    "arson": "ARS",
    "assault": "ASS",
    "burglary": "BUR",
    "larceny": "LAR",
    "motor-vehicle-theft": "MVT",
    "robbery": "ROB",
}

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

_zip_cache = None

def load_zip_cache():
    global _zip_cache
    if _zip_cache is not None:
        return _zip_cache
    if os.path.exists(ZIP_CACHE):
        try:
            with open(ZIP_CACHE, "r", encoding="utf-8") as f:
                _zip_cache = json.load(f)
                return _zip_cache
        except Exception:
            console.print("[red]Error reading .zipcache.json, rebuilding cache...[/red]")

    console.print("[yellow]Building ZIP cache from USCities.json (one-time)...[/yellow]")
    _zip_cache = {}
    try:
        with open(ZIP_DB, "r", encoding="utf-8") as f:
            records = json.load(f)
        for entry in records:
            z = entry.get("zip_code")
            if z:
                _zip_cache[z] = {
                    "county": entry.get("county", "Unknown County"),
                    "state": entry.get("state", "Unknown"),
                    "lat": entry.get("latitude"),
                    "lon": entry.get("longitude")
                }
        with open(ZIP_CACHE, "w", encoding="utf-8") as f:
            json.dump(_zip_cache, f)
    except Exception as e:
        console.print(f"[red]Error building ZIP cache: {e}[/red]")
        _zip_cache = {}

    return _zip_cache

def get_county_from_zip(zip_code):
    cache = load_zip_cache()
    if zip_code in cache:
        c = cache[zip_code]
        return c["county"], c["state"], c["lat"], c["lon"]
    return "Unknown County", "Unknown", 0.0, 0.0

def fetch_fbi_crime_data(state_abbr, offense, year, api_key):
    headers = {"x-api-key": api_key}
    attempted_years = [year, year - 1]
    offense_code = OFFENSE_CODES.get(offense, offense)

    for attempt_year in attempted_years:
        try:
            # Handle hate-crime separately
            if offense == "hate-crime":
                from_date = f"01-{attempt_year}"
                to_date = f"12-{attempt_year}"
                url = f"{FBI_BASE_URL}/hate-crime/state/{state_abbr.upper()}?type=counts&from={from_date}&to={to_date}&API_KEY={api_key}"
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code in (403, 404):
                    continue
                res.raise_for_status()
                data = res.json()
                offenses = data.get("actuals", {}).get("Ohio Offenses", {})
                incidents = data.get("actuals", {}).get("Ohio Incidents", {})
                total = sum(v for v in offenses.values() if isinstance(v, (int, float)))
                if total == 0:
                    continue

                month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                month_table = Table(title=f"Hate Crime Data {attempt_year}", title_style="bold yellow")
                month_table.add_column("Month", style="cyan")
                month_table.add_column("Offenses", style="magenta", justify="right")
                month_table.add_column("Incidents", style="green", justify="right")
                offenses_total = incidents_total = 0
                missing_months = []
                for idx, m in enumerate(month_names, start=1):
                    key = f"{idx:02d}-{attempt_year}"
                    off_val = offenses.get(key)
                    inc_val = incidents.get(key)
                    off_str = f"[green]{off_val}[/green]" if isinstance(off_val, (int, float)) else "[red]N/A[/red]"
                    inc_str = f"[green]{inc_val}[/green]" if isinstance(inc_val, (int, float)) else "[red]N/A[/red]"
                    if isinstance(off_val, (int, float)):
                        offenses_total += off_val
                    else:
                        missing_months.append(m)
                    if isinstance(inc_val, (int, float)):
                        incidents_total += inc_val
                    month_table.add_row(m, off_str, inc_str)
                note = f"{attempt_year} (partial)" if missing_months else str(attempt_year)
                month_table.add_row("[bold]Total[/bold]",
                                    f"[bold yellow]{offenses_total}[/bold yellow]",
                                    f"[bold yellow]{incidents_total}[/bold yellow]")
                return total, note, month_table

            # For all other offenses
            from_date = f"01-{attempt_year}"
            to_date = f"12-{attempt_year}"
            url = f"{FBI_BASE_URL}/summarized/state/{state_abbr.upper()}/{offense_code}?from={from_date}&to={to_date}&API_KEY={api_key}"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code in (403, 404):
                continue
            res.raise_for_status()
            data = res.json()

            # New format: nested `offenses.actuals.Ohio`
            actuals = data.get("offenses", {}).get("actuals", {}).get("Ohio", {})
            if actuals:
                month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                month_table = Table(title=f"{offense_code} Data {attempt_year}", title_style="bold yellow")
                month_table.add_column("Month", style="cyan")
                month_table.add_column("Offenses", style="magenta", justify="right")
                offenses_total = 0
                missing_months = []
                for idx, m in enumerate(month_names, start=1):
                    key = f"{idx:02d}-{attempt_year}"
                    val = actuals.get(key)
                    if isinstance(val, (int, float)):
                        offenses_total += val
                        val_str = f"[green]{val}[/green]"
                    else:
                        val_str = "[red]N/A[/red]"
                        missing_months.append(m)
                    month_table.add_row(m, val_str)
                note = f"{attempt_year} (partial)" if missing_months else str(attempt_year)
                month_table.add_row("[bold]Total[/bold]", f"{offenses_total}")
                return offenses_total, note, month_table

            # Legacy format: `results` array
            results = data.get("results", [])
            if results:
                month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                month_table = Table(title=f"{offense.replace('-', ' ').title()} Data {attempt_year}", title_style="bold yellow")
                month_table.add_column("Month", style="cyan")
                month_table.add_column("Offenses", style="magenta", justify="right")
                offenses_total = 0
                month_data = {int(item.get("month", 0)): item.get("actual") for item in results}
                missing_months = []
                for idx, m in enumerate(month_names, start=1):
                    val = month_data.get(idx)
                    if isinstance(val, (int, float)):
                        offenses_total += val
                        val_str = f"[green]{val}[/green]"
                    else:
                        val_str = "[red]N/A[/red]"
                        missing_months.append(m)
                    month_table.add_row(m, val_str)
                note = f"{attempt_year} (partial)" if missing_months else str(attempt_year)
                month_table.add_row("[bold]Total[/bold]", f"[bold yellow]{offenses_total}[/bold yellow]")
                return offenses_total, note, month_table

        except Exception:
            continue

    return None, f"No FBI crime data available for {state_abbr} near {year}.", None

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

def generate_html_single(date, name, illum, rise, sett, location, emoji, art, crime_text, filename, month_table=None):
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
  .crime {{ margin-top: 20px; color: #f1fa8c; }}
  table {{ border-collapse: collapse; margin-top: 20px; width: 100%; max-width: 500px; color: #f8f8f2; margin-left: auto; margin-right: auto; }}
  th, td {{ border: 1px solid #bd93f9; padding: 8px; text-align: right; }}
  th {{ background-color: #44475a; text-align: center; }}
  caption {{ margin-bottom: 10px; font-weight: bold; color: #50fa7b; }}
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
"""

    # Render month_table as an actual HTML table
    if month_table:
        html += "<table>\n"
        # Use the table title as a caption
        if month_table.title:
            html += f"<caption>{month_table.title}</caption>\n"
        # Add headers if the Rich Table has columns
        if month_table.columns:
            html += "<tr>"
            for col in month_table.columns:
                html += f"<th>{col.header}</th>"
            html += "</tr>\n"
        # Add data rows
        for row in month_table.rows:
            html += "<tr>"
            # Safely convert each cell
            for cell in getattr(row, "_cells", []):
                html += f"<td>{cell}</td>"
            html += "</tr>\n"
        html += "</table>\n"

    html += "</body>\n</html>"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    console.print(f"[green]Saved HTML report to [bold]{filename}[/bold][/green]")
def print_single(date, lat, lon, location, crime_text, month_table=None, ask_html=False, html_filename="moonphase_report.html"):
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
        generate_html_single(date.strftime("%Y-%m-%d"), name, illum, rise, sett, location, emoji, art, crime_text, html_filename, month_table)

def print_week(start_date, lat, lon, location, crime_text, days=7):
    table = Table(title=f"🦇 Moon Phases for {location}", title_style="bold magenta")
    table.add_column("Date", style="cyan", justify="center")
    table.add_column("Phase", style="magenta", justify="left")
    table.add_column("Illum", style="yellow", justify="center")
    table.add_column("Rise", style="green", justify="center")
    table.add_column("Set", style="red", justify="center")

    for i in range(days):
        d = start_date + timedelta(days=i)
        name, illum = phase_name_and_illumination(d)
        rise, sett = moonrise_moonset(d, lat, lon)
        emoji = PHASE_EMOJI.get(name, "🌙")
        table.add_row(d.strftime("%Y-%m-%d"), f"{emoji} {name}", f"{illum:.1f}%", rise, sett)

    console.print(table)
    if crime_text:
        console.print(f"\n[dim]{crime_text}[/dim]\n")

@click.command()
@click.option("--date", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--zip", "zip_code", default=None, help="US ZIP code")
@click.option("--days", default=None, type=int, help="1 for single-day, 7 for weekly")
@click.option("--html", "html_file", default=None, help="Save output as HTML file")
def main(date, zip_code, days, html_file):
    if date is None:
        date = inquirer.text("Enter date (YYYY-MM-DD):", default=datetime.date.today().isoformat()).execute()
    if zip_code is None:
        while True:
            zip_code = inquirer.text("Enter ZIP code (5 digits):").execute()
            if zip_code.isdigit() and len(zip_code) == 5:
                break
            console.print("[red]Invalid ZIP code. Please enter 5 digits.[/red]")

    start_date = dt.fromisoformat(date)
    year = start_date.year
    county, state_abbr, lat, lon = get_county_from_zip(zip_code)
    location = f"{county}, {state_abbr}" if county != "Unknown County" else f"ZIP {zip_code}"

    crime_text = ""
    crime_choice = inquirer.confirm("Fetch FBI crime stats for this state?", default=False).execute()
    if crime_choice:

        offense_options = [
            {"name": "🗡 Violent Crime", "value": "V"},
            {"name": "🏠 Property Crime", "value": "P"},
            {"name": "🔪 Homicide", "value": "HOM"},
            {"name": "🔥 Arson", "value": "ARS"},
            {"name": "💀 Hate Crime", "value": "hate-crime"}  
        ]
        offense_code = inquirer.select(
            message="Which offense type?",
            choices=offense_options,
            default="V",
            pointer="👉"
        ).execute()

        
        offense_choice = offense_code if offense_code != "hate-crime" else "hate-crime"

        api_key = os.getenv("FBI_API_KEY")
        if not api_key:
            api_key = inquirer.text("Enter FBI API key (leave blank to skip):", default="").execute()
        if api_key and state_abbr != "Unknown":
            total, note, month_table = fetch_fbi_crime_data(state_abbr, offense_choice, year, api_key)
            if total:
                # For label, display the pretty name from offense_options
                display_name = next((item["name"] for item in offense_options if item["value"] == offense_code), offense_choice.replace('-', ' ').title())
                crime_text = f"FBI Crime Stats: ~{total} {display_name} incidents in {state_abbr} ({note})"
                if month_table:
                    console.print(month_table)
            elif note:
                crime_text = f"[red]{note}[/red]"

    if days is None:
        choice = inquirer.select(
            message="Choose a report:",
            choices=[{"name": "🌙 1 Day", "value": 1}, {"name": "📅 7 Days (Weekly Calendar)", "value": 7}],
            default=1,
            pointer="👉"
        ).execute()
        days = int(choice)

    if html_file is None:
        save_choice = inquirer.confirm("Would you like to save this as HTML?", default=True).execute()
        if save_choice:
            html_file = inquirer.text("Enter filename:", default="moonphase_report.html").execute()

    if days > 1:
        print_week(start_date, lat, lon, location, crime_text, days)
    else:
        print_single(start_date, lat, lon, location, crime_text, month_table, ask_html=bool(html_file), html_filename=html_file or "moonphase_report.html")

if __name__ == "__main__":
    main()