"""Build the static dashboard: one HTML file with the data embedded (works from disk or any host).

Published by the workflow to Cloudflare Pages behind Cloudflare Access (email login), or opened
locally. The data is the last N days of stories at or above the configured band, plus the run log.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tracker.config import AppConfig
from tracker.db import connect
from tracker.reports import IST, _same_event, _words, load_stories
from tracker.sources import load_sources
from tracker.taxonomy import load_taxonomy

TEMPLATE = Path(__file__).parent / "site_assets" / "index.html"


def news_date(published: str, first_seen: str, now: datetime) -> str:
    """When the news happened: the publisher's date if it is sane, else when we first saw it."""
    try:
        when = datetime.fromisoformat(published.replace("Z", "+00:00"))
        if when.tzinfo and now - timedelta(days=60) <= when <= now + timedelta(hours=1):
            return when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        pass
    return first_seen
PLACEHOLDER = "/*__TRACKER_DATA__*/null"


def similar_groups(stories, overlap: float = 0.4) -> list[str]:
    """Group id per story: another outlet's take on an already-listed event joins that event's group."""
    leaders: list[tuple[str, set[str]]] = []
    groups = []
    for story in stories:  # stories arrive best-first
        words = _words(story.title)
        leader = next((key for key, lw in leaders if _same_event(words, lw, overlap)), None)
        if leader is None:
            leader = story.item_key
            leaders.append((leader, words))
        groups.append(leader)
    return groups


def build_site(cfg: AppConfig, out_dir: Path | None = None, now: datetime | None = None) -> Path:
    now = now or datetime.now(timezone.utc)
    tax = load_taxonomy(cfg.config_dir)
    days = cfg.settings.dashboard.days
    conn = connect(cfg.db_path)
    try:
        stories = load_stories(conn, now - timedelta(days=days), cfg.settings.dashboard.min_band, tax)
        runs = [dict(r) for r in conn.execute(
            "SELECT started_at, finished_at, mode, items_seen, items_new, relevant, status FROM runs "
            "WHERE started_at >= ? ORDER BY id DESC LIMIT 400",
            ((now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ"),))]
        labels = conn.execute("SELECT COUNT(*) FROM feedback WHERE value IS NOT NULL").fetchone()[0]
        published = {row["item_key"]: row["published_at"] for row in conn.execute(
            "SELECT item_key, published_at FROM items WHERE published_at != ''")}
    finally:
        conn.close()

    data = {
        "profile": cfg.settings.profile.name,
        "generated": now.astimezone(IST).strftime("%d %b %Y, %H:%M IST"),
        "generated_iso": now.isoformat(),
        "labels": labels,
        "sources": len(load_sources(cfg.config_dir)),
        "sectors": {sid: s.label for sid, s in tax.sectors.items()},
        "categories": {cid: c.label for cid, c in tax.categories.items()},
        "states": {code: s.name for code, s in tax.gazetteer.states.items()},
        "stories": [{
            "g": group,
            "t": s.title, "u": s.url if s.is_link else "", "s": s.source_name, "o": s.outlets, "sc": s.score,
            "b": s.band, "p": s.priority, "c": s.category, "sec": s.sectors, "st": s.states, "lv": s.level,
            "lg": s.language, "d": news_date(published.get(s.item_key, ""), s.first_seen, now),
            "why": s.reasons[:4], "by": s.decided_by,
        } for s, group in zip(stories, similar_groups(stories))],
        "runs": runs,
    }
    html = TEMPLATE.read_text(encoding="utf-8").replace(
        PLACEHOLDER, json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    out = out_dir or cfg.resolve(cfg.settings.dashboard.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    return out / "index.html"
