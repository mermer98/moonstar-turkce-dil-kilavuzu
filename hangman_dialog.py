"""Adam Asmaca: orijinal kuralları (6 hata, ipucu -20 puan, her hata -10 puan, MT*.WAV sesleri)."""
from __future__ import annotations

import random

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

import data as dt
import theme
from widgets import ToolDialog, caption

MAX_WRONG = 6


class GallowsCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.wrong = 0
        self.palette_name = "klasik"
        self.setMinimumSize(300, 230)

    def set_state(self, wrong: int, palette_name: str):
        self.wrong, self.palette_name = wrong, palette_name
        self.update()

    def paintEvent(self, _e):
        pal = theme.PALETTES.get(self.palette_name, theme.PALETTES["klasik"])
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(pal["canvas_bg"]))
        sx, sy = self.width() / 300, self.height() / 230
        p.scale(sx, sy)
        ink = QColor(pal["ink"])
        pen = QPen(ink, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        for a, b in (((18, 205), (130, 205)), ((66, 205), (66, 20)), ((66, 20), (152, 20)), ((152, 20), (152, 38))):
            p.drawLine(QPointF(*a), QPointF(*b))
        p.setPen(QPen(ink, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        parts = [
            lambda: p.drawEllipse(QRectF(138, 38, 28, 28)),
            lambda: p.drawLine(QPointF(152, 66), QPointF(152, 118)),
            lambda: p.drawLine(QPointF(152, 84), QPointF(128, 102)),
            lambda: p.drawLine(QPointF(152, 84), QPointF(176, 102)),
            lambda: p.drawLine(QPointF(152, 118), QPointF(132, 156)),
            lambda: p.drawLine(QPointF(152, 118), QPointF(172, 156)),
        ]
        for draw in parts[: self.wrong]:
            draw()
        p.end()


class HangmanDialog(ToolDialog):
    def __init__(self, ctx):
        super().__init__(ctx, "Adam Asmaca — Kelime Oyunu")
        self.word = ""
        self.guessed: set[str] = set()
        self.wrong_letters: list[str] = []
        self.used_hint = False
        self.finished = True
        self.score = 100
        self.hint_text = ""

        self.canvas = GallowsCanvas()
        self.word_label = QLabel("_ _ _")
        self.word_label.setObjectName("bigword")
        self.word_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_label = QLabel("Puan: 100")
        self.hint_label = QLabel("İpucu: -")
        self.wrong_label = QLabel("Yanlış harfler: -")
        self.message = QLabel("Başla ile yeni oyun başlatın.")
        self.message.setObjectName("caption")
        for lbl in (self.hint_label, self.wrong_label, self.message):
            lbl.setWordWrap(True)
        self.summary = QLabel()
        self.difficulty = QComboBox()
        self.difficulty.addItems(list(dt.DIFFICULTY))
        self.difficulty.setCurrentText("Orta")
        self.only_syn = QCheckBox("Sadece eş anlamlısı olanlar")
        self.sound_check = QCheckBox("Ses")
        self.sound_check.setChecked(True)

        letters = QGridLayout()
        letters.setSpacing(2)
        self.letter_buttons: dict[str, QPushButton] = {}
        for i, ch in enumerate(dt.HANGMAN_LETTERS):
            btn = QPushButton(dt.tr_upper(ch))
            btn.setObjectName("letter")
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.clicked.connect(lambda _=False, c=ch: self.guess(c))
            letters.addWidget(btn, i // 2, i % 2)
            self.letter_buttons[ch] = btn

        left = QVBoxLayout()
        left.addWidget(caption("Harfler"))
        left.addLayout(letters)
        left.addStretch(1)

        centre = QVBoxLayout()
        title = QLabel("KELİME OYUNU")
        title.setObjectName("caption")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        centre.addWidget(title)
        centre.addWidget(self.canvas, 1)
        centre.addWidget(caption("Gizli Kelime"))
        centre.addWidget(self.word_label)

        right = QVBoxLayout()
        right.addWidget(caption("Zorluk"))
        right.addWidget(self.difficulty)
        right.addWidget(self.only_syn)
        right.addWidget(self.sound_check)
        right.addSpacing(8)
        right.addWidget(self.score_label)
        right.addWidget(self.hint_label)
        right.addWidget(self.wrong_label)
        right.addWidget(self.message)
        hint_btn = QPushButton("İpucu")
        hint_btn.clicked.connect(self.use_hint)
        right.addWidget(hint_btn)
        right.addStretch(1)
        right.setContentsMargins(0, 0, 0, 0)
        right_w = QWidget()
        right_w.setFixedWidth(210)
        right_w.setLayout(right)

        body = QHBoxLayout()
        body.addLayout(left)
        body.addLayout(centre, 1)
        body.addWidget(right_w)

        dict_btn = QPushButton("Sözlük")
        start_btn = QPushButton("Başla / Yeni Oyun")
        cancel_btn = QPushButton("İptal")
        dict_btn.clicked.connect(self.open_in_dictionary)
        start_btn.clicked.connect(self.start_game)
        cancel_btn.clicked.connect(lambda: self.cancel_game())
        actions = QHBoxLayout()
        for b in (dict_btn, start_btn, cancel_btn):
            actions.addWidget(b)

        root = QVBoxLayout(self)
        root.addLayout(body, 1)
        root.addLayout(actions)
        root.addWidget(self.summary)
        self.resize(720, 520)
        self.sound_check.toggled.connect(lambda on: setattr(ctx.sound, "enabled", on))
        self.cancel_game(initial=True)

    # ---------------------------------------------------------------- oyun akışı
    @property
    def wrong(self) -> int:
        return len(self.wrong_letters)

    def refresh_summary(self):
        s = self.ctx.user.game_summary()
        self.summary.setText(f"Oynanan: {s['played']} | Kazanılan: {s['won']} | Kaybedilen: {s['lost']} | En yüksek puan: {s['high']}")

    def start_game(self):
        words = dt.hangman_words(self.ctx.data, self.difficulty.currentText(), self.only_syn.isChecked())
        self.word = random.choice(words) if words else ""
        self.guessed, self.wrong_letters = set(), []
        self.used_hint, self.hint_text = False, ""
        self.finished = not self.word
        if not self.word:
            self.message.setText("Uygun kelime bulunamadı.")
        else:
            self.message.setText("Tahmin etmeye başlayın.")
            self.ctx.sound.play("new")
        self.refresh()

    def cancel_game(self, initial: bool = False):
        self.word, self.finished = "", True
        self.guessed, self.wrong_letters = set(), []
        self.used_hint, self.hint_text = False, ""
        self.message.setText("Başla ile yeni oyun başlatın." if initial else "Oyun iptal edildi.")
        self.refresh()

    def guess(self, letter: str):
        if self.finished or not self.word or letter in self.guessed:
            return
        self.guessed.add(letter)
        if any(dt.tr_lower(c) == letter for c in self.word):
            self.message.setText(f"Doğru harf: {dt.tr_upper(letter)}")
            self.ctx.sound.play("correct")
            if all(c == " " or dt.tr_lower(c) in self.guessed for c in self.word):
                self.finish(True)
        else:
            self.wrong_letters.append(dt.tr_upper(letter))
            self.message.setText(f"Yanlış harf: {dt.tr_upper(letter)}")
            if self.wrong >= MAX_WRONG:
                self.finish(False)
            else:
                self.ctx.sound.play("lose")
        self.refresh()

    def use_hint(self):
        if self.finished or not self.word:
            return
        hint = dt.hangman_hint(self.ctx.data, self.ctx.tdk, self.word)
        if not hint:
            self.hint_label.setText("İpucu: bulunamadı.")
            return
        self.used_hint, self.hint_text = True, hint
        self.message.setText("İpucu kullanıldı.")
        self.ctx.sound.play("correct")
        self.refresh()

    def finish(self, won: bool):
        self.finished = True
        final = self.score_now() if won else 0
        self.message.setText("Kazandınız!" if won else f"Kaybettiniz. Doğru kelime: {self.word}")
        self.ctx.sound.play("finish")
        self.ctx.user.record_game(self.word, won, self.wrong, self.used_hint, final)

    def score_now(self) -> int:
        return max(0, 100 - self.wrong * 10 - (20 if self.used_hint else 0))

    def open_in_dictionary(self):
        if self.word:
            self.ctx.open_synonyms(self.word)

    def keyPressEvent(self, e):
        text = e.text()
        if len(text) == 1 and text.isalpha():
            self.guess(dt.tr_lower(text))
            return
        super().keyPressEvent(e)

    # ---------------------------------------------------------------- görünüm
    def refresh(self):
        self.score = self.score_now()
        self.score_label.setText(f"Puan: {self.score}")
        self.hint_label.setText(self.hint_text or "İpucu: -")
        self.wrong_label.setText(f"Yanlış harfler: {', '.join(self.wrong_letters) or '-'}")
        if not self.word:
            self.word_label.setText("_ _ _")
        elif self.finished and self.wrong >= MAX_WRONG:
            self.word_label.setText(self.word)
        else:
            self.word_label.setText(" ".join(c if c == " " or dt.tr_lower(c) in self.guessed else "_" for c in self.word))
        self.canvas.set_state(self.wrong, self.ctx.theme_name)
        for ch, btn in self.letter_buttons.items():
            btn.setEnabled(not self.finished and ch not in self.guessed)
        self.refresh_summary()
