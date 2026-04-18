from __future__ import annotations

import argparse
import io

import pandas as pd
import psycopg

from src.config.settings import get_settings
from src.utils.logging import get_logger


LOGGER = get_logger(__name__)


def _copy_dataframe(connection: psycopg.Connection, dataframe: pd.DataFrame, table_name: str) -> None:
    buffer = io.StringIO()
    dataframe.to_csv(buffer, index=False)
    buffer.seek(0)
    with connection.cursor() as cursor:
        with cursor.copy(f"COPY {table_name} FROM STDIN WITH (FORMAT CSV, HEADER TRUE)") as copy:
            copy.write(buffer.getvalue())


def _copy_csv_file(connection: psycopg.Connection, source_path: str, table_name: str) -> None:
    with open(source_path, "r", encoding="utf-8", newline="") as file_handle:
        with connection.cursor() as cursor:
            with cursor.copy(f"COPY {table_name} FROM STDIN WITH (FORMAT CSV, HEADER TRUE)") as copy:
                while True:
                    chunk = file_handle.read(1024 * 1024)
                    if not chunk:
                        break
                    copy.write(chunk)


def bootstrap_warehouse() -> None:
    settings = get_settings()
    sql_path = settings.sql_dir / "bootstrap_warehouse.sql"
    LOGGER.info("Bootstrapping warehouse with %s", sql_path)
    with psycopg.connect(settings.postgres_dsn, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql_path.read_text(encoding="utf-8"))


def load_lookup() -> None:
    settings = get_settings()
    source_path = settings.raw_dir / "reference" / "taxi_zone_lookup.csv"
    dataframe = pd.read_csv(source_path)
    dataframe = dataframe.rename(
        columns={
            "LocationID": "location_id",
            "Borough": "borough",
            "Zone": "zone",
            "service_zone": "service_zone",
        }
    )
    dataframe["source_file"] = str(source_path)
    dataframe["ingested_at"] = pd.Timestamp.now(tz="UTC").tz_localize(None).floor("s")

    with psycopg.connect(settings.postgres_dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE raw.taxi_zone_lookup")
        _copy_dataframe(connection, dataframe, "raw.taxi_zone_lookup")
        connection.commit()
    LOGGER.info("Loaded %s lookup rows", len(dataframe))


def load_taxi_month(month: str, dataset: str = "yellow") -> None:
    settings = get_settings()
    source_path = settings.processed_dir / "taxi" / dataset / f"{dataset}_tripdata_{month}.csv"

    with psycopg.connect(settings.postgres_dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM raw.taxi_trips_yellow WHERE ingestion_month = %s", (f"{month}-01",))
        _copy_csv_file(connection, str(source_path), "raw.taxi_trips_yellow")
        connection.commit()
    LOGGER.info("Loaded taxi rows for %s from %s", month, source_path)


def load_weather_month(month: str) -> None:
    settings = get_settings()
    source_path = settings.processed_dir / "weather" / f"weather_{month}.csv"

    with psycopg.connect(settings.postgres_dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM raw.weather_hourly WHERE source_month = %s", (f"{month}-01",))
        _copy_csv_file(connection, str(source_path), "raw.weather_hourly")
        connection.commit()
    LOGGER.info("Loaded weather rows for %s from %s", month, source_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load processed CSVs into PostgreSQL.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("bootstrap", help="Create schemas and raw tables.")
    subparsers.add_parser("load_lookup", help="Load taxi zone lookup CSV.")

    taxi_parser = subparsers.add_parser("load_taxi", help="Load processed taxi CSV.")
    taxi_parser.add_argument("--month", required=True)
    taxi_parser.add_argument("--dataset", default="yellow")

    weather_parser = subparsers.add_parser("load_weather", help="Load processed weather CSV.")
    weather_parser.add_argument("--month", required=True)

    args = parser.parse_args()

    if args.command == "bootstrap":
        bootstrap_warehouse()
    elif args.command == "load_lookup":
        load_lookup()
    elif args.command == "load_taxi":
        load_taxi_month(month=args.month, dataset=args.dataset)
    elif args.command == "load_weather":
        load_weather_month(month=args.month)


if __name__ == "__main__":
    main()
