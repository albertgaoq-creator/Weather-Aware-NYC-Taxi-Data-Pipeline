from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from src.config.settings import get_settings
from src.ingestion.weather import build_weather_output_path
from src.utils.logging import get_logger


LOGGER = get_logger(__name__)


def build_weather_processed_dataframe(payload: dict, source_file: str, month: str) -> pd.DataFrame:
    borough = payload["requested_borough"]
    hourly = payload.get("hourly", {})
    dataframe = pd.DataFrame(hourly)
    if dataframe.empty:
        raise ValueError(f"Weather payload for {borough} is empty")

    dataframe["borough"] = borough
    dataframe["weather_ts_hour"] = pd.to_datetime(dataframe["time"], errors="coerce")
    dataframe = dataframe.rename(
        columns={
            "precipitation": "precipitation_mm",
            "rain": "rain_mm",
            "snowfall": "snowfall_cm",
            "windspeed_10m": "wind_speed_10m",
        }
    )
    for column in [
        "temperature_2m",
        "precipitation_mm",
        "rain_mm",
        "snowfall_cm",
        "wind_speed_10m",
        "weathercode",
    ]:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    dataframe["source_month"] = pd.Timestamp(f"{month}-01").date()
    dataframe["source_file"] = source_file
    dataframe["ingested_at"] = pd.Timestamp.now(tz="UTC").tz_localize(None).floor("s")
    dataframe["weather_record_id"] = (
        dataframe[["borough", "weather_ts_hour"]]
        .astype(str)
        .agg("|".join, axis=1)
        .map(lambda value: hashlib.md5(value.encode("utf-8")).hexdigest())
    )

    ordered_columns = [
        "weather_record_id",
        "borough",
        "weather_ts_hour",
        "temperature_2m",
        "precipitation_mm",
        "rain_mm",
        "snowfall_cm",
        "wind_speed_10m",
        "weathercode",
        "source_month",
        "source_file",
        "ingested_at",
    ]
    return dataframe[ordered_columns].drop_duplicates(subset=["weather_record_id"]).reset_index(drop=True)


def preprocess_weather_month(month: str) -> Path:
    settings = get_settings()
    frames: list[pd.DataFrame] = []

    for borough in ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]:
        source_path = build_weather_output_path(month=month, borough=borough)
        if not source_path.exists():
            raise FileNotFoundError(f"Weather source file not found: {source_path}")

        payload = json.loads(source_path.read_text(encoding="utf-8"))
        frames.append(build_weather_processed_dataframe(payload, source_file=str(source_path), month=month))

    processed = pd.concat(frames, ignore_index=True)
    output_path = settings.processed_dir / "weather" / f"weather_{month}.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    processed.to_csv(output_path, index=False)
    LOGGER.info("Wrote %s processed weather rows to %s", len(processed), output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize weather JSON payloads into CSV for loading.")
    parser.add_argument("--month", required=True, help="Month in YYYY-MM format.")
    args = parser.parse_args()

    preprocess_weather_month(month=args.month)


if __name__ == "__main__":
    main()
