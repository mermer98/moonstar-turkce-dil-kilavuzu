"""İngilizce/Türkçe ve Türkçe/İngilizce sözlük pencereleri (tam alfabetik liste + anlık arama)."""
from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLineEdit, QListWidget

from widgets import FavButton, ToolDialog, WordList, caption, ok_button, readonly_field

MODES = {
    "en_tr": dict(title="İngilizce Türkçe Sözlük", left="İngilizce Sözcükler", right="Türkçe Karşılıkları", bottom="Türkçe Karşılık", kind="en"),
    "tr_en": dict(title="Türkçe İngilizce Sözlük", left="Türkçe Sözcükler", right="İngilizce Karşılıkları", bottom="İngilizce Karşılık", kind="tr"),
}


class TranslateDialog(ToolDialog):
    def __init__(self, ctx, mode: str):
        cfg = MODES[mode]
        super().__init__(ctx, cfg["title"])
        self.mode = mode
        self.kind = cfg["kind"]
        data = ctx.data
        self.lex = data.en_lex if mode == "en_tr" else data.tr_lex
        self.table = data.en_tr if mode == "en_tr" else data.tr_en
        self.current = ""
        self.resize(540, 520)

        self.edit = QLineEdit()
        self.ok_btn = ok_button()
        self.fav = FavButton(ctx, self.kind, lambda: self.current)
        self.words = WordList()
        self.words.set_words(self.lex.words)
        self.meanings = QListWidget()
        self.result = readonly_field()

        top = QHBoxLayout()
        top.addWidget(self.edit, 1)
        top.addWidget(self.ok_btn)
        top.addWidget(self.fav)

        grid = QGridLayout(self)
        grid.addWidget(caption("Sözcük"), 0, 0, 1, 2)
        grid.addLayout(top, 1, 0, 1, 2)
        grid.addWidget(caption(cfg["left"]), 2, 0)
        grid.addWidget(caption(cfg["right"]), 2, 1)
        grid.addWidget(self.words, 3, 0)
        grid.addWidget(self.meanings, 3, 1)
        grid.addWidget(caption(cfg["bottom"]), 4, 0, 1, 2)
        grid.addWidget(self.result, 5, 0, 1, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(3, 1)

        self.timer = QTimer(self, singleShot=True, interval=80)
        self.timer.timeout.connect(self.search)
        self.edit.textChanged.connect(self.timer.start)
        self.edit.returnPressed.connect(self.search)
        self.ok_btn.clicked.connect(self.search)
        self.words.picked.connect(self._picked)
        self.meanings.currentRowChanged.connect(self._meaning_selected)
        self.search()

    def open_word(self, word: str):
        self.edit.setText(word)
        self.search()
        self.show()
        self.raise_()
        self.activateWindow()

    def _picked(self, word: str):
        self.edit.blockSignals(True)
        self.edit.setText(word)
        self.edit.blockSignals(False)
        self._show(word)

    def search(self):
        q = self.edit.text().strip()
        if not q:
            self._show("")
            return
        idx = self.lex.nearest(q)
        self.words.select_row(idx)
        word = self.lex.words[idx]
        # Yazılan metin bulunan sözcüğün başı değilse en yakın komşuyu göster, ama anlam panelini boşalt
        self._show(word if self.lex.match(q) else "", nearest=word)

    def _show(self, word: str, nearest: str = ""):
        self.current = word
        self.meanings.clear()
        if word:
            self.meanings.addItems([f"{i}. {m}" for i, m in enumerate(self.table[word], 1)])
            self.meanings.setCurrentRow(0)
        else:
            self.result.setText(f"“{self.edit.text().strip()}” bulunamadı; en yakın: {nearest}" if nearest else "")
        self.fav.refresh()

    def _meaning_selected(self, row: int):
        if row >= 0 and self.current:
            self.result.setText(self.table[self.current][row])
