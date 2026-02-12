import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from .chart_items import CandlestickItem, TimeAxisItem
from .theme import ACCENT, CHART_BG, CHART_GRID, GREEN, RED, TEXT, TEXT_DIM

_CLR_EMA_SHORT = ACCENT
_CLR_EMA_LONG  = "#00B0FF"
_CLR_SMA       = "#B39DDB"
_CLR_BB        = "#90A4AE"


def _build_legend():
    return f"""<div style="font-size:11px; color:{TEXT_DIM}; line-height:1.45;">
    <b style="color:{TEXT};">Legend</b><br/>
    <span style="color:{_CLR_EMA_SHORT};">&#9608;</span> EMA 9&nbsp;
    <span style="color:{_CLR_EMA_LONG};">&#9608;</span> EMA 21&nbsp;
    <span style="color:{_CLR_SMA};">&#9608;</span> SMA 20<br/>
    <span style="color:{_CLR_BB};">&#9608;</span> Bollinger&nbsp;&nbsp;
    <span style="color:{GREEN};">&#8212;</span> Support&nbsp;
    <span style="color:{RED};">&#8212;</span> Resistance
    </div>"""


class ChartPanel(QWidget):

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        self._ind_lines = []
        self._sr_lines = []

        self.time_axis = TimeAxisItem(orientation="bottom")
        self.pw = pg.PlotWidget(axisItems={"bottom": self.time_axis})
        self.pw.setStyleSheet(f"border: 1px solid {CHART_GRID};")
        self.pw.setBackground(CHART_BG)
        self.pw.showGrid(x=True, y=True, alpha=0.18)
        self.pw.setLabel("left", "Price")
        self.pw.setLabel("bottom", "Time")
        for axis in ("left", "bottom"):
            self.pw.getAxis(axis).setPen(pg.mkPen(TEXT_DIM))
        lay.addWidget(self.pw, stretch=1)

        self.candles = CandlestickItem()
        self.pw.addItem(self.candles)

        self._legend = QFrame(self)
        self._legend.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._legend.setMinimumWidth(200)
        self._legend.setStyleSheet(
            "background-color: #161A1E; border: 1px solid #2B3139; "
            "border-radius: 4px; padding: 4px;")
        lbl = QLabel(_build_legend())
        lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        lbl.setTextFormat(Qt.RichText)
        ll = QVBoxLayout(self._legend)
        ll.setContentsMargins(8, 5, 8, 5)
        ll.addWidget(lbl)
        self._legend.adjustSize()

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        w, h = self._legend.width(), self._legend.height()
        if w <= 0 or h <= 0:
            self._legend.adjustSize()
            w, h = self._legend.width(), self._legend.height()
        self._legend.setGeometry(self.width() - w - 8, 8, w, h)

    def update_chart(self, df, indicators, supports, resistances):
        if df.empty:
            return
        df = df.reset_index(drop=True)
        self.candles.set_data(df)
        self.time_axis.set_timestamps(self.candles.timestamps)

        for item in self._ind_lines:
            self.pw.removeItem(item)
        self._ind_lines.clear()

        x = np.arange(len(df))

        def _overlay(series, color, w=1):
            line = pg.PlotDataItem(x, series.values, pen=pg.mkPen(color, width=w))
            self.pw.addItem(line)
            self._ind_lines.append(line)

        _overlay(indicators.ema_short, _CLR_EMA_SHORT)
        _overlay(indicators.ema_long, _CLR_EMA_LONG)
        _overlay(indicators.sma, _CLR_SMA)
        _overlay(indicators.bb_upper, _CLR_BB)
        _overlay(indicators.bb_mid, _CLR_BB)
        _overlay(indicators.bb_lower, _CLR_BB)

        for item in self._sr_lines:
            self.pw.removeItem(item)
        self._sr_lines.clear()

        for lvl in supports:
            ln = pg.InfiniteLine(pos=lvl, angle=0,
                                 pen=pg.mkPen(GREEN, width=1, style=Qt.DashLine))
            self.pw.addItem(ln)
            self._sr_lines.append(ln)

        for lvl in resistances:
            ln = pg.InfiniteLine(pos=lvl, angle=0,
                                 pen=pg.mkPen(RED, width=1, style=Qt.DashLine))
            self.pw.addItem(ln)
            self._sr_lines.append(ln)
