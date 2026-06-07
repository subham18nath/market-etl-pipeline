"""Orchestrates one ETL run: Extract -> Transform -> Load.

Run locally:   python -m src.main
Run in Docker: docker run --rm --env-file .env market-etl
Run in CI:     handled by .github/workflows/etl.yml
"""
from __future__ import annotations

import sys

from dotenv import load_dotenv

from .extract import extract
from .load_s3 import load
from .transform import transform
from .utils import get_logger, load_tickers

log = get_logger("etl.main")


def run() -> int:
    load_dotenv()  # picks up .env locally; no-op in CI where env vars are set directly
    log.info("=== Indian Market ETL: starting ===")

    tickers = load_tickers()
    raw = extract(tickers)
    clean = transform(raw)
    destination = load(clean)

    log.info("=== Done. %d rows landed at %s ===", len(clean), destination)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except Exception as exc:  # noqa: BLE001
        log.error("ETL run failed: %s", exc)
        sys.exit(1)
