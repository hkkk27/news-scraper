"""Telegram bot: the client's mobile app for training and manual feed-in.

* Item cards carry buttons: 👍 Relevant · 👎 Not relevant · ⭐ Key · 🔇 Mute source.
  A press is stored in the `feedback` table and trains the relevance model.
* Anything forwarded to the bot (a link, a PDF, or plain text) becomes an item in
  data/feeds/manual-feed-in.xml, which the engine ingests; it also counts as a positive label.
* Only chat IDs in TELEGRAM_ALLOWED_CHAT_IDS are served. Anyone else who sends /start is told
  their chat ID so an admin can add it.

Runs in two ways:
* `tracker bot poll`   — process pending updates once (used by the scheduled pipeline).
* `tracker bot listen` — long-poll continuously (instant replies on a laptop or small server).
"""

from __future__ import annotations

import html
import io
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from tracker.config import PROJECT_ROOT
from tracker.db import kv_get, kv_set, utcnow
from tracker.log import get_logger
from tracker.rssfile import FeedItem, merge_items, read_feed, write_feed
from tracker.urls import canonical_url, item_key

log = get_logger("tracker.bot")

MANUAL_FEED = PROJECT_ROOT / "data" / "feeds" / "manual-feed-in.xml"
URL_RE = re.compile(r"https?://[^\s<>\"']+")
LABELS = {
    "r": ("relevant", 1, "👍 Relevant"),
    "n": ("not_relevant", 0, "👎 Not relevant"),
    "k": ("key", 1, "⭐ Key item"),
    "m": ("mute_source", None, "🔇 Source muted"),
}
HELP = (
    "<b>News & Election Tracker</b>\n\n"
    "• Tap the buttons under each item to train me:\n"
    "  👍 relevant · 👎 not relevant · ⭐ key item · 🔇 mute this source\n"
    "• Forward or paste a <b>link</b>, send a <b>PDF</b>, or paste <b>text</b> to add it to the tracker.\n"
    "• /today — today's brief · /search &lt;words&gt; · /state &lt;name&gt; · /sector &lt;name&gt;\n"
    "• /id — show this chat's ID"
)


@dataclass
class Card:
    """What the bot needs to render one item."""
    url: str
    title: str
    feed_id: str = ""
    source_name: str = ""
    meta: str = ""          # e.g. "Maharashtra · Higher education · Court · Core 86"

    @property
    def key(self) -> str:
        return item_key(self.url)


def card_keyboard(key: str) -> dict:
    return {"inline_keyboard": [[
        {"text": "👍", "callback_data": f"fb:r:{key}"},
        {"text": "👎", "callback_data": f"fb:n:{key}"},
        {"text": "⭐", "callback_data": f"fb:k:{key}"},
        {"text": "🔇", "callback_data": f"fb:m:{key}"},
    ]]}


def card_text(card: Card) -> str:
    title = html.escape(card.title.strip())
    lines = [f"<b>{title}</b>"]
    detail = " · ".join(x for x in (card.source_name, card.meta) if x)
    if detail:
        lines.append(html.escape(detail))
    if card.url.startswith("http"):
        lines.append(f'<a href="{html.escape(card.url, quote=True)}">Open</a>')
    return "\n".join(lines)


class Bot:
    def __init__(self, client, conn: sqlite3.Connection, allowed_chat_ids: list[int], http=None,
                 manual_feed: Path = MANUAL_FEED, commands: dict | None = None):
        self.client = client
        self.conn = conn
        self.allowed = set(allowed_chat_ids)
        self.http = http              # used to look up titles of forwarded links
        self.manual_feed = manual_feed
        self.commands = commands or {}  # extra /commands registered by other modules (reports, search)

    # --- sending ------------------------------------------------------------------------------

    def send_cards(self, chat_id: int, cards: list[Card]) -> int:
        sent = 0
        for card in cards:
            message = self.client.send_message(chat_id, card_text(card), reply_markup=card_keyboard(card.key))
            self.conn.execute(
                "INSERT OR REPLACE INTO cards(item_key, chat_id, message_id, url, title, feed_id, sent_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (card.key, chat_id, message.get("message_id"), card.url, card.title, card.feed_id, utcnow()))
            sent += 1
        self.conn.commit()
        return sent

    # --- receiving ----------------------------------------------------------------------------

    def poll_once(self, long_poll_seconds: int = 0) -> dict:
        """Process all pending updates; returns counters. long_poll_seconds > 0 waits for new ones."""
        offset = int(kv_get(self.conn, "telegram_offset", "0") or 0)
        updates = self.client.get_updates(offset=offset + 1 if offset else None, timeout=long_poll_seconds)
        stats = {"updates": len(updates), "feedback": 0, "intake": 0, "ignored": 0}
        for update in updates:
            try:
                kind = self.handle_update(update)
                stats[kind] = stats.get(kind, 0) + 1
            except Exception as exc:  # one bad update must not stop the rest
                log.warning("update %s failed: %s", update.get("update_id"), exc)
            kv_set(self.conn, "telegram_offset", str(update["update_id"]))
        return stats

    def handle_update(self, update: dict) -> str:
        if "callback_query" in update:
            return self.handle_callback(update["callback_query"])
        message = update.get("message") or {}
        chat_id = (message.get("chat") or {}).get("id")
        if chat_id is None:
            return "ignored"
        text = (message.get("text") or message.get("caption") or "").strip()
        if chat_id not in self.allowed:
            if text.startswith(("/start", "/id")):
                self.client.send_message(chat_id, f"This chat's ID is <code>{chat_id}</code>. Ask the tracker "
                                                  "admin to add it to TELEGRAM_ALLOWED_CHAT_IDS.")
            return "ignored"
        if text.startswith("/"):
            return self.handle_command(chat_id, text)
        return self.handle_intake(message)

    def handle_command(self, chat_id: int, text: str) -> str:
        name, _, arg = text.partition(" ")
        name = name.split("@")[0].lower()
        if name in ("/start", "/help"):
            self.client.send_message(chat_id, HELP)
        elif name == "/id":
            self.client.send_message(chat_id, f"This chat's ID is <code>{chat_id}</code>.")
        elif name in self.commands:
            reply = self.commands[name](arg.strip())
            if isinstance(reply, list):  # a list of Cards
                if reply:
                    self.send_cards(chat_id, reply)
                else:
                    self.client.send_message(chat_id, "Nothing found.")
            else:
                self.client.send_message(chat_id, reply or "Nothing found.")
        else:
            self.client.send_message(chat_id, "Unknown command. Send /help.")
        return "command"

    def handle_callback(self, query: dict) -> str:
        data = query.get("data") or ""
        message = query.get("message") or {}
        chat_id = (message.get("chat") or {}).get("id")
        if chat_id not in self.allowed or not data.startswith("fb:"):
            return "ignored"
        _, code, key = data.split(":", 2)
        if code not in LABELS:
            return "ignored"
        label, value, confirmation = LABELS[code]
        user = query.get("from") or {}
        card = self.conn.execute("SELECT url, title, feed_id FROM cards WHERE item_key = ? AND chat_id = ?",
                                 (key, chat_id)).fetchone()
        url, title, feed_id = (card["url"], card["title"], card["feed_id"]) if card else ("", "", "")
        self.conn.execute(
            "INSERT INTO feedback(item_key, url, title, label, value, feed_id, user_id, user_name, chat_id, source, "
            "created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (key, url, title, label, value, feed_id, user.get("id"), user.get("first_name", ""), chat_id,
             "telegram", utcnow()))
        if label == "mute_source" and feed_id:
            self.conn.execute("INSERT OR IGNORE INTO muted_sources(feed_id, muted_by, created_at) VALUES(?,?,?)",
                              (feed_id, user.get("first_name", ""), utcnow()))
        self.conn.commit()
        # Acknowledge. Old callbacks (processed at the next scheduled run) may be expired: ignore.
        for action in (lambda: self.client.answer_callback(query["id"], confirmation),
                       lambda: self.client.edit_reply_markup(chat_id, message.get("message_id"), {
                           "inline_keyboard": [[{"text": f"✓ {confirmation}", "callback_data": "noop"}]]})):
            try:
                action()
            except Exception as exc:
                log.debug("telegram ack skipped: %s", exc)
        return "feedback"

    def handle_intake(self, message: dict) -> str:
        chat_id = message["chat"]["id"]
        user = message.get("from") or {}
        text = (message.get("text") or message.get("caption") or "").strip()
        now = datetime.fromtimestamp(message.get("date", 0) or datetime.now(timezone.utc).timestamp(), timezone.utc)
        items: list[tuple[str, FeedItem]] = []

        document = message.get("document")
        if document and (document.get("mime_type") == "application/pdf"
                         or document.get("file_name", "").lower().endswith(".pdf")):
            summary = self._pdf_text(document["file_id"])
            title = text.splitlines()[0][:200] if text else document.get("file_name", "Uploaded PDF")
            link = f"tg://upload/{document.get('file_unique_id', document['file_id'])}"
            items.append(("pdf", FeedItem(title=title, link=link, published=now, summary=summary or text,
                                          categories=["manual"])))
        else:
            for url in URL_RE.findall(text):
                url = url.rstrip(".,);]")
                title = self._link_title(url) or url
                items.append(("link", FeedItem(title=title, link=canonical_url(url), published=now,
                                               summary=text[:500], categories=["manual"])))
            if not items and text:
                first_line = text.splitlines()[0][:200]
                link = f"tg://message/{chat_id}/{message.get('message_id')}"
                items.append(("text", FeedItem(title=first_line, link=link, published=now, summary=text[:1500],
                                               categories=["manual"])))
        if not items:
            self.client.send_message(chat_id, "Send a link, a PDF or some text to add it. /help for more.")
            return "ignored"

        write_feed(self.manual_feed, "Manual feed-in (Telegram)",
                   merge_items(read_feed(self.manual_feed), [item for _, item in items]))
        for kind, item in items:
            self.conn.execute("INSERT INTO intake(kind, url, title, chat_id, user_id, created_at) VALUES(?,?,?,?,?,?)",
                              (kind, item.link, item.title, chat_id, user.get("id"), utcnow()))
            self.conn.execute(
                "INSERT INTO feedback(item_key, url, title, label, value, feed_id, user_id, user_name, chat_id, "
                "source, created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (item_key(item.link), item.link, item.title, "manual", 1, "manual-feed-in", user.get("id"),
                 user.get("first_name", ""), chat_id, "manual", utcnow()))
        self.conn.commit()
        added = "\n".join(f"• {html.escape(item.title[:120])}" for _, item in items)
        self.client.send_message(chat_id, f"✅ Added to the tracker:\n{added}")
        return "intake"

    # --- helpers --------------------------------------------------------------------------------

    def _link_title(self, url: str) -> str:
        if self.http is None:
            return ""
        try:
            response = self.http.get(url)
            match = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', response.text, re.I) \
                or re.search(r"<title[^>]*>(.*?)</title>", response.text, re.I | re.S)
            return html.unescape(" ".join(match.group(1).split()))[:250] if match else ""
        except Exception:
            return ""

    def _pdf_text(self, file_id: str) -> str:
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(self.client.download_file(file_id)))
            text = reader.pages[0].extract_text() if reader.pages else ""
            return " ".join((text or "").split())[:1500]
        except Exception as exc:
            log.debug("pdf intake text failed: %s", exc)
            return ""
