"""Read and write the small local RSS 2.0 files the India layer produces for the engine.

Collectors (official-page watcher, Telegram intake, X) each keep a rolling RSS file; the engine
ingests them like any other feed, so its filters, AI tagging, alerts and reports apply unchanged.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime
from pathlib import Path


@dataclass
class FeedItem:
    title: str
    link: str
    published: datetime
    summary: str = ""
    guid: str = ""
    categories: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.guid:
            self.guid = self.link
        if self.published.tzinfo is None:
            self.published = self.published.replace(tzinfo=timezone.utc)


def read_feed(path: Path) -> list[FeedItem]:
    if not path.is_file():
        return []
    root = ET.parse(path).getroot()
    items = []
    for node in root.iter("item"):
        pub = node.findtext("pubDate") or ""
        try:
            published = parsedate_to_datetime(pub)
        except (TypeError, ValueError):
            published = datetime.now(timezone.utc)
        items.append(FeedItem(
            title=node.findtext("title") or "",
            link=node.findtext("link") or "",
            published=published,
            summary=node.findtext("description") or "",
            guid=node.findtext("guid") or "",
            categories=[c.text or "" for c in node.findall("category")],
        ))
    return items


def write_feed(path: Path, title: str, items: list[FeedItem], link: str = "", description: str = "",
               max_items: int = 300) -> Path:
    """Write items newest-first, keeping at most `max_items`."""
    items = sorted(items, key=lambda i: i.published, reverse=True)[:max_items]
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = title
    ET.SubElement(channel, "link").text = link or "about:blank"
    ET.SubElement(channel, "description").text = description or title
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(datetime.now(timezone.utc))
    for item in items:
        node = ET.SubElement(channel, "item")
        ET.SubElement(node, "title").text = item.title
        ET.SubElement(node, "link").text = item.link
        ET.SubElement(node, "guid", isPermaLink="false").text = item.guid
        ET.SubElement(node, "pubDate").text = format_datetime(item.published)
        if item.summary:
            ET.SubElement(node, "description").text = item.summary
        for category in item.categories:
            ET.SubElement(node, "category").text = category
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(rss).write(path, encoding="utf-8", xml_declaration=True)
    return path


def merge_items(existing: list[FeedItem], new: list[FeedItem]) -> list[FeedItem]:
    """New items first; drop any whose guid is already present."""
    seen = {item.guid for item in existing}
    return [item for item in new if item.guid not in seen] + existing
