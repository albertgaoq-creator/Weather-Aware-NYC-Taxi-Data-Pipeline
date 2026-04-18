from __future__ import annotations

import argparse
from calendar import monthrange

import pandas as pd
import psycopg

from src.config.settings import get_settings
from src.utils.logging import get_logger


LOGGER = get_logger(__name__)


class QualityCheckError(RuntimeError):
    pass


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise QualityCheckError(message)


def run_raw_file_checks(month: str) -> None:
    settings = get_settings()
    raw_taxi_path = settings.raw_dir / "taxi" / "yellow" / f"year={month[:4]}" / f"month={month[5:7]}" / f"yellow_tripdata_{month}.parquet"
    raw_weather_path = settings.raw_dir / "weather" / f"year={month[:4]}" / f"month={month[5:7]}"
    raw_lookup_path = settings.raw_dir / "reference" / "taxi_zone_lookup.csv"
    processed_taxi_path = settings.processed_dir / "taxi" / "yellow" / f"yellow_tripdata_{month}.csv"
    processed_weather_path = settings.processed_dir / "weather" / f"weather_{month}.csv"

    for path in [raw_taxi_path, raw_lookup_path, processed_taxi_path, processed_weather_path]:
        _assert(path.exists(), f"Required pipeline artifact is missing: {path}")

    weather_files = list(raw_weather_path.glob("*.json"))
    _assert(len(weather_files) == 5, f"Expected 5 borough weather files, found {len(weather_files)}")

    taxi_df = pd.read_csv(processed_taxi_path, nrows=5000)
    weather_df = pd.read_csv(processed_weather_path)
    required_taxi_columns = {
        "record_hash",
        "pickup_datetime",
        "dropoff_datetime",
        "pickup_location_id",
        "dropoff_location_id",
        "trip_distance",
        "fare_amount",
        "total_amount",
    }
    required_weather_columns = {
        "weather_record_id",
        "borough",
        "weather_ts_hour",
        "temperature_2m",
        "precipitation_mm",
        "weathercode",
    }
    _assert(required_taxi_columns.issubset(taxi_df.columns), "Processed taxi columns are incomplete")
    _assert(required_weather_columns.issubset(weather_df.columns), "Processed weather columns are incomplete")
    _assert(len(weather_df) > 24 * 20, "Weather row count looks suspiciously low")
    LOGGER.info("Raw and processed file checks passed for %s", month)


def _fetch_one(cursor: psycopg.Cursor, sql: str, params: tuple | None = None):
    cursor.execute(sql, params or ())
    row = cursor.fetchone()
    return row[0] if row else None


def run_warehouse_checks(month: str) -> None:
    settings = get_settings()
    year, month_number = [int(part) for part in month.split("-")]
    expected_hours = monthrange(year, month_number)[1] * 24 * 5

    with psycopg.connect(settings.postgres_dsn) as connection:
        with connection.cursor() as cursor:
            taxi_rows = _fetch_one(
                cursor,
                "SELECT COUNT(*) FROM raw.taxi_trips_yellow WHERE ingestion_month = %s",
                (f"{month}-01",),
            )
            weather_rows = _fetch_one(
                cursor,
                "SELECT COUNT(*) FROM raw.weather_hourly WHERE source_month = %s",
                (f"{month}-01",),
            )
            weather_join_coverage = _fetch_one(
                cursor,
                """
                SELECT COALESCE(AVG(CASE WHEN weather_key <> 'unknown' THEN 1.0 ELSE 0.0 END), 0.0)
                FROM mart.fct_taxi_trips
                WHERE DATE_TRUNC('month', pickup_ts_local)::date = %s
                """,
                (f"{month}-01",),
            )
            hourly_consistency_gap = _fetch_one(
                cursor,
                """
                WITH detailed AS (
                    SELECT COUNT(*) AS trip_count
                    FROM mart.fct_taxi_trips
                    WHERE DATE_TRUNC('month', pickup_ts_local)::date = %s
                ),
                aggregated AS (
                    SELECT COALESCE(SUM(trip_count), 0) AS trip_count
                    FROM mart.fct_hourly_demand
                    WHERE DATE_TRUNC('month', pickup_hour)::date = %s
                )
                SELECT detailed.trip_count - aggregated.trip_count
                FROM detailed
                CROSS JOIN aggregated
                """,
                (f"{month}-01", f"{month}-01"),
            )

    _assert(taxi_rows is not None and taxi_rows >= settings.min_taxi_rows, f"Taxi row count too low: {taxi_rows}")
    _assert(weather_rows is not None and weather_rows >= expected_hours * 0.95, f"Weather row count too low: {weather_rows}")
    _assert(
        weather_join_coverage is not None and weather_join_coverage >= settings.min_weather_join_coverage,
        f"Weather join coverage below threshold: {weather_join_coverage}",
    )
    _assert(hourly_consistency_gap == 0, f"Hourly demand mart is inconsistent by {hourly_consistency_gap} rows")
    LOGGER.info("Warehouse checks passed for %s", month)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pipeline data quality checks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    raw_parser = subparsers.add_parser("raw", help="Check landed files and processed extracts.")
    raw_parser.add_argument("--month", required=True)

    warehouse_parser = subparsers.add_parser("warehouse", help="Check loaded mart tables.")
    warehouse_parser.add_argument("--month", required=True)

    args = parser.parse_args()
    if args.command == "raw":
        run_raw_file_checks(month=args.month)
    elif args.command == "warehouse":
        run_warehouse_checks(month=args.month)


if __name__ == "__main__":
    main()
