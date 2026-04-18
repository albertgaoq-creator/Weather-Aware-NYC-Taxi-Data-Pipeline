from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path

from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.operators.python import get_current_context

from src.ingestion.lookup import download_zone_lookup
from src.ingestion.taxi import download_taxi_month
from src.ingestion.weather import download_weather_month
from src.loaders.postgres import bootstrap_warehouse, load_lookup, load_taxi_month, load_weather_month
from src.processing.preprocess_taxi import preprocess_taxi_month
from src.processing.preprocess_weather import preprocess_weather_month
from src.quality.checks import run_raw_file_checks, run_warehouse_checks


PROJECT_DIR = Path(os.getenv("PROJECT_DIR", "/opt/project"))


def _run_dbt(command: str) -> None:
    env = os.environ.copy()
    env.setdefault("DBT_PROFILES_DIR", str(PROJECT_DIR / "dbt"))
    subprocess.run(
        ["dbt", command, "--project-dir", str(PROJECT_DIR / "dbt"), "--profiles-dir", str(PROJECT_DIR / "dbt")],
        check=True,
        cwd=PROJECT_DIR,
        env=env,
    )


@dag(
    dag_id="weather_aware_taxi_pipeline",
    description="Batch pipeline for NYC yellow taxi data enriched with borough-level weather.",
    schedule="0 6 2 * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    params={"month": Param(default=None, type=["null", "string"])},
    tags=["taxi", "weather", "dbt", "postgres"],
)
def weather_aware_taxi_pipeline():
    @task
    def resolve_month() -> str:
        context = get_current_context()
        dag_run = context.get("dag_run")
        requested_month = dag_run.conf.get("month") if dag_run and dag_run.conf else None
        if requested_month:
            return requested_month
        return context["logical_date"].subtract(months=1).format("YYYY-MM")

    @task
    def bootstrap() -> None:
        bootstrap_warehouse()

    @task
    def ingest_lookup() -> str:
        return str(download_zone_lookup())

    @task
    def ingest_taxi(month: str) -> str:
        return str(download_taxi_month(month=month))

    @task
    def ingest_weather(month: str) -> list[str]:
        return [str(path) for path in download_weather_month(month=month)]

    @task
    def preprocess_taxi(month: str) -> str:
        return str(preprocess_taxi_month(month=month))

    @task
    def preprocess_weather(month: str) -> str:
        return str(preprocess_weather_month(month=month))

    @task
    def raw_quality(month: str) -> None:
        run_raw_file_checks(month=month)

    @task
    def load_lookup_task() -> None:
        load_lookup()

    @task
    def load_taxi_task(month: str) -> None:
        load_taxi_month(month=month)

    @task
    def load_weather_task(month: str) -> None:
        load_weather_month(month=month)

    @task
    def dbt_run() -> None:
        _run_dbt("run")

    @task
    def dbt_test() -> None:
        _run_dbt("test")

    @task
    def warehouse_quality(month: str) -> None:
        run_warehouse_checks(month=month)

    month = resolve_month()
    warehouse_bootstrap = bootstrap()
    lookup_ready = ingest_lookup()
    taxi_ready = ingest_taxi(month)
    weather_ready = ingest_weather(month)
    processed_taxi = preprocess_taxi(month)
    processed_weather = preprocess_weather(month)
    raw_quality_task = raw_quality(month)
    lookup_loaded = load_lookup_task()
    taxi_loaded = load_taxi_task(month)
    weather_loaded = load_weather_task(month)
    dbt_run_task = dbt_run()
    dbt_test_task = dbt_test()
    warehouse_quality_task = warehouse_quality(month)

    lookup_ready >> raw_quality_task
    lookup_ready >> lookup_loaded
    taxi_ready >> processed_taxi >> raw_quality_task
    weather_ready >> processed_weather >> raw_quality_task
    warehouse_bootstrap >> [lookup_loaded, taxi_loaded, weather_loaded]
    processed_taxi >> taxi_loaded
    processed_weather >> weather_loaded
    raw_quality_task >> [lookup_loaded, taxi_loaded, weather_loaded]
    [lookup_loaded, taxi_loaded, weather_loaded] >> dbt_run_task >> dbt_test_task
    dbt_test_task >> warehouse_quality_task


weather_aware_taxi_pipeline()
