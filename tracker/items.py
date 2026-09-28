"""The item model shared by collectors, the tagger, reports and the bot."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

from tracker.urls import item_key

TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    return " ".join(html.unescape(TAG_RE.sub(" ", text or "")).split())


@dataclass
class Item:
    url: str
    title: str
    summary: str = ""
    feed_id: str = ""
    source_name: str = ""        # publisher or feed name
    published_at: str = ""       # ISO 8601 (UTC)
    engine_score: float | None = None   # engine AI-filter relevance (0-1), when the engine ran its AI filter
    engine_tag: str = ""                # engine AI-filter tag

    def __post_init__(self):
        self.title = " ".join((self.title or "").split())
        self.summary = strip_html(self.summary)
        # Google News titles end with " - Publisher"; keep the publisher separately so names like
        # "Punjab Kesari" or "Telangana Today" are not mistaken for places.
        if self.feed_id.startswith("gn-") and " - " in self.title:
            head, _, publisher = self.title.rpartition(" - ")
            if head and len(publisher) <= 60:
                self.title, self.source_name = head.strip(), publisher.strip()
        if self.summary.startswith(self.title):  # Google News repeats the title in the summary
            self.summary = self.summary[len(self.title):].strip(" -–")

    @property
    def key(self) -> str:
        return item_key(self.url)


@dataclass
class Tags:
    sectors: list[str] = field(default_factory=list)
    category: str = "news"
    category2: str | None = None
    states: list[str] = field(default_factory=list)
    level: str = "national"
    actors: list[str] = field(default_factory=list)
    language: str = "en"
    rule_score: int = 0
    reasons: list[str] = field(default_factory=list)
