"""WAV oynatıcı. MT1-MT6.WAV dosyaları telaffuz değil, orijinal programın oyun/arayüz sesleridir."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QUrl

try:
    from PyQt6.QtMultimedia import QSoundEffect
except ImportError:  # QtMultimedia yoksa winsound'a düş
    QSoundEffect = None

try:
    import winsound
except ImportError:
    winsound = None

# Adam asmaca olaylarının ses dosyaları (orijinal uygulamadaki eşleme)
HANGMAN_SOUNDS = {"new": "MT1.WAV", "correct": "MT2.WAV", "finish": "MT3.WAV", "lose": "MT4.WAV"}


class SoundPlayer:
    def __init__(self, sound_dir: Path, mapping: dict[str, str] | None = None):
        self.paths = {k: sound_dir / v for k, v in (mapping or HANGMAN_SOUNDS).items()}
        self.enabled = True
        self._effects: dict[str, object] = {}

    def play(self, key: str):
        path = self.paths.get(key)
        if not self.enabled or path is None or not path.exists():
            return
        if QSoundEffect is not None:
            fx = self._effects.get(key)
            if fx is None:
                fx = QSoundEffect()
                fx.setSource(QUrl.fromLocalFile(str(path)))
                self._effects[key] = fx
            fx.play()
        elif winsound is not None:
            winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
