import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    twelve_data_api_key: str
    gmail_username: str
    gmail_app_password: str
    gmail_recipient: str

    symbol: str = "XAU/USD"
    interval: str = "15min"
    output_size: int = 200

    fast_ema: int = 8
    slow_ema: int = 50

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587


def _required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Required environment variable is missing: {name}"
        )

    return value


def load_config() -> Config:
    return Config(
        twelve_data_api_key=_required_env("TWELVE_DATA_API_KEY"),
        gmail_username=_required_env("GMAIL_USERNAME"),
        gmail_app_password=_required_env("GMAIL_APP_PASSWORD"),
        gmail_recipient=_required_env("GMAIL_RECIPIENT"),
    )


# Backwards-compatible constants expected by other modules/tests.
API_TIMEOUT = 30
INTERVAL = "15min"
OUTPUT_SIZE = 200
SYMBOL = "XAU/USD"
# Twelve Data API key; tests import this symbol but may not set it.
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "")


# Uppercase aliases and runtime helpers expected by other modules.
GMAIL_USERNAME = os.getenv("GMAIL_USERNAME", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_RECIPIENT = os.getenv("GMAIL_RECIPIENT", "")


STATE_FILE = "state/signal_state.json"


def require_runtime_secrets() -> None:
    """Raise when essential runtime secrets are missing.

    This mirrors the behavior expected by `src.main` and the
    original project structure.
    """
    missing = [
        name for name in ("TWELVE_DATA_API_KEY", "GMAIL_USERNAME", "GMAIL_APP_PASSWORD", "GMAIL_RECIPIENT")
        if not os.getenv(name)
    ]
    if missing:
        raise RuntimeError("Missing required environment variables: " + ", ".join(missing))