"""Taxonomy and gazetteer: load the vocabularies from config and match them in text.

The matching rules are deliberately simple and explainable (they are shown to the client as
"why this item matched"):

* Latin-script terms match whole words, case-insensitively ("school" does not match "schooling").
* ALL-CAPS terms (CBSE, ITI, UP) match case-sensitively, so "iti" inside "politics" never counts.
* Indic-script terms must start a word; Devanagari/Bengali terms must also end at a word end or
  continue only with a vowel sign (so "छात्र" matches "छात्रों" but "कहा" does not match "कहानी").
  Other Indic scripts (Tamil, Telugu, Kannada, Malayalam, Gujarati...) allow suffixes, because
  those languages attach case endings directly to the word.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from tracker.config import read_yaml, read_yaml_dir

_ASCII_WORD = r"A-Za-z0-9"
# Scripts where a whole-word end check is reliable (inflections are vowel signs, not letters).
_STRICT_END_BLOCKS = [(0x0900, 0x097F), (0x0980, 0x09FF)]  # Devanagari, Bengali/Assamese


def _is_ascii(term: str) -> bool:
    return all(ord(ch) < 128 for ch in term)


def _is_acronym(term: str) -> bool:
    letters = [ch for ch in term if ch.isalpha()]
    return bool(letters) and all(ch.isupper() for ch in letters) and len(term) <= 12


def _strict_end(term: str) -> bool:
    return any(lo <= ord(term[0]) <= hi for lo, hi in _STRICT_END_BLOCKS)


def flatten_terms(value: Any) -> list[str]:
    """Accept a list, or a {language: [terms]} mapping, and return a flat de-duplicated list."""
    if not value:
        return []
    if isinstance(value, dict):
        items: Iterable = (t for terms in value.values() for t in (terms or []))
    else:
        items = value
    seen: dict[str, None] = {}
    for term in items:
        term = str(term).strip()
        if term:
            seen.setdefault(term, None)
    return list(seen)


class TermMatcher:
    """Find which configured terms occur in a text. Each term can carry a payload."""

    def __init__(self, terms: dict[str, Any] | Iterable[str]):
        payloads = dict(terms) if isinstance(terms, dict) else {t: t for t in terms}
        self._ci: dict[str, tuple[str, Any]] = {}
        self._cs: dict[str, tuple[str, Any]] = {}
        self._indic: dict[str, tuple[str, Any]] = {}
        for term, payload in payloads.items():
            if _is_ascii(term):
                if _is_acronym(term):
                    self._cs[term] = (term, payload)
                else:
                    self._ci[term.lower()] = (term, payload)
            else:
                self._indic[unicodedata.normalize("NFC", term)] = (term, payload)
        self._re_ci = self._compile(self._ci.keys(), re.IGNORECASE, ascii_bounds=True)
        self._re_cs = self._compile(self._cs.keys(), 0, ascii_bounds=True)
        self._re_indic = self._compile(self._indic.keys(), 0, ascii_bounds=False)

    @staticmethod
    def _compile(terms: Iterable[str], flags: int, ascii_bounds: bool) -> re.Pattern | None:
        ordered = sorted(set(terms), key=len, reverse=True)
        if not ordered:
            return None
        body = "|".join(re.escape(t) for t in ordered)
        if ascii_bounds:
            return re.compile(rf"(?<![{_ASCII_WORD}])({body})(?![{_ASCII_WORD}])", flags)
        return re.compile(f"({body})", flags)

    def __bool__(self) -> bool:
        return bool(self._ci or self._cs or self._indic)

    def find(self, text: str) -> list[tuple[str, Any]]:
        """Matched (term, payload) pairs in order of first appearance, without repeats."""
        if not text:
            return []
        hits: list[tuple[int, str, Any]] = []
        if self._re_ci:
            hits += [(m.start(), *self._ci[m.group(1).lower()]) for m in self._re_ci.finditer(text)]
        if self._re_cs:
            hits += [(m.start(), *self._cs[m.group(1)]) for m in self._re_cs.finditer(text)]
        if self._re_indic:
            norm = unicodedata.normalize("NFC", text)
            for m in self._re_indic.finditer(norm):
                if self._indic_boundary_ok(norm, m.start(), m.end(), m.group(1)):
                    hits.append((m.start(), *self._indic[m.group(1)]))
        hits.sort(key=lambda h: h[0])
        seen: set[str] = set()
        out: list[tuple[str, Any]] = []
        for _, term, payload in hits:
            if term not in seen:
                seen.add(term)
                out.append((term, payload))
        return out

    def terms_in(self, text: str) -> list[str]:
        return [term for term, _ in self.find(text)]

    @staticmethod
    def _indic_boundary_ok(text: str, start: int, end: int, term: str) -> bool:
        if start > 0 and unicodedata.category(text[start - 1])[0] in "LM":
            return False  # the term is the tail of a longer word
        if end < len(text) and _strict_end(term):
            return unicodedata.category(text[end]) != "Lo"  # a vowel sign (inflection) is fine
        return True


# ---------------------------------------------------------------------------
# Definitions
# ---------------------------------------------------------------------------


@dataclass
class SectorDef:
    id: str
    label: str
    strong: TermMatcher
    terms: TermMatcher


@dataclass
class CategoryDef:
    id: str
    label: str
    precedence: int
    strong: TermMatcher
    requires_any: TermMatcher | None = None
    announcement: TermMatcher | None = None


@dataclass
class ActorDef:
    id: str
    label: str
    type: str
    sectors: list[str] = field(default_factory=list)
    state: str | None = None
    level: str | None = None


@dataclass
class StateDef:
    code: str
    name: str
    type: str


@dataclass
class Gazetteer:
    country: str
    states: dict[str, StateDef]
    names: TermMatcher        # payload: state code (strong)
    cities: TermMatcher       # payload: state code (weaker)
    weak: TermMatcher         # payload: state code (datelines etc.)
    country_names: TermMatcher
    national: TermMatcher
    municipal: TermMatcher
    district: TermMatcher
    foreign: TermMatcher

    def strip_weak(self, text: str) -> str:
        """Blank out weak phrases (e.g. a "New Delhi" dateline) so they don't count as strong names."""
        for term, _ in self.weak.find(text):
            text = text.replace(term, " " * len(term))
        return text


@dataclass
class Taxonomy:
    sectors: dict[str, SectorDef]
    categories: dict[str, CategoryDef]
    actors: dict[str, ActorDef]
    actor_matcher: TermMatcher  # payload: actor id
    negative: TermMatcher
    gazetteer: Gazetteer

    def sector_label(self, sector_id: str) -> str:
        return self.sectors[sector_id].label if sector_id in self.sectors else sector_id

    def category_label(self, category_id: str) -> str:
        return self.categories[category_id].label if category_id in self.categories else category_id

    def state_name(self, code: str) -> str:
        state = self.gazetteer.states.get(code)
        return state.name if state else code


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def _load_sectors(data: dict) -> dict[str, SectorDef]:
    return {
        sid: SectorDef(
            id=sid,
            label=spec.get("label", sid),
            strong=TermMatcher(flatten_terms(spec.get("strong"))),
            terms=TermMatcher(flatten_terms(spec.get("terms"))),
        )
        for sid, spec in (data.get("sectors") or {}).items()
    }


def _load_categories(data: dict) -> dict[str, CategoryDef]:
    out = {}
    for cid, spec in (data.get("categories") or {}).items():
        requires = flatten_terms(spec.get("requires_any"))
        announce = flatten_terms(spec.get("announcement"))
        out[cid] = CategoryDef(
            id=cid,
            label=spec.get("label", cid),
            precedence=int(spec.get("precedence", 50)),
            strong=TermMatcher(flatten_terms(spec.get("strong"))),
            requires_any=TermMatcher(requires) if requires else None,
            announcement=TermMatcher(announce) if announce else None,
        )
    if "news" not in out:
        out["news"] = CategoryDef("news", "Sector news", 99, TermMatcher([]))
    return out


def _load_actors(data: dict) -> tuple[dict[str, ActorDef], TermMatcher]:
    actors: dict[str, ActorDef] = {}
    alias_map: dict[str, str] = {}
    for spec in data.get("actors") or []:
        actor = ActorDef(
            id=spec["id"],
            label=spec.get("label", spec["id"]),
            type=spec.get("type", "other"),
            sectors=list(spec.get("sector") or []),
            state=spec.get("state"),
            level=spec.get("level"),
        )
        actors[actor.id] = actor
        for alias in flatten_terms(spec.get("aliases")):
            alias_map.setdefault(alias, actor.id)
    return actors, TermMatcher(alias_map)


def _load_gazetteer(files: list[tuple[Path, dict]]) -> Gazetteer:
    states: dict[str, StateDef] = {}
    names: dict[str, str] = {}
    cities: dict[str, str] = {}
    weak: dict[str, str] = {}
    lists: dict[str, list[str]] = {k: [] for k in ("country_names", "national_terms", "municipal_terms",
                                                   "district_terms", "foreign_terms")}
    country = "IN"
    for _, data in files:
        country = data.get("country", country)
        for key in lists:
            lists[key] += flatten_terms(data.get(key))
        for spec in data.get("states") or []:
            code = spec["code"]
            states[code] = StateDef(code=code, name=spec.get("name", code), type=spec.get("type", "state"))
            for term in flatten_terms(spec.get("names")):
                names.setdefault(term, code)
            for term in flatten_terms(spec.get("cities")):
                cities.setdefault(term, code)
            for term in flatten_terms(spec.get("weak")):
                weak.setdefault(term, code)
    return Gazetteer(
        country=country,
        states=states,
        names=TermMatcher(names),
        cities=TermMatcher(cities),
        weak=TermMatcher(weak),
        country_names=TermMatcher(lists["country_names"]),
        national=TermMatcher(lists["national_terms"]),
        municipal=TermMatcher(lists["municipal_terms"]),
        district=TermMatcher(lists["district_terms"]),
        foreign=TermMatcher(lists["foreign_terms"]),
    )


def load_taxonomy(config_dir: Path) -> Taxonomy:
    tax_dir = config_dir / "taxonomy"
    sectors_data = read_yaml(tax_dir / "sectors.yaml") if (tax_dir / "sectors.yaml").exists() else {}
    categories_data = read_yaml(tax_dir / "categories.yaml") if (tax_dir / "categories.yaml").exists() else {}
    actors_data = read_yaml(tax_dir / "actors.yaml") if (tax_dir / "actors.yaml").exists() else {}
    actors, actor_matcher = _load_actors(actors_data)
    return Taxonomy(
        sectors=_load_sectors(sectors_data),
        categories=_load_categories(categories_data),
        actors=actors,
        actor_matcher=actor_matcher,
        negative=TermMatcher(flatten_terms(sectors_data.get("negative"))),
        gazetteer=_load_gazetteer(read_yaml_dir(config_dir / "geography")),
    )
