"""Favoriler: sık kullanılan sözcükler (SQLite)."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout

from widgets import ToolDialog, caption

KIND_LABEL = {"syn": "Eş anlamlı", "en": "İngilizce", "tr": "Türkçe"}


class FavoritesDialog(ToolDialog):
    def __init__(self, ctx):
        super().__init__(ctx, "Favoriler")
        self.list = QListWidget()
        open_btn = QPushButton("Aç")
        del_btn = QPushButton("Favoriden Çıkar")
        open_btn.clicked.connect(self.open_selected)
        del_btn.clicked.connect(self.remove_selected)
        self.list.itemDoubleClicked.connect(lambda _it: self.open_selected())
        row = QHBoxLayout()
        row.addWidget(open_btn)
        row.addWidget(del_btn)
        root = QVBoxLayout(self)
        root.addWidget(caption("Kayıtlı sözcükler (çift tıklayarak açın)"))
        root.addWidget(self.list, 1)
        root.addLayout(row)
        self.resize(360, 420)

    def reload(self):
        self.list.clear()
        for word, kind in self.ctx.user.favorites():
            item = QListWidgetItem(f"{word}   [{KIND_LABEL.get(kind, kind)}]")
            item.setData(Qt.ItemDataRole.UserRole, (word, kind))
            self.list.addItem(item)

    def showEvent(self, e):
        self.reload()
        super().showEvent(e)

    def open_selected(self):
        item = self.list.currentItem()
        if item:
            word, kind = item.data(Qt.ItemDataRole.UserRole)
            self.ctx.open_favorite(word, kind)

    def remove_selected(self):
        item = self.list.currentItem()
        if item:
            word, kind = item.data(Qt.ItemDataRole.UserRole)
            self.ctx.user.toggle_favorite(word, kind)
            self.reload()
