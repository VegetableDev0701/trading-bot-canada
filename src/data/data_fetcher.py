import os
import time

import ccxt
import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal


class DataFetcher(QThread):

    candles_updated = pyqtSignal(pd.DataFrame)
    ticker_updated = pyqtSignal(dict)
    tickers_updated = pyqtSignal(dict)
    symbols_updated = pyqtSignal(list)
    order_book_updated = pyqtSignal(dict)
    status_updated = pyqtSignal(str)

    def __init__(self, symbol, timeframe, interval_sec,
                 order_book_depth=0, symbols_for_table=None):
        super().__init__()
        self.symbol = symbol
        self.timeframe = timeframe
        self.interval_sec = interval_sec
        self.order_book_depth = order_book_depth
        self.symbols_for_table = symbols_for_table or []
        self._running = True
        self._markets_loaded = False
        self.exchange = self._build_exchange()

    def _build_exchange(self):
        opts = {"enableRateLimit": True}
        key = os.getenv("KUCOIN_API_KEY")
        secret = os.getenv("KUCOIN_API_SECRET")
        passphrase = os.getenv("KUCOIN_API_PASSPHRASE")
        if key and secret and passphrase:
            opts["apiKey"] = key
            opts["secret"] = secret
            opts["password"] = passphrase

        ex = ccxt.kucoin(opts)
        if os.getenv("READ_ONLY", "true").lower() == "true":
            ex.set_sandbox_mode(False)
        return ex

    def stop(self):
        self._running = False

    def set_timeframe(self, tf):
        self.timeframe = tf

    def set_symbol(self, sym):
        self.symbol = sym

    def set_interval(self, sec):
        self.interval_sec = max(0.5, float(sec))

    def set_symbols_for_table(self, syms):
        self.symbols_for_table = syms or []

    def run(self):
        while self._running:
            try:
                if not self._markets_loaded:
                    mkts = self.exchange.load_markets()
                    pairs = sorted(s for s in mkts if "/" in s)
                    if pairs:
                        self.symbols_updated.emit(pairs)
                    self._markets_loaded = True

                raw = self.exchange.fetch_ohlcv(
                    self.symbol, timeframe=self.timeframe, limit=200)
                df = pd.DataFrame(
                    raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

                ticker = self.exchange.fetch_ticker(self.symbol)

                self.candles_updated.emit(df)
                self.ticker_updated.emit(ticker)

                try:
                    if self.symbols_for_table:
                        snap = self.exchange.fetch_tickers(self.symbols_for_table)
                    else:
                        snap = self.exchange.fetch_tickers()
                    self.tickers_updated.emit(snap)
                except Exception as e:
                    self.status_updated.emit(f"Ticker snapshot error: {e}")

                if self.order_book_depth > 0:
                    ob = self.exchange.fetch_order_book(
                        self.symbol, limit=self.order_book_depth)
                    self.order_book_updated.emit(ob)

            except Exception as e:
                self.status_updated.emit(f"Fetch error: {e}")

            time.sleep(self.interval_sec)
