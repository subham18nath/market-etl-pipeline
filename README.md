# Indian Market ETL Pipeline

A robust Extract-Transform-Load pipeline for Indian market data (NSE equities + NIFTY 50 index).

## Features

- **Extract**: Downloads daily OHLCV data from Yahoo Finance for 10 Indian blue-chip stocks + NIFTY 50 index
- **Transform**: Cleans data, engineers metrics (MA-7, MA-21, volatility, volume spikes)
- **Load**: Writes NDJSON to S3 (or local disk if offline)

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your AWS credentials (or leave blank for local-only mode)
   ```

3. **Run locally:**
   ```bash
   python -m src.main
   ```

4. **Run in Docker:**
   ```bash
   docker build -t market-etl .
   docker run --rm --env-file .env.local market-etl
   ```

## Data Flow

```
tickers.json
    ↓
extract.py (Yahoo Finance) → raw DataFrame (11 tickers × 7 days = ~77 rows)
    ↓
transform.py (clean + metrics) → engineered DataFrame (15 columns, MA-7/21, volatility, etc.)
    ↓
load_s3.py (NDJSON → S3 or local ./output/)
```

## Files

- `src/main.py` - Orchestrator (calls extract → transform → load)
- `src/extract.py` - Downloads data via yfinance
- `src/transform.py` - Cleans and engineers features
- `src/load_s3.py` - Uploads NDJSON to S3 (or local disk)
- `config/tickers.json` - Watchlist configuration
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container image

## Troubleshooting

**Issue: "Extraction produced no data"**
- Ensure internet connection (yfinance fetches from Yahoo servers)
- Check tickers in `config/tickers.json` are valid NSE symbols (e.g., `RELIANCE.NS`)

**Issue: S3 upload fails**
- Verify AWS credentials in `.env.local`
- Data will fall back to `./output/` if credentials are missing (offline mode)

**Issue: Data looks wrong**
- Check trade dates—NSE is closed on weekends/holidays
- Data is limited to last 10 days by default (see `src/extract.py`)

## Running on Schedule

Use cron (Linux/macOS):
```bash
0 16 * * 1-5 cd /path/to/pipeline && python -m src.main
```

Or GitHub Actions (see `.github/workflows/etl.yml` if present).
