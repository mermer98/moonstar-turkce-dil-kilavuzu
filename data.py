"""Veri katmanı: moonstar_all.sqlite (salt okunur), TDK veritabanı ve kullanıcı verisi (favoriler, oyun istatistikleri)."""
from __future__ import annotations

import random
import re
import sqlite3
import threading
from bisect import bisect_left
from datetime import datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent


def _find_data_dir() -> Path:
    for d in (APP_DIR / "data", APP_DIR, APP_DIR.parent):
        if (d / "moonstar_all.sqlite").exists():
            return d
    return APP_DIR.parent


DATA_DIR = _find_data_dir()
ALL_DB = DATA_DIR / "moonstar_all.sqlite"
TDK_DB = DATA_DIR / "guncel-turkce-sozluk-master" / "sozluk" / "v12" / "v12.gts.sqlite3.db"
USER_DB = APP_DIR / "user_data.sqlite"
SOUND_DIR = DATA_DIR

TR_ALPHABET = "abcçdefgğhıijklmnoöpqrsştuüvwxyz"
_ORDER = {c: i + 2 for i, c in enumerate(TR_ALPHABET)}


def tr_lower(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()


def tr_upper(s: str) -> str:
    return s.replace("i", "İ").replace("ı", "I").upper()


def tr_key(s: str) -> str:
    """Türkçe alfabe sırasına göre sıralama anahtarı."""
    out = []
    for c in tr_lower(s):
        if c == " ":
            out.append(chr(1))
        else:
            out.append(chr(_ORDER.get(c, 100 + min(ord(c), 0xF000))))
    return "".join(out)


def en_key(s: str) -> str:
    return s.casefold()


class Lexicon:
    """Sıralı sözcük listesi; en yakın sözcüğü ikili aramayla bulur."""

    def __init__(self, words, keyfunc):
        self.keyfunc = keyfunc
        pairs = sorted({(keyfunc(w), w) for w in words if w and w.strip()})
        self.keys = [k for k, _ in pairs]
        self.words = [w for _, w in pairs]

    def __len__(self):
        return len(self.words)

    def nearest(self, query: str) -> int:
        if not self.words:
            return -1
        return min(bisect_left(self.keys, self.keyfunc(query)), len(self.words) - 1)

    def match(self, query: str) -> str | None:
        """Yazılan metinle başlayan ilk sözcük (tam eşleşme önce gelir)."""
        q = self.keyfunc(query.strip())
        if not q or not self.words:
            return None
        i = bisect_left(self.keys, q)
        if i < len(self.keys) and self.keys[i].startswith(q):
            return self.words[i]
        return None

    def prefixed(self, query: str, limit: int = 50) -> list[str]:
        q = self.keyfunc(query.strip())
        i = bisect_left(self.keys, q)
        out = []
        while i < len(self.keys) and self.keys[i].startswith(q) and len(out) < limit:
            out.append(self.words[i])
            i += 1
        return out


class DictionaryData:
    def __init__(self, db_path: Path = ALL_DB):
        con = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
        try:
            syn: dict[str, dict[int, list[str]]] = {}
            rev: dict[str, set[str]] = {}
            for hw, s, g, _o in con.execute(
                "select headword, synonym, group_no, order_no from synonyms order by headword, group_no, order_no"
            ):
                lst = syn.setdefault(hw, {}).setdefault(int(g), [])
                if s not in lst:
                    lst.append(s)
                rev.setdefault(s, set()).add(hw)
            en_tr: dict[str, list[str]] = {}
            for e, t in con.execute("select english, turkish from en_tr order by english, order_no"):
                en_tr.setdefault(e, []).append(t)
            tr_en: dict[str, list[str]] = {}
            for t, e in con.execute("select turkish, english from tr_en order by turkish, order_no"):
                tr_en.setdefault(t, []).append(e)
        finally:
            con.close()
        self.syn = syn
        self.rev = {k: sorted(v, key=tr_key) for k, v in rev.items()}
        self.en_tr = {k: list(dict.fromkeys(v)) for k, v in en_tr.items()}
        self.tr_en = {k: list(dict.fromkeys(v)) for k, v in tr_en.items()}
        self.syn_lex = Lexicon(syn, tr_key)
        self.rev_lex = Lexicon(self.rev, tr_key)
        self.en_lex = Lexicon(self.en_tr, en_key)
        self.tr_lex = Lexicon(self.tr_en, tr_key)
        self._roots: dict[str, str] = {}
        for hw, groups in syn.items():
            last = max(groups)
            if self._is_derived(hw, groups[last], last, len(groups)):
                for w in groups[last]:
                    cur = self._roots.get(w)
                    if cur is None or len(hw) < len(cur):
                        self._roots[w] = hw

    @staticmethod
    def _is_derived(headword: str, words: list[str], group_no: int, n_groups: int) -> bool:
        if n_groups < 2 or len(words) < 3:
            return False
        stem = tr_lower(headword)
        return sum(tr_lower(w).startswith(stem) for w in words) / len(words) >= 0.6

    def groups(self, headword: str) -> list[tuple[str, list[str], bool]]:
        """[(etiket, sözcükler, türemiş_mi)] — orijinaldeki '1.Anlam', '2.Anlam', 'Türemiş' grupları."""
        groups = self.syn.get(headword, {})
        out, n = [], 0
        for g in sorted(groups):
            if self._is_derived(headword, groups[g], g, len(groups)) and g == max(groups):
                out.append(("Türemiş", groups[g], True))
            else:
                n += 1
                out.append((f"{n}.Anlam", groups[g], False))
        return out

    def root_of(self, headword: str) -> str:
        return self._roots.get(headword, headword)

    def all_synonyms(self, headword: str) -> list[str]:
        seen = {}
        for _label, words, derived in self.groups(headword):
            if not derived:
                seen.update(dict.fromkeys(words))
        return list(seen)


def parse_langs(lisan: str) -> tuple[str, ...]:
    """'Rumca + Farsça ḫāne' -> ('Rumca', 'Farsça'); boş köken -> ()."""
    out = []
    for part in (lisan or "").split("+"):
        tokens = part.strip().split()
        if tokens and tokens[0][:1].isupper():
            out.append(tokens[0])
    return tuple(out)


_UNACCENT = str.maketrans("âîûÂÎÛ", "aiuaiu")


def unaccent(s: str) -> str:
    return s.translate(_UNACCENT)


_ROMAN_RE = re.compile(r"\s*\((?:I|II|III|IV|V|VI|VII|VIII|IX|X)\)\s*$")


class TdkData:
    """TDK Güncel Türkçe Sözlük. Kaynak dosyada indeks olmadığından, ilk kullanımda gerekli tablolar
    indeksli bir bellek veritabanına kopyalanır (kaynak dosya değiştirilmez)."""

    _TABLES = {
        "madde": "madde_id, madde, trl(madde) as mk, lisan, telaffuz",
        "anlam": "anlam_id, anlam_sira, anlam, madde_id",
        "ornek": "anlam_id, ornek_sira, ornek, yazar_id",
        "yazar": "yazar_id, tam_adi",
        "atasozu": "madde_id, madde",
        "madde_atasozu": "madde_id, atasozu_madde_id",
        "anlam_ozellik": "anlam_id, ozellik_id",
        "ozellik": "ozellik_id, tam_adi, tur",
    }
    _INDEXES = [
        ("madde", "mk"), ("madde", "madde_id"), ("anlam", "madde_id"), ("ornek", "anlam_id"),
        ("madde_atasozu", "madde_id"), ("anlam_ozellik", "anlam_id"), ("atasozu", "madde_id"),
    ]

    def __init__(self, db_path: Path = TDK_DB):
        self.path = db_path
        self.available = db_path.exists()
        self._mem: sqlite3.Connection | None = None
        self._langs: dict[str, tuple[str, ...]] = {}
        self._raw: dict[str, str] = {}
        self._cache: dict[str, dict] = {}
        self._plain: dict[str, str] = {}  # şapkasız yazılış -> TDK'daki yazılış (anahtar)
        self._lock = threading.RLock()

    def preload(self):
        """Bellek kopyasını arka planda hazırla; erken gelen sorgu kilit üzerinde bekler."""
        if self.available and self._mem is None:
            threading.Thread(target=self._db, daemon=True).start()

    def _db(self) -> sqlite3.Connection:
        with self._lock:
            return self._build()

    def _build(self) -> sqlite3.Connection:
        if self._mem is None:
            mem = sqlite3.connect(":memory:", uri=True, check_same_thread=False)
            mem.create_function("trl", 1, tr_lower)
            mem.execute("attach database ? as src", (f"file:{self.path.as_posix()}?mode=ro",))
            for name, cols in self._TABLES.items():
                mem.execute(f"create table {name} as select {cols} from src.{name}")
            for table, col in self._INDEXES:
                mem.execute(f"create index ix_{table}_{col} on {table}({col})")
            mem.commit()
            mem.execute("detach database src")
            langs: dict[str, set[str]] = {}
            for mk, lisan in mem.execute("select mk, lisan from madde"):
                bucket = langs.setdefault(mk, set())
                parsed = parse_langs(lisan)
                bucket.update(parsed)
                if parsed and mk not in self._raw:
                    self._raw[mk] = lisan.strip()
            self._langs = {k: tuple(sorted(v)) for k, v in langs.items()}
            for k in self._langs:
                self._plain.setdefault(unaccent(k), k)
            self._mem = mem
        return self._mem

    def entries(self) -> list[str]:
        if not self.available:
            return []
        return [r[0] for r in self._db().execute("select distinct madde from madde where madde is not null")]

    def _resolve(self, key: str) -> str:
        """Yazılan anahtarı TDK'daki yazılışa eşle (â/î/û farkı)."""
        return key if key in self._langs else self._plain.get(unaccent(key), key)

    def origin(self, word: str):
        """None: TDK'da yok · (): köken belirtilmemiş · ('Arapça', ...): yabancı köken."""
        if not self.available:
            return None
        self._db()
        key = self._resolve(tr_lower(word).strip())
        return self._langs.get(key)

    def origin_raw(self, word: str) -> str:
        self._db()
        return self._raw.get(self._resolve(tr_lower(word).strip()), "")

    def _entry(self, con, mid: int, name: str, lisan: str) -> dict:
        types: dict[int, list[str]] = {}
        for aid, label, kind in con.execute(
            """select ao.anlam_id, oz.tam_adi, oz.tur from anlam a
               join anlam_ozellik ao on ao.anlam_id = a.anlam_id
               join ozellik oz on oz.ozellik_id = ao.ozellik_id where a.madde_id = ? order by a.anlam_sira""",
            (mid,),
        ):
            if label and kind == 3:
                types.setdefault(aid, []).append(label)
        meanings: dict[int, dict] = {}
        for aid, no, text, ex, author in con.execute(
            """select a.anlam_id, a.anlam_sira, a.anlam, o.ornek, y.tam_adi from anlam a
               left join ornek o on o.anlam_id = a.anlam_id left join yazar y on y.yazar_id = o.yazar_id
               where a.madde_id = ? order by a.anlam_sira, o.ornek_sira""",
            (mid,),
        ):
            m = meanings.setdefault(
                aid, {"no": int(no or 0), "text": (text or "").strip(), "types": types.get(aid, []), "examples": []}
            )
            if ex:
                m["examples"].append((ex.strip(), (author or "").strip()))
        return {"madde_id": mid, "headword": name, "origin": (lisan or "").strip(), "meanings": list(meanings.values())}

    def lookup(self, word: str) -> dict:
        """{'status': 'ok'|'missing'|'not_found', 'entries': [...]} — eş sesli maddelerin hepsi; ilk madde ayrıca üst düzeyde."""
        if not self.available:
            return {"status": "missing"}
        con = self._db()
        key = self._resolve(tr_lower(word).strip())
        if key in self._cache:
            return self._cache[key]
        rows = con.execute("select madde_id, madde, lisan from madde where mk = ? order by madde_id", (key,)).fetchall()
        if not rows:
            stripped = _ROMAN_RE.sub("", key)
            if stripped != key:
                rows = con.execute("select madde_id, madde, lisan from madde where mk = ? order by madde_id", (stripped,)).fetchall()
        if not rows:
            result = {"status": "not_found"}
        else:
            entries = [self._entry(con, mid, name, lisan) for mid, name, lisan in rows]
            first = entries[0]
            result = {"status": "ok", "entries": entries, "headword": first["headword"], "origin": first["origin"],
                      "meanings": first["meanings"]}
        self._cache[key] = result
        return result

    def idioms(self, word: str) -> list[tuple[int, str]]:
        """Sözcükle ilişkili atasözü ve deyimler: [(madde_id, metin)]."""
        if not self.available:
            return []
        con = self._db()
        rows = con.execute(
            """select distinct a.madde_id, a.madde from madde m
               join madde_atasozu ma on ma.madde_id = m.madde_id
               join atasozu a on a.madde_id = ma.atasozu_madde_id where m.mk = ?""",
            (self._resolve(tr_lower(word).strip()),),
        ).fetchall()
        return sorted(rows, key=lambda r: tr_key(r[1]))

    def idiom_detail(self, madde_id: int, name: str) -> dict:
        return self._entry(self._db(), madde_id, name, "")


class UserStore:
    """Favoriler, oyun istatistikleri ve ayarlar (SQLite)."""

    def __init__(self, path: Path = USER_DB):
        self.path = path
        with self._con() as con:
            con.executescript(
                """
                create table if not exists favorites (
                    id integer primary key autoincrement, word text not null, kind text not null,
                    created text not null, unique (word, kind));
                create table if not exists hangman_stats (
                    id integer primary key autoincrement, word text not null, won integer not null,
                    wrong_count integer not null, used_hint integer not null, score integer not null, played_at text not null);
                create table if not exists settings (key text primary key, value text not null);
                """
            )

    def _con(self):
        return sqlite3.connect(self.path)

    @staticmethod
    def _now():
        return datetime.now().isoformat(timespec="seconds")

    def is_favorite(self, word: str, kind: str) -> bool:
        with self._con() as con:
            return con.execute("select 1 from favorites where word=? and kind=?", (word, kind)).fetchone() is not None

    def toggle_favorite(self, word: str, kind: str) -> bool:
        with self._con() as con:
            if con.execute("select 1 from favorites where word=? and kind=?", (word, kind)).fetchone():
                con.execute("delete from favorites where word=? and kind=?", (word, kind))
                return False
            con.execute("insert into favorites (word, kind, created) values (?,?,?)", (word, kind, self._now()))
            return True

    def favorites(self) -> list[tuple[str, str]]:
        with self._con() as con:
            return con.execute("select word, kind from favorites order by created desc").fetchall()

    def record_game(self, word: str, won: bool, wrong: int, hint: bool, score: int):
        with self._con() as con:
            con.execute(
                "insert into hangman_stats (word, won, wrong_count, used_hint, score, played_at) values (?,?,?,?,?,?)",
                (word, int(won), wrong, int(hint), score, self._now()),
            )

    def game_summary(self) -> dict:
        with self._con() as con:
            played, won, high = con.execute(
                "select count(*), coalesce(sum(won),0), coalesce(max(score),0) from hangman_stats"
            ).fetchone()
        return {"played": played, "won": won, "lost": played - won, "high": high}

    def get_setting(self, key: str, default: str = "") -> str:
        with self._con() as con:
            row = con.execute("select value from settings where key=?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str):
        with self._con() as con:
            con.execute("insert or replace into settings (key, value) values (?,?)", (key, value))


# ---------------------------------------------------------------- yazım denetimi
_SUFFIXES = sorted(
    set(
        "lar ler ın in un ün ı i u ü a e da de ta te dan den tan ten la le ya ye yı yi yu yü nın nin nun nün sı si su sü "
        "lık lik luk lük cı ci cu cü çı çi çu çü lı li lu lü sız siz suz süz dır dir dur dür tır tir tur tür ım im um üm ız iz uz üz "
        "sın sin sun sün m n k ki mış miş muş müş dı di du dü tı ti tu tü yor acak ecek ma me ar er ır ir ur ür".split()
    ),
    key=len,
    reverse=True,
)
_SOFT = {"ğ": "k", "b": "p", "c": "ç", "d": "t"}
_EDIT_ALPHABET = TR_ALPHABET


class SpellChecker:
    """Sözlük kelime kümesine dayalı basit denetleyici. Çekim eklerini sezgisel olarak soyar; tam bir morfolojik çözümleyici değildir."""

    def __init__(self, data: DictionaryData, tdk: TdkData):
        known: set[str] = set()
        for lex in (data.syn_lex, data.rev_lex, data.tr_lex):
            for w in lex.words:
                known.update(tr_lower(p) for p in re.split(r"[\s\-']+", w) if p)
        for w in tdk.entries():
            known.update(tr_lower(p) for p in re.split(r"[\s\-']+", w) if p)
        self.known = known

    def _has_stem(self, stem: str) -> bool:
        k = self.known
        if stem in k or stem + "mak" in k or stem + "mek" in k:
            return True
        if stem and stem[-1] in _SOFT and (stem[:-1] + _SOFT[stem[-1]]) in k:
            return True
        return False

    def is_known(self, word: str) -> bool:
        w = tr_lower(word)
        if w in self.known or not any(c.isalpha() for c in w):
            return True
        frontier = {w}
        for _ in range(3):
            nxt = set()
            for cur in frontier:
                for s in _SUFFIXES:
                    if cur.endswith(s) and len(cur) - len(s) >= 2:
                        stem = cur[: -len(s)]
                        if self._has_stem(stem):
                            return True
                        nxt.add(stem)
            frontier = nxt
        return False

    def suggest(self, word: str, limit: int = 8) -> list[str]:
        w = tr_lower(word)
        splits = [(w[:i], w[i:]) for i in range(len(w) + 1)]
        cands = set()
        for a, b in splits:
            if b:
                cands.add(a + b[1:])
            if len(b) > 1:
                cands.add(a + b[1] + b[0] + b[2:])
            for c in _EDIT_ALPHABET:
                if b:
                    cands.add(a + c + b[1:])
                cands.add(a + c + b)
        cands.discard(w)
        found = [c for c in cands if c in self.known]
        return sorted(found, key=lambda c: (abs(len(c) - len(w)), tr_key(c)))[:limit]


# ---------------------------------------------------------------- adam asmaca
HANGMAN_RE = re.compile(r"^[A-Za-zÇĞİÖŞÜçğıöşü]+$")
HANGMAN_LETTERS = list("abcçdefgğhıijklmnoöprsştuüvyz")
DIFFICULTY = {"Kolay": (3, 5), "Orta": (6, 8), "Zor": (9, 10_000)}


def hangman_words(data: DictionaryData, difficulty: str, only_synonyms: bool) -> list[str]:
    lo, hi = DIFFICULTY[difficulty]
    out = []
    for w in data.syn_lex.words:
        if HANGMAN_RE.match(w) and lo <= len(w) <= hi and (not only_synonyms or data.all_synonyms(w)):
            out.append(w)
    return out


def hangman_hint(data: DictionaryData, tdk: TdkData, word: str) -> str:
    res = tdk.lookup(word)
    if res.get("status") == "ok":
        for m in res["meanings"]:
            if m["text"] and not m["text"].startswith("►"):
                return f"TDK ipucu: {m['text'][:120]}"
    syns = [s for s in data.all_synonyms(word) if s != word]
    if syns:
        return f"Eş anlamlı ipucu: {random.choice(syns)}"
    return ""
