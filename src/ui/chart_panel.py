import numpy as np
import pyqtgraph as pg
from pyqtgraph import Point
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import (QCheckBox, QFrame, QGridLayout, QLabel,
                              QVBoxLayout, QWidget)

from .chart_items import CandlestickItem, TimeAxisItem
from .theme import ACCENT, CHART_BG, CHART_GRID, GREEN, RED, TEXT, TEXT_DIM


class RightAnchoredViewBox(pg.ViewBox):
    """ViewBox that zooms in/out anchored to the right edge (zoom expands/contracts to the left)."""

    def _right_center(self):
        vr = self.targetRect()
        return Point(vr.right(), (vr.top() + vr.bottom()) * 0.5)

    def wheelEvent(self, ev, axis=None):
        if axis in (0, 1):
            mask = [False, False]
            mask[axis] = self.state["mouseEnabled"][axis]
        else:
            mask = self.state["mouseEnabled"][:]

        if not any(mask):
            ev.ignore()
            return

        s = 1.02 ** (ev.delta() * self.state["wheelScaleFactor"])
        s = [None if m is False else s for m in mask]
        self._resetTarget()
        self.scaleBy(s, self._right_center())
        ev.accept()
        self.sigRangeChangedManually.emit(mask)

    def mouseDragEvent(self, ev, axis=None):
        ev.accept()
        pos = ev.pos()
        lastPos = ev.lastPos()
        dif = pos - lastPos
        dif = dif * -1

        mouseEnabled = np.array(self.state["mouseEnabled"], dtype=np.float64)
        mask = mouseEnabled.copy()
        if axis is not None:
            mask[1 - axis] = 0.0

        if ev.button() in [Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton]:
            # Pan: use default behavior
            super().mouseDragEvent(ev, axis=axis)
            return
        if ev.button() & Qt.MouseButton.RightButton:
            # Right-drag zoom: anchor to right edge instead of mouse position
            if self.state["aspectLocked"] is not False:
                mask[0] = 0
            dif = ev.screenPos() - ev.lastScreenPos()
            dif = np.array([dif.x(), dif.y()])
            dif[0] *= -1
            s = ((mask * 0.02) + 1) ** dif
            x = s[0] if mouseEnabled[0] == 1 else None
            y = s[1] if mouseEnabled[1] == 1 else None
            center = self._right_center()
            self._resetTarget()
            self.scaleBy(x=x, y=y, center=center)
            self.sigRangeChangedManually.emit(self.state["mouseEnabled"])

_CLR_EMA_SHORT = ACCENT
_CLR_EMA_LONG  = "#00B0FF"
_CLR_SMA       = "#B39DDB"
_CLR_BB        = "#90A4AE"
_CLR_RSI       = "#F0B90B"
_CLR_MACD      = "#00B0FF"
_CLR_MACD_SIG  = "#F6465D"
_CLR_MACD_HIST = "#5E6673"
_CLR_ATR       = "#B39DDB"


class ChartPanel(QWidget):

    desired_candle_limit_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        self._last_df = None
        self._last_indicators = None
        self._last_supports = None
        self._last_resistances = None
        self._last_pivot_levels = None
        self._default_visible_bars = 80

        self._ind_lines = []
        self._sr_lines = []
        self._pivot_lines = []
        self._rsi_lines = []
        self._macd_lines = []
        self._atr_lines = []

        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setStyleSheet(f"border: 1px solid {CHART_GRID};")
        self.glw.setBackground(CHART_BG)

        # Price plot (top) - hide bottom axis; time shown on ATR panel; zoom anchored to right
        self.pw = self.glw.addPlot(0, 0, viewBox=RightAnchoredViewBox())
        self.pw.showGrid(x=True, y=True, alpha=0.18)
        self.pw.setLabel("left", "Price")
        self._vb_price = self.pw.getViewBox()
        self._vb_price.setBackgroundColor(CHART_BG)
        self._vb_price.setMouseEnabled(y=False)
        self._vb_price.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
        self.pw.hideAxis("bottom")
        for axis in ("left", "bottom"):
            self.pw.getAxis(axis).setPen(pg.mkPen(TEXT_DIM))
        self._limit_timer = QTimer(self)
        self._limit_timer.setSingleShot(True)
        self._limit_timer.timeout.connect(self._emit_desired_candle_limit)
        self._vb_price.sigRangeChanged.connect(self._on_view_range_changed)

        self.candles = CandlestickItem()
        self.pw.addItem(self.candles)

        # RSI plot (row 1) - same right-anchored zoom as price
        self.rsi_plot = self.glw.addPlot(1, 0, viewBox=RightAnchoredViewBox())
        self.rsi_plot.showGrid(x=True, y=True, alpha=0.18)
        self.rsi_plot.setLabel("left", "RSI")
        vb_rsi = self.rsi_plot.getViewBox()
        vb_rsi.setBackgroundColor(CHART_BG)
        vb_rsi.setMouseEnabled(y=False)
        vb_rsi.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
        self.rsi_plot.setXLink(self.pw)
        self.rsi_plot.setMaximumHeight(120)
        for axis in ("left", "bottom"):
            self.rsi_plot.getAxis(axis).setPen(pg.mkPen(TEXT_DIM))
        self.rsi_plot.hideAxis("bottom")

        # MACD plot (row 2) - same right-anchored zoom as price
        self.macd_plot = self.glw.addPlot(2, 0, viewBox=RightAnchoredViewBox())
        self.macd_plot.showGrid(x=True, y=True, alpha=0.18)
        self.macd_plot.setLabel("left", "MACD")
        vb_macd = self.macd_plot.getViewBox()
        vb_macd.setBackgroundColor(CHART_BG)
        vb_macd.setMouseEnabled(y=False)
        vb_macd.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
        self.macd_plot.setXLink(self.pw)
        self.macd_plot.setMaximumHeight(120)
        for axis in ("left", "bottom"):
            self.macd_plot.getAxis(axis).setPen(pg.mkPen(TEXT_DIM))
        self.macd_plot.hideAxis("bottom")

        # ATR plot (row 3) - same right-anchored zoom as price; time axis is on row 4
        self.atr_plot = self.glw.addPlot(3, 0, viewBox=RightAnchoredViewBox())
        self.atr_plot.showGrid(x=True, y=True, alpha=0.18)
        self.atr_plot.setLabel("left", "ATR")
        vb_atr = self.atr_plot.getViewBox()
        vb_atr.setBackgroundColor(CHART_BG)
        vb_atr.setMouseEnabled(y=False)
        vb_atr.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
        self.atr_plot.setXLink(self.pw)
        self.atr_plot.setMaximumHeight(100)
        self.atr_plot.hideAxis("bottom")
        for axis in ("left", "bottom"):
            self.atr_plot.getAxis(axis).setPen(pg.mkPen(TEXT_DIM))

        # Timeline (row 4) - always visible so time labels show even when ATR is hidden
        self.time_axis = TimeAxisItem(orientation="bottom")
        self.time_plot = self.glw.addPlot(4, 0, axisItems={"bottom": self.time_axis}, viewBox=RightAnchoredViewBox())
        self.time_plot.setXLink(self.pw)
        self.time_plot.setMaximumHeight(32)
        self.time_plot.setMinimumHeight(28)
        self.time_plot.hideAxis("left")
        self.time_plot.setLabel("bottom", "Time")
        vb_time = self.time_plot.getViewBox()
        vb_time.setBackgroundColor(CHART_BG)
        vb_time.setMouseEnabled(False)
        vb_time.setVisible(False)  # hide plot area, keep only axis
        self.time_plot.getAxis("bottom").setPen(pg.mkPen(TEXT_DIM))

        lay.addWidget(self.glw, stretch=1)

        self._legend = QFrame(self)
        self._legend.setMinimumWidth(220)
        self._legend.setStyleSheet(
            "background-color: #161A1E; border: 1px solid #2B3139; "
            "border-radius: 4px; padding: 4px; "
            "QCheckBox { color: #848E9C; font-size: 11px; spacing: 6px; } "
            "QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #2B3139; "
            "border-radius: 3px; background: #2B3139; } "
            "QCheckBox::indicator:checked { background: #F0B90B; border-color: #F0B90B; }")
        ll = QVBoxLayout(self._legend)
        ll.setContentsMargins(8, 6, 8, 6)
        title = QLabel("Indicators")
        title.setStyleSheet(f"color: {TEXT}; font-weight: bold; font-size: 11px;")
        ll.addWidget(title)
        grid = QGridLayout()
        self._cb_ema_short = QCheckBox("EMA 9")
        self._cb_ema_long = QCheckBox("EMA 21")
        self._cb_sma = QCheckBox("SMA 20")
        self._cb_bb = QCheckBox("Bollinger")
        self._cb_rsi = QCheckBox("RSI")
        self._cb_macd = QCheckBox("MACD")
        self._cb_atr = QCheckBox("ATR")
        self._cb_support = QCheckBox("Support")
        self._cb_resistance = QCheckBox("Resistance")
        self._cb_pivots = QCheckBox("Pivot points")
        for cb in (self._cb_ema_short, self._cb_ema_long, self._cb_sma, self._cb_bb,
                   self._cb_rsi, self._cb_macd, self._cb_atr,
                   self._cb_support, self._cb_resistance, self._cb_pivots):
            cb.setChecked(True)
            cb.stateChanged.connect(self._on_visibility_changed)
        grid.addWidget(self._cb_ema_short, 0, 0)
        grid.addWidget(self._cb_ema_long, 0, 1)
        grid.addWidget(self._cb_sma, 1, 0)
        grid.addWidget(self._cb_bb, 1, 1)
        grid.addWidget(self._cb_rsi, 2, 0)
        grid.addWidget(self._cb_macd, 2, 1)
        grid.addWidget(self._cb_atr, 3, 0)
        grid.addWidget(self._cb_support, 4, 0)
        grid.addWidget(self._cb_resistance, 4, 1)
        grid.addWidget(self._cb_pivots, 5, 0)
        ll.addLayout(grid)
        self._legend.adjustSize()

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        w, h = self._legend.width(), self._legend.height()
        if w <= 0 or h <= 0:
            self._legend.adjustSize()
            w, h = self._legend.width(), self._legend.height()
        self._legend.setGeometry(self.width() - w - 8, 8, w, h)

    def _on_visibility_changed(self):
        if self._last_df is not None and self._last_indicators is not None:
            self.update_chart(
                self._last_df, self._last_indicators,
                self._last_supports or [], self._last_resistances or [],
                self._last_pivot_levels)

    def _on_view_range_changed(self):
        self._limit_timer.start(200)

    def _emit_desired_candle_limit(self):
        x_min, x_max = self._vb_price.viewRange()[0]
        visible_bars = max(1, int(x_max - x_min))
        desired = max(100, min(1000, int(visible_bars * 1.2)))
        self.desired_candle_limit_changed.emit(desired)

    def update_chart(self, df, indicators, supports, resistances, pivot_levels=None):
        if df.empty:
            return
        # Capture current X view width before updating (preserve zoom; right edge will be fixed to last candle)
        try:
            x_min, x_max = self._vb_price.viewRange()[0]
            visible_width = max(10, x_max - x_min)
        except Exception:
            visible_width = self._default_visible_bars
        if self._last_df is None:
            visible_width = self._default_visible_bars

        self._last_df = df
        self._last_indicators = indicators
        self._last_supports = supports
        self._last_resistances = resistances
        self._last_pivot_levels = pivot_levels

        df = df.reset_index(drop=True)
        self.candles.set_data(df)
        self.time_axis.set_timestamps(self.candles.timestamps)

        x = np.arange(len(df))

        def _overlay(plot, series, color, w=1):
            line = pg.PlotDataItem(x, series.values, pen=pg.mkPen(color, width=w))
            plot.addItem(line)
            return line

        for item in self._ind_lines:
            self.pw.removeItem(item)
        self._ind_lines.clear()
        if self._cb_ema_short.isChecked():
            self._ind_lines.append(_overlay(self.pw, indicators.ema_short, _CLR_EMA_SHORT))
        if self._cb_ema_long.isChecked():
            self._ind_lines.append(_overlay(self.pw, indicators.ema_long, _CLR_EMA_LONG))
        if self._cb_sma.isChecked():
            self._ind_lines.append(_overlay(self.pw, indicators.sma, _CLR_SMA))
        if self._cb_bb.isChecked():
            self._ind_lines.append(_overlay(self.pw, indicators.bb_upper, _CLR_BB))
            self._ind_lines.append(_overlay(self.pw, indicators.bb_mid, _CLR_BB))
            self._ind_lines.append(_overlay(self.pw, indicators.bb_lower, _CLR_BB))

        for item in self._sr_lines:
            self.pw.removeItem(item)
        self._sr_lines.clear()
        if self._cb_support.isChecked():
            for lvl in supports:
                ln = pg.InfiniteLine(pos=lvl, angle=0,
                                     pen=pg.mkPen(GREEN, width=1, style=Qt.DashLine))
                self.pw.addItem(ln)
                self._sr_lines.append(ln)
        if self._cb_resistance.isChecked():
            for lvl in resistances:
                ln = pg.InfiniteLine(pos=lvl, angle=0,
                                     pen=pg.mkPen(RED, width=1, style=Qt.DashLine))
                self.pw.addItem(ln)
                self._sr_lines.append(ln)

        for item in self._pivot_lines:
            self.pw.removeItem(item)
        self._pivot_lines.clear()
        if pivot_levels and self._cb_pivots.isChecked():
            pp = pivot_levels.get("PP")
            if pp is not None:
                ln = pg.InfiniteLine(pos=pp, angle=0,
                                     pen=pg.mkPen(ACCENT, width=1.5, style=Qt.DashLine))
                self.pw.addItem(ln)
                self._pivot_lines.append(ln)
            for key, lvl in pivot_levels.items():
                if key == "PP" or lvl is None:
                    continue
                color = RED if key.startswith("R") else GREEN
                ln = pg.InfiniteLine(pos=lvl, angle=0,
                                     pen=pg.mkPen(color, width=1, style=Qt.DotLine))
                self.pw.addItem(ln)
                self._pivot_lines.append(ln)

        # Fix price Y range (zoom only changes X)
        price_vals = [df["low"].min(), df["high"].max()]
        if self._cb_bb.isChecked():
            price_vals.extend([indicators.bb_lower.min(), indicators.bb_upper.max()])
        if self._cb_support.isChecked() and supports:
            price_vals.extend(supports)
        if self._cb_resistance.isChecked() and resistances:
            price_vals.extend(resistances)
        if pivot_levels and self._cb_pivots.isChecked():
            for v in pivot_levels.values():
                if v is not None:
                    price_vals.append(v)
        y_min = min(price_vals)
        y_max = max(price_vals)
        pad = (y_max - y_min) * 0.02 or 1e-6
        self.pw.setYRange(y_min - pad, y_max + pad, padding=0)

        # Fix X range: last candle on the right; zoom out shows more candles to the left
        n = len(df)
        x_right = n - 1
        x_left = max(0, x_right - visible_width)
        self._vb_price.setXRange(x_left, x_right, padding=0)

        # RSI panel
        for item in self._rsi_lines:
            self.rsi_plot.removeItem(item)
        self._rsi_lines.clear()
        if self._cb_rsi.isChecked():
            self.rsi_plot.setMaximumHeight(120)
            self.rsi_plot.setVisible(True)
            self._rsi_lines.append(_overlay(self.rsi_plot, indicators.rsi, _CLR_RSI))
            for lvl in (30, 70):
                ref = pg.InfiniteLine(pos=lvl, angle=0,
                                      pen=pg.mkPen(TEXT_DIM, width=1, style=Qt.DotLine))
                self.rsi_plot.addItem(ref)
                self._rsi_lines.append(ref)
            self.rsi_plot.setYRange(0, 100, padding=0.02)
        else:
            self.rsi_plot.setMaximumHeight(0)
            self.rsi_plot.setVisible(False)

        # MACD panel (line, signal, histogram)
        for item in self._macd_lines:
            self.macd_plot.removeItem(item)
        self._macd_lines.clear()
        if self._cb_macd.isChecked():
            self.macd_plot.setMaximumHeight(120)
            self.macd_plot.setVisible(True)
            self._macd_lines.append(_overlay(self.macd_plot, indicators.macd, _CLR_MACD))
            self._macd_lines.append(_overlay(self.macd_plot, indicators.macd_signal, _CLR_MACD_SIG))
            hist_vals = np.nan_to_num(np.array(indicators.macd_hist.values, copy=True, dtype=float), 0)
            hist_colors = [GREEN if v >= 0 else RED for v in hist_vals]
            no_pen = pg.mkPen(None)
            bar = pg.BarGraphItem(x=x, height=hist_vals, width=0.6,
                                  brushes=hist_colors, pens=[no_pen] * len(hist_vals))
            self.macd_plot.addItem(bar)
            self._macd_lines.append(bar)
            macd_vals = np.concatenate([
                np.nan_to_num(np.array(indicators.macd.values, copy=True, dtype=float), 0),
                np.nan_to_num(np.array(indicators.macd_signal.values, copy=True, dtype=float), 0),
                hist_vals])
            m_min, m_max = float(np.nanmin(macd_vals)), float(np.nanmax(macd_vals))
            m_pad = (m_max - m_min) * 0.05 or 1e-6
            self.macd_plot.setYRange(m_min - m_pad, m_max + m_pad, padding=0)
        else:
            self.macd_plot.setMaximumHeight(0)
            self.macd_plot.setVisible(False)

        # ATR panel
        for item in self._atr_lines:
            self.atr_plot.removeItem(item)
        self._atr_lines.clear()
        if self._cb_atr.isChecked():
            self.atr_plot.setMaximumHeight(100)
            self.atr_plot.setVisible(True)
            self._atr_lines.append(_overlay(self.atr_plot, indicators.atr, _CLR_ATR))
            atr_max = float(np.nanmax(indicators.atr.values))
            atr_pad = atr_max * 0.05 or 1e-6
            self.atr_plot.setYRange(0, atr_max + atr_pad, padding=0)
        else:
            self.atr_plot.setMaximumHeight(0)
            self.atr_plot.setVisible(False)
