from __future__ import annotations

import argparse
import calendar
from pathlib import Path

import requests

from src.config.settings import get_settings
from src.utils.logging import get_logger


LOGGER = get_logger(__name__)
TAXI_URL_TEMPLATE = "https://d37ci6vzurychx.cloudfront.net/trip-data/{dataset}_tripdata_{month}.parquet"


def month_components(month: str) -> tuple[int, int]:
    year, month_number = month.split("-")
    return int(year), int(month_number)


def build_taxi_output_path(month: str, dataset: str = "yellow") -> Path:
    settings = get_settings()
    year, month_number = month_components(month)
    return (
        settings.raw_dir
        / "taxi"
        / dataset
        / f"year={year}"
        / f"month={month_number:02d}"
        / f"{dataset}_tripdata_{month}.parquet"
    )


def download_taxi_month(month: str, dataset: str = "yellow", force: bool = False) -> Path:
    output_path = build_taxi_output_path(month=month, dataset=dataset)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not force:
        LOGGER.info("Taxi file already exists at %s", output_path)
        return output_path

    url = TAXI_URL_TEMPLATE.format(dataset=dataset, month=month)
    LOGGER.info("Downloading %s taxi data for %s", dataset, month)
    with requests.get(url, stream=True, timeout=600) as response:
        response.raise_for_status()
        with output_path.open("wb") as file_handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file_handle.write(chunk)

    LOGGER.info("Downloaded %s", output_path)
    return output_path


def month_date_range(month: str) -> tuple[str, str]:
    year, month_number = month_components(month)
    _, last_day = calendar.monthrange(year, month_number)
    return f"{year:04d}-{month_number:02d}-01", f"{year:04d}-{month_number:02d}-{last_day:02d}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a monthly NYC taxi parquet file.")
    parser.add_argument("--month", required=True, help="Month in YYYY-MM format.")
    parser.add_argument("--dataset", default="yellow", help="Taxi dataset, defaults to yellow.")
    parser.add_argument("--force", action="store_true", help="Re-download the source file.")
    args = parser.parse_args()

    download_taxi_month(month=args.month, dataset=args.dataset, force=args.force)


if __name__ == "__main__":
    main()
