"""Shared helpers: logging + config loading."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path


def get_logger(name: str = "etl") -> logging.Logger:
    """Return a configured logger that prints clean lines to stdout (CI-friendly)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%Y-%m-%d %H:%M:%S")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def load_tickers(config_path: str | Path = "config/tickers.json") -> list[str]:
    """Read the watchlist (equities + index benchmarks) from config."""
    path = Path(config_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    tickers = list(data.get("tickers", []))
    tickers += list(data.get("index_benchmarks", []))
    return tickers


def env(key: str, default: str | None = None) -> str | None:
    """Small wrapper around os.environ with an optional default."""
    return os.environ.get(key, default)
