# Power BI Dashboard Guide — Indian Market ETL

## Step 1: Connect to Snowflake

1. Open **Power BI Desktop** → **Get data** → **Database** → **Snowflake**.
2. Enter your Snowflake server (e.g. `your-account.snowflakecomputing.com`).
3. Set the warehouse: `market_etl_wh`, database: `market_data`, schema: `equities`.
4. Use **Import** or **DirectQuery** mode.
   - **DirectQuery** = dashboard refreshes every time you open it (truly live).
   - **Import** = snapshot refreshed on a schedule you set (faster, but not live).

## Step 2: Load the data

Select the `vw_daily_summary` view (or the `daily_equities` table directly).

## Step 3: Build the DAX measures

Create these measures in the **Modeling** tab → **New measure**:

```dax
-- 1. Daily Volatility (average across selected period)
Avg Volatility = AVERAGE(daily_equities[volatility])

-- 2. Average Volume Spike
Avg Volume Spike = AVERAGE(daily_equities[volume_spike])

-- 3. Max Volume Spike (highlight unusual days)
Max Volume Spike = MAX(daily_equities[volume_spike])

-- 4. Count of trading days in selection
Trading Days = DISTINCTCOUNT(daily_equities[trade_date])

-- 5. Cumulative Return (for performance curves)
Cumulative Return = 
  PRODUCTX(
    VALUES(daily_equities[trade_date]),
    1 + daily_equities[daily_return]
  ) - 1
```

## Step 4: Recommended visuals

| Visual | Fields | Purpose |
|--------|--------|---------|
| Line chart | `trade_date` (X) + `close` / `ma_7` / `ma_21` (Y), `ticker` in Legend | Price + trend overlay per ticker |
| Area chart | `trade_date` (X) + `volatility` (Y) | Market-wide volatility over time |
| Bar chart | `ticker` (X) + `volume_spike` (Y) | Which stocks spiked in volume today |
| Matrix (heatmap) | `ticker` (Rows), `trade_date` (Cols), `daily_return` (Values) | Daily % change heatmap |
| Card | `Avg Volatility` | Top-level metric |
| KPI | `daily_return` (value) vs previous day | Quick win/lose indicator |

## Step 5: Auto-refresh schedule

- **If DirectQuery**: the dashboard is already live. You only need to refresh the browser.
- **If Import**: set a scheduled refresh in **Power BI Service** (published to the web) once per day at 17:00 IST so it captures the newly landed data.

## Step 6: Publish

- Publish to **Power BI Service** (free workspace is enough for personal use).
- Enable "Publish to web" if you want a public embed URL for your portfolio.
