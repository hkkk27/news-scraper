"""The India layer's own SQLite database (data/tracker.db).

The engine keeps its own per-day databases; this one holds what the India layer adds:
feedback labels, Telegram cards and intake, key/value state, and (from M1-07) tagged items.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS kv (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- One row per training signal. value: 1 = relevant, 0 = not relevant.
CREATE TABLE IF NOT EXISTS feedback (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    item_key   TEXT NOT NULL,
    url        TEXT DEFAULT '',
    title      TEXT DEFAULT '',
    label      TEXT NOT NULL,          -- relevant | not_relevant | key | mute_source | manual
    value      INTEGER,                -- 1 / 0 for relevance labels, NULL otherwise
    feed_id    TEXT DEFAULT '',
    user_id    INTEGER,
    user_name  TEXT DEFAULT '',
    chat_id    INTEGER,
    source     TEXT DEFAULT 'telegram', -- telegram | manual | import
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_feedback_item ON feedback(item_key);

-- Items sent to Telegram as cards, so button presses can be mapped back to the item.
CREATE TABLE IF NOT EXISTS cards (
    item_key   TEXT NOT NULL,
    chat_id    INTEGER NOT NULL,
    message_id INTEGER,
    url        TEXT DEFAULT '',
    title      TEXT DEFAULT '',
    feed_id    TEXT DEFAULT '',
    sent_at    TEXT NOT NULL,
    PRIMARY KEY (item_key, chat_id)
);

-- Things users forwarded to the bot.
CREATE TABLE IF NOT EXISTS intake (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    kind       TEXT NOT NULL,          -- link | pdf | text
    url        TEXT DEFAULT '',
    title      TEXT DEFAULT '',
    chat_id    INTEGER,
    user_id    INTEGER,
    created_at TEXT NOT NULL
);

-- Sources muted by users (the tagger lowers their scores).
CREATE TABLE IF NOT EXISTS muted_sources (
    feed_id    TEXT PRIMARY KEY,
    muted_by   TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def kv_get(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def kv_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT INTO kv(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                 (key, value))
    conn.commit()
