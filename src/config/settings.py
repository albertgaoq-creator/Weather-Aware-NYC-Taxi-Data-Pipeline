from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BOROUGH_ANCHORS = {
    "Manhattan": (40.7831, -73.9712),
    "Brooklyn": (40.6782, -73.9442),
    "Queens": (40.7282, -73.7949),
    "Bronx": (40.8448, -73.8648),
    "Staten Island": (40.5795, -74.1502),
}


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    data_dir: Path
    raw_dir: Path
    processed_dir: Path
    external_dir: Path
    sql_dir: Path
    dbt_dir: Path
    timezone: str
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    min_taxi_rows: int
    min_weather_join_coverage: float

    @property
    def postgres_dsn(self) -> str:
        return (
            f"host={self.postgres_host} "
            f"port={self.postgres_port} "
            f"dbname={self.postgres_db} "
            f"user={self.postgres_user} "
            f"password={self.postgres_password}"
        )


def get_settings() -> Settings:
    base_dir = Path(__file__).resolve().parents[2]
    data_dir = Path(os.getenv("DATA_DIR", base_dir / "data"))

    return Settings(
        base_dir=base_dir,
        data_dir=data_dir,
        raw_dir=data_dir / "raw",
        processed_dir=data_dir / "processed",
        external_dir=data_dir / "external",
        sql_dir=base_dir / "sql",
        dbt_dir=base_dir / "dbt",
        timezone=os.getenv("PIPELINE_TIMEZONE", "America/New_York"),
        postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
        postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
        postgres_db=os.getenv("POSTGRES_DB", "taxi_weather"),
        postgres_user=os.getenv("POSTGRES_USER", "analytics"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "analytics"),
        min_taxi_rows=int(os.getenv("MIN_TAXI_ROWS", "1000")),
        min_weather_join_coverage=float(os.getenv("MIN_WEATHER_JOIN_COVERAGE", "0.95")),
    )
