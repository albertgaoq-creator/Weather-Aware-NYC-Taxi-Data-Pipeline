from __future__ import annotations

import argparse
import calendar
import json
from pathlib import Path

import requests

from src.config.settings import BOROUGH_ANCHORS, get_settings
from src.utils.logging import get_logger


LOGGER = get_logger(__name__)
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
HOURLY_FIELDS = "temperature_2m,precipitation,rain,snowfall,windspeed_10m,weathercode"


def month_date_range(month: str) -> tuple[str, str]:
    year, month_number = [int(part) for part in month.split("-")]
    _, last_day = calendar.monthrange(year, month_number)
    return f"{year:04d}-{month_number:02d}-01", f"{year:04d}-{month_number:02d}-{last_day:02d}"


def build_weather_output_path(month: str, borough: str) -> Path:
    settings = get_settings()
    year, month_number = [int(part) for part in month.split("-")]
    borough_slug = borough.lower().replace(" ", "_")
    return (
        settings.raw_dir
        / "weather"
        / f"year={year}"
        / f"month={month_number:02d}"
        / f"{borough_slug}.json"
    )


def download_weather_month(month: str, force: bool = False) -> list[Path]:
    settings = get_settings()
    start_date, end_date = month_date_range(month)
    saved_files: list[Path] = []

    for borough, (latitude, longitude) in BOROUGH_ANCHORS.items():
        output_path = build_weather_output_path(month=month, borough=borough)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists() and not force:
            LOGGER.info("Weather file already exists at %s", output_path)
            saved_files.append(output_path)
            continue

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": HOURLY_FIELDS,
            "timezone": settings.timezone,
        }
        response = requests.get(OPEN_METEO_URL, params=params, timeout=120)
        response.raise_for_status()
        payload = response.json()
        payload["requested_borough"] = borough
        payload["requested_month"] = month
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        LOGGER.info("Downloaded weather for %s to %s", borough, output_path)
        saved_files.append(output_path)

    return saved_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Download hourly Open-Meteo weather data.")
    parser.add_argument("--month", required=True, help="Month in YYYY-MM format.")
    parser.add_argument("--force", action="store_true", help="Re-download the source files.")
    args = parser.parse_args()

    download_weather_month(month=args.month, force=args.force)


if __name__ == "__main__":
    main()
