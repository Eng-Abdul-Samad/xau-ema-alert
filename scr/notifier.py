from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from .config import GMAIL_APP_PASSWORD, GMAIL_RECIPIENT, GMAIL_USERNAME
from .strategy import Signal


def _validate_email_config() -> None:
    if not GMAIL_USERNAME or not GMAIL_APP_PASSWORD or not GMAIL_RECIPIENT:
        raise RuntimeError("Gmail configuration is incomplete")


def send_signal_email(signal: Signal) -> None:
    _validate_email_config()

    if signal.side == "BUY":
        subject = "🟢 XAU/USD BUY — EMA 8/50 — 15m"
        reason = "EMA 8 crossed above EMA 50 on the latest completed 15-minute candle."
    else:
        subject = "🔴 XAU/USD SELL — EMA 8/50 — 15m"
        reason = "EMA 8 crossed below EMA 50 on the latest completed 15-minute candle."

    message = EmailMessage()
    message["From"] = GMAIL_USERNAME
    message["To"] = GMAIL_RECIPIENT
    message["Subject"] = subject
    message.set_content(
        "XAU/USD EMA Crossover Alert\n\n"
        f"Signal: {signal.side}\n\n"
        "Timeframe: 15 minutes\n\n"
        "Fast EMA: 8\n"
        "Slow EMA: 50\n\n"
        f"Trigger candle: {signal.candle_time.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"Gold closing price: ${signal.close:.2f}\n\n"
        f"EMA 8: {signal.ema_fast:.2f}\n"
        f"EMA 50: {signal.ema_slow:.2f}\n\n"
        f"Reason: {reason}\n\n"
        "This is a technical alert only and is not financial advice."
    )

    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as smtp:
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()
        smtp.login(GMAIL_USERNAME, GMAIL_APP_PASSWORD)
        smtp.send_message(message)
