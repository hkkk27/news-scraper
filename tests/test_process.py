import json
import sqlite3
from datetime import date

from tracker.config import PROJECT_ROOT, load_config
from tracker.engine_store import engine_available, read_engine_items
from tracker.items import Item
from tracker.process import process

# Minimal copies of the engine's tables (only the columns the reader uses).
RSS_DDL = """
CREATE TABLE rss_feeds (id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE rss_items (id INTEGER PRIMARY KEY, title TEXT, feed_id TEXT, url TEXT, summary TEXT,
                        published_at TEXT, first_crawl_time TEXT);
"""
NEWS_DDL = """
CREATE TABLE ai_filter_tags (id INTEGER PRIMARY KEY, tag TEXT, status TEXT);
CREATE TABLE ai_filter_results (news_item_id INTEGER, source_type TEXT, tag_id INTEGER, relevance_score REAL,
                                status TEXT);
"""


def make_engine_output(root, day):
    (root / "rss").mkdir(parents=True)
    (root / "news").mkdir()
    rss = sqlite3.connect(root / "rss" / f"{day}.db")
    rss.executescript(RSS_DDL)
    rss.execute("INSERT INTO rss_feeds VALUES ('gn-higher-en', 'Google News — Higher education (en)')")
    rss.execute("INSERT INTO rss_items VALUES (1, 'UGC notifies draft regulations - The Hindu', 'gn-higher-en', "
                "'https://example.com/ugc', '<b>UGC</b> notifies', '2026-09-28T04:00:00+00:00', '09:30')")
    rss.execute("INSERT INTO rss_items VALUES (2, 'IPL auction news', 'gn-higher-en', 'https://example.com/ipl', '', "
                "'', '09:30')")
    rss.commit(); rss.close()
    news = sqlite3.connect(root / "news" / f"{day}.db")
    news.executescript(NEWS_DDL)
    news.execute("INSERT INTO ai_filter_tags VALUES (3, 'Education policy', 'active')")
    news.execute("INSERT INTO ai_filter_results VALUES (1, 'rss', 3, 0.92, 'active')")
    news.commit(); news.close()


def test_engine_store_reads_items_and_ai_scores(tmp_path):
    day = date(2026, 9, 28)
    make_engine_output(tmp_path, day.isoformat())
    assert engine_available(tmp_path)
    items = {i.url: i for i in read_engine_items(tmp_path, days=1, today=day)}
    ugc = items["https://example.com/ugc"]
    assert ugc.title == "UGC notifies draft regulations" and ugc.source_name == "The Hindu"
    assert ugc.engine_score == 0.92 and ugc.engine_tag == "Education policy"
    assert items["https://example.com/ipl"].engine_score is None


def test_process_tags_scores_saves_and_logs_run(tmp_path, monkeypatch):
    cfg = load_config(PROJECT_ROOT / "config")
    monkeypatch.setattr(type(cfg), "db_path", property(lambda self: tmp_path / "tracker.db"))
    items = [
        Item(url="https://example.com/a", title="Bombay HC quashes fee hike order for unaided schools", feed_id="livelaw"),
        Item(url="https://example.com/b", title="India vs Pakistan cricket final tonight", feed_id="bhaskar"),
    ]
    report = process(cfg, mode="test", items=items)
    assert report.seen == 2 and report.new == 2 and report.relevant == 1
    again = process(cfg, mode="test", items=items)
    assert again.new == 0

    conn = sqlite3.connect(tmp_path / "tracker.db")
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM items WHERE url = 'https://example.com/a'").fetchone()
    assert row["band"] == "core" and json.loads(row["states"]) == ["MH"] and row["category"] == "court"
    assert row["priority"] == "high" and json.loads(row["reasons"])
    runs = conn.execute("SELECT status, items_seen FROM runs ORDER BY id").fetchall()
    assert [(r["status"], r["items_seen"]) for r in runs] == [("ok", 2), ("ok", 2)]


def test_human_label_overrides_rules(tmp_path, monkeypatch):
    from tracker.db import connect, utcnow
    from tracker.urls import item_key

    cfg = load_config(PROJECT_ROOT / "config")
    monkeypatch.setattr(type(cfg), "db_path", property(lambda self: tmp_path / "tracker.db"))
    conn = connect(tmp_path / "tracker.db")
    conn.execute("INSERT INTO feedback(item_key, label, value, created_at) VALUES(?,?,?,?)",
                 (item_key("https://example.com/b"), "relevant", 1, utcnow()))
    conn.commit(); conn.close()
    process(cfg, mode="test", items=[Item(url="https://example.com/b", title="Something the rules miss",
                                          feed_id="bhaskar")])
    conn = sqlite3.connect(tmp_path / "tracker.db")
    band, decided = conn.execute("SELECT band, decided_by FROM items").fetchone()
    assert (band, decided) == ("core", "human")
