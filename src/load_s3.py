"""LOAD: write the processed data as newline-delimited JSON and upload to S3.

NDJSON (one JSON object per line) is the friendliest format for Snowflake's
COPY / Snowpipe auto-ingest. If AWS credentials are absent, we fall back to a
local ./output folder so you can test the pipeline end-to-end offline.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
import pandas as pd

from .utils import env, get_logger

log = get_logger(__name__)

def _object_key(prefix: str) -> str:
    """Partition the data lake by date: raw/equities/2026/06/05/market_2026-06-05.json"""
    today = dt.date.today()
    fname = f"market_{today.isoformat()}.json"
    return f"{prefix}/{today:%Y/%m/%d}/{fname}"

def _clean_region(raw: str | None) -> str:
    """Return a valid AWS region, falling back to ap-south-1 if the env var is malformed."""
    if not raw:
        return "ap-south-1"
    
    # Strip quotes, dollar signs, and common template noise that can leak in from CI
    cleaned = raw.strip().strip('"').strip("'")
    
    # If it still contains spaces or looks like a shell expression, it's invalid
    if " " in cleaned or "$" in cleaned or "vars" in cleaned or "secrets" in cleaned:
        log.warning("Malformed AWS_REGION '%s', falling back to ap-south-1", raw)
        return "ap-south-1"
    
    # Basic check: AWS regions only contain letters, digits, and hyphens
    if all(c.isalnum() or c == "-" for c in cleaned):
        return cleaned
        
    log.warning("Invalid AWS_REGION '%s', falling back to ap-south-1", raw)
    return "ap-south-1"

def load(df: pd.DataFrame) -> str:
    """Serialise to NDJSON and push to S3 (or local disk if no creds)."""
    ndjson = df.to_json(orient="records", lines=True, date_format="iso")
    
    bucket = env("S3_BUCKET")
    prefix = env("S3_PREFIX", "raw/equities")
    key = _object_key(prefix)
    
    if not bucket or not env("AWS_ACCESS_KEY_ID"):
        out = Path("output") / key
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(ndjson, encoding="utf-8")
        log.warning("No S3 creds found — wrote locally to %s", out)
        return str(out)
        
    import boto3  # imported lazily so local/offline runs don't need it
    
    region = _clean_region(env("AWS_REGION"))
    s3 = boto3.client("s3", region_name=region)
    
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=ndjson.encode("utf-8"),
        ContentType="application/x-ndjson",
    )
    
    uri = f"s3://{bucket}/{key}"
    log.info("Uploaded %d rows -> %s", len(df), uri)
    return uri
