#!/usr/bin/env python3
import datetime
from datetime import datetime as dt, timedelta
import click
import ephem
from rich.console import Console

console = Console()

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

def phase_name(date):
    """Return the phase name and illumination percentage for a given date."""
    moon = ephem.Moon(date)
    illum = moon.phase  # illumination percentage
    # Determine rough phase based on illumination and waxing/waning
    age = ephem.previous_new_moon(date)
    lunation = (date - age.datetime()).days + (date - age.datetime()).seconds / 86400
    cycle = 29.53
    fraction = lunation / cycle

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

def print_day(date):
    name, illum = phase_name(date)
    emoji = PHASE_EMOJI.get(name, "🌙")
    art = ASCII_MOONS.get(name, "")
    console.print(f"{emoji} [bold cyan]{name}[/bold cyan] on [bold]{date.strftime('%Y-%m-%d')}[/bold]")
    console.print(f"Illumination: {illum}%")
    console.print(f"[bold yellow]{art}[/bold yellow]")

def print_week(start_date, days):
    console.print(f"\n[bold magenta]Moon Phases[/bold magenta]\n")
    console.print("[bold]Date         Phase               Illumination[/bold]")
    console.print("------------------------------------------------------")
    for i in range(days):
        day = start_date + timedelta(days=i)
        name, illum = phase_name(day)
        emoji = PHASE_EMOJI.get(name, "🌙")
        console.print(f"{day.strftime('%Y-%m-%d')}   {emoji} {name:<20}  {illum:>5.1f}%")

@click.command()
@click.option('--date', default=datetime.date.today().isoformat(),
              help='Start date (YYYY-MM-DD)')
@click.option('--days', default=1, type=int,
              help='Number of days (1 = single day, >1 = calendar)')
def main(date, days):
    start_date = dt.fromisoformat(date)
    if days > 1:
        print_week(start_date, days)
    else:
        print_day(start_date)

if __name__ == '__main__':
    main()