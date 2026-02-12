import pyqtgraph as pg
from pyqtgraph import QtCore

from .theme import GREEN, RED


class CandlestickItem(pg.GraphicsObject):

    def __init__(self):
        super().__init__()
        self._bars = []
        self.timestamps = []

    def set_data(self, df):
        self._bars = [
            (i, row["open"], row["close"], row["low"], row["high"])
            for i, row in df.iterrows()
        ]
        self.timestamps = df["timestamp"].tolist()
        self.prepareGeometryChange()
        self.update()

    def paint(self, p, *_args):
        for x, o, c, lo, hi in self._bars:
            col = pg.mkColor(GREEN if c >= o else RED)
            p.setPen(pg.mkPen(col))
            p.drawLine(QtCore.QPointF(x, lo), QtCore.QPointF(x, hi))
            body = QtCore.QRectF(x - 0.3, min(o, c), 0.6, abs(c - o) or 0.0001)
            p.fillRect(body, col)
            p.drawRect(body)

    def boundingRect(self):
        if not self._bars:
            return QtCore.QRectF()
        xs   = [b[0] for b in self._bars]
        lows = [b[3] for b in self._bars]
        his  = [b[4] for b in self._bars]
        return QtCore.QRectF(
            min(xs), min(lows),
            max(xs) - min(xs), max(his) - min(lows))


class TimeAxisItem(pg.AxisItem):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._ts = []

    def set_timestamps(self, ts_list):
        self._ts = ts_list
        self.picture = None
        self.update()

    def tickStrings(self, values, scale, spacing):
        if not self._ts:
            return [""] * len(values)
        out = []
        for v in values:
            idx = int(round(v))
            if 0 <= idx < len(self._ts):
                out.append(self._ts[idx].strftime("%H:%M"))
            else:
                out.append("")
        return out
