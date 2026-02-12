import json
import os
import sys
import time
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from .data.data_fetcher import DataFetcher
from .logic.logic import check_entry_signal
from .logic.indicators import compute_indicators, compute_support_resistance
from .ui.alerts import AlertManager, AlertPayload
from .ui.chart_ui import ChartWindow

ROOT = Path(__file__).resolve().parent.parent

INTERVAL_MAP = {1: 0.3, 2: 1, 3: 2, 4: 3, 5: 4}


def _load_config():
    with (ROOT / "config.json").open() as f:
        return json.load(f)


def _resolve(p):
    return p if os.path.isabs(p) else str(ROOT / p)


def main():
    cfg = _load_config()
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

    fetcher = DataFetcher(
        symbol=default_sym,
        timeframe=cfg["default_timeframe"],
        interval_sec=cfg["fetch_interval_sec"],
        order_book_depth=cfg["order_book_depth"],
        symbols_for_table=symbols)

    alert_mgr = AlertManager(
        log_csv=_resolve(alerts_cfg.get("log_csv", "alerts.csv")),
        log_txt=_resolve(alerts_cfg.get("log_txt", "alerts.txt")),
        repeat_seconds=alert_repeat,
        sound_mode=sound_mode,
        sounds_dir=str(ROOT / "sounds"))

    def on_candles(df):
        ind = compute_indicators(df, cfg["indicators"])
        sups, ress = compute_support_resistance(df, cfg["support_resistance"])
        window.update_chart(df, ind, sups, ress)

        sig = check_entry_signal(df, ind, sups, ress, cfg)
        if sig.triggered and sig.buy_line and sig.expected_return_pct is not None:
            alert_mgr.fire(AlertPayload(
                symbol=default_sym,
                price=df["close"].iloc[-1],
                buy_line=sig.buy_line,
                expected_return_pct=sig.expected_return_pct,
                reasons=sig.reasons))

    def on_ticker(ticker):
        window.update_ticker(ticker)

    def on_tickers(tickers):
        cur = window.symbol_list.currentItem()
        sym = cur.text() if cur else default_sym
        window.update_price_table(tickers, sym, time.strftime("%H:%M:%S"))

    def on_order_book(ob):
        window.update_order_book(ob)

    def on_symbols(sym_list):
        nonlocal symbols, default_sym
        symbols = sym_list
        if default_sym not in symbols and symbols:
            default_sym = symbols[0]
        window.set_symbols(symbols, default_sym)
        fetcher.set_symbols_for_table([default_sym])
        if symbols:
            fetcher.set_symbol(default_sym)

    fetcher.candles_updated.connect(on_candles)
    fetcher.ticker_updated.connect(on_ticker)
    fetcher.tickers_updated.connect(on_tickers)
    fetcher.order_book_updated.connect(on_order_book)
    fetcher.symbols_updated.connect(on_symbols)
    fetcher.status_updated.connect(lambda msg: print(msg))

    window.timeframe_combo.currentTextChanged.connect(fetcher.set_timeframe)
    window.set_alert_manager(alert_mgr)

    def _on_symbol_change():
        item = window.symbol_list.currentItem()
        if item:
            s = item.text()
            fetcher.set_symbol(s)
            fetcher.set_symbols_for_table([s])

    window.symbol_list.currentRowChanged.connect(lambda _: _on_symbol_change())

    def _on_interval(text):
        if text.isdigit():
            fetcher.set_interval(INTERVAL_MAP.get(int(text), 1))

    window.interval_combo.currentTextChanged.connect(_on_interval)

    fetcher.start()
    app.aboutToQuit.connect(fetcher.stop)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
