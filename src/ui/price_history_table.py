from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QAbstractScrollArea, QHeaderView,
                              QTableWidget, QTableWidgetItem)

from .theme import GREEN, RED

MAX_ROWS = 200


class PriceHistoryTable(QTableWidget):

    def __init__(self):
        super().__init__(0, 5)
        self.setHorizontalHeaderLabels(["Time", "Last", "Bid", "Ask", "Chg %"])
        self.setMinimumWidth(300)
        self.setMaximumWidth(360)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setAlternatingRowColors(True)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.ElideRight)

        hdr = self.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for col in (1, 2, 3):
            hdr.setSectionResizeMode(col, QHeaderView.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)

    def update_price_table(self, tickers, symbol, timestamp):
        if symbol not in tickers:
            return
        t = tickers[symbol] or {}

        last = t.get("last")
        bid = t.get("bid")
        ask = t.get("ask")
        pct = t.get("percentage")

        self.insertRow(0)
        self.setItem(0, 0, QTableWidgetItem(timestamp))
        self.setItem(0, 1, QTableWidgetItem("—" if last is None else f"{last:.6f}"))
        self.setItem(0, 2, QTableWidgetItem("—" if bid is None else f"{bid:.6f}"))
        self.setItem(0, 3, QTableWidgetItem("—" if ask is None else f"{ask:.6f}"))

        pct_cell = QTableWidgetItem("—" if pct is None else f"{pct:.2f}%")
        if pct is not None:
            pct_cell.setForeground(QColor(GREEN if float(pct) >= 0 else RED))
        self.setItem(0, 4, pct_cell)

        while self.rowCount() > MAX_ROWS:
            self.removeRow(self.rowCount() - 1)
