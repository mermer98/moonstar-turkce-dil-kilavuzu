"""İki tema: 'klasik' (Win95 görünümü) ve 'karanlık'."""
from __future__ import annotations

CLASSIC_QSS = """
* { font-family: Tahoma, 'MS Sans Serif'; font-size: 9pt; }
QWidget { background: #c0c0c0; color: #000000; }
QLabel { background: transparent; }
QLabel#caption { font-weight: bold; }
QLabel#bigword { background: #ffffff; border: 2px solid; border-color: #808080 #ffffff #ffffff #808080;
                 font-family: 'Courier New'; font-size: 17pt; font-weight: bold; padding: 4px 8px; }
QLabel#readonly { background: #c8c8c8; border: 2px solid; border-color: #808080 #ffffff #ffffff #808080; padding: 3px 5px; }
QPushButton { background: #c0c0c0; border: 2px solid; border-color: #ffffff #404040 #404040 #ffffff;
              padding: 4px 12px; min-height: 18px; }
QPushButton:pressed, QPushButton:checked { border-color: #404040 #ffffff #ffffff #404040; padding: 5px 11px 3px 13px; }
QPushButton:disabled { color: #808080; }
QPushButton#launch { font-size: 9pt; padding: 6px 4px; min-width: 96px; min-height: 52px; }
QPushButton#letter { color: #1a3fa0; font-weight: bold; padding: 1px 0; min-width: 26px; min-height: 16px; }
QPushButton#letter:disabled { color: #8a8a8a; }
QPushButton#key { background: #d4d0c8; font-size: 11pt; padding: 2px; min-width: 34px; min-height: 30px; }
QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser, QListView, QListWidget, QComboBox {
    background: #ffffff; border: 2px solid; border-color: #808080 #ffffff #ffffff #808080;
    selection-background-color: #0a246a; selection-color: #ffffff; }
QListView::item:selected, QListWidget::item:selected { background: #0a246a; color: #ffffff; }
QComboBox { padding: 2px 4px; }
QComboBox QAbstractItemView { background: #ffffff; border: 1px solid #404040; }
QCheckBox { spacing: 6px; }
QGroupBox { border: 2px groove #ffffff; margin-top: 8px; padding-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 3px; }
QScrollBar:vertical { background: #d8d8d8; width: 16px; }
QScrollBar::handle:vertical { background: #c0c0c0; border: 2px solid; border-color: #ffffff #404040 #404040 #ffffff; min-height: 24px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QToolTip { background: #ffffe1; color: #000000; border: 1px solid #000000; }
"""

DARK_QSS = """
* { font-family: 'Segoe UI', Tahoma; font-size: 9.5pt; }
QWidget { background: #1b1d23; color: #e6e6e6; }
QLabel { background: transparent; }
QLabel#caption { color: #f2b01e; font-weight: bold; }
QLabel#bigword { background: #101216; border: 1px solid #3a3f4b; border-radius: 4px;
                 font-family: Consolas, 'Courier New'; font-size: 18pt; font-weight: bold; padding: 4px 8px; color: #f2b01e; }
QLabel#readonly { background: #23262e; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 6px; }
QPushButton { background: #2a2e38; border: 1px solid #3a3f4b; border-radius: 5px; padding: 5px 14px; min-height: 18px; }
QPushButton:hover { background: #353a47; border-color: #f2b01e; }
QPushButton:pressed, QPushButton:checked { background: #f2b01e; color: #1b1d23; }
QPushButton:disabled { color: #6b7080; background: #20232a; }
QPushButton#launch { padding: 6px 4px; min-width: 96px; min-height: 52px; }
QPushButton#letter { color: #8ab4ff; font-weight: bold; padding: 1px 0; min-width: 26px; min-height: 16px; }
QPushButton#letter:disabled { color: #4a4f5c; }
QPushButton#key { font-size: 11pt; padding: 2px; min-width: 34px; min-height: 30px; }
QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser, QListView, QListWidget, QComboBox {
    background: #101216; border: 1px solid #3a3f4b; border-radius: 4px;
    selection-background-color: #f2b01e; selection-color: #1b1d23; }
QListView::item:selected, QListWidget::item:selected { background: #f2b01e; color: #1b1d23; }
QComboBox { padding: 3px 6px; }
QComboBox QAbstractItemView { background: #101216; border: 1px solid #3a3f4b; }
QCheckBox { spacing: 6px; }
QGroupBox { border: 1px solid #3a3f4b; border-radius: 5px; margin-top: 10px; padding-top: 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 3px; color: #f2b01e; }
QScrollBar:vertical { background: #1b1d23; width: 12px; }
QScrollBar::handle:vertical { background: #3a3f4b; border-radius: 5px; min-height: 24px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QToolTip { background: #23262e; color: #e6e6e6; border: 1px solid #f2b01e; }
"""

THEMES = {"klasik": CLASSIC_QSS, "karanlık": DARK_QSS}

# Çizimlerde (adam asmaca tahtası, başlık) kullanılan renkler
PALETTES = {
    "klasik": {"canvas_bg": "#ffffff", "ink": "#000000", "accent": "#7a0000"},
    "karanlık": {"canvas_bg": "#101216", "ink": "#e6e6e6", "accent": "#f2b01e"},
}
