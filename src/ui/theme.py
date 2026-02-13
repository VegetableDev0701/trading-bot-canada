# Dark theme color palette
BG_MAIN     = "#0B0E11"
BG_PANEL    = "#161A1E"
BG_CARD     = "#1E2329"
BG_INPUT    = "#2B3139"

TEXT        = "#EAECEF"
TEXT_DIM    = "#848E9C"
TEXT_MUTED  = "#5E6673"

GREEN       = "#0ECB81"
RED         = "#F6465D"
ACCENT      = "#F0B90B"

BORDER      = "#2B3139"
BORDER_HI   = "#474D57"

CHART_BG    = "#131A21"
CHART_GRID  = "#1E2329"

LEGEND_BG   = "#161A1E"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG_MAIN};
    color: {TEXT};
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}}
QLabel {{ color: {TEXT}; }}

QLineEdit {{
    background: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 10px;
    color: {TEXT};
    selection-background-color: {ACCENT};
}}
QLineEdit:focus {{ border-color: {ACCENT}; }}

QComboBox {{
    background: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 10px;
    color: {TEXT};
    min-width: 70px;
}}
QComboBox:hover {{ border-color: {BORDER_HI}; }}
QComboBox::drop-down {{ border: none; padding-right: 4px; }}
QComboBox QAbstractItemView {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    selection-background-color: {BG_INPUT};
}}

QListWidget {{
    background: {BG_PANEL};
    border: none;
    border-radius: 4px;
    outline: none;
    padding: 2px;
}}
QListWidget::item {{
    padding: 7px 10px;
    border-radius: 4px;
    color: {TEXT};
}}
QListWidget::item:hover {{ background: {BG_INPUT}; }}
QListWidget::item:selected {{ background: {BG_INPUT}; color: {ACCENT}; }}

QTableWidget {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 4px;
    gridline-color: {BORDER};
    color: {TEXT};
    alternate-background-color: {BG_CARD};
}}
QHeaderView::section {{
    background: {BG_CARD};
    color: {TEXT_DIM};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 7px 10px;
    font-weight: 600;
}}

QScrollBar:vertical {{
    background: {BG_PANEL};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_HI};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {TEXT_MUTED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QFrame#topBar {{
    background: {BG_PANEL};
    border-bottom: 1px solid {BORDER};
    border-radius: 0;
}}
QFrame#leftPanel {{
    background: {BG_PANEL};
    border-right: 1px solid {BORDER};
    border-radius: 0;
}}
QFrame#rightPanel {{
    background: {BG_PANEL};
    border-left: 1px solid {BORDER};
    border-radius: 0;
}}
"""
