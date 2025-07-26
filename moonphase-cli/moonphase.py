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
from InquirerPy.utils import get_style

console = Console()

# API for ZIP → Coordinates (for rise/set times)
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
    place = data["places"][0]
    lat = float(place["latitude"])
    lon = float(place["longitude"])
    loc = f"{place['place name']}, {place['state abbreviation']}"
    return lat, lon, loc


def phase_name_and_illumination(date):
    """Return the phase name and illumination percentage for a given date."""
    moon = ephem.Moon(date)
    illum = moon.phase
    prev_new = ephem.previous_new_moon(date)
    lunation_days = (date - prev_new.datetime()).days + (
        date - prev_new.datetime()
    ).seconds / 86400
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
    """Print a single day's moon info with ASCII art."""
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


def print_week(start_date, days, lat, lon, location):
    """Print a 7-day (or multi-day) forecast in a spooky table."""
    table = Table(title=f"🦇 Moon Phases for {location}", title_style="bold magenta")
    table.add_column("Date", style="cyan", justify="center")
    table.add_column("Phase", style="magenta", justify="left")
    table.add_column("Illum", style="yellow", justify="center")
    table.add_column("Rise", style="green", justify="center")
    table.add_column("Set", style="red", justify="center")

    for i in range(days):
        day = start_date + timedelta(days=i)
        name, illum = phase_name_and_illumination(day)
        rise, sett = moonrise_moonset(day, lat, lon)
        emoji = PHASE_EMOJI.get(name, "🌙")
        table.add_row(
            day.strftime("%Y-%m-%d"),
            f"{emoji} {name}",
            f"{illum:.1f}%",
            rise,
            sett,
        )

    console.print(table)


@click.command()
@click.option(
    "--date", default=datetime.date.today().isoformat(), help="Start date (YYYY-MM-DD)"
)
@click.option("--zip", "zip_code", required=True, help="US ZIP code for location")
@click.option(
    "--days", default=None, type=int, help="Number of days (if skipped, interactive menu)"
)
def main(date, zip_code, days):
    start_date = dt.fromisoformat(date)
    lat, lon, location = get_coords(zip_code)

    # Interactive Dracula-style menu if --days isn't provided
    if days is None:
        console.print("\n[bold purple]🦇 Bark at the Moon - Paranormal Research[/bold purple]")
        console.print("[dim]Use arrow keys or Tab to select, Enter to confirm[/dim]\n")

        console.print(
            Panel.fit(
                "[bold magenta]Select your moon report:[/bold magenta]",
                border_style="purple",
                title="🌙 Moonphase CLI",
                subtitle="🦇",
            )
        )

        custom_style = get_style(
            {
                "question": "#bd93f9 bold",
                "pointer": "#ff79c6 bold",
                "highlighted": "#50fa7b bold",
                "selected": "#8be9fd bold",
                "instruction": "italic #f1fa8c",
            }
        )

        choice = inquirer.select(
            message="Choose a report:",
            choices=[
                {"name": "🌙  1 Day (Today)", "value": 1},
                {"name": "📅  7 Days (Weekly Calendar)", "value": 7},
            ],
            default=1,
            pointer="👉",
            style=custom_style,
        ).execute()

        days = int(choice)

    # Run the report
    if days > 1:
        print_week(start_date, days, lat, lon, location)
    else:
        print_single(start_date, lat, lon, location)


if __name__ == "__main__":
    main()