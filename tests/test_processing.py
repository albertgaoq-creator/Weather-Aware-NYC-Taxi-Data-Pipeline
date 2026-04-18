import pandas as pd

from src.processing.preprocess_taxi import build_taxi_processed_dataframe
from src.processing.preprocess_weather import build_weather_processed_dataframe


def test_build_taxi_processed_dataframe_adds_record_hash_and_partition_columns():
    source = pd.DataFrame(
        {
            "VendorID": [1],
            "tpep_pickup_datetime": ["2025-01-01 08:00:00"],
            "tpep_dropoff_datetime": ["2025-01-01 08:20:00"],
            "PULocationID": [161],
            "DOLocationID": [230],
            "trip_distance": [2.5],
            "fare_amount": [14.5],
            "total_amount": [18.5],
        }
    )

    processed = build_taxi_processed_dataframe(source, source_file="sample.parquet", month="2025-01")

    assert processed.loc[0, "record_hash"]
    assert processed.loc[0, "ingestion_month"].isoformat() == "2025-01-01"
    assert processed.loc[0, "pickup_location_id"] == 161


def test_build_weather_processed_dataframe_normalizes_open_meteo_payload():
    payload = {
        "requested_borough": "Manhattan",
        "hourly": {
            "time": ["2025-01-01T00:00"],
            "temperature_2m": [4.2],
            "precipitation": [1.1],
            "rain": [1.1],
            "snowfall": [0.0],
            "windspeed_10m": [12.4],
            "weathercode": [61],
        },
    }

    processed = build_weather_processed_dataframe(payload, source_file="manhattan.json", month="2025-01")

    assert processed.loc[0, "borough"] == "Manhattan"
    assert processed.loc[0, "precipitation_mm"] == 1.1
    assert processed.loc[0, "weathercode"] == 61
