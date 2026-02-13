# KuCoin Trading Bot Assistant

Local Python app: live KuCoin data, chart with indicators and support/resistance, alerts on entry conditions. Read-only by default.

## Configuration

Edit **config.json** in the project root:

- **symbols** / **default_symbol** — trading pairs (e.g. `BTC/USDT`)
- **timeframes** / **default_timeframe** — e.g. `1m`, `5m`, `15m`
- **indicators** — EMA, SMA, RSI, MACD, Bollinger, ATR periods
- **support_resistance** — pivot lookback, cluster tolerance
- **entry_rules** — support-touch buffer, min expected return
- **alerts** — repeat interval, sound, log files (CSV/TXT)

API keys are optional for public data. For authenticated endpoints, set:

```
KUCOIN_API_KEY=...
KUCOIN_API_SECRET=...
KUCOIN_API_PASSPHRASE=...
```

## How to start

```bash
python -m venv venv
venv\Scripts\activate    # Windows
pip install -r requirements.txt
python -m src.main
```
