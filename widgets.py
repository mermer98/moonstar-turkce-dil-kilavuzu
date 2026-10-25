"""Pencerelerin ortak bileşenleri."""
from __future__ import annotations

from PyQt6.QtCore import QStringListModel, Qt, pyqtSignal
from PyQt6.QtWidgets import QAbstractItemView, QDialog, QLabel, QListView, QPushButton

import icons


def caption(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("caption")
    return lbl


def readonly_field(text: str = "") -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("readonly")
    lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    lbl.setMinimumHeight(24)
    return lbl


def ok_button(text: str = "Tamam") -> QPushButton:
    btn = QPushButton(text)
    btn.setIcon(icons.pm_icon(icons.ok_pixmap()))
    btn.setDefault(True)
    return btn


class WordList(QListView):
    """Alfabetik sözcük listesi; programatik seçim `picked` sinyalini tetiklemez."""

    picked = pyqtSignal(str)
    _quiet = False  # setModel() currentChanged'i özniteliklerden önce çağırabilir

    def __init__(self):
        super().__init__()
        self._model = QStringListModel(self)
        self.setModel(self._model)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setUniformItemSizes(True)

    def set_words(self, words: list[str]):
        self._model.setStringList(words)

    def select_row(self, row: int):
        if not 0 <= row < self._model.rowCount():
            return
        idx = self._model.index(row)
        self._quiet = True
        self.setCurrentIndex(idx)
        self.scrollTo(idx, QAbstractItemView.ScrollHint.PositionAtCenter)
        self._quiet = False

    def currentChanged(self, current, previous):
        super().currentChanged(current, previous)
        if not self._quiet and current.isValid():
            self.picked.emit(current.data())


class FavButton(QPushButton):
    """Geçerli sözcüğü favorilere ekler/çıkarır. `get_word` boş dönerse pasif olur."""

    changed = pyqtSignal()

    def __init__(self, ctx, kind: str, get_word):
        super().__init__("☆ Favori")
        self.ctx, self.kind, self.get_word = ctx, kind, get_word
        self.clicked.connect(self._toggle)
        self.refresh()

    def refresh(self):
        word = self.get_word()
        self.setEnabled(bool(word))
        fav = bool(word) and self.ctx.user.is_favorite(word, self.kind)
        self.setText("★ Favori" if fav else "☆ Favori")

    def _toggle(self):
        word = self.get_word()
        if word:
            self.ctx.user.toggle_favorite(word, self.kind)
            self.refresh()
            self.changed.emit()


class ToolDialog(QDialog):
    """Modsuz araç penceresi: kapatılınca silinmez, başlatıcı aynı pencereyi yeniden gösterir."""

    def __init__(self, ctx, title: str):
        super().__init__(ctx)
        self.ctx = ctx
        self.setWindowTitle(title)
        self.setWindowIcon(icons.app_icon())
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
