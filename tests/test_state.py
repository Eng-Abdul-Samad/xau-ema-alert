from src.state import already_sent, load_state, save_signal


def test_same_candle_is_suppressed(tmp_path):
    path = tmp_path / "state.json"
    save_signal(str(path), "BUY", "2026-08-19T10:15:00+00:00")
    state = load_state(str(path))
    assert already_sent(state, "BUY", "2026-08-19T10:15:00+00:00")


def test_different_candle_is_not_suppressed(tmp_path):
    path = tmp_path / "state.json"
    save_signal(str(path), "BUY", "2026-08-19T10:15:00+00:00")
    state = load_state(str(path))
    assert not already_sent(state, "BUY", "2026-08-19T10:30:00+00:00")
