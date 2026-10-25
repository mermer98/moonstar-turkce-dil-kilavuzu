"""Türkçe Eş Anlamlı Sözcükler penceresi (orijinaldeki Sözcük / Kök Sözcük / Anlam Grupları / Eş Anlamları düzeni)
+ TDK anlamı (tıklanabilir ► başvurular), atasözleri/deyimler ve köken etiketleri."""
from __future__ import annotations

import re
from html import escape
from urllib.parse import quote, unquote

from PyQt6.QtCore import QEvent, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QGuiApplication
from PyQt6.QtWidgets import (
    QCheckBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QSplitter,
    QTabWidget, QTextBrowser, QVBoxLayout, QWidget,
)

import origin
from widgets import FavButton, ToolDialog, caption, ok_button, readonly_field

_LINK_COLOR = {"klasik": "#0000cc", "karanlık": "#f2b01e"}


def _ref_target(part: str) -> str:
    part = part.split(":")[0]
    part = re.sub(r"\s*\((?:I|II|III|IV|V|VI|VII|VIII|IX|X)\)", "", part)
    return re.sub(r"\s+karşıtı$", "", part).strip()


def linkify(text: str) -> str:
    """'► kelime, kelime2' biçimindeki çapraz başvuruları tıklanabilir bağlantıya çevirir."""
    if not text.startswith("►"):
        return escape(text)
    out = []
    for part in (p.strip() for p in text[1:].split(",")):
        target = _ref_target(part)
        if target and len(target.split()) <= 3:
            out.append(f'<a href="w:{quote(target)}">{escape(part)}</a>')
        else:
            out.append(escape(part))
    return "► " + ", ".join(out)


class SynonymDialog(ToolDialog):
    def __init__(self, ctx):
        super().__init__(ctx, "Türkçe Eş Anlamlı Sözcükler")
        self.resize(600, 640)
        self.current = ""
        self.history: list[str] = []
        self._groups: list[tuple[str, list[str], bool]] = []
        self._tdk_shown = ""
        self._idioms_for = ""

        self.edit = QLineEdit()
        self.edit.setPlaceholderText("Bir Türkçe sözcük yazın…")
        self.root = readonly_field()
        self.status = readonly_field()
        self.origin_label = QLabel()
        self.origin_label.setWordWrap(True)
        self.origin_label.setTextFormat(Qt.TextFormat.RichText)
        self.turkce_label = QLabel()
        self.turkce_label.setWordWrap(True)
        self.turkce_label.setMinimumHeight(34)
        self.turkce_label.setTextFormat(Qt.TextFormat.RichText)
        self.groups_list = QListWidget()
        self.syn_list = QListWidget()
        self.tdk_check = QCheckBox("TDK anlamını göster")
        self.tdk_check.setChecked(ctx.user.get_setting("syn_tdk", "1") == "1")

        # alt panel: Anlam | Atasözü ve Deyimler
        self.tdk_view = self._browser()
        self.idiom_list = QListWidget()
        self.idiom_view = self._browser()
        split = QSplitter(Qt.Orientation.Vertical)
        split.addWidget(self.idiom_list)
        split.addWidget(self.idiom_view)
        split.setSizes([110, 110])
        self.tabs = QTabWidget()
        self.tabs.addTab(self.tdk_view, "Anlam")
        self.tabs.addTab(split, "Atasözü ve Deyimler")
        self.tabs.setMinimumHeight(190)

        self.ok_btn = ok_button()
        self.back_btn = QPushButton("◄ Geri")
        self.copy_btn = QPushButton("Kopyala")
        self.fav = FavButton(ctx, "syn", lambda: self.current)

        left = QVBoxLayout()
        left.addWidget(caption("Sözcük"))
        left.addWidget(self.edit)
        left.addWidget(caption("Kök Sözcük"))
        left.addWidget(self.root)
        left.addWidget(caption("Anlam Grupları"))
        left.addWidget(self.groups_list, 1)
        row = QHBoxLayout()
        row.addWidget(self.ok_btn)
        row.addWidget(self.back_btn)
        left.addLayout(row)

        right = QVBoxLayout()
        right.addWidget(caption("Eş Anlamları"))
        right.addWidget(self.syn_list, 1)
        row2 = QHBoxLayout()
        row2.addWidget(self.copy_btn)
        row2.addWidget(self.fav)
        right.addLayout(row2)

        grid = QGridLayout(self)
        grid.addLayout(left, 0, 0)
        grid.addLayout(right, 0, 1)
        grid.addWidget(self.status, 1, 0, 1, 2)
        grid.addWidget(self.origin_label, 2, 0, 1, 2)
        grid.addWidget(self.turkce_label, 3, 0, 1, 2)
        grid.addWidget(self.tdk_check, 4, 0, 1, 2)
        grid.addWidget(self.tabs, 5, 0, 1, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(0, 3)
        grid.setRowStretch(5, 2)

        self.timer = QTimer(self, singleShot=True, interval=150)
        self.timer.timeout.connect(self.search)
        self.edit.textChanged.connect(self.timer.start)
        self.edit.returnPressed.connect(lambda: self.search(push=True))
        self.ok_btn.clicked.connect(lambda: self.search(push=True))
        self.back_btn.clicked.connect(self.go_back)
        self.copy_btn.clicked.connect(self.copy_selected)
        self.groups_list.currentRowChanged.connect(self.show_group)
        self.syn_list.itemDoubleClicked.connect(lambda it: self.goto(it.data(Qt.ItemDataRole.UserRole) or it.text()))
        # Eş anlamlının üzerine gelince / seçince alttaki anlam o sözcüğe geçer
        self.syn_list.setMouseTracking(True)
        self.syn_list.viewport().installEventFilter(self)
        self.syn_list.itemEntered.connect(lambda it: self._show_tdk(it.text()))
        self.syn_list.currentItemChanged.connect(self._syn_selected)
        self.idiom_list.currentItemChanged.connect(self._idiom_selected)
        self.tdk_check.toggled.connect(self._tdk_toggled)
        self.tabs.setVisible(self.tdk_check.isChecked())
        self._update_buttons()

    def _browser(self) -> QTextBrowser:
        b = QTextBrowser()
        b.setOpenLinks(False)
        b.setOpenExternalLinks(False)
        b.anchorClicked.connect(self._link_clicked)
        return b

    def _style_browsers(self):
        css = f"a {{ color: {_LINK_COLOR.get(self.ctx.theme_name, '#0000cc')}; }}"
        for b in (self.tdk_view, self.idiom_view):
            b.document().setDefaultStyleSheet(css)

    # ---------------------------------------------------------------- arama
    def open_word(self, word: str):
        self.goto(word)
        self.show()
        self.raise_()
        self.activateWindow()

    def goto(self, word: str, push: bool = True):
        self.edit.blockSignals(True)
        self.edit.setText(word)
        self.edit.blockSignals(False)
        self.search(push=push)

    def _link_clicked(self, url):
        text = url.toString()
        if text.startswith("w:"):
            self.goto(unquote(text[2:]))

    def search(self, push: bool = False):
        query = self.edit.text().strip()
        data = self.ctx.data
        if not query:
            self._clear("", "")
            return
        hw = data.syn_lex.match(query)
        if hw:
            self._show_headword(hw, push)
            return
        syn = data.rev_lex.match(query)
        heads = data.rev.get(syn or "", [])
        if heads:
            self._show_reverse(syn, heads)
            return
        self._clear("Bu sözcük eş anlamlılar sözlüğünde bulunamadı; TDK'da varsa anlamı altta gösterilir.", query)

    def _clear(self, message: str, query: str):
        self.current = ""
        self._groups = []
        self.root.setText("")
        self.groups_list.clear()
        self.syn_list.clear()
        self.status.setText(message)
        self.turkce_label.clear()
        self.origin_label.clear()
        self.tdk_view.clear()
        self._tdk_shown = ""
        self._idioms_for = ""
        self.idiom_list.clear()
        self.idiom_view.clear()
        self.tabs.setTabText(1, "Atasözü ve Deyimler")
        if query:
            self._show_tdk(query)
            self._refresh_idioms(query)
        self.fav.refresh()

    def _show_headword(self, hw: str, push: bool):
        if push and self.current and self.current != hw:
            self.history.append(self.current)
        self.current = hw
        self.root.setText(self.ctx.data.root_of(hw))
        self._groups = self.ctx.data.groups(hw)
        self.groups_list.blockSignals(True)
        self.groups_list.clear()
        self.groups_list.addItems([label for label, _w, _d in self._groups])
        self.groups_list.blockSignals(False)
        self.status.setText(f"{hw} — {sum(len(w) for _l, w, _d in self._groups)} eş anlamlı / türemiş sözcük")
        self._tdk_shown = ""
        if self._groups:
            self.groups_list.setCurrentRow(0)
        else:
            self.syn_list.clear()
            self._after_selection_change()
        self.fav.refresh()
        self._update_buttons()

    def _show_reverse(self, synonym: str, heads: list[str]):
        """Yazılan sözcük başlık değil; eş anlamlı olarak geçtiği başlıkları göster."""
        self.current = ""
        self.root.setText("")
        self._groups = [("Geçtiği başlıklar", heads, False)]
        self.groups_list.blockSignals(True)
        self.groups_list.clear()
        self.groups_list.addItem("Geçtiği başlıklar")
        self.groups_list.blockSignals(False)
        self._tdk_shown = ""
        self.groups_list.setCurrentRow(0)
        self.status.setText(f"“{synonym}” başlık değil; {len(heads)} başlıkta eş anlamlı olarak geçiyor.")
        self.turkce_label.clear()
        self.fav.refresh()
        self._update_buttons()

    def show_group(self, row: int):
        self.syn_list.blockSignals(True)
        self.syn_list.clear()
        if 0 <= row < len(self._groups):
            theme = self.ctx.theme_name
            for word in self._groups[row][1]:
                item = QListWidgetItem(word)
                langs = self.ctx.tdk.origin(word) if self.ctx.tdk.available else None
                color = origin.color_for(langs, theme) if langs else None
                if color:
                    item.setForeground(QBrush(QColor(color)))
                    item.setToolTip(f"Köken: {' + '.join(langs)}")
                self.syn_list.addItem(item)
        self.syn_list.blockSignals(False)
        group = self._groups[row] if 0 <= row < len(self._groups) else None
        self._update_turkce_suggestions(self.current, group[1] if group and not group[2] else [])
        self._after_selection_change()

    def eventFilter(self, obj, event):
        # Fare listeden çıkınca seçili sözcüğün (yoksa başlığın) anlamına dön
        if obj is self.syn_list.viewport() and event.type() == QEvent.Type.Leave:
            self._show_tdk(self._tdk_base())
        return super().eventFilter(obj, event)

    def _syn_selected(self, cur, _prev):
        self._show_tdk(cur.text() if cur else self._tdk_base())
        self._refresh_idioms(self._tdk_base())

    def _after_selection_change(self):
        base = self._tdk_base()
        self._show_tdk(base)
        self._refresh_idioms(base)

    def go_back(self):
        if self.history:
            self.goto(self.history.pop(), push=False)

    def copy_selected(self):
        item = self.syn_list.currentItem()
        if item:
            QGuiApplication.clipboard().setText(item.text())

    def _update_buttons(self):
        self.back_btn.setEnabled(bool(self.history))

    def _tdk_base(self) -> str:
        item = self.syn_list.currentItem()
        return item.text() if item else (self.current or self.edit.text().strip())

    # ---------------------------------------------------------------- köken önerisi
    def _update_turkce_suggestions(self, hw: str, words: list[str]):
        """Başlık yabancı kökenliyse, seçili anlam grubundaki köken belirtilmemiş eş anlamlıları öner."""
        tdk = self.ctx.tdk
        langs = tdk.origin(hw) if hw and tdk.available else None
        if not langs or all(l == "Türkçe" for l in langs):
            self.turkce_label.clear()
            return
        picks = [s for s in words if s != hw and tdk.origin(s) == ()][:6]
        if picks:
            self.turkce_label.setText(
                f"<b>Türkçe karşılık önerisi</b> (TDK'da yabancı köken yazılmamış eş anlamlılar): {escape(', '.join(picks))}"
            )
        else:
            self.turkce_label.clear()

    # ---------------------------------------------------------------- TDK paneli
    def _tdk_toggled(self, on: bool):
        self.ctx.user.set_setting("syn_tdk", "1" if on else "0")
        self.tabs.setVisible(on)
        self._tdk_shown = ""
        self._idioms_for = ""
        if on:
            self._after_selection_change()

    def _show_tdk(self, word: str):
        """Anlam sekmesi ve köken satırı `word` için; üzerine gelince de çağrılır."""
        if not self.tdk_check.isChecked() or not word or word == self._tdk_shown:
            return
        self._tdk_shown = word
        self._style_browsers()
        tdk = self.ctx.tdk
        self.origin_label.setText(origin.origin_html(word, tdk.origin(word), tdk.origin_raw(word), self.ctx.theme_name)
                                  if tdk.available else "")
        res = tdk.lookup(word)
        if res["status"] != "ok":
            note = "TDK anlamı bulunamadı." if res["status"] == "not_found" else "TDK veritabanı yok."
            self.tdk_view.setHtml(f"<b>{escape(word)}</b><br><i>{note}</i>")
            return
        self.tdk_view.setHtml(self._entries_html(res["entries"]))

    def _entries_html(self, entries: list[dict], max_meanings: int = 12) -> str:
        parts = []
        for e in entries:
            head = f"<b>{escape(e['headword'])}</b>"
            if e["origin"]:
                head += f" <i>({escape(e['origin'])})</i>"
            parts.append(head)
            for m in e["meanings"][:max_meanings]:
                kinds = f"<i>{escape(', '.join(m['types']))}</i> " if m["types"] else ""
                parts.append(f"{m['no']}. {kinds}{linkify(m['text'])}")
                for ex, author in m["examples"][:1]:
                    parts.append(f"&nbsp;&nbsp;&nbsp;“{escape(ex)}”" + (f" — <i>{escape(author)}</i>" if author else ""))
            if len(entries) > 1:
                parts.append("<hr>")
        return "<br>".join(parts)

    # ---------------------------------------------------------------- atasözleri ve deyimler
    def _refresh_idioms(self, word: str):
        if not self.tdk_check.isChecked() or word == self._idioms_for:
            return
        self._idioms_for = word
        self.idiom_list.blockSignals(True)
        self.idiom_list.clear()
        self.idiom_view.clear()
        items = self.ctx.tdk.idioms(word) if word else []
        for mid, text in items:
            it = QListWidgetItem(text)
            it.setData(Qt.ItemDataRole.UserRole, (mid, text))
            self.idiom_list.addItem(it)
        self.idiom_list.blockSignals(False)
        self.tabs.setTabText(1, f"Atasözü ve Deyimler ({len(items)})" if items else "Atasözü ve Deyimler")
        if not items:
            self.idiom_view.setHtml("<i>Bu sözcükle ilişkili atasözü veya deyim bulunamadı.</i>" if word else "")
        else:
            self.idiom_view.setHtml("<i>Anlamını görmek için bir atasözü veya deyim seçin.</i>")

    def _idiom_selected(self, cur, _prev):
        if cur is None:
            return
        mid, text = cur.data(Qt.ItemDataRole.UserRole)
        self._style_browsers()
        e = self.ctx.tdk.idiom_detail(mid, text)
        lines = [f"<b>{escape(text)}</b>"]
        for m in e["meanings"]:
            lines.append(f"{m['no']}. {linkify(m['text'])}")
            for ex, author in m["examples"][:2]:
                lines.append(f"&nbsp;&nbsp;&nbsp;“{escape(ex)}”" + (f" — <i>{escape(author)}</i>" if author else ""))
        if not e["meanings"]:
            lines.append("<i>Anlam kaydı yok.</i>")
        self.idiom_view.setHtml("<br>".join(lines))
