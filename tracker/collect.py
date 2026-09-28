"""Direct collector: fetch the registry's feeds without the engine.

Used when the engine has not run (standalone mode, demos, tests). The engine remains the main
collector in production; this path keeps the India layer usable on its own.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from tracker.config import PROJECT_ROOT
from tracker.items import Item
from tracker.log import get_logger
from tracker.sources import FeedSpec

log = get_logger("tracker.collect")


def _published(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc)
    return None


def parse_feed(spec: FeedSpec, content: bytes | str, cutoff: datetime, max_items: int) -> list[Item]:
    import feedparser

    parsed = feedparser.parse(content)
    items = []
    for entry in parsed.entries[:max_items]:
        published = _published(entry)
        if published and published < cutoff:
            continue
        link = entry.get("link") or entry.get("id") or ""
        title = entry.get("title") or ""
        if not link or not title:
            continue
        items.append(Item(url=link, title=title, summary=entry.get("summary", ""), feed_id=spec.id,
                          source_name=spec.name, published_at=published.isoformat() if published else ""))
    return items


def collect(specs: list[FeedSpec], user_agent: str, timeout: float = 20, lookback_hours: int = 72,
            max_items: int = 150, workers: int = 8) -> tuple[list[Item], dict[str, str]]:
    """Fetch all feeds in parallel. Returns (items, errors by feed id)."""
    import httpx

    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    errors: dict[str, str] = {}

    def fetch(spec: FeedSpec) -> list[Item]:
        try:
            if spec.is_local:
                path = PROJECT_ROOT / spec.url[len("file://"):]
                if not path.exists():
                    return []
                return parse_feed(spec, path.read_bytes(), cutoff, max_items)
            with httpx.Client(headers={"User-Agent": user_agent}, timeout=timeout, follow_redirects=True) as client:
                response = client.get(spec.url)
                response.raise_for_status()
            return parse_feed(spec, response.content, cutoff, max_items)
        except Exception as exc:
            errors[spec.id] = f"{type(exc).__name__}: {exc}"[:200]
            return []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        batches = list(pool.map(fetch, specs))
    items: dict[str, Item] = {}
    for batch in batches:
        for item in batch:
            items.setdefault(item.key, item)
    log.info("direct collect: %d items from %d feeds (%d errors)", len(items), len(specs), len(errors))
    return list(items.values()), errors
