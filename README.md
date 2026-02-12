# KuCoin Trading Bot Assistant

Local Python app that pulls live KuCoin data, shows a chart with indicators
and support/resistance levels, and pops an alert when entry conditions fire.
Read-only by default — no orders are placed.

## Quick start

```
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python -m src.main
```

## Configuration

Edit **config.json** to change symbols, timeframes, indicator periods,
support/resistance sensitivity, entry rule thresholds, and alert behaviour.

API keys are optional for public market data. If you need authenticated
endpoints, set these environment variables:

```
KUCOIN_API_KEY=...
KUCOIN_API_SECRET=...
KUCOIN_API_PASSPHRASE=...
```

## Project structure

```
src/
  main.py              — entry point, wires everything together
  data/
    data_fetcher.py    — background thread that polls KuCoin via ccxt
  logic/
    indicators.py      — EMA, SMA, RSI, MACD, Bollinger, ATR, S/R detection
    logic.py           — entry signal evaluation (all-conditions check)
  ui/
    chart_ui.py        — main window layout
    chart_panel.py     — pyqtgraph chart with candles + overlays
    chart_items.py     — custom candlestick and time-axis items
    top_bar.py         — timeframe/interval selectors, live price display
    symbol_list.py     — searchable symbol sidebar
    price_history_table.py — scrolling price snapshot table
    alerts.py          — popup, sound, Windows toast, CSV + TXT logging
    theme.py           — dark colour palette and Qt stylesheet
```

## Demo and tests

See how the bot pipeline works without live data:

1. **Generate demo candles** (200 rows of sample OHLCV):
   ```
   python demo_data.py
   ```
   Creates **demo_candles.csv** in the project root.

2. **Run the demo** (indicators + support/resistance + entry logic, then optional alert):
   ```
   python run_demo.py
   ```
   Prints the pipeline result (support/resistance levels, whether the entry signal triggered, reasons). Then shows the alert popup and appends to **alerts.csv** and **alerts.txt**. Use `--no-alert` to skip the popup and file writes.

3. **Run entry-logic tests**:
   ```
   python tests/test_entry_logic.py
   ```
   Runs three test cases: too-few-rows (no signal), all-conditions-met (signal), and expected-return-too-low (no signal).

4. **Test alert only** (popup + CSV/TXT, no candle data):
   ```
   python test_alert.py
   ```
   Use `--no-gui` to only append one row to the log files.

## Alerts

When an entry signal fires the app will:
- show a popup dialog inside the app
- play a system beep (if `alerts.sound` is true)
- send a Windows toast notification (if `win11toast` is installed)
- append a row to **alerts.csv**
- append a line to **alerts.txt**
