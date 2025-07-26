#!/usr/bin/env python3
import requests
import datetime
from datetime import datetime as dt, timedelta
import click
import ephem
from rich.console import Console

console = Console()

# Get coordinates for ZIP codes (for rise/set times)
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
    """Look up latitude, longitude, and place name for a ZIP code."""
    res = requests.get(ZIP_COORDS_API.format(zip=zip_code))
    res.raise_for_status()
    data = res.json()
    place = data['places'][0]
    lat = float(place['latitude'])
    lon = float(place['longitude'])
    loc = f"{place['place name']}, {place['state abbreviation']}"
    return lat, lon, loc

def phase_name_and_illumination(date):
    """Return the phase name and illumination percentage for a given date."""
    moon = ephem.Moon(date)
    illum = moon.phase  # percentage illuminated
    # Find position within lunation cycle (new moon to next new moon)
    prev_new = ephem.previous_new_moon(date)
    lunation_days = (date - prev_new.datetime()).days + (date - prev_new.datetime()).seconds / 86400
    fraction = lunation_days / 29.53

    # Determine phase category
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
    """Calculate moonrise and moonset times for a location on a date."""
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

def print_single(date, lat, lon, location):
    name, illum = phase_name_and_illumination(date)
    rise, sett = moonrise_moonset(date, lat, lon)
    emoji = PHASE_EMOJI.get(name, "🌙")
    art = ASCII_MOONS.get(name, "")

    console.print(f"{emoji} [bold cyan]{name}[/bold cyan] on [bold]{date.strftime('%Y-%m-%d')}[/bold] for {location}")
    console.print(f"Illumination: {illum}%")
    console.print(f"Moonrise: {rise}, Moonset: {sett}")
    console.print(f"[bold yellow]{art}[/bold yellow]")

def print_week(start_date, days, lat, lon, location):
    console.print(f"\n[bold magenta]Moon Phases for {location}[/bold magenta]\n")
    console.print("[bold]Date         Phase               Illum    Rise    Set[/bold]")
    console.print("--------------------------------------------------------------")
    for i in range(days):
        day = start_date + timedelta(days=i)
        name, illum = phase_name_and_illumination(day)
        rise, sett = moonrise_moonset(day, lat, lon)
        emoji = PHASE_EMOJI.get(name, "🌙")
        console.print(f"{day.strftime('%Y-%m-%d')}   {emoji} {name:<18}  {illum:5.1f}%  {rise:<5}  {sett:<5}")

@click.command()
@click.option('--date', default=datetime.date.today().isoformat(),
              help='Start date (YYYY-MM-DD)')
@click.option('--zip', 'zip_code', required=True,
              help='US ZIP code for location and rise/set')
@click.option('--days', default=1, type=int,
              help='Number of days (1 = single day, >1 = weekly calendar)')
def main(date, zip_code, days):
    start_date = dt.fromisoformat(date)
    lat, lon, location = get_coords(zip_code)
    if days > 1:
        print_week(start_date, days, lat, lon, location)
    else:
        print_single(start_date, lat, lon, location)

if __name__ == '__main__':
    main()