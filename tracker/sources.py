"""Source registry: direct feeds plus Google News query packs, expanded into one feed list.

The same list feeds two consumers:
* the engine (TrendRadar) — exported as its `rss.feeds` config block;
* the India layer — which uses the extra metadata (type, language, prior, sector/stream hints)
  when it scores and tags items.
"""

from __future__ import annotations

import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from tracker.config import read_yaml

GOOGLE_NEWS_SEARCH = "https://news.google.com/rss/search"


@dataclass
class FeedSpec:
    id: str
    name: str
    url: str
    type: str = "national_media"
    language: str = "en"
    prior: int = 0
    sector: str | None = None
    stream: str | None = None
    enabled: bool = True
    max_age_days: int | None = None

    @property
    def is_local(self) -> bool:
        return self.url.startswith("file://")


def google_news_url(query: str, lang: str, hl: str, recency: str = "") -> str:
    q = f"{query} {recency}".strip()
    params = {"q": q, "hl": hl, "gl": "IN", "ceid": f"IN:{lang}"}
    return f"{GOOGLE_NEWS_SEARCH}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"


def _direct_feeds(data: dict) -> list[FeedSpec]:
    out = []
    for spec in data.get("feeds") or []:
        out.append(FeedSpec(
            id=spec["id"],
            name=spec.get("name", spec["id"]),
            url=spec["url"],
            type=spec.get("type", "national_media"),
            language=spec.get("language", "en"),
            prior=int(spec.get("prior", 0)),
            sector=spec.get("sector"),
            stream=spec.get("stream"),
            enabled=bool(spec.get("enabled", True)),
            max_age_days=spec.get("max_age_days"),
        ))
    return out


def _google_news_feeds(data: dict) -> list[FeedSpec]:
    defaults = data.get("defaults") or {}
    languages = data.get("languages") or {}
    out = []
    for pack in data.get("packs") or []:
        recency = pack.get("recency", defaults.get("recency", ""))
        for lang, query in (pack.get("queries") or {}).items():
            lang_cfg = languages.get(lang, {"hl": lang, "enabled": True})
            out.append(FeedSpec(
                id=f"gn-{pack['id']}-{lang}",
                name=f"Google News — {pack.get('name', pack['id'])} ({lang})",
                url=google_news_url(query, lang, lang_cfg.get("hl", lang), recency),
                type=pack.get("type", defaults.get("type", "aggregator")),
                language=lang,
                prior=int(pack.get("prior", 5)),
                sector=pack.get("sector"),
                stream=pack.get("stream"),
                enabled=bool(lang_cfg.get("enabled", True)) and bool(pack.get("enabled", True)),
            ))
    return out


def load_sources(config_dir: Path, include_disabled: bool = False) -> list[FeedSpec]:
    src_dir = config_dir / "sources"
    specs: list[FeedSpec] = []
    if (src_dir / "feeds.yaml").exists():
        specs += _direct_feeds(read_yaml(src_dir / "feeds.yaml"))
    if (src_dir / "google_news.yaml").exists():
        specs += _google_news_feeds(read_yaml(src_dir / "google_news.yaml"))
    ids = [s.id for s in specs]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        raise ValueError(f"duplicate source ids: {sorted(duplicates)}")
    return specs if include_disabled else [s for s in specs if s.enabled]


def engine_feed_entries(specs: list[FeedSpec]) -> list[dict]:
    """The engine's `rss.feeds` entries (TrendRadar format)."""
    entries = []
    for spec in specs:
        entry = {"id": spec.id, "name": spec.name, "url": spec.url, "enabled": spec.enabled}
        if spec.max_age_days is not None:
            entry["max_age_days"] = spec.max_age_days
        entries.append(entry)
    return entries


def export_engine_feeds(specs: list[FeedSpec], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump({"feeds": engine_feed_entries(specs)}, allow_unicode=True, sort_keys=False, width=1000)
    out_path.write_text(text, encoding="utf-8")
    return out_path


def check_sources(specs: list[FeedSpec], user_agent: str, timeout: float = 20, workers: int = 8) -> list[dict]:
    """Fetch every remote feed once and count items. Returns one result dict per spec."""
    import feedparser
    import httpx

    def check(spec: FeedSpec) -> dict:
        result = {"id": spec.id, "status": None, "items": 0, "error": ""}
        if spec.is_local:
            result["error"] = "local file feed (written by the India layer)"
            return result
        try:
            with httpx.Client(headers={"User-Agent": user_agent}, timeout=timeout, follow_redirects=True) as client:
                response = client.get(spec.url)
            result["status"] = response.status_code
            result["items"] = len(feedparser.parse(response.content).entries)
        except Exception as exc:  # network errors are reported, not raised
            result["error"] = f"{type(exc).__name__}: {exc}"[:200]
        return result

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(check, specs))


def as_dict(spec: FeedSpec) -> dict:
    return asdict(spec)
