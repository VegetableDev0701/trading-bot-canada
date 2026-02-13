"""Order book depth table: bids and asks from exchange."""
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QFrame, QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from .theme import BG_PANEL, BORDER, GREEN, RED, TEXT_DIM


class OrderBookWidget(QFrame):
    """Order book depth: top N levels of bids and asks in a table."""

    def __init__(self, max_levels=15, parent=None):
        """Build order book table with title and max_levels rows for bids/asks."""
        super().__init__(parent)
        self.setObjectName("orderBookWidget")
        self.setStyleSheet(
            f"QFrame#orderBookWidget {{ background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 4px; }}")
        self.max_levels = max_levels
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        self._title = QLabel("Order book depth")
        self._title.setStyleSheet(f"color: {TEXT_DIM}; font-weight: bold; font-size: 11px;")
        lay.addWidget(self._title)
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Bid size", "Bid", "Ask", "Ask size"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(
            "QTableWidget { background: transparent; gridline-color: #2B3139; } "
            "QHeaderView::section { background: #1E2329; color: #848E9C; padding: 6px; }")
        lay.addWidget(self._table, 1)
        self.setMinimumWidth(200)

    def update_depth(self, ob):
        """Update table from order book dict with 'bids' and 'asks' ([price, size] lists)."""
        bids = (ob.get("bids") or [])[: self.max_levels]
        asks = (ob.get("asks") or [])[: self.max_levels]
        n = max(len(bids), len(asks), 1)
        self._table.setRowCount(n)
        for i in range(n):
            for col in range(4):
                item = self._table.item(i, col)
                if item is None:
                    item = QTableWidgetItem("")
                    self._table.setItem(i, col, item)
                item.setText("")
                item.setForeground(self._table.palette().brush(self._table.foregroundRole()))
            if i < len(bids):
                price, size = bids[i]
                self._table.item(i, 0).setText(_format_size(size))
                self._table.item(i, 1).setText(_format_price(price))
                self._table.item(i, 0).setForeground(QColor(GREEN))
                self._table.item(i, 1).setForeground(QColor(GREEN))
            if i < len(asks):
                price, size = asks[i]
                self._table.item(i, 2).setText(_format_price(price))
                self._table.item(i, 3).setText(_format_size(size))
                self._table.item(i, 2).setForeground(QColor(RED))
                self._table.item(i, 3).setForeground(QColor(RED))
        self._table.viewport().update()

    def clear(self):
        """Remove all rows from the order book table."""
        self._table.setRowCount(0)


def _format_size(x):
    """Format size for display (fewer decimals for small values)."""
    try:
        f = float(x)
        if f >= 1:
            return f"{f:,.2f}"
        return f"{f:.4f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(x)


def _format_price(x):
    """Format price with commas and two decimals."""
    try:
        return f"{float(x):,.2f}"
    except (TypeError, ValueError):
        return str(x)
