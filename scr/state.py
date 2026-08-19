from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_state(path: str) -> dict[str, Any]:
    file = Path(path)
    if not file.exists():
        return {}
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"State file is invalid JSON: {file}") from exc


def already_sent(state: dict[str, Any], side: str, candle_time: str) -> bool:
    return (
        state.get("last_signal") == side
        and state.get("last_signal_candle") == candle_time
    )


def save_signal(path: str, side: str, candle_time: str) -> None:
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_signal": side,
        "last_signal_candle": candle_time,
    }
    file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
