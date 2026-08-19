from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

from .config import API_TIMEOUT, INTERVAL, OUTPUT_SIZE, SYMBOL, TWELVE_DATA_API_KEY

log = logging.getLogger(__name__)


def fetch_gold_data() -> pd.DataFrame:
    if not TWELVE_DATA_API_KEY:
        raise RuntimeError("TWELVE_DATA_API_KEY is not configured")

    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "outputsize": OUTPUT_SIZE,
        "apikey": TWELVE_DATA_API_KEY,
    }

    log.info("Requesting %s %s candles", OUTPUT_SIZE, INTERVAL)
    response = requests.get(url, params=params, timeout=API_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    if "values" not in data:
        message = data.get("message", "Twelve Data returned no values")
        raise RuntimeError(f"Twelve Data error: {message}")

    df = pd.DataFrame(data["values"])
    if df.empty:
        raise RuntimeError("Twelve Data returned zero candles")

    required = {"datetime", "open", "high", "low", "close"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing required candle columns: {sorted(missing)}")

    df["datetime"] = pd.to_datetime(df["datetime"], utc=True, errors="coerce")
    for column in ["open", "high", "low", "close"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["datetime", "open", "high", "low", "close"])
    df = df.drop_duplicates(subset=["datetime"], keep="last")
    df = df.sort_values("datetime").reset_index(drop=True)

    bad = (
        (df["high"] < df["open"])
        | (df["high"] < df["close"])
        | (df["high"] < df["low"])
        | (df["low"] > df["open"])
        | (df["low"] > df["close"])
    )
    if bad.any():
        raise RuntimeError(f"Found {int(bad.sum())} invalid OHLC rows")

    if len(df) < 50:
        raise RuntimeError(f"Insufficient candles: {len(df)}; need at least 50")

    log.info("Received %d valid candles", len(df))
    return df


def completed_candles(df: pd.DataFrame, now: datetime | None = None) -> pd.DataFrame:
    """Return only candles whose 15-minute period has fully closed."""
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    interval = timedelta(minutes=15)
    cutoff = now.astimezone(timezone.utc) - interval
    result = df[df["datetime"] <= cutoff].copy()

    if result.empty:
        raise RuntimeError("No completed 15-minute candles available")

    latest = result.iloc[-1]["datetime"]
    log.info("Latest completed candle: %s", latest.strftime("%Y-%m-%d %H:%M UTC"))
    return result
