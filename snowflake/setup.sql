-- ============================================================
-- Snowflake setup for the Indian Market ETL Pipeline
-- Run these in a Snowflake worksheet (or SnowSQL) once.
-- ============================================================

-- 1. Create the warehouse and database
CREATE WAREHOUSE IF NOT EXISTS market_etl_wh
  WITH WAREHOUSE_SIZE = 'XSMALL'
       AUTO_SUSPEND = 300
       AUTO_RESUME = TRUE;

USE WAREHOUSE market_etl_wh;

CREATE DATABASE IF NOT EXISTS market_data;
USE DATABASE market_data;

CREATE SCHEMA IF NOT EXISTS equities;
USE SCHEMA equities;

-- 2. Stage pointing to your S3 bucket (use the AWS IAM role method for production)
CREATE OR REPLACE STAGE s3_market_stage
  URL = 's3://your-bucket-name/raw/equities'
  CREDENTIALS = ( AWS_KEY_ID = '<YOUR_KEY>' AWS_SECRET_KEY = '<YOUR_SECRET>' )
  FILE_FORMAT = ( TYPE = 'JSON'  COMPRESSION = 'AUTO' );

-- 3. The main table (flattened from NDJSON)
CREATE OR REPLACE TABLE daily_equities (
    trade_date        DATE,
    ticker            VARCHAR(20),
    open              NUMBER(10,4),
    high              NUMBER(10,4),
    low               NUMBER(10,4),
    close             NUMBER(10,4),
    adj_close         NUMBER(10,4),
    volume            NUMBER(18,0),
    daily_return      NUMBER(10,6),
    volatility        NUMBER(10,6),
    ma_7              NUMBER(10,4),
    ma_21             NUMBER(10,4),
    avg_vol_20        NUMBER(18,4),
    volume_spike      NUMBER(10,4),
    extracted_at      TIMESTAMP_NTZ,
    _loaded_at        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 4. Pipe that auto-ingests new S3 files (event-based via S3 → SQS → Snowpipe)
CREATE OR REPLACE PIPE market_pipe
  AUTO_INGEST = TRUE
  AS
  COPY INTO daily_equities (trade_date, ticker, open, high, low, close, adj_close, volume,
                            daily_return, volatility, ma_7, ma_21, avg_vol_20, volume_spike, extracted_at)
  FROM (
    SELECT
      TO_DATE(f.value:trade_date::STRING, 'YYYY-MM-DD'),
      f.value:ticker::STRING,
      f.value:open::NUMBER,
      f.value:high::NUMBER,
      f.value:low::NUMBER,
      f.value:close::NUMBER,
      f.value:adj_close::NUMBER,
      f.value:volume::NUMBER,
      f.value:daily_return::NUMBER,
      f.value:volatility::NUMBER,
      f.value:ma_7::NUMBER,
      f.value:ma_21::NUMBER,
      f.value:avg_vol_20::NUMBER,
      f.value:volume_spike::NUMBER,
      TO_TIMESTAMP_NTZ(f.value:extracted_at::STRING)
    FROM @s3_market_stage (FILE_FORMAT => 'JSON') AS f
  )
  ON_ERROR = 'SKIP_FILE_5';

-- 5. Optional: a simple reporting view for Power BI
CREATE OR REPLACE VIEW vw_daily_summary AS
SELECT
  trade_date,
  ticker,
  close,
  daily_return,
  volatility,
  ma_7,
  ma_21,
  volume_spike
FROM daily_equities
WHERE trade_date >= CURRENT_DATE - 90
ORDER BY trade_date DESC;

-- 6. Verify the pipe is running
SELECT SYSTEM$PIPE_STATUS('market_pipe');
