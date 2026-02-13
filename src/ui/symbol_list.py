from PyQt5.QtWidgets import QLineEdit, QListWidget, QVBoxLayout, QWidget


class SymbolList(QWidget):

    def __init__(self, symbols, default_symbol):
        """Build search box and list of symbols with default selection."""
        super().__init__()
        self.setFixedWidth(200)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search pairs...")
        self._search.setClearButtonEnabled(True)
        lay.addWidget(self._search)

        self._list = QListWidget()
        lay.addWidget(self._list)

        self._all = []
        self._selected = default_symbol

        self.currentRowChanged = self._list.currentRowChanged

        self._search.textChanged.connect(self._apply_filter)
        self._list.currentRowChanged.connect(self._on_row)

    def _apply_filter(self):
        """Filter list by search text and try to keep current selection."""
        q = self._search.text().strip().upper()
        self._list.clear()
        if q:
            self._list.addItems([s for s in self._all if q in s])
        else:
            self._list.addItems(self._all)
        self._try_select(self._selected)

    def _try_select(self, sym):
        """Select list row matching symbol, or first row if not found."""
        for i in range(self._list.count()):
            if self._list.item(i).text() == sym:
                self._list.setCurrentRow(i)
                return
        if self._list.count():
            self._list.setCurrentRow(0)

    def _on_row(self, row):
        """Store selected symbol when user picks a row."""
        if 0 <= row < self._list.count():
            self._selected = self._list.item(row).text()

    def set_symbols(self, symbols, default_symbol):
        """Replace symbol list and set default selection."""
        self._all = sorted(symbols)
        self._selected = default_symbol
        self._search.clear()
        self._list.clear()
        self._list.addItems(self._all)
        self._try_select(default_symbol)

    def currentItem(self):
        """Return the currently selected list item."""
        return self._list.currentItem()
