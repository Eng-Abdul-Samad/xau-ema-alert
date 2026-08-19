# XAU/USD EMA 8/50 Gmail Alert

A small GitHub Actions + Python monitor for XAU/USD 15-minute EMA 8/50 crossovers.

## Behavior

- Fetches XAU/USD 15-minute candles from Twelve Data.
- Uses only completed 15-minute candles.
- Calculates SMA-seeded EMA 8 and EMA 50, matching the verification logic from the original script.
- Sends Gmail only on a genuine EMA crossover.
- Suppresses the same crossover candle on repeated workflow runs.
- Does not display or generate charts.

## Required GitHub Secrets

- `TWELVE_DATA_API_KEY`
- `GMAIL_USERNAME`
- `GMAIL_APP_PASSWORD`
- `GMAIL_RECIPIENT`

Never commit these values.

## Local tests

```powershell
pip install -r requirements.txt
pytest -q
```

Tests use local sample data and do not send email or call Twelve Data.

## Manual live run

Set the four environment variables in your local shell, then:

```powershell
python -m src.main
```

## GitHub Actions

The workflow runs approximately every 15 minutes at minute 2, 17, 32 and 47, and can also be started with `workflow_dispatch`.

GitHub scheduled workflows can be delayed. This is an approximate schedule, not real-time execution.

## State

`state/signal_state.json` stores the last successfully emailed crossover. The workflow commits a changed state file back to the repository. The state is written only after Gmail SMTP reports success.

## Security

The API key and Gmail App Password are read only from environment variables. They are not stored in Python source, the README, or workflow YAML.

## Disclaimer

This is a technical alerting tool only. It does not execute trades or guarantee profitable signals. EMA crossovers can produce false signals.
