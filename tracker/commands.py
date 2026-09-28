"""Telegram commands backed by the tracker database: /today, /week, /search, /state, /sector."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from tracker.bot import Card
from tracker.config import AppConfig
from tracker.db import connect
from tracker.reports import Story, load_stories, pick_top
from tracker.taxonomy import load_taxonomy

MAX_CARDS = 8


def story_card(story: Story) -> Card:
    extra = f" · {story.outlets} outlets" if story.outlets > 1 else ""
    meta = " · ".join(x for x in (story.where, ", ".join(story.sector_labels), story.category_label,
                                  f"{story.band} {story.score}") if x)
    return Card(url=story.url, title=story.title, feed_id="", source_name=story.source_name + extra, meta=meta)


def build_commands(cfg: AppConfig) -> dict:
    tax = load_taxonomy(cfg.config_dir)

    def stories(days: int, min_band: str = "relevant") -> list[Story]:
        conn = connect(cfg.db_path)
        try:
            return load_stories(conn, datetime.now(timezone.utc) - timedelta(days=days), min_band, tax)
        finally:
            conn.close()

    def match_state(query: str) -> str | None:
        q = query.strip().lower()
        for code, state in tax.gazetteer.states.items():
            if q in (code.lower(), state.name.lower()) or (len(q) >= 4 and state.name.lower().startswith(q)):
                return code
        found = tax.gazetteer.names.find(query) or tax.gazetteer.cities.find(query)
        return found[0][1] if found else None

    def today(_: str):
        return [story_card(s) for s in pick_top(stories(1), MAX_CARDS)]

    def week(_: str):
        return [story_card(s) for s in pick_top(stories(7), MAX_CARDS)]

    def search(query: str):
        if not query:
            return "Usage: /search words (e.g. /search NEET counselling)"
        words = [w.lower() for w in query.split()]
        hits = [s for s in stories(14, "peripheral") if all(w in s.title.lower() for w in words)]
        return [story_card(s) for s in hits[:MAX_CARDS]]

    def state(query: str):
        code = match_state(query) if query else None
        if not code:
            return "Usage: /state name (e.g. /state Maharashtra or /state MH)"
        return [story_card(s) for s in stories(7) if code in s.states][:MAX_CARDS]

    def sector(query: str):
        q = query.strip().lower()
        sid = next((sid for sid, sec in tax.sectors.items() if q and (q in sid or q in sec.label.lower())), None)
        if not sid:
            names = ", ".join(sec.label for sec in tax.sectors.values())
            return f"Usage: /sector name ({names})"
        return [story_card(s) for s in stories(7) if sid in s.sectors][:MAX_CARDS]

    return {"/today": today, "/week": week, "/search": search, "/state": state, "/sector": sector}
