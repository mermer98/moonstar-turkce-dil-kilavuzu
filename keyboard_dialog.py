"""Klavye: ekran Türkçe Q ve F klavyesi (MTU.INI'deki iki düzen)."""
from __future__ import annotations

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout

import data as dt
from widgets import ToolDialog, caption

LAYOUTS = {
    "Türkçe Q": ["1234567890*-", "qwertyuıopğü", "asdfghjklşi,", "zxcvbnmöç.:"],
    "Türkçe F": ["1234567890/-", "fgğıodrnhpqwx", "uieaütkmlyş", "jövcçzsb.,:"],
}


class KeyboardDialog(ToolDialog):
    def __init__(self, ctx):
        super().__init__(ctx, "Türkçe Klavye")
        self.shift = False
        self.text = QPlainTextEdit()
        self.text.setMinimumHeight(110)
        self.layout_box = QComboBox()
        self.layout_box.addItems(list(LAYOUTS))
        self.shift_btn = QPushButton("⇧ Büyük/Küçük")
        self.shift_btn.setCheckable(True)
        self.keys = QGridLayout()
        self.keys.setSpacing(3)

        copy_btn = QPushButton("Kopyala")
        clear_btn = QPushButton("Temizle")
        back_btn = QPushButton("⌫")
        space_btn = QPushButton("Boşluk")
        for b in (back_btn, space_btn):
            b.setObjectName("key")
        copy_btn.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.text.toPlainText()))
        clear_btn.clicked.connect(self.text.clear)
        back_btn.clicked.connect(lambda: self.text.textCursor().deletePreviousChar())
        space_btn.clicked.connect(lambda: self.text.insertPlainText(" "))

        top = QHBoxLayout()
        top.addWidget(caption("Düzen"))
        top.addWidget(self.layout_box)
        top.addStretch(1)
        top.addWidget(copy_btn)
        top.addWidget(clear_btn)
        bottom = QHBoxLayout()
        bottom.addWidget(self.shift_btn)
        bottom.addWidget(space_btn, 1)
        bottom.addWidget(back_btn)

        root = QVBoxLayout(self)
        root.addLayout(top)
        root.addWidget(self.text, 1)
        root.addLayout(self.keys)
        root.addLayout(bottom)
        self.layout_box.currentTextChanged.connect(self.build_keys)
        self.shift_btn.toggled.connect(self._set_shift)
        self.build_keys()
        self.resize(560, 360)

    def _set_shift(self, on: bool):
        self.shift = on
        self.build_keys()

    def build_keys(self, *_):
        while self.keys.count():
            w = self.keys.takeAt(0).widget()
            if w:
                w.deleteLater()
        for r, row in enumerate(LAYOUTS[self.layout_box.currentText()]):
            for c, ch in enumerate(row):
                label = dt.tr_upper(ch) if self.shift else ch
                btn = QPushButton(label)
                btn.setObjectName("key")
                btn.clicked.connect(lambda _=False, t=label: self.text.insertPlainText(t))
                self.keys.addWidget(btn, r, c)
