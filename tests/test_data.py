from datetime import datetime, timezone

import pandas as pd

from src.market_data import completed_candles


def test_live_candle_is_excluded():
    now = datetime(2026, 8, 19, 10, 37, tzinfo=timezone.utc)
    times = pd.to_datetime([
        "2026-08-19 10:00:00+00:00",
        "2026-08-19 10:15:00+00:00",
        "2026-08-19 10:30:00+00:00",
    ], utc=True)
    df = pd.DataFrame({"datetime": times, "close": [1, 2, 3]})
    result = completed_candles(df, now)
    assert result.iloc[-1]["datetime"] == pd.Timestamp("2026-08-19 10:15:00+00:00")
