"""TRANSFORM: clean the raw candles and engineer the metrics the dashboard needs."""
from __future__ import annotations

import pandas as pd

from .utils import get_logger

log = get_logger(__name__)

# Canonical column names we want downstream (Snowflake-friendly: lower_snake_case)
RENAME = {
    "Date": "trade_date",
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Adj Close": "adj_close",
    "Volume": "volume",
}


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Clean + enrich the extracted frame.

    Adds:
      - daily_return    : pct change of close per ticker
      - volatility      : (high - low) / open
      - ma_7 / ma_21    : trailing moving averages of close
      - avg_vol_20      : 20-day average volume (for spike detection)
      - volume_spike    : volume / avg_vol_20
    """
    log.info("Transforming %d raw rows", len(df))

    df = df.rename(columns=RENAME).copy()

    # Normalise types
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date.astype(str)
    numeric_cols = ["open", "high", "low", "close", "adj_close", "volume"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows with no close price (bad/holiday data)
    before = len(df)
    df = df.dropna(subset=["close"]).reset_index(drop=True)
    log.info("  dropped %d rows with null close", before - len(df))

    # Sort so rolling windows are correct
    df = df.sort_values(["ticker", "trade_date"]).reset_index(drop=True)

    # Engineered metrics, computed per ticker
    grp = df.groupby("ticker", group_keys=False)
    df["daily_return"] = grp["close"].pct_change()
    df["volatility"] = (df["high"] - df["low"]) / df["open"]
    df["ma_7"] = grp["close"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    df["ma_21"] = grp["close"].transform(lambda s: s.rolling(21, min_periods=1).mean())
    df["avg_vol_20"] = grp["volume"].transform(lambda s: s.rolling(20, min_periods=1).mean())
    df["volume_spike"] = df["volume"] / df["avg_vol_20"]

    # Round floats for cleaner storage
    float_cols = df.select_dtypes(include="float").columns
    df[float_cols] = df[float_cols].round(4)

    log.info("Transform complete -> %d clean rows, %d columns", len(df), len(df.columns))
    return df
