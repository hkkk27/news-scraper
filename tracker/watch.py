"""Watch official web pages for new notices, circulars, orders and PDFs.

Same idea as changedetection.io, reduced to what a scheduled job needs: fetch the page, list
its links, compare with the links already seen, and publish the new ones as RSS items.

* First run of a page only records its current links (a baseline), so years-old menu PDFs are
  never reported as "new".
* `max_new` caps what one run can emit, so a site redesign doesn't flood the reports.
* New PDFs can be downloaded (size-capped) to add their first-page text to the summary.
"""

from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urldefrag

from tracker.config import PROJECT_ROOT, read_yaml
from tracker.log import get_logger
from tracker.rssfile import FeedItem, merge_items, read_feed, write_feed

log = get_logger("tracker.watch")

FEEDS_DIR = PROJECT_ROOT / "data" / "feeds"
STATE_PATH = PROJECT_ROOT / "data" / "state" / "watch_seen.json"
MAX_SEEN_PER_PAGE = 3000
PDF_MAX_BYTES = 6 * 1024 * 1024


@dataclass
class WatchPage:
    id: str
    name: str
    url: str
    include: str | None = None
    exclude: str | None = None
    min_text: int = 12
    max_new: int = 15
    pdf_text: bool = True
    prior: int = 15
    sector: str | None = None
    stream: str | None = None
    state: str | None = None

    @property
    def feed_id(self) -> str:
        return f"official-{self.id}"

    @property
    def feed_path(self) -> Path:
        return FEEDS_DIR / f"{self.feed_id}.xml"


@dataclass
class Link:
    url: str
    text: str


@dataclass
class PageResult:
    page_id: str
    ok: bool
    new: int = 0
    baseline: bool = False
    error: str = ""
    items: list[FeedItem] = field(default_factory=list)


def load_watch_pages(config_dir: Path) -> list[WatchPage]:
    path = config_dir / "sources" / "watch.yaml"
    if not path.exists():
        return []
    data = read_yaml(path)
    defaults = data.get("defaults") or {}
    pages = []
    for spec in data.get("pages") or []:
        merged = {**defaults, **spec}
        pages.append(WatchPage(**{k: v for k, v in merged.items() if k in WatchPage.__dataclass_fields__}))
    return pages


GENERIC_LABEL = re.compile(r"\b(read more|click here|download|view details|view|details|more|here|pdf|link|new)\b\W*",
                           re.I)
FILE_SIZE = re.compile(r"\(\s*\d+(?:\.\d+)?\s*(?:KB|MB|kb|mb)\s*\)")
BLOCK_TAGS = {"p", "li", "td", "tr", "div", "span", "dd", "h3", "h4", "h5", "strong"}


def _clean(text: str) -> str:
    return " ".join(FILE_SIZE.sub(" ", text or "").split())


def _link_text(el, min_text: int = 12) -> str:
    """Anchor text, or the surrounding block's text when the anchor says only "Read more" etc."""
    text = _clean(el.text_content() or el.get("title") or "")
    if len(GENERIC_LABEL.sub("", text).strip()) >= min_text:
        return text
    for ancestor in el.iterancestors():
        if ancestor.tag not in BLOCK_TAGS:
            continue
        block = _clean(GENERIC_LABEL.sub(" ", ancestor.text_content() or ""))
        if len(block) > 400:
            break  # reached a container of many notices; don't merge them
        if len(block) >= min_text:
            return block
    return text


def extract_links(html: str, base_url: str) -> list[Link]:
    """All <a href> links, absolute, fragment-free, de-duplicated (longest text wins)."""
    import lxml.html

    try:
        doc = lxml.html.fromstring(html)
    except Exception:
        return []
    doc.make_links_absolute(base_url, resolve_base_href=True)
    best: dict[str, str] = {}
    for el in doc.iter("a"):
        href = (el.get("href") or "").strip()
        if not href.startswith(("http://", "https://")):
            continue
        href = urldefrag(href)[0]
        text = _link_text(el)
        if len(text) > len(best.get(href, "")):
            best[href] = text
        else:
            best.setdefault(href, text)
    return [Link(url, text) for url, text in best.items()]


def select_links(links: list[Link], page: WatchPage) -> list[Link]:
    include = re.compile(page.include, re.I) if page.include else None
    exclude = re.compile(page.exclude, re.I) if page.exclude else None
    chosen = []
    for link in links:
        haystack = f"{link.text} {link.url}"
        if len(link.text) < page.min_text:
            continue
        if include and not include.search(haystack):
            continue
        if exclude and exclude.search(haystack):
            continue
        chosen.append(link)
    return chosen


def pdf_first_page_text(client, url: str, max_chars: int = 600) -> str:
    """Best-effort text of a PDF's first page (empty for scanned PDFs or failures)."""
    try:
        from pypdf import PdfReader

        response = client.get(url)
        if response.status_code != 200 or len(response.content) > PDF_MAX_BYTES:
            return ""
        reader = PdfReader(io.BytesIO(response.content))
        text = reader.pages[0].extract_text() if reader.pages else ""
        return " ".join((text or "").split())[:max_chars]
    except Exception as exc:
        log.debug("pdf text failed for %s: %s", url, exc)
        return ""


def _load_state(path: Path) -> dict[str, list[str]]:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_state(path: Path, state: dict[str, list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=0), encoding="utf-8")


def watch_page(client, page: WatchPage, seen: list[str], now: datetime) -> tuple[PageResult, list[str]]:
    try:
        response = client.get(page.url)
        response.raise_for_status()
    except Exception as exc:
        return PageResult(page.id, ok=False, error=f"{type(exc).__name__}: {exc}"[:200]), seen

    candidates = select_links(extract_links(response.text, str(response.url)), page)
    if not seen:  # first visit: record a baseline, emit nothing
        urls = [link.url for link in candidates]
        return PageResult(page.id, ok=True, baseline=True), urls[-MAX_SEEN_PER_PAGE:]

    seen_set = set(seen)
    new_links = [link for link in candidates if link.url not in seen_set][: page.max_new]
    items = []
    for link in new_links:
        summary = ""
        if page.pdf_text and link.url.lower().split("?")[0].endswith(".pdf"):
            # Many government PDFs are scans without a text layer; say so rather than guess.
            summary = pdf_first_page_text(client, link.url) or f"PDF on {page.name} (no extractable text; likely scanned)"
        categories = [c for c in (page.sector, page.stream, page.state and f"state:{page.state}") if c]
        items.append(FeedItem(title=link.text, link=link.url, published=now,
                              summary=summary or f"New on {page.name}", categories=categories))
    updated = (seen + [link.url for link in new_links])[-MAX_SEEN_PER_PAGE:]
    return PageResult(page.id, ok=True, new=len(items), items=items), updated


def run_watch(pages: list[WatchPage], user_agent: str, timeout: float = 25,
              state_path: Path = STATE_PATH, now: datetime | None = None, client=None) -> list[PageResult]:
    import httpx

    now = now or datetime.now(timezone.utc)
    state = _load_state(state_path)
    own_client = client is None
    client = client or httpx.Client(headers={"User-Agent": user_agent}, timeout=timeout, follow_redirects=True)
    results = []
    try:
        for page in pages:
            result, state[page.id] = watch_page(client, page, state.get(page.id, []), now)
            if result.items:
                existing = read_feed(page.feed_path)
                write_feed(page.feed_path, page.name, merge_items(existing, result.items), link=page.url)
            elif not page.feed_path.exists():
                write_feed(page.feed_path, page.name, [], link=page.url)  # engine expects the file
            status = "baseline recorded" if result.baseline else (f"{result.new} new" if result.ok else result.error)
            log.info("watch %-8s %s", page.id, status)
            results.append(result)
    finally:
        if own_client:
            client.close()
    _save_state(state_path, state)
    return results
