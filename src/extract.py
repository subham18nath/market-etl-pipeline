"""EXTRACT: pull daily OHLCV market data from Yahoo Finance."""
from __future__ import annotations

import datetime as dt
import pandas as pd
import yfinance as yf

from .utils import get_logger

log = get_logger(__name__)

def extract(tickers: list[str], period: str = "5d", interval: str = "1d") -> pd.DataFrame:
    """Download recent daily candles for each ticker via Yahoo Finance."""
    log.info("Extracting %d tickers from Yahoo Finance...", len(tickers))
    frames: list[pd.DataFrame] = []
    
    # Use actual dates, not future dates
    end_date = dt.date.today()
    start_date = end_date - dt.timedelta(days=30)  # Last 30 days

    for ticker in tickers:
        try:
            log.info("  Fetching %s...", ticker)
            
            # Skip unsupported indices
            if "^BSESN" in ticker:
                log.warning("Skipping BSE index %s", ticker)
                continue
            
            # Download via yfinance with progress=False to reduce logging
            df_raw = yf.download(ticker, start=start_date, end=end_date, progress=False, threads=False)
            
            if df_raw is None or df_raw.empty:
                log.warning("No data returned for %s", ticker)
                continue

            # yfinance returns MultiIndex columns when downloading multiple tickers
            # For single ticker, we get a simple DataFrame
            if isinstance(df_raw.columns, pd.MultiIndex):
                df_raw.columns = df_raw.columns.get_level_values(0)
            
            # Reset index to make Date a column
            df_raw = df_raw.reset_index()
            
            # Rename the index column to Date if needed
            if 'Date' not in df_raw.columns and 'index' in df_raw.columns:
                df_raw = df_raw.rename(columns={'index': 'Date'})
            
            # Map to standard format
            df = pd.DataFrame()
            df["Date"] = pd.to_datetime(df_raw["Date"])
            df["Open"] = pd.to_numeric(df_raw["Open"], errors='coerce')
            df["High"] = pd.to_numeric(df_raw["High"], errors='coerce')
            df["Low"] = pd.to_numeric(df_raw["Low"], errors='coerce')
            df["Close"] = pd.to_numeric(df_raw["Close"], errors='coerce')
            df["Adj Close"] = pd.to_numeric(df_raw.get("Adj Close", df_raw["Close"]), errors='coerce')
            df["Volume"] = pd.to_numeric(df_raw["Volume"], errors='coerce')

            # Drop rows with no close
            df = df.dropna(subset=["Close"])
            
            if df.empty:
                log.warning("All rows dropped for %s (no close prices)", ticker)
                continue
            
            df = df.sort_values("Date").reset_index(drop=True)
            df["ticker"] = ticker
            
            frames.append(df)
            log.info("    -> %d rows", len(df))
            
        except Exception as exc:
            log.error("Failed to extract %s: %s", ticker, exc)

    if not frames:
        raise RuntimeError("Extraction produced no data for any ticker.")

    combined = pd.concat(frames, ignore_index=True)
    combined["extracted_at"] = dt.datetime.utcnow().isoformat()
    return combined
