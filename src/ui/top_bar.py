from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget

from .theme import ACCENT, GREEN, RED, TEXT_DIM


class TopBar(QWidget):

    def __init__(self, timeframes, default_tf, intervals, default_interval,
                 alert_repeat_sec=30, sound_mode="beep"):
        super().__init__()
        row = QHBoxLayout(self)
        row.setAlignment(Qt.AlignLeft)
        row.setSpacing(14)

        row.addWidget(QLabel("Timeframe"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(timeframes)
        self.timeframe_combo.setCurrentText(default_tf)
        row.addWidget(self.timeframe_combo)

        row.addWidget(QLabel("Refresh"))
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(str(i) for i in intervals)
        self.interval_combo.setCurrentText(str(default_interval))
        row.addWidget(self.interval_combo)

        row.addWidget(QLabel("Alert repeat (s)"))
        self.alert_repeat_combo = QComboBox()
        self.alert_repeat_combo.addItems("15 30 60 120".split())
        self.alert_repeat_combo.setCurrentText(str(alert_repeat_sec)
            if str(alert_repeat_sec) in ("15", "30", "60", "120") else "30")
        row.addWidget(self.alert_repeat_combo)

        row.addWidget(QLabel("Sound"))
        self.sound_combo = QComboBox()
        self.sound_combo.addItems(["Off", "Beep", "Alert 1", "Alert 2", "Alert 3"])
        smap = {"off": "Off", "beep": "Beep", "alert1": "Alert 1",
                "alert2": "Alert 2", "alert3": "Alert 3"}
        self.sound_combo.setCurrentText(smap.get(sound_mode, "Beep"))
        row.addWidget(self.sound_combo)

        row.addStretch()

        self._sym = self._make_label("—", TEXT_DIM, 600, 13)
        self._price = self._make_label("—", ACCENT, 700, 18)
        self._change = self._make_label("—", TEXT_DIM, 600, 13)
        self._vol = self._make_label("Vol: —", TEXT_DIM, 400, 12)
        self._depth = self._make_label("Depth: —", TEXT_DIM, 400, 12)

        for w in (self._sym, self._price, self._change, self._vol, self._depth):
            row.addWidget(w)

    def _make_label(self, text, color, weight, size):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color:{color}; font-weight:{weight}; font-size:{size}px;")
        return lbl

    def update_ticker(self, ticker):
        sym = ticker.get("symbol")
        last = ticker.get("last")
        pct = ticker.get("percentage")
        bvol = ticker.get("baseVolume")
        qvol = ticker.get("quoteVolume")

        if sym:
            self._sym.setText(str(sym))
        if last is not None:
            self._price.setText(f"{last:,.4f}".rstrip("0").rstrip("."))

        if pct is not None:
            p = float(pct)
            c = GREEN if p >= 0 else RED
            self._change.setText(f"{p:+.2f}%")
            self._change.setStyleSheet(f"color:{c}; font-weight:600; font-size:13px;")
        else:
            self._change.setText("—")

        if bvol is not None and qvol is not None:
            if qvol >= 1e9:
                txt = f"{bvol:,.0f} / {qvol/1e9:.2f}B"
            elif qvol >= 1e6:
                txt = f"{bvol:,.0f} / {qvol/1e6:.2f}M"
            else:
                txt = f"{bvol:,.2f} / {qvol:,.2f}"
            self._vol.setText(f"Vol: {txt}")
        elif bvol is not None:
            self._vol.setText(f"Vol: {bvol:,.2f}")

    def update_order_book(self, ob):
        bids = ob.get("bids") or []
        asks = ob.get("asks") or []
        d = min(len(bids), len(asks))
        self._depth.setText(f"Depth: {d}" if d else "Depth: —")
