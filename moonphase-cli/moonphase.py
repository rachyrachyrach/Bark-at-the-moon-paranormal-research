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

# ---------------- ZIP + COUNTY LOOKUP (with caching) ----------------
_zip_cache = None

def get_county_from_zip(zip_code):
    """
    Look up county and state for a given ZIP using the USCities.json dataset.
    Caches the JSON in memory so it's only read once.
    """
    global _zip_cache
    if _zip_cache is None:
        try:
            with open(ZIP_DB, "r", encoding="utf-8") as f:
                _zip_cache = json.load(f)
        except Exception as e:
            console.print(f"[red]Error reading ZIP database: {e}[/red]")
            _zip_cache = []

    for entry in _zip_cache:
        if entry.get("zip_code") == zip_code:
            county = entry.get("county", "Unknown County")
            state = entry.get("state", "Unknown")
            return county, state
    return "Unknown County", "Unknown"

# ---------------- CRIME DATA ----------------
def fetch_fbi_crime_data(state_abbr, county_name, api_key):
    """Fetch recent violent crime totals for the given state (county-level not available directly)."""
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

# ---------------- MOON CALCULATIONS ----------------
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

# ---------------- HTML GENERATION ----------------
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

# ---------------- TERMINAL OUTPUT ----------------
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

# ---------------- CLI ENTRY ----------------
@click.command()
@click.option("--date", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--zip", "zip_code", default=None, help="US ZIP code for location")
@click.option("--days", default=None, type=int, help="Number of days (1 or 7)")
@click.option("--html", "html_file", default=None, help="Optional filename to save as HTML")
def main(date, zip_code, days, html_file):
    # Ask for date & ZIP
    if date is None:
        date = inquirer.text("Enter date (YYYY-MM-DD):", default=datetime.date.today().isoformat()).execute()
    if zip_code is None:
        while True:
            zip_code = inquirer.text("Enter ZIP code (5 digits):").execute()
            if zip_code.isdigit() and len(zip_code) == 5:
                break
            console.print("[red]Invalid ZIP code. Please enter 5 digits.[/red]")

    start_date = dt.fromisoformat(date)

    # Get county/state from local JSON (cached)
    county, state_abbr = get_county_from_zip(zip_code)

    # Crime stats
    crime_text = ""
    crime_choice = inquirer.confirm("Would you like to fetch FBI crime stats for this ZIP's county?", default=False).execute()
    if crime_choice:
        api_key = os.getenv("FBI_API_KEY")
        if not api_key:
            api_key = inquirer.text("Enter your FBI API key (leave blank to skip):", default="").execute()
        if api_key and state_abbr != "Unknown":
            total, details = fetch_fbi_crime_data(state_abbr, county, api_key)
            if total:
                crime_text = f"[bold magenta]FBI Crime Stats[/bold magenta]: ~[yellow]{total}[/yellow] violent crimes (2021–2022) in {county}, {state_abbr}"
            else:
                crime_text = f"[red]Could not fetch FBI data: {details}[/red]"
        else:
            crime_text = "[yellow]County not found for this ZIP — skipping FBI data.[/yellow]"

    # Default to single-day report
    if days is None:
        days = 1

    # HTML output prompt
    if html_file is None:
        save_choice = inquirer.confirm("Would you like to save this as HTML?", default=True).execute()
        if save_choice:
            html_file = inquirer.text("Enter filename:", default="moonphase_report.html").execute()

    # Print the single-day report (multi-day forecast could be added later)
    print_single(start_date, 40.0985, -83.1537, f"{county}, {state_abbr}", bool(html_file), html_file or "moonphase_report.html", crime_text)

if __name__ == "__main__":
    main()