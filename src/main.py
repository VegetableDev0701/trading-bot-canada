"""KuCoin Trading Assistant entry point: loads config, starts UI and data fetcher."""
import json
import os
import sys
import time
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from .data.data_fetcher import DataFetcher
from .logic.logic import evaluate_entry_signal
from .logic.indicators import (
    build_indicator_set,
    build_support_resistance,
    classic_pivot_levels,
    prior_hlc_for_pivots,
)
from .ui.alerts import AlertManager, AlertPayload
from .ui.chart_ui import ChartWindow

ROOT = Path(__file__).resolve().parent.parent

# Display interval label -> fetch interval in seconds
INTERVAL_MAP = {1: 0.3, 2: 1, 3: 2, 4: 3, 5: 4}


def _read_config():
    """Load and return config from config.json."""
    with (ROOT / "config.json").open() as f:
        return json.load(f)


def _resolve_path(p):
    """Return path as-is if absolute, else path under project root."""
    return p if os.path.isabs(p) else str(ROOT / p)


def main():
    """Load config, create UI and fetcher, wire signals, run event loop."""
    cfg = _read_config()
    app = QApplication(sys.argv)

    symbols = cfg.get("symbols") or [cfg["symbol"]]
    default_sym = cfg.get("default_symbol", symbols[0])

    display_intervals = list(INTERVAL_MAP.keys())
    default_fetch = float(cfg["fetch_interval_sec"])
    default_display = next(
        (k for k, v in INTERVAL_MAP.items() if v == default_fetch), 2)

    alerts_cfg = cfg.get("alerts") or {}
    alert_repeat = int(alerts_cfg.get("repeat_seconds", 30))
    sound_mode = alerts_cfg.get("sound_mode", "beep" if alerts_cfg.get("sound", True) else "off")

    window = ChartWindow(
        cfg["timeframes"], cfg["default_timeframe"],
        display_intervals, default_display,
        symbols, default_sym,
        alert_repeat_sec=alert_repeat, sound_mode=sound_mode)
    window.show()

    pivot_cfg = cfg.get("pivot_points") or {}
    fetch_daily_for_pivots = pivot_cfg.get("source") == "daily"

    fetcher = DataFetcher(
        symbol=default_sym,
        timeframe=cfg["default_timeframe"],
        interval_sec=cfg["fetch_interval_sec"],
        order_book_depth=cfg["order_book_depth"],
        symbols_for_table=symbols,
        fetch_daily_for_pivots=fetch_daily_for_pivots,
        candle_limit=cfg.get("candle_limit", 500))

    alert_mgr = AlertManager(
        log_csv=_resolve_path(alerts_cfg.get("log_csv", "alerts.csv")),
        log_txt=_resolve_path(alerts_cfg.get("log_txt", "alerts.txt")),
        repeat_seconds=alert_repeat,
        sound_mode=sound_mode,
        sounds_dir=str(ROOT / "sounds"))

    last_daily_df = [None]  # use list so closure can rebind

    def on_daily_candles(df_1d):
        """Store daily candles for pivot calculation."""
        last_daily_df[0] = df_1d

    def on_candles(df):
        """Compute indicators, S/R, pivots; update chart and fire alert if entry signal."""
        ind = build_indicator_set(df, cfg["indicators"])
        sups, ress = build_support_resistance(df, cfg["support_resistance"])
        pivot_levels = None
        if pivot_cfg.get("source") == "daily" and last_daily_df[0] is not None:
            daily = last_daily_df[0]
            if len(daily) >= 2:
                prev = daily.iloc[-2]
                pivot_levels = classic_pivot_levels(
                    float(prev["high"]), float(prev["low"]), float(prev["close"]))
        if pivot_levels is None:
            hlc = prior_hlc_for_pivots(df, cfg)
            if hlc is not None:
                pivot_levels = classic_pivot_levels(*hlc)
        window.update_chart(df, ind, sups, ress, pivot_levels)

        sig = evaluate_entry_signal(df, ind, sups, ress, cfg)
        if sig.triggered and sig.buy_line and sig.expected_return_pct is not None:
            alert_mgr.fire(AlertPayload(
                symbol=default_sym,
                price=df["close"].iloc[-1],
                buy_line=sig.buy_line,
                expected_return_pct=sig.expected_return_pct,
                reasons=sig.reasons))

    def on_ticker(ticker):
        """Forward latest ticker to the top bar."""
        window.update_ticker(ticker)

    def on_tickers(tickers):
        """Update price history table for current symbol."""
        cur = window.symbol_list.currentItem()
        sym = cur.text() if cur else default_sym
        window.update_price_table(tickers, sym, time.strftime("%H:%M:%S"))

    def on_order_book(ob):
        """Forward order book snapshot to the order book widget."""
        window.update_order_book(ob)

    def on_symbols(sym_list):
        """Refresh symbol list and default symbol from exchange."""
        nonlocal symbols, default_sym
        symbols = sym_list
        if default_sym not in symbols and symbols:
            default_sym = symbols[0]
        window.set_symbols(symbols, default_sym)
        fetcher.set_symbols_for_table([default_sym])
        if symbols:
            fetcher.set_symbol(default_sym)

    fetcher.candles_updated.connect(on_candles)
    if fetch_daily_for_pivots:
        fetcher.daily_candles_updated.connect(on_daily_candles)
    fetcher.ticker_updated.connect(on_ticker)
    fetcher.tickers_updated.connect(on_tickers)
    fetcher.order_book_updated.connect(on_order_book)
    fetcher.symbols_updated.connect(on_symbols)
    fetcher.status_updated.connect(lambda msg: print(msg))

    window.timeframe_combo.currentTextChanged.connect(fetcher.set_timeframe)
    window.chart_panel.desired_candle_limit_changed.connect(fetcher.set_candle_limit)
    window.set_alert_manager(alert_mgr)

    def _on_symbol_change():
        """Switch fetcher to the selected symbol and update table."""
        item = window.symbol_list.currentItem()
        if item:
            s = item.text()
            fetcher.set_symbol(s)
            fetcher.set_symbols_for_table([s])

    window.symbol_list.currentRowChanged.connect(lambda _: _on_symbol_change())

    def _on_interval(text):
        """Set fetcher poll interval from combo box selection."""
        if text.isdigit():
            fetcher.set_interval(INTERVAL_MAP.get(int(text), 1))

    window.interval_combo.currentTextChanged.connect(_on_interval)

    fetcher.start()
    app.aboutToQuit.connect(fetcher.stop)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
