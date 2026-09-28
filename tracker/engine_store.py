"""Read items the engine (TrendRadar) collected, straight from its SQLite files.

Read-only and schema-level (no import of engine code), so the India layer stays decoupled:
    <engine output>/rss/<YYYY-MM-DD>.db    rss_items, rss_feeds
    <engine output>/news/<YYYY-MM-DD>.db   ai_filter_results / ai_filter_tags (source_type = 'rss')
The AI filter's 0-1 relevance score and tag, when present, become the item's engine_score/tag.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from tracker.config import PROJECT_ROOT
from tracker.items import Item
from tracker.log import get_logger

log = get_logger("tracker.engine_store")

DEFAULT_ENGINE_OUTPUT = PROJECT_ROOT / "engine" / "output"


def _ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _ai_scores(news_db: Path) -> dict[int, tuple[float, str]]:
    if not news_db.exists():
        return {}
    try:
        with _ro(news_db) as conn:
            rows = conn.execute(
                "SELECT r.news_item_id AS id, MAX(r.relevance_score) AS score, t.tag AS tag "
                "FROM ai_filter_results r JOIN ai_filter_tags t ON r.tag_id = t.id "
                "WHERE r.source_type = 'rss' AND r.status = 'active' AND t.status = 'active' "
                "GROUP BY r.news_item_id").fetchall()
        return {row["id"]: (float(row["score"] or 0), row["tag"] or "") for row in rows}
    except sqlite3.Error:
        return {}  # AI filter not used


def _to_iso(value: str) -> str:
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return value


def read_engine_items(output_dir: Path = DEFAULT_ENGINE_OUTPUT, days: int = 3, today: date | None = None) -> list[Item]:
    today = today or date.today()
    items: dict[str, Item] = {}
    for offset in range(days):
        day = (today - timedelta(days=offset)).isoformat()
        rss_db = output_dir / "rss" / f"{day}.db"
        if not rss_db.exists():
            continue
        scores = _ai_scores(output_dir / "news" / f"{day}.db")
        with _ro(rss_db) as conn:
            rows = conn.execute(
                "SELECT i.id, i.title, i.url, i.summary, i.published_at, i.first_crawl_time, i.feed_id, "
                "COALESCE(f.name, i.feed_id) AS feed_name FROM rss_items i LEFT JOIN rss_feeds f ON f.id = i.feed_id"
            ).fetchall()
        for row in rows:
            score, tag = scores.get(row["id"], (None, ""))
            item = Item(url=row["url"], title=row["title"], summary=row["summary"] or "", feed_id=row["feed_id"],
                        source_name=row["feed_name"], published_at=_to_iso(row["published_at"] or ""),
                        engine_score=score, engine_tag=tag)
            items.setdefault(item.key, item)  # newest day wins (read first)
    log.info("engine store: %d items from %s", len(items), output_dir)
    return list(items.values())


def engine_available(output_dir: Path = DEFAULT_ENGINE_OUTPUT) -> bool:
    return (output_dir / "rss").is_dir() and any((output_dir / "rss").glob("*.db"))
