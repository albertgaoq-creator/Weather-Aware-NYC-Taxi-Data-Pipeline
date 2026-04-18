from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

from src.config.settings import get_settings
from src.ingestion.taxi import build_taxi_output_path
from src.utils.logging import get_logger


LOGGER = get_logger(__name__)
TAXI_COLUMN_RENAME_MAP = {
    "VendorID": "vendor_id",
    "tpep_pickup_datetime": "pickup_datetime",
    "tpep_dropoff_datetime": "dropoff_datetime",
    "passenger_count": "passenger_count",
    "trip_distance": "trip_distance",
    "RatecodeID": "rate_code_id",
    "store_and_fwd_flag": "store_and_fwd_flag",
    "PULocationID": "pickup_location_id",
    "DOLocationID": "dropoff_location_id",
    "payment_type": "payment_type",
    "fare_amount": "fare_amount",
    "extra": "extra",
    "mta_tax": "mta_tax",
    "tip_amount": "tip_amount",
    "tolls_amount": "tolls_amount",
    "improvement_surcharge": "improvement_surcharge",
    "total_amount": "total_amount",
    "congestion_surcharge": "congestion_surcharge",
    "Airport_fee": "airport_fee",
    "airport_fee": "airport_fee",
    "cbd_congestion_fee": "cbd_congestion_fee",
}

REQUIRED_TAXI_COLUMNS = [
    "pickup_datetime",
    "dropoff_datetime",
    "pickup_location_id",
    "dropoff_location_id",
    "trip_distance",
    "fare_amount",
    "total_amount",
]


def build_taxi_processed_dataframe(df: pd.DataFrame, source_file: str, month: str) -> pd.DataFrame:
    normalized = df.rename(columns=TAXI_COLUMN_RENAME_MAP).copy()

    missing_columns = [column for column in REQUIRED_TAXI_COLUMNS if column not in normalized.columns]
    if missing_columns:
        raise ValueError(f"Taxi source file is missing required columns: {missing_columns}")

    for column in ("pickup_datetime", "dropoff_datetime"):
        normalized[column] = pd.to_datetime(normalized[column], errors="coerce")

    numeric_columns = [
        "vendor_id",
        "passenger_count",
        "trip_distance",
        "rate_code_id",
        "pickup_location_id",
        "dropoff_location_id",
        "payment_type",
        "fare_amount",
        "extra",
        "mta_tax",
        "tip_amount",
        "tolls_amount",
        "improvement_surcharge",
        "total_amount",
        "congestion_surcharge",
        "airport_fee",
        "cbd_congestion_fee",
    ]
    for column in numeric_columns:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
        else:
            normalized[column] = pd.NA

    normalized["pickup_hour"] = normalized["pickup_datetime"].dt.floor("h")
    normalized["pickup_date"] = normalized["pickup_datetime"].dt.date
    normalized["ingestion_month"] = pd.Timestamp(f"{month}-01").date()
    normalized["source_file"] = source_file
    normalized["ingested_at"] = pd.Timestamp.now(tz="UTC").tz_localize(None).floor("s")

    hash_source_columns = [
        "pickup_datetime",
        "dropoff_datetime",
        "pickup_location_id",
        "dropoff_location_id",
        "fare_amount",
        "total_amount",
        "trip_distance",
    ]
    normalized["record_hash"] = (
        normalized[hash_source_columns]
        .fillna("null")
        .astype(str)
        .agg("|".join, axis=1)
        .map(lambda value: hashlib.md5(value.encode("utf-8")).hexdigest())
    )

    ordered_columns = [
        "record_hash",
        "vendor_id",
        "pickup_datetime",
        "dropoff_datetime",
        "passenger_count",
        "trip_distance",
        "rate_code_id",
        "store_and_fwd_flag",
        "pickup_location_id",
        "dropoff_location_id",
        "payment_type",
        "fare_amount",
        "extra",
        "mta_tax",
        "tip_amount",
        "tolls_amount",
        "improvement_surcharge",
        "total_amount",
        "congestion_surcharge",
        "airport_fee",
        "cbd_congestion_fee",
        "pickup_hour",
        "pickup_date",
        "ingestion_month",
        "source_file",
        "ingested_at",
    ]
    normalized = normalized[ordered_columns].drop_duplicates(subset=["record_hash"]).reset_index(drop=True)
    return normalized


def preprocess_taxi_month(month: str, dataset: str = "yellow") -> Path:
    settings = get_settings()
    source_path = build_taxi_output_path(month=month, dataset=dataset)
    if not source_path.exists():
        raise FileNotFoundError(f"Taxi source file not found: {source_path}")

    LOGGER.info("Reading taxi parquet from %s", source_path)
    dataframe = pd.read_parquet(source_path)
    processed = build_taxi_processed_dataframe(dataframe, source_file=str(source_path), month=month)

    output_path = settings.processed_dir / "taxi" / dataset / f"{dataset}_tripdata_{month}.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    processed.to_csv(output_path, index=False)
    LOGGER.info("Wrote %s processed taxi rows to %s", len(processed), output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize monthly taxi parquet into CSV for loading.")
    parser.add_argument("--month", required=True, help="Month in YYYY-MM format.")
    parser.add_argument("--dataset", default="yellow", help="Taxi dataset, defaults to yellow.")
    args = parser.parse_args()

    preprocess_taxi_month(month=args.month, dataset=args.dataset)


if __name__ == "__main__":
    main()
