"""MoonStar Türkçe Dil Kılavuzu — PyQt6 yeniden yapımı. Çalıştır: python main.py"""
from __future__ import annotations

import sys

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QMessageBox, QPushButton, QVBoxLayout, QWidget

import data as dt
import icons
import theme
from audio_player import SoundPlayer
from favorites_dialog import FavoritesDialog
from hangman_dialog import HangmanDialog
from keyboard_dialog import KeyboardDialog
from spell_dialog import SpellDialog
from syn_dialog import SynonymDialog
from translate_dialog import TranslateDialog

ABOUT = (
    "<b>MoonStar Türkçe Dil Kılavuzu</b><br>PyQt6 yeniden yapımı<br><br>"
    "1990'ların MoonStar MTU Sözlük programının görünüm ve çalışma mantığından esinlenmiştir.<br>"
    "Veri: moonstar_all.sqlite (MTU.EXE çalışma zamanından çıkarılmış eş anlamlılar ve çeviriler), "
    "isteğe bağlı olarak TDK Güncel Türkçe Sözlük.<br><br>"
    "Orijinal MoonStar programının geliştiricisi merhum Müjdat Özalp'i rahmetle anıyoruz."
)


class Launcher(QWidget):
    """Ana pencere; aynı zamanda diğer pencerelerin kullandığı ortak bağlam (veri, kullanıcı deposu, ses)."""

    def __init__(self, data: dt.DictionaryData, tdk: dt.TdkData, user: dt.UserStore):
        super().__init__()
        self.data, self.tdk, self.user = data, tdk, user
        self.sound = SoundPlayer(dt.SOUND_DIR)
        tdk.preload()  # TDK bellek kopyası arka planda hazırlansın
        self.theme_name = user.get_setting("theme", "klasik")
        self._dialogs: dict[str, QWidget] = {}
        self.setWindowTitle("MoonStar Türkçe Dil Kılavuzu")
        self.setWindowIcon(icons.app_icon())

        buttons = [
            ("Türkçe\nDenetim", icons.check_pixmap(), "spell", 40),
            ("Türkçe / İngilizce", icons.flags_pixmap("tr", "en"), "tr_en", 76),
            ("Türkçe\nEş Anlamlılar", icons.synonyms_pixmap(), "syn", 40),
            ("Klavye", icons.keyboard_pixmap(), "keyboard", 40),
            ("İngilizce / Türkçe", icons.flags_pixmap("en", "tr"), "en_tr", 76),
            ("Adam Asma", icons.hangman_pixmap(), "hangman", 40),
        ]
        grid = QGridLayout()
        grid.setSpacing(4)
        for i, (label, pm, key, w) in enumerate(buttons):
            btn = QPushButton(label)
            btn.setObjectName("launch")
            btn.setIcon(icons.pm_icon(pm))
            btn.setIconSize(QSize(w, pm.height()))
            btn.clicked.connect(lambda _=False, k=key: self.open_tool(k))
            grid.addWidget(btn, i // 3, i % 3)

        fav_btn = QPushButton("★ Favoriler")
        self.theme_btn = QPushButton()
        about_btn = QPushButton("Hakkında")
        fav_btn.clicked.connect(lambda: self.open_tool("favorites"))
        self.theme_btn.clicked.connect(self.toggle_theme)
        about_btn.clicked.connect(lambda: QMessageBox.about(self, "Hakkında", ABOUT))
        foot = QHBoxLayout()
        for b in (fav_btn, self.theme_btn, about_btn):
            foot.addWidget(b)

        root = QVBoxLayout(self)
        root.addLayout(grid)
        root.addWidget(icons.Banner())
        root.addLayout(foot)
        self.apply_theme(self.theme_name)

    # ---------------------------------------------------------------- pencereleri aç
    def _tool(self, key: str) -> QWidget:
        if key not in self._dialogs:
            factory = {
                "spell": lambda: SpellDialog(self),
                "tr_en": lambda: TranslateDialog(self, "tr_en"),
                "en_tr": lambda: TranslateDialog(self, "en_tr"),
                "syn": lambda: SynonymDialog(self),
                "keyboard": lambda: KeyboardDialog(self),
                "hangman": lambda: HangmanDialog(self),
                "favorites": lambda: FavoritesDialog(self),
            }[key]
            self._dialogs[key] = factory()
        return self._dialogs[key]

    def open_tool(self, key: str):
        dlg = self._tool(key)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def open_synonyms(self, word: str = ""):
        dlg = self._tool("syn")
        dlg.open_word(word) if word else self.open_tool("syn")

    def open_favorite(self, word: str, kind: str):
        if kind == "syn":
            self.open_synonyms(word)
        else:
            self._tool("en_tr" if kind == "en" else "tr_en").open_word(word)

    # ---------------------------------------------------------------- tema
    def apply_theme(self, name: str):
        self.theme_name = name
        QApplication.instance().setStyleSheet(theme.THEMES[name])
        self.theme_btn.setText("Tema: Karanlık" if name == "karanlık" else "Tema: Klasik")
        self.user.set_setting("theme", name)
        hang = self._dialogs.get("hangman")
        if hang is not None:
            hang.refresh()

    def toggle_theme(self):
        self.apply_theme("klasik" if self.theme_name == "karanlık" else "karanlık")


def _excepthook(exc_type, exc, tb):
    """PyQt6 yakalanmamış slot hatasında süreci sonlandırır; bunun yerine hatayı göster."""
    import traceback

    text = "".join(traceback.format_exception(exc_type, exc, tb))
    print(text, file=sys.stderr)
    if QApplication.instance() is not None:
        QMessageBox.critical(None, "MoonStar — Hata", text[-1500:])


def main() -> int:
    sys.excepthook = _excepthook
    app = QApplication(sys.argv)
    app.setApplicationName("MoonStar")
    if not dt.ALL_DB.exists():
        QMessageBox.critical(None, "MoonStar", f"Veri dosyası bulunamadı:\n{dt.ALL_DB}")
        return 1
    win = Launcher(dt.DictionaryData(), dt.TdkData(), dt.UserStore())
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
