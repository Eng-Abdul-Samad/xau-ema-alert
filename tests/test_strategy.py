import pandas as pd

from src.strategy import detect_crossover, tradingview_style_ema


def frame(values):
    times = pd.date_range("2026-08-19 00:00", periods=len(values), freq="15min", tz="UTC")
    return pd.DataFrame({"datetime": times, "close": values})


def test_buy_crossover():
    closes = [100] * 60
    closes[-2] = 90
    closes[-1] = 120
    df = frame(closes)
    signal = detect_crossover(df)
    assert signal is not None
    assert signal.side == "BUY"


def test_sell_crossover():
    closes = [100] * 60
    closes[-2] = 110
    closes[-1] = 80
    df = frame(closes)
    signal = detect_crossover(df)
    assert signal is not None
    assert signal.side == "SELL"


def test_no_crossover():
    df = frame([100] * 60)
    assert detect_crossover(df) is None


def test_ema_requires_enough_data():
    with __import__("pytest").raises(ValueError):
        tradingview_style_ema(pd.Series([1, 2, 3]), 8)
