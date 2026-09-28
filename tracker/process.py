"""The India layer's processing pass: gather items, tag and score them, and save.

    gather  →  engine store (if the engine has run) or direct collection
    tag     →  L1 rules (tracker.tagger)
    score   →  final score and band (the learned model and LLM layers plug in here later)
    save    →  items table (upsert), runs table (evidence log)
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from tracker.config import AppConfig
from tracker.db import connect, utcnow
from tracker.items import Item, Tags
from tracker.log import get_logger
from tracker.sources import FeedSpec, load_sources
from tracker.tagger import Tagger, load_scoring, priority_for
from tracker.taxonomy import load_taxonomy

log = get_logger("tracker.process")


@dataclass
class RunReport:
    run_id: int
    mode: str
    seen: int = 0
    new: int = 0
    relevant: int = 0
    bands: dict[str, int] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)


def gather(cfg: AppConfig, specs: list[FeedSpec], mode: str = "auto") -> tuple[list[Item], dict[str, str], str]:
    from tracker.engine_store import engine_available, read_engine_items

    days = max(1, cfg.settings.collection.lookback_hours // 24)
    if mode == "engine" or (mode == "auto" and engine_available()):
        return read_engine_items(days=days), {}, "engine"
    from tracker.collect import collect

    c = cfg.settings.collection
    items, errors = collect(specs, c.user_agent, c.http_timeout_seconds, c.lookback_hours, c.max_items_per_source)
    return items, errors, "direct"


def upsert_item(conn: sqlite3.Connection, item: Item, tags: Tags, spec: FeedSpec | None, final: int, band: str,
                priority: str, decided_by: str, model_score: float | None = None) -> bool:
    """Insert or update one item. Returns True if it was new."""
    now = utcnow()
    exists = conn.execute("SELECT 1 FROM items WHERE item_key = ?", (item.key,)).fetchone() is not None
    conn.execute(
        """INSERT INTO items(item_key, url, title, summary, feed_id, source_name, source_type, language,
               published_at, first_seen, sectors, category, category2, states, level, actors, rule_score,
               model_score, engine_score, engine_tag, final_score, band, priority, decided_by, reasons, updated_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(item_key) DO UPDATE SET
               title=excluded.title, summary=excluded.summary, sectors=excluded.sectors,
               category=excluded.category, category2=excluded.category2, states=excluded.states,
               level=excluded.level, actors=excluded.actors, rule_score=excluded.rule_score,
               model_score=excluded.model_score, engine_score=COALESCE(excluded.engine_score, items.engine_score),
               engine_tag=CASE WHEN excluded.engine_tag != '' THEN excluded.engine_tag ELSE items.engine_tag END,
               final_score=excluded.final_score, band=excluded.band, priority=excluded.priority,
               decided_by=excluded.decided_by, reasons=excluded.reasons, updated_at=excluded.updated_at""",
        (item.key, item.url, item.title, item.summary[:2000], item.feed_id, item.source_name,
         spec.type if spec else "", tags.language, item.published_at, now, json.dumps(tags.sectors),
         tags.category, tags.category2, json.dumps(tags.states), tags.level, json.dumps(tags.actors),
         tags.rule_score, model_score, item.engine_score, item.engine_tag, final, band, priority, decided_by,
         json.dumps(tags.reasons, ensure_ascii=False), now))
    return not exists


def muted_sources(conn: sqlite3.Connection) -> set[str]:
    return {row["feed_id"] for row in conn.execute("SELECT feed_id FROM muted_sources")}


def human_labels(conn: sqlite3.Connection) -> dict[str, int]:
    """Latest relevance label per item from Telegram/manual feedback (1 relevant, 0 not)."""
    rows = conn.execute("SELECT item_key, value FROM feedback WHERE value IS NOT NULL ORDER BY id").fetchall()
    return {row["item_key"]: row["value"] for row in rows}


def combine(rule_score: int, probability: float | None, engine_score: float | None, model, llm_cfg) -> tuple[int, str]:
    """L1 rules → L2 model → L3 engine AI filter. Returns (final score, deciding layer)."""
    final, decided_by = rule_score, "rules"
    if model is not None and probability is not None and model.weight > 0:
        final, moved = model.blend(rule_score, probability)
        if moved:
            decided_by = "model"
    if engine_score is not None:
        ai = round(100 * engine_score)
        if llm_cfg.uncertain_low <= final <= llm_cfg.uncertain_high:
            final, decided_by = round((final + ai) / 2), "llm"   # AI settles the uncertain band
        elif engine_score >= 0.85 and final < llm_cfg.uncertain_low:
            final, decided_by = max(final, llm_cfg.uncertain_high), "llm"  # AI strongly disagrees with a miss
    return int(max(0, min(100, final))), decided_by


def process(cfg: AppConfig, mode: str = "auto", items: list[Item] | None = None) -> RunReport:
    specs = load_sources(cfg.config_dir, include_disabled=True)
    by_id = {s.id: s for s in specs}
    conn = connect(cfg.db_path)
    run_id = conn.execute("INSERT INTO runs(started_at, mode) VALUES(?, ?)", (utcnow(), mode)).lastrowid
    conn.commit()
    report = RunReport(run_id=run_id, mode=mode)
    try:
        if items is None:
            items, report.errors, report.mode = gather(cfg, [s for s in specs if s.enabled], mode)
        taxonomy = load_taxonomy(cfg.config_dir)
        scoring = load_scoring(cfg.config_dir)
        tagger = Tagger(taxonomy, scoring, by_id, muted_sources(conn))
        bands_cfg = cfg.settings.relevance.bands
        labels = human_labels(conn)
        from tracker.learn import RelevanceModel, text_of

        model = RelevanceModel.load(cfg.settings.relevance.model)
        probabilities = model.probabilities([text_of(i.title, i.summary) for i in items]) if model else []
        for index, item in enumerate(items):
            tags = tagger.tag(item)
            probability = probabilities[index] if probabilities else None
            final, decided_by = combine(tags.rule_score, probability, item.engine_score, model,
                                        cfg.settings.relevance.llm)
            if item.key in labels:  # a human label overrides every model
                final, decided_by = (95 if labels[item.key] else 10), "human"
            band = bands_cfg.band(final)
            priority = priority_for(final, tags.category, bool(tags.sectors), scoring)
            if upsert_item(conn, item, tags, by_id.get(item.feed_id), final, band, priority, decided_by,
                           model_score=probability):
                report.new += 1
            report.bands[band] = report.bands.get(band, 0) + 1
        from tracker.stories import update_stories

        stories = update_stories(conn, cfg.settings.dedup.window_hours, cfg.settings.dedup.story_similarity)
        log.info("grouped recent relevant items into %d stories", stories)
        report.seen = len(items)
        report.relevant = report.bands.get("core", 0) + report.bands.get("relevant", 0)
        purge_before = (datetime.now(timezone.utc) - timedelta(days=cfg.settings.retention.not_relevant_days))
        conn.execute("DELETE FROM items WHERE band = 'not_relevant' AND first_seen < ?",
                     (purge_before.strftime("%Y-%m-%dT%H:%M:%SZ"),))
        status = "ok"
    except Exception as exc:
        report.errors["_run"] = f"{type(exc).__name__}: {exc}"
        status = "failed"
        raise
    finally:
        conn.execute("UPDATE runs SET finished_at=?, mode=?, items_seen=?, items_new=?, relevant=?, errors=?, status=? "
                     "WHERE id=?", (utcnow(), report.mode, report.seen, report.new, report.relevant,
                                   json.dumps(report.errors, ensure_ascii=False), status, run_id))
        conn.commit()
        conn.close()
    log.info("processed %d items (%d new) via %s: %s", report.seen, report.new, report.mode, report.bands)
    return report
