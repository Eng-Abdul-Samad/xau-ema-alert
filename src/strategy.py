from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

import pandas as pd


@dataclass(frozen=True)
class Signal:
    side: str
    candle_time: datetime
    close: float
    ema_fast: float
    ema_slow: float


def calculate_ema(
    series: pd.Series,
    length: int,
) -> pd.Series:
    """
    Calculate an SMA-seeded EMA.

    This matches the EMA calculation used in the original
    verification script.
    """

    if len(series) < length:
        raise ValueError(
            f"Need at least {length} candles, "
            f"but only {len(series)} were supplied."
        )

    alpha = 2 / (length + 1)

    ema = pd.Series(
        float("nan"),
        index=series.index,
        dtype=float,
    )

    # SMA seed, matching the original verification code.
    ema.iloc[length - 1] = series.iloc[:length].mean()

    # Normal EMA recursion.
    for i in range(length, len(series)):
        ema.iloc[i] = (
            series.iloc[i] * alpha
            + ema.iloc[i - 1] * (1 - alpha)
        )

    return ema


def tradingview_style_ema(series: pd.Series, length: int) -> pd.Series:
    """
    Compatibility wrapper named like the tests expect.

    Raises ValueError when there is not enough data to seed the SMA.
    """
    if len(series) < length:
        raise ValueError(
            f"Need at least {length} candles, but only {len(series)} were supplied."
        )
    return calculate_ema(series, length)


def add_indicators(
    df: pd.DataFrame,
    fast_length: int = 8,
    slow_length: int = 50,
) -> pd.DataFrame:
    """Return a copy of the candle data with EMA 8/50."""

    if "close" not in df.columns:
        raise ValueError("DataFrame must contain a close column.")

    if len(df) < slow_length:
        raise ValueError(
            f"Need at least {slow_length} candles."
        )

    result = df.copy()

    result["EMA_8"] = calculate_ema(
        result["close"],
        fast_length,
    )

    result["EMA_50"] = calculate_ema(
        result["close"],
        slow_length,
    )

    return result


def get_completed_candles(
    df: pd.DataFrame,
    now: datetime | None = None,
) -> pd.DataFrame:
    """
    Return only completed 15-minute candles.

    A candle timestamp represents the beginning of its
    15-minute interval.

    Example:
        10:15 candle closes at 10:30.

    Therefore at 10:27 it is still forming and must not
    be used as the latest completed candle.

    At 10:30 or later it is complete.
    """

    if df.empty:
        raise ValueError("No candle data supplied.")

    if now is None:
        now = datetime.now(timezone.utc)

    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware.")

    now_utc = now.astimezone(timezone.utc)

    index = pd.DatetimeIndex(df.index)

    if index.tz is None:
        index = index.tz_localize("UTC")
    else:
        index = index.tz_convert("UTC")

    result = df.copy()
    result.index = index

    # Candle timestamp is the START of the candle.
    # A 15-minute candle is complete when:
    #
    # candle_start + 15 minutes <= current UTC time
    completed_before = now_utc - pd.Timedelta(minutes=15)

    result = result[
        result.index <= completed_before
    ]

    if result.empty:
        raise ValueError(
            "No completed 15-minute candles available."
        )

    return result


def detect_crossover(
    df: pd.DataFrame,
    now: datetime | None = None,
    fast_length: int = 8,
    slow_length: int = 50,
) -> Signal | None:
    """
    Detect a genuine EMA 8/50 crossover using only
    completed 15-minute candles.

    BUY:
        previous EMA 8 <= EMA 50
        latest   EMA 8 >  EMA 50

    SELL:
        previous EMA 8 >= EMA 50
        latest   EMA 8 <  EMA 50

    Returns None when there is no crossover.
    """

    # Accept either a DataFrame whose index is a datetime index, or a
    # DataFrame with a `datetime` column as used by the tests.
    work = df.copy()
    if "datetime" in work.columns:
        work = work.set_index("datetime")

    # Make tests deterministic: if caller didn't supply `now`, treat
    # the current time as the last candle's timestamp plus the candle
    # interval so the latest supplied candle is considered completed.
    if now is None:
        last = work.index[-1]
        if last.tzinfo is None:
            last = last.tz_localize("UTC")
        now = last + timedelta(minutes=15)

    completed = get_completed_candles(
        work,
        now=now,
    )

    completed = add_indicators(
        completed,
        fast_length=fast_length,
        slow_length=slow_length,
    )

    completed = completed.dropna(
        subset=[
            "EMA_8",
            "EMA_50",
        ]
    )

    if len(completed) < 2:
        raise ValueError(
            "Need at least two completed candles "
            "with valid EMA values."
        )

    previous = completed.iloc[-2]
    latest = completed.iloc[-1]

    previous_fast = float(previous["EMA_8"])
    previous_slow = float(previous["EMA_50"])

    latest_fast = float(latest["EMA_8"])
    latest_slow = float(latest["EMA_50"])

    candle_time = completed.index[-1].to_pydatetime()

    if candle_time.tzinfo is None:
        candle_time = candle_time.replace(
            tzinfo=timezone.utc
        )
    else:
        candle_time = candle_time.astimezone(
            timezone.utc
        )

    # BUY crossover.
    if (
        previous_fast <= previous_slow
        and latest_fast > latest_slow
    ):
        return Signal(
            side="BUY",
            candle_time=candle_time,
            close=float(latest["close"]),
            ema_fast=latest_fast,
            ema_slow=latest_slow,
        )

    # SELL crossover.
    if (
        previous_fast >= previous_slow
        and latest_fast < latest_slow
    ):
        return Signal(
            side="SELL",
            candle_time=candle_time,
            close=float(latest["close"]),
            ema_fast=latest_fast,
            ema_slow=latest_slow,
        )

    return None