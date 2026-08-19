from __future__ import annotations

import logging

from .config import STATE_FILE, require_runtime_secrets
from .market_data import completed_candles, fetch_gold_data
from .notifier import send_signal_email
from .state import already_sent, load_state, save_signal
from .strategy import detect_crossover

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
log = logging.getLogger(__name__)


def run() -> int:
    log.info("XAU/USD EMA monitor started")
    require_runtime_secrets()

    df = fetch_gold_data()
    closed = completed_candles(df)
    signal = detect_crossover(closed)

    if signal is None:
        log.info("No crossover detected")
        return 0

    candle_key = signal.candle_time.isoformat()
    state = load_state(STATE_FILE)

    if already_sent(state, signal.side, candle_key):
        log.info("Duplicate %s suppressed for candle %s", signal.side, candle_key)
        return 0

    log.info(
        "New %s crossover: candle=%s close=%.2f EMA8=%.2f EMA50=%.2f",
        signal.side,
        candle_key,
        signal.close,
        signal.ema_fast,
        signal.ema_slow,
    )

    # State is written only after SMTP succeeds.
    send_signal_email(signal)
    save_signal(STATE_FILE, signal.side, candle_key)
    log.info("Gmail alert sent successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
