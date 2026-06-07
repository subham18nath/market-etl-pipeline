# Quick Start Guide

## What Was Fixed

Your ETL pipeline was failing because the NSE data source (`nsepython`) stopped working. We switched to **Yahoo Finance**, which is more reliable and provides the same data.

## Installation (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment (optional for S3)
cp .env.example .env.local
# Edit .env.local with your AWS credentials if you have them
# If you skip this, data will save to ./output/ locally
```

## Run the Pipeline

**Option A: Local Python**
```bash
python -m src.main
```

**Option B: Docker**
```bash
docker build -t market-etl .
docker run --rm --env-file .env.local market-etl
```

**Option C: Schedule on Linux/macOS (daily at 4 PM)**
```bash
crontab -e
# Add this line:
0 16 * * 1-5 cd /path/to/etl-pipeline && python -m src.main
```

## Expected Output

```
2026-06-07 13:07:22 | INFO    | === Indian Market ETL: starting ===
2026-06-07 13:07:22 | INFO    | Extracting 11 tickers from Yahoo Finance...
2026-06-07 13:07:24 | INFO    |   Fetching RELIANCE.NS...
2026-06-07 13:07:24 | INFO    |     -> 7 rows
[... more tickers ...]
2026-06-07 13:07:27 | INFO    | Transform complete -> 76 clean rows, 15 columns
2026-06-07 13:07:29 | INFO    | Uploaded 76 rows -> s3://...
2026-06-07 13:07:29 | INFO    | === Done. ===
```

## Files Changed

| File | Change | Impact |
|------|--------|--------|
| `src/extract.py` | Switched from nsepython → yfinance | **Fixes the JSON parsing errors** |
| `config/tickers.json` | Updated ticker format to yfinance (.NS suffix) | Data now downloads successfully |
| `requirements.txt` | Removed nsepython | Cleaner dependencies |
| `.env.example` | New file for AWS setup | Documentation |
| `README.md` | New documentation | Setup guide |
| `FIXES.md` | Detailed explanation of all changes | Technical reference |

## Troubleshooting

**Q: "No module named 'yfinance'"**
```bash
pip install -r requirements.txt
```

**Q: "No data returned for ticker"**
- Ticker may be delisted or NSE closed
- Check `config/tickers.json` - tickers must use `.NS` suffix for yfinance

**Q: "S3 upload failed"**
- Data falls back to `./output/` locally
- Add AWS credentials to `.env.local` if you want S3 upload

**Q: "ModuleNotFoundError: No module named 'src'"**
```bash
# Run from project root:
cd /path/to/etl-pipeline
python -m src.main
```

## Data Flow

```
config/tickers.json (11 stocks + NIFTY 50)
    ↓
extract.py: Download from Yahoo Finance
    → 76 rows of OHLCV data
    ↓
transform.py: Add metrics (MA-7, MA-21, volatility, volume spike)
    → 76 rows × 15 columns
    ↓
load_s3.py: Upload as NDJSON
    → s3://bucket/raw/equities/2026/06/07/market_2026-06-07.json
      OR ./output/raw/equities/2026/06/07/market_2026-06-07.json (if no S3)
```

## What Data You Get

Each row contains:

- `trade_date` - Trading day (YYYY-MM-DD)
- `ticker` - Stock symbol (e.g., RELIANCE.NS)
- `open`, `high`, `low`, `close` - OHLC prices
- `adj_close` - Adjusted close
- `volume` - Trading volume
- `daily_return` - Price change %
- `volatility` - Intraday range
- `ma_7`, `ma_21` - 7-day and 21-day moving averages
- `avg_vol_20` - 20-day average volume
- `volume_spike` - Volume relative to 20-day average
- `extracted_at` - Extraction timestamp

## Next Steps

1. ✅ **Run the pipeline** → `python -m src.main`
2. 🔍 **Check output** → Look in `./output/` or S3
3. 📊 **Load to Snowflake** → Use COPY from S3 path
4. 📈 **Build dashboards** → Connect Snowflake to BI tools

---

See `FIXES.md` for technical details. See `README.md` for full documentation.
