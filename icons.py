"""Başlatıcı butonlarının ve banner'ın nostaljik görselleri; hepsi QPainter ile çizilir, dış dosya gerekmez."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PyQt6.QtWidgets import QWidget


def _canvas(w: int, h: int):
    pm = QPixmap(w, h)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    return pm, p


def _star(cx, cy, r, rot=-90):
    pts = []
    for i in range(10):
        ang = math.radians(rot + i * 36)
        rad = r if i % 2 == 0 else r * 0.4
        pts.append(QPointF(cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    return QPolygonF(pts)


def _flag_tr(p: QPainter, r: QRectF):
    p.fillRect(r, QColor("#e30a17"))
    cx, cy, rad = r.left() + r.width() * 0.38, r.center().y(), r.height() * 0.30
    moon = QPainterPath()
    moon.addEllipse(QPointF(cx, cy), rad, rad)
    cut = QPainterPath()
    cut.addEllipse(QPointF(cx + rad * 0.28, cy), rad * 0.8, rad * 0.8)
    p.fillPath(moon.subtracted(cut), QColor("white"))
    p.setBrush(QColor("white"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(_star(cx + rad * 1.15, cy, rad * 0.42, rot=-70))


def _flag_uk(p: QPainter, r: QRectF):
    p.save()
    p.setClipRect(r)
    p.fillRect(r, QColor("#012169"))
    tl, br, tr, bl = r.topLeft(), r.bottomRight(), r.topRight(), r.bottomLeft()
    for color, width in (("white", r.height() * 0.22), ("#c8102e", r.height() * 0.09)):
        p.setPen(QPen(QColor(color), width))
        p.drawLine(tl, br)
        p.drawLine(tr, bl)
    for color, width in (("white", r.height() * 0.34), ("#c8102e", r.height() * 0.20)):
        p.setPen(QPen(QColor(color), width))
        p.drawLine(QPointF(r.left(), r.center().y()), QPointF(r.right(), r.center().y()))
        p.drawLine(QPointF(r.center().x(), r.top()), QPointF(r.center().x(), r.bottom()))
    p.restore()


def _arrow(p: QPainter, x1, x2, y, color="#c00000"):
    p.setPen(QPen(QColor(color), 3))
    p.drawLine(QPointF(x1, y), QPointF(x2 - 4, y))
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(QPolygonF([QPointF(x2, y), QPointF(x2 - 8, y - 5), QPointF(x2 - 8, y + 5)]))


def flags_pixmap(src: str, dst: str) -> QPixmap:
    pm, p = _canvas(76, 30)
    flags = {"tr": _flag_tr, "en": _flag_uk}
    flags[src](p, QRectF(1, 3, 26, 20))
    flags[dst](p, QRectF(49, 3, 26, 20))
    _arrow(p, 29, 47, 13)
    p.setPen(QPen(QColor("#404040"), 1))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRect(QRectF(1, 3, 26, 20))
    p.drawRect(QRectF(49, 3, 26, 20))
    p.end()
    return pm


def check_pixmap() -> QPixmap:
    pm, p = _canvas(40, 40)
    p.setBrush(QColor("white"))
    p.setPen(QPen(QColor("#404040"), 1.5))
    p.drawRect(QRectF(7, 3, 22, 30))
    p.setPen(QPen(QColor("#4a6fd0"), 1.5))
    for y in (10, 15, 20, 25):
        p.drawLine(QPointF(11, y), QPointF(25, y))
    p.setPen(QPen(QColor("#d01010"), 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.drawPolyline(QPolygonF([QPointF(20, 28), QPointF(25, 34), QPointF(36, 18)]))
    p.setPen(QPen(QColor("#404040"), 2))
    p.setBrush(QColor(255, 255, 255, 90))
    p.drawEllipse(QRectF(17, 13, 13, 13))
    p.drawLine(QPointF(28, 24), QPointF(36, 33))
    p.end()
    return pm


def synonyms_pixmap() -> QPixmap:
    pm, p = _canvas(40, 40)
    for cx, cy, color in ((14, 15, "#e0302a"), (27, 13, "#2a8be0"), (20, 24, "#f2c01e"), (31, 26, "#3cb44b"), (11, 28, "#b94fd8")):
        g = QLinearGradient(cx - 7, cy - 7, cx + 7, cy + 7)
        g.setColorAt(0, QColor(color).lighter(150))
        g.setColorAt(1, QColor(color))
        p.setBrush(QBrush(g))
        p.setPen(QPen(QColor("#303030"), 1))
        p.drawEllipse(QPointF(cx, cy), 7.5, 8.5)
        p.drawLine(QPointF(cx, cy + 8.5), QPointF(cx + 2, cy + 14))
    p.end()
    return pm


def keyboard_pixmap() -> QPixmap:
    pm, p = _canvas(40, 40)
    p.setBrush(QColor("#9a9a9a"))
    p.setPen(QPen(QColor("#303030"), 1.5))
    p.drawRoundedRect(QRectF(3, 10, 34, 22), 3, 3)
    p.setBrush(QColor("#f4f4f4"))
    p.setPen(QPen(QColor("#505050"), 1))
    for row, y in enumerate((13, 19, 25)):
        for i in range(6 if row < 2 else 4):
            x = 6 + i * 5.2 + (4 if row == 2 else 0)
            p.drawRect(QRectF(x, y, 4, 4))
    p.end()
    return pm


def hangman_pixmap() -> QPixmap:
    pm, p = _canvas(40, 40)
    pen = QPen(QColor("#202020"), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.drawLine(QPointF(4, 37), QPointF(20, 37))
    p.drawLine(QPointF(10, 37), QPointF(10, 4))
    p.drawLine(QPointF(10, 4), QPointF(26, 4))
    p.drawLine(QPointF(26, 4), QPointF(26, 9))
    p.setBrush(QColor("#202020"))
    p.drawEllipse(QPointF(26, 13), 4.2, 4.2)
    p.drawLine(QPointF(26, 17), QPointF(26, 27))
    p.drawLine(QPointF(26, 20), QPointF(21, 25))
    p.drawLine(QPointF(26, 20), QPointF(31, 25))
    p.drawLine(QPointF(26, 27), QPointF(22, 34))
    p.drawLine(QPointF(26, 27), QPointF(30, 34))
    p.end()
    return pm


def ok_pixmap() -> QPixmap:
    """'Tamam' butonundaki başparmak yerine sarı daire içinde onay işareti."""
    pm, p = _canvas(22, 22)
    p.setBrush(QColor("#f2c01e"))
    p.setPen(QPen(QColor("#6b5200"), 1.2))
    p.drawEllipse(QPointF(11, 11), 9, 9)
    p.setPen(QPen(QColor("#2a6e10"), 2.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.drawPolyline(QPolygonF([QPointF(6.5, 11.5), QPointF(10, 15), QPointF(16, 7)]))
    p.end()
    return pm


def app_icon() -> QIcon:
    pm, p = _canvas(64, 64)
    p.setBrush(QColor("#a00000"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(2, 2, 60, 60), 10, 10)
    moon = QPainterPath()
    moon.addEllipse(QPointF(30, 32), 20, 20)
    cut = QPainterPath()
    cut.addEllipse(QPointF(40, 28), 17, 17)
    p.fillPath(moon.subtracted(cut), QColor("#ffd400"))
    p.setBrush(QColor("#ffd400"))
    p.drawPolygon(_star(46, 22, 7, rot=-70))
    p.end()
    return QIcon(pm)


def pm_icon(pm: QPixmap) -> QIcon:
    return QIcon(pm)


class Banner(QWidget):
    """Başlatıcının altındaki kırmızı 'MoonStar — Özgün programlar yaratın' afişi."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(96)
        self.setMinimumWidth(300)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, QColor("#c00000"))
        g.setColorAt(1, QColor("#6e0000"))
        p.fillRect(r, QBrush(g))
        # küçük bilgisayar
        p.setPen(QPen(QColor("#303030"), 1.5))
        p.setBrush(QColor("#d8d4c8"))
        p.drawRoundedRect(QRectF(14, 20, 40, 34), 3, 3)
        p.setBrush(QColor("#1a2a5a"))
        p.drawRect(QRectF(19, 25, 30, 20))
        p.setBrush(QColor("#d8d4c8"))
        p.drawRect(QRectF(10, 58, 48, 8))
        # logo
        f = QFont("Arial", 27)
        f.setItalic(True)
        f.setWeight(QFont.Weight.Black)
        path = QPainterPath()
        path.addText(QPointF(70, 58), f, "MoonStar")
        p.setPen(QPen(QColor("#2a0000"), 3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        p.fillPath(path, QColor("#ffd400"))
        t = QFont("Times New Roman", 9)
        t.setItalic(True)
        p.setFont(t)
        p.setPen(QColor("white"))
        p.drawText(QPointF(78, 80), "“ Özgün programlar yaratın ”")
        p.end()
