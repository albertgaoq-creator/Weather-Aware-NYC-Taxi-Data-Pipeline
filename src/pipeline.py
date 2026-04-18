from __future__ import annotations

import argparse
import os
import subprocess

from src.ingestion.lookup import download_zone_lookup
from src.ingestion.taxi import download_taxi_month
from src.ingestion.weather import download_weather_month
from src.loaders.postgres import bootstrap_warehouse, load_lookup, load_taxi_month, load_weather_month
from src.processing.preprocess_taxi import preprocess_taxi_month
from src.processing.preprocess_weather import preprocess_weather_month
from src.quality.checks import run_raw_file_checks, run_warehouse_checks
from src.utils.logging import get_logger


LOGGER = get_logger(__name__)


def run_dbt(command: str) -> None:
    env = os.environ.copy()
    env.setdefault("DBT_PROFILES_DIR", "dbt")
    subprocess.run(
        ["dbt", command, "--project-dir", "dbt", "--profiles-dir", "dbt"],
        check=True,
        env=env,
    )


def run_month(month: str, dataset: str = "yellow", skip_dbt: bool = False) -> None:
    LOGGER.info("Starting pipeline for %s", month)
    download_zone_lookup()
    download_taxi_month(month=month, dataset=dataset)
    download_weather_month(month=month)
    preprocess_taxi_month(month=month, dataset=dataset)
    preprocess_weather_month(month=month)
    run_raw_file_checks(month=month)
    bootstrap_warehouse()
    load_lookup()
    load_taxi_month(month=month, dataset=dataset)
    load_weather_month(month=month)
    if not skip_dbt:
        run_dbt("run")
        run_dbt("test")
    run_warehouse_checks(month=month)
    LOGGER.info("Pipeline completed for %s", month)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the weather-aware taxi pipeline end to end.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap_parser = subparsers.add_parser("bootstrap", help="Create PostgreSQL schemas and tables.")
    bootstrap_parser.set_defaults(handler=lambda args: bootstrap_warehouse())

    run_month_parser = subparsers.add_parser("run-month", help="Run the full pipeline for one month.")
    run_month_parser.add_argument("--month", required=True, help="Month in YYYY-MM format.")
    run_month_parser.add_argument("--dataset", default="yellow")
    run_month_parser.add_argument("--skip-dbt", action="store_true")
    run_month_parser.set_defaults(handler=lambda args: run_month(args.month, dataset=args.dataset, skip_dbt=args.skip_dbt))

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
