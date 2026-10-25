"""Türkçe Denetim: metindeki bilinmeyen sözcükleri işaretler ve öneri sunar."""
from __future__ import annotations

import re

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import QApplication, QGridLayout, QLabel, QListWidget, QPlainTextEdit, QPushButton, QTextEdit

import data as dt
from widgets import ToolDialog, caption

WORD_RE = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşüÂâÎîÛû]+(?:['’][A-Za-zÇĞİÖŞÜçğıöşü]+)?")


class SpellDialog(ToolDialog):
    def __init__(self, ctx):
        super().__init__(ctx, "Türkçe Denetim")
        self.checker: dt.SpellChecker | None = None
        self.misspelled: list[tuple[int, int, str]] = []

        self.text = QPlainTextEdit()
        self.text.setPlaceholderText("Denetlenecek metni buraya yazın veya yapıştırın…")
        self.check_btn = QPushButton("Denetle")
        self.replace_btn = QPushButton("Önerilenle Değiştir")
        self.bad_list = QListWidget()
        self.sug_list = QListWidget()
        self.info = QLabel("Sözlükte olmayan sözcükler kırmızı çizilir. Çekim ekleri sezgisel çözülür; sonuçlar kesin değildir.")
        self.info.setWordWrap(True)

        grid = QGridLayout(self)
        grid.addWidget(caption("Metin"), 0, 0, 1, 2)
        grid.addWidget(self.text, 1, 0, 1, 2)
        grid.addWidget(self.check_btn, 2, 0, 1, 2)
        grid.addWidget(caption("Bilinmeyen sözcükler"), 3, 0)
        grid.addWidget(caption("Öneriler"), 3, 1)
        grid.addWidget(self.bad_list, 4, 0)
        grid.addWidget(self.sug_list, 4, 1)
        grid.addWidget(self.replace_btn, 5, 0, 1, 2)
        grid.addWidget(self.info, 6, 0, 1, 2)
        grid.setRowStretch(1, 2)
        grid.setRowStretch(4, 1)
        self.resize(560, 560)

        self.check_btn.clicked.connect(self.run_check)
        self.bad_list.currentRowChanged.connect(self.show_suggestions)
        self.sug_list.itemDoubleClicked.connect(lambda _it: self.replace_selected())
        self.replace_btn.clicked.connect(self.replace_selected)

    def _checker(self) -> dt.SpellChecker:
        if self.checker is None:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                self.info.setText("Sözlük kelime kümesi hazırlanıyor…")
                QApplication.processEvents()
                self.checker = dt.SpellChecker(self.ctx.data, self.ctx.tdk)
            finally:
                QApplication.restoreOverrideCursor()
        return self.checker

    def run_check(self):
        checker = self._checker()
        text = self.text.toPlainText()
        self.misspelled = [(m.start(), m.end(), m.group()) for m in WORD_RE.finditer(text) if not checker.is_known(m.group())]
        selections = []
        for start, end, _w in self.misspelled:
            sel = QTextEdit.ExtraSelection()
            fmt = QTextCharFormat()
            fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
            fmt.setUnderlineColor(QColor("#e00000"))
            sel.format = fmt
            cur = QTextCursor(self.text.document())
            cur.setPosition(start)
            cur.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            sel.cursor = cur
            selections.append(sel)
        self.text.setExtraSelections(selections)
        self.bad_list.clear()
        self.bad_list.addItems([w for _s, _e, w in self.misspelled])
        total = len(WORD_RE.findall(text))
        self.info.setText(f"{total} sözcük denetlendi, {len(self.misspelled)} bilinmeyen sözcük bulundu.")
        if self.misspelled:
            self.bad_list.setCurrentRow(0)
        else:
            self.sug_list.clear()

    def show_suggestions(self, row: int):
        self.sug_list.clear()
        if 0 <= row < len(self.misspelled):
            start, end, word = self.misspelled[row]
            self.sug_list.addItems(self._checker().suggest(word))
            cur = self.text.textCursor()
            cur.setPosition(start)
            cur.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            self.text.setTextCursor(cur)

    def replace_selected(self):
        row, sug = self.bad_list.currentRow(), self.sug_list.currentItem()
        if row < 0 or sug is None:
            return
        start, end, _w = self.misspelled[row]
        cur = self.text.textCursor()
        cur.setPosition(start)
        cur.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cur.insertText(sug.text())
        self.run_check()
