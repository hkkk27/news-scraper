"""L1 rule tagger: sector, category, geography, actors, language and an explainable score.

Every point added or removed is recorded in `reasons`, e.g.
    ["sector higher_education: 'UGC' in title (+40)", "policy + sector (+25)", "actor UGC (+10)", ...]
so the client can see why an item was ranked where it was, and correct it from Telegram.
"""

from __future__ import annotations

from pathlib import Path

from tracker.config import read_yaml
from tracker.items import Item, Tags
from tracker.sources import FeedSpec
from tracker.taxonomy import Taxonomy

# Unicode blocks → language. Devanagari is Hindi unless the source says Marathi.
SCRIPTS = [
    ((0x0900, 0x097F), "hi"), ((0x0980, 0x09FF), "bn"), ((0x0A00, 0x0A7F), "pa"), ((0x0A80, 0x0AFF), "gu"),
    ((0x0B00, 0x0B7F), "or"), ((0x0B80, 0x0BFF), "ta"), ((0x0C00, 0x0C7F), "te"), ((0x0C80, 0x0CFF), "kn"),
    ((0x0D00, 0x0D7F), "ml"),
]
NATIONAL_ACTOR_TYPES = {"ministry", "regulator", "board"}
SCORING_ACTOR_TYPES = {"ministry", "regulator", "board", "court", "election_body"}


def detect_language(text: str, hint: str = "en") -> str:
    counts: dict[str, int] = {}
    for ch in text:
        code = ord(ch)
        if code < 0x0900:
            continue
        for (lo, hi), lang in SCRIPTS:
            if lo <= code <= hi:
                counts[lang] = counts.get(lang, 0) + 1
                break
    if not counts:
        return "en"
    lang = max(counts, key=counts.get)
    if lang == "hi" and hint == "mr":
        return "mr"
    return lang


def load_scoring(config_dir: Path) -> dict:
    path = config_dir / "taxonomy" / "scoring.yaml"
    return read_yaml(path) if path.exists() else {}


class Tagger:
    def __init__(self, taxonomy: Taxonomy, scoring: dict, sources: dict[str, FeedSpec] | None = None,
                 muted_sources: set[str] | None = None):
        self.tax = taxonomy
        self.cfg = scoring
        self.sources = sources or {}
        self.muted = muted_sources or set()
        from tracker.taxonomy import TermMatcher

        self.noise = TermMatcher(scoring.get("noise_terms") or [])

    # --- parts ------------------------------------------------------------------------------

    def _sectors(self, title: str, body: str, reasons: list[str]) -> tuple[list[str], int]:
        c = self.cfg.get("sector", {})
        found: list[tuple[str, int]] = []
        for sid, sector in self.tax.sectors.items():
            hits: list[tuple[int, str, str]] = []
            for matcher, where, points in ((sector.strong, "title", c.get("title_strong", 40)),
                                           (sector.terms, "title", c.get("title_term", 25))):
                hits += [(points, term, where) for term in matcher.terms_in(title)]
            for matcher, where, points in ((sector.strong, "summary", c.get("body_strong", 20)),
                                           (sector.terms, "summary", c.get("body_term", 10))):
                hits += [(points, term, where) for term in matcher.terms_in(body)]
            if not hits:
                continue
            hits.sort(key=lambda h: -h[0])
            distinct = {h[1].lower() for h in hits}
            score = min(hits[0][0] + c.get("extra_hit", 5) * (len(distinct) - 1), c.get("max", 55))
            found.append((sid, score))
            reasons.append(f"sector {sid}: '{hits[0][1]}' in {hits[0][2]}" + (f" +{len(distinct) - 1} more" if len(distinct) > 1 else "")
                           + f" ({score})")
        found.sort(key=lambda f: -f[1])
        min_points = c.get("body_strong", 20)
        sectors = [sid for sid, score in found if score >= min_points]
        return sectors, (found[0][1] if found and sectors else 0)

    def _categories(self, text: str) -> tuple[list[str], bool, list[str]]:
        found = []
        evidence = []
        announcement = False
        for cid, cat in sorted(self.tax.categories.items(), key=lambda kv: kv[1].precedence):
            terms = cat.strong.terms_in(text)
            if not terms:
                continue
            if cat.requires_any is not None:
                required = cat.requires_any.terms_in(text)
                if not required:
                    continue
                terms = terms[:1] + required[:1]
            if cid == "election" and cat.announcement is not None and cat.announcement.terms_in(text):
                announcement = True
            found.append(cid)
            evidence.append(f"{cid}: " + " + ".join(f"'{t}'" for t in terms[:2]))
        return found, announcement, evidence

    def _geography(self, text: str, actor_states: list[str], spec: FeedSpec | None, national_hit: bool,
                   reasons: list[str]) -> tuple[list[str], str]:
        gz = self.tax.gazetteer
        clean = gz.strip_weak(text)
        states: list[str] = []
        for _, code in gz.names.find(clean):
            if code not in states:
                states.append(code)
        for code in actor_states:
            if code not in states:
                states.append(code)
        city_hits = gz.cities.find(clean)
        for _, code in city_hits:
            if code not in states:
                states.append(code)
        if not states and spec and spec.state:
            states.append(spec.state)
        if states:
            reasons.append("state " + ", ".join(states))
        if gz.municipal.find(text) and states:
            level = "municipal"
        elif gz.district.find(text) and states:
            level = "district"
        elif states:
            level = "state"
        else:
            level = "national"
        if national_hit and not states:
            level = "national"
        return states, level

    # --- main -------------------------------------------------------------------------------

    def tag(self, item: Item) -> Tags:
        spec = self.sources.get(item.feed_id)
        title, body = item.title, item.summary
        text = f"{title} {body}"
        reasons: list[str] = []
        tags = Tags(language=detect_language(title, spec.language if spec else "en"))

        tags.sectors, sector_score = self._sectors(title, body, reasons)

        categories, announcement, evidence = self._categories(text)
        hint_only = False
        if not categories and spec and spec.stream:
            categories, hint_only = [spec.stream], True
            evidence.append(f"{spec.stream}: from source focus only")
        tags.category = categories[0] if categories else "news"
        tags.category2 = categories[1] if len(categories) > 1 else None
        if evidence:
            reasons.append("category " + evidence[0])

        actor_hits = [(term, aid) for term, aid in self.tax.actor_matcher.find(text)]
        tags.actors = list(dict.fromkeys(aid for _, aid in actor_hits))
        actor_states = [self.tax.actors[a].state for a in tags.actors if self.tax.actors[a].state]
        national_hit = bool(self.tax.gazetteer.national.find(text)) or any(
            self.tax.actors[a].type in NATIONAL_ACTOR_TYPES and not self.tax.actors[a].state for a in tags.actors)
        tags.states, tags.level = self._geography(text, actor_states, spec, national_hit, reasons)

        # --- score ---
        score = sector_score
        bases = self.cfg.get("stream_base", {})

        def base_of(cat: str) -> tuple[str, int]:
            key = "election_announcement" if cat == "election" and announcement else cat
            return key, bases.get(key, 0)

        # An item can be both (e.g. a court case about voter rolls): count the stronger stream.
        base_key, base = max((base_of(c) for c in categories[:2]), key=lambda kb: kb[1], default=("news", 0))
        if hint_only:
            base = int(base * self.cfg.get("source_hint_only", 0.5))
        if base:
            score += base
            reasons.append(f"{base_key.replace('_', ' ')} (+{base})")
        if tags.sectors and not hint_only:
            bonus = self.cfg.get("sector_bonus", {}).get(tags.category, 0)
            if bonus:
                score += bonus
                reasons.append(f"{tags.category} + sector (+{bonus})")
        scoring_actors = [a for a in tags.actors if self.tax.actors[a].type in SCORING_ACTOR_TYPES]
        if scoring_actors:
            bonus = self.cfg.get("actor_bonus", 10)
            score += bonus
            reasons.append(f"actor {self.tax.actors[scoring_actors[0]].label} (+{bonus})")
        if spec:
            if spec.prior:
                score += spec.prior
                reasons.append(f"source prior (+{spec.prior})")
            if (spec.sector and spec.sector in tags.sectors) or (
                    spec.stream and spec.stream == tags.category and not hint_only):
                bonus = self.cfg.get("hint_bonus", 10)
                score += bonus
                reasons.append(f"source focus agrees (+{bonus})")
        negative = self.tax.negative.terms_in(text)
        if negative:
            neg = self.cfg.get("negative", {})
            penalty = neg.get("with_sector", -15) if tags.sectors else neg.get("without_sector", -45)
            score += penalty
            reasons.append(f"off-topic '{negative[0]}' ({penalty})")
        noise = self.noise.terms_in(text)
        if noise:
            penalty = self.cfg.get("noise_penalty", -45)
            score += penalty
            reasons.append(f"round-up/SEO '{noise[0]}' ({penalty})")
        gz = self.tax.gazetteer
        if gz.foreign.find(text) and not tags.states and not gz.country_names.find(text):
            penalty = self.cfg.get("foreign_without_india", -15)
            score += penalty
            reasons.append(f"foreign, no India link ({penalty})")
        if item.feed_id in self.muted:
            penalty = self.cfg.get("muted_source", -30)
            score += penalty
            reasons.append(f"muted source ({penalty})")
        if spec and spec.type == "manual":
            score = max(score, self.cfg.get("manual_score", 95))
            reasons.append("added by the client")

        tags.rule_score = int(max(0, min(100, score)))
        tags.reasons = reasons
        return tags


def priority_for(score: float, category: str, has_sector: bool, scoring: dict) -> str:
    cfg = scoring.get("priority", {})
    if score >= cfg.get("high_min_score", 80) and category in cfg.get("high_categories", []) and (
            has_sector or category == "transfer"):
        return "high"
    if score >= cfg.get("medium_min_score", 60):
        return "medium"
    return "low"
