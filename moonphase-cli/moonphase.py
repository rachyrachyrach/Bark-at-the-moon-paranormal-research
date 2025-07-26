#!/usr/bin/env python3
import requests
import datetime
from datetime import datetime as dt, timedelta
import click
from rich.console import Console

console = Console()

ZIP_COORDS_API = "http://api.zippopotam.us/us/{zip}"
OPEN_METEO_API = (
    "https://api.open-meteo.com/v1/forecast?"
    "latitude={lat}&longitude={lon}"
    "&daily=moon_phase,moonrise,moonset&timezone=auto"
    "&start_date={start}&end_date={end}"
)

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

def fetch_phase_data(start, end, lat, lon):
    url = OPEN_METEO_API.format(lat=lat, lon=lon, start=start, end=end)
    res = requests.get(url)
    res.raise_for_status()
    return res.json()

def phase_name_from_value(val):
    # Map numeric phase to descriptive name
    if val == 0 or val == 1:
        return "New Moon"
    if val == 0.25:
        return "First Quarter"
    if val == 0.5:
        return "Full Moon"
    if val == 0.75:
        return "Last Quarter"
    if 0 < val < 0.25:
        return "Waxing Crescent"
    if 0.25 < val < 0.5:
        return "Waxing Gibbous"
    if 0.5 < val < 0.75:
        return "Waning Gibbous"
    if 0.75 < val < 1:
        return "Waning Crescent"
    return "Unknown"

def print_week(start_date, days, lat, lon, location):
    end_date = (dt.fromisoformat(start_date) + timedelta(days=days-1)).date().isoformat()
    data = fetch_phase_data(start_date, end_date, lat, lon)
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    phases = daily.get("moon_phase", [])
    rises = daily.get("moonrise", [])
    sets = daily.get("moonset", [])

    console.print(f"\n[bold magenta]Moon Phases for {location}[/bold magenta]\n")
    console.print("[bold]Date         Phase             Rise     Set[/bold]")
    console.print("------------------------------------------------")
    for d, val, r, s in zip(dates, phases, rises, sets):
        name = phase_name_from_value(val)
        emoji = PHASE_EMOJI.get(name, "🌙")
        art = ASCII_MOONS.get(name, "   ●   ")
        # convert unix timestamps into local time string
        rise = dt.fromtimestamp(r).strftime("%H:%M") if r else "N/A"
        sett = dt.fromtimestamp(s).strftime("%H:%M") if s else "N/A"
        console.print(f"{d}   {emoji} {name:<16}  {rise:<7}  {sett:<7}")

def print_single(date, lat, lon, location):
    data = fetch_phase_data(date, date, lat, lon)
    d = data["daily"]["time"][0]
    val = data["daily"]["moon_phase"][0]
    r = data["daily"]["moonrise"][0]
    s = data["daily"]["moonset"][0]
    name = phase_name_from_value(val)
    emoji = PHASE_EMOJI.get(name, "🌙")
    art = ASCII_MOONS.get(name, "")
    rise = dt.fromtimestamp(r).strftime("%H:%M") if r else "N/A"
    sett = dt.fromtimestamp(s).strftime("%H:%M") if s else "N/A"
    console.print(f"{emoji} [bold cyan]{name}[/bold cyan] on [bold]{d}[/bold] for {location}")
    console.print(f"Moonrise: {rise}, Moonset: {sett}")
    console.print(f"[bold yellow]{art}[/bold yellow]")

@click.command()
@click.option('--date', default=datetime.date.today().isoformat(),
              help='Start date (YYYY-MM-DD)')
@click.option('--zip', 'zip_code', required=True, help='US ZIP code')
@click.option('--days', default=1, type=int,
              help='Number of days (1 = single day, >1 = calendar)')
def main(date, zip_code, days):
    lat, lon, location = get_coords(zip_code)
    if days > 1:
        print_week(date, days, lat, lon, location)
    else:
        print_single(date, lat, lon, location)

if __name__ == '__main__':
    main()