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

-- Public users who pressed Start; they receive the briefs while telegram.public is on.
-- Only the chat ID is kept (no names): this database is saved to the repository's data branch.
CREATE TABLE IF NOT EXISTS subscribers (
    chat_id    INTEGER PRIMARY KEY,
    active     INTEGER DEFAULT 1,      -- 0 after /stop, or when the user blocked the bot
    joined_at  TEXT NOT NULL
);

-- Sources muted by users (the tagger lowers their scores).
CREATE TABLE IF NOT EXISTS muted_sources (
    feed_id    TEXT PRIMARY KEY,
    muted_by   TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

-- Every item the India layer has seen, with its tags and scores (lists stored as JSON).
CREATE TABLE IF NOT EXISTS items (
    item_key     TEXT PRIMARY KEY,
    url          TEXT NOT NULL,
    title        TEXT NOT NULL,
    summary      TEXT DEFAULT '',
    feed_id      TEXT DEFAULT '',
    source_name  TEXT DEFAULT '',
    source_type  TEXT DEFAULT '',
    language     TEXT DEFAULT 'en',
    published_at TEXT DEFAULT '',
    first_seen   TEXT NOT NULL,
    sectors      TEXT DEFAULT '[]',
    category     TEXT DEFAULT 'news',
    category2    TEXT,
    states       TEXT DEFAULT '[]',
    level        TEXT DEFAULT 'national',
    actors       TEXT DEFAULT '[]',
    rule_score   INTEGER DEFAULT 0,
    model_score  REAL,
    engine_score REAL,
    engine_tag   TEXT DEFAULT '',
    final_score  INTEGER DEFAULT 0,
    band         TEXT DEFAULT 'not_relevant',
    priority     TEXT DEFAULT 'low',
    decided_by   TEXT DEFAULT 'rules',
    reasons      TEXT DEFAULT '[]',
    story_id     TEXT,
    sources_count INTEGER DEFAULT 1,
    updated_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_items_seen ON items(first_seen);
CREATE INDEX IF NOT EXISTS idx_items_band ON items(band);
CREATE INDEX IF NOT EXISTS idx_items_story ON items(story_id);

-- AI (L3) scores, one per item, so an item is never sent twice.
CREATE TABLE IF NOT EXISTS ai_scores (
    item_key   TEXT PRIMARY KEY,
    score      REAL NOT NULL,          -- 0-1
    reason     TEXT DEFAULT '',
    model      TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

-- One row per pipeline run: the evidence log for the 14-day uninterrupted run.
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    mode        TEXT DEFAULT '',
    items_seen  INTEGER DEFAULT 0,
    items_new   INTEGER DEFAULT 0,
    relevant    INTEGER DEFAULT 0,
    errors      TEXT DEFAULT '{}',
    status      TEXT DEFAULT 'running'
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
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns introduced after a database was first created."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(items)")}
    if "sources_count" not in columns:
        conn.execute("ALTER TABLE items ADD COLUMN sources_count INTEGER DEFAULT 1")
        conn.commit()


def kv_get(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def kv_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT INTO kv(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                 (key, value))
    conn.commit()
