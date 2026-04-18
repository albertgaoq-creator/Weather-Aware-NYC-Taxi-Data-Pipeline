from __future__ import annotations

import argparse
from pathlib import Path

import requests

from src.config.settings import get_settings
from src.utils.logging import get_logger


LOGGER = get_logger(__name__)
ZONE_LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"


def download_zone_lookup(force: bool = False) -> Path:
    settings = get_settings()
    output_path = settings.raw_dir / "reference" / "taxi_zone_lookup.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not force:
        LOGGER.info("Zone lookup already exists at %s", output_path)
        return output_path

    response = requests.get(ZONE_LOOKUP_URL, timeout=60)
    response.raise_for_status()
    output_path.write_bytes(response.content)
    LOGGER.info("Downloaded zone lookup to %s", output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download TLC taxi zone lookup.")
    parser.add_argument("--force", action="store_true", help="Re-download the lookup file.")
    args = parser.parse_args()
    download_zone_lookup(force=args.force)


if __name__ == "__main__":
    main()
