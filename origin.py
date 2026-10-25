"""Köken (lisan) etiketleri: renkler ve açıklama metinleri."""
from __future__ import annotations

from html import escape

_COLORS = {
    "klasik": {
        "Arapça": "#0b6b3a", "Farsça": "#6a2c91", "Fransızca": "#1b4f9c", "İngilizce": "#a01818",
        "İtalyanca": "#a0600f", "Rumca": "#0b6b8a", "Yunanca": "#0b6b8a", "Latince": "#0b6b8a", "Rusça": "#555555",
        "_": "#7a5c10",
    },
    "karanlık": {
        "Arapça": "#5fd08c", "Farsça": "#c39bf0", "Fransızca": "#7fb2ff", "İngilizce": "#ff8c8c",
        "İtalyanca": "#ffb866", "Rumca": "#6fd0e8", "Yunanca": "#6fd0e8", "Latince": "#6fd0e8", "Rusça": "#b0b0b0",
        "_": "#d8b85a",
    },
}


def color_for(langs: tuple[str, ...], theme: str) -> str | None:
    """Yabancı kökenliyse o dilin rengi; köken belirtilmemişse/yoksa None (varsayılan metin rengi)."""
    foreign = [l for l in langs if l != "Türkçe"]
    if not foreign:
        return None
    palette = _COLORS.get(theme, _COLORS["klasik"])
    return palette.get(foreign[0], palette["_"])


def origin_html(word: str, langs, raw: str, theme: str) -> str:
    """Köken satırı (zengin metin). langs: None=TDK'da yok, ()=köken belirtilmemiş, (...)=yabancı."""
    w = f"<b>{escape(word)}</b>"
    if langs is None:
        return f"{w} — TDK'da kayıt yok"
    if not langs:
        return f"{w} — köken belirtilmemiş (TDK yabancı köken yazmamış; çoğunlukla Türkçe)"
    color = color_for(langs, theme)
    names = " + ".join(langs)
    badge = f'<span style="color:{color}; font-weight:bold">{escape(names)}</span>' if color else escape(names)
    detail = f" ({escape(raw)})" if raw and raw != names else ""
    return f"{w} — köken: {badge}{detail}"
