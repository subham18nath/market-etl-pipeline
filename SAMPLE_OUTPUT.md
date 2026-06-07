# Sample Output

When you run the pipeline, you get NDJSON output (one JSON object per line). Here's a sample of what 2 rows look like:

## Format

```json
{"trade_date":"2026-06-03","ticker":"RELIANCE.NS","open":1308.948015,"high":1317.906594,"low":1295.012446,"close":1307.156250,"adj_close":1307.156250,"volume":20012293,"daily_return":0.00110000,"volatility":0.0175,"ma_7":1321.30,"ma_21":1330.50,"avg_vol_20":28500000.0,"volume_spike":0.7019,"extracted_at":"2026-06-07T13:07:27.123456"}
{"trade_date":"2026-06-04","ticker":"RELIANCE.NS","open":1310.500000,"high":1324.000000,"low":1305.000000,"close":1312.500000,"adj_close":1312.500000,"volume":22000000,"daily_return":0.00403000,"volatility":0.0145,"ma_7":1318.50,"ma_21":1329.75,"avg_vol_20":27800000.0,"volume_spike":0.7914,"extracted_at":"2026-06-07T13:07:27.123456"}
```

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `trade_date` | String (YYYY-MM-DD) | Trading day |
| `ticker` | String | Stock symbol (e.g., RELIANCE.NS, ^NSEI) |
| `open` | Number | Opening price (₹) |
| `high` | Number | Highest price during day (₹) |
| `low` | Number | Lowest price during day (₹) |
| `close` | Number | Closing price (₹) |
| `adj_close` | Number | Adjusted closing price (₹) |
| `volume` | Number | Trading volume (shares) |
| `daily_return` | Number | Price change % (e.g., 0.0011 = +0.11%) |
| `volatility` | Number | Intraday range as % of open (high-low)/open |
| `ma_7` | Number | 7-day moving average of close (₹) |
| `ma_21` | Number | 21-day moving average of close (₹) |
| `avg_vol_20` | Number | 20-day average volume (shares) |
| `volume_spike` | Number | Volume relative to 20-day avg (>1 = spike) |
| `extracted_at` | String (ISO 8601) | Extraction timestamp (UTC) |

## Storage Locations

**With S3 credentials (.env.local configured):**
```
s3://insomnia-market-data-2026/raw/equities/2026/06/07/market_2026-06-07.json
```

**Without S3 credentials (offline mode):**
```
./output/raw/equities/2026/06/07/market_2026-06-07.json
```

## Typical Daily Output

- **Tickers extracted**: 10 Indian stocks + 1 index = 11 total
- **Trading days captured**: Last 10 days (adjusts for weekends/holidays)
- **Rows per run**: ~76 (7 days × 10 stocks + 6 days × 1 index = ~76)
- **File size**: ~20-30 KB (NDJSON is compact)
- **Upload time**: ~2 seconds to S3

## Usage in Snowflake

```sql
-- Create stage pointing to S3
CREATE OR REPLACE STAGE market_stage
  URL = 's3://insomnia-market-data-2026/raw/equities/'
  CREDENTIALS = (AWS_KEY_ID = '...' AWS_SECRET_KEY = '...');

-- Load latest data
COPY INTO market.daily_prices
  FROM @market_stage/2026/06/07/market_2026-06-07.json
  FILE_FORMAT = (TYPE = 'JSON' STRIP_OUTER_ARRAY = FALSE);

-- Query
SELECT * FROM market.daily_prices 
WHERE trade_date = '2026-06-07' 
ORDER BY ticker;
```

## Example Query Results

```
trade_date   ticker         open        high         low        close    volume
────────────────────────────────────────────────────────────────────────────────
2026-06-03   RELIANCE.NS    1308.95    1317.91    1295.01    1307.16    20M
2026-06-03   TCS.NS         3450.50    3475.00    3440.00    3465.25    2.5M
2026-06-03   HDFCBANK.NS    1650.00    1680.50    1645.00    1672.50    8M
2026-06-03   ^NSEI          22500.00   22750.00   22400.00   22650.50   -
...
```

## Notes

- All prices are in Indian Rupees (₹)
- Volumes in number of shares traded
- NIFTY 50 index (^NSEI) returns price levels only (no volume in traditional sense)
- Moving averages include the current day
- null rows with missing close prices are automatically dropped
- Dates exclude weekends and NSE holidays

---

See `QUICKSTART.md` for how to get this data. See `README.md` for full documentation.
