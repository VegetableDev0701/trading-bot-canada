from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QMainWindow,
                              QVBoxLayout, QWidget)

from .chart_panel import ChartPanel
from .components import PriceHistoryTable, SymbolList, TopBar
from .theme import STYLESHEET


class ChartWindow(QMainWindow):

    def __init__(self, timeframes, default_tf, intervals, default_interval,
                 symbols, default_symbol, alert_repeat_sec=30, sound_mode="beep"):
        super().__init__()
        self.setWindowTitle("KuCoin Trading Assistant")
        self.resize(1680, 900)
        self.setStyleSheet(STYLESHEET)

        root = QWidget()
        self.setCentralWidget(root)
        hlayout = QHBoxLayout(root)
        hlayout.setSpacing(0)
        hlayout.setContentsMargins(0, 0, 0, 0)

        left = QFrame()
        left.setObjectName("leftPanel")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        self.symbol_list = SymbolList(symbols, default_symbol)
        ll.addWidget(self.symbol_list)
        hlayout.addWidget(left)

        center = QWidget()
        cl = QVBoxLayout(center)
        cl.setSpacing(0)
        cl.setContentsMargins(0, 0, 0, 0)

        top_frame = QFrame()
        top_frame.setObjectName("topBar")
        tl = QVBoxLayout(top_frame)
        tl.setContentsMargins(12, 8, 12, 8)
        self.top_bar = TopBar(timeframes, default_tf, intervals, default_interval,
                             alert_repeat_sec, sound_mode)
        self.timeframe_combo = self.top_bar.timeframe_combo
        self.interval_combo = self.top_bar.interval_combo
        self.alert_repeat_combo = self.top_bar.alert_repeat_combo
        self.sound_combo = self.top_bar.sound_combo
        tl.addWidget(self.top_bar)
        cl.addWidget(top_frame)

        self.chart_panel = ChartPanel()
        cl.addWidget(self.chart_panel, stretch=1)
        hlayout.addWidget(center, stretch=1)

        right = QFrame()
        right.setObjectName("rightPanel")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self.price_table = PriceHistoryTable()
        rl.addWidget(self.price_table)
        hlayout.addWidget(right)

    def update_ticker(self, ticker):
        self.top_bar.update_ticker(ticker)

    def update_order_book(self, ob):
        self.top_bar.update_order_book(ob)

    def set_symbols(self, symbols, default_symbol):
        self.symbol_list.set_symbols(symbols, default_symbol)

    def update_price_table(self, tickers, symbol_filter, timestamp):
        self.price_table.update_price_table(tickers, symbol_filter, timestamp)

    def update_chart(self, df, indicators, supports, resistances):
        self.chart_panel.update_chart(df, indicators, supports, resistances)

    def set_alert_manager(self, mgr):
        def _on_repeat(text):
            if text and text.isdigit():
                mgr.set_repeat_seconds(int(text))

        def _on_sound(text):
            m = {"Off": "off", "Beep": "beep", "Alert 1": "alert1",
                 "Alert 2": "alert2", "Alert 3": "alert3"}
            if text in m:
                mgr.set_sound_mode(m[text])

        self.alert_repeat_combo.currentTextChanged.connect(_on_repeat)
        self.sound_combo.currentTextChanged.connect(_on_sound)
        _on_repeat(self.alert_repeat_combo.currentText())
        _on_sound(self.sound_combo.currentText())
