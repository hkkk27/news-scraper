"""Story clustering: group reports of the same event from different outlets into one story.

Level 1 (exact) de-duplication happens earlier: every item is keyed by its canonical URL.
This module is level 2 (near-duplicate): items whose normalized titles are similar (TF-IDF
cosine on word 1-2 grams) are grouped, within one language and a time window, and only when
their states agree ("Tamil Nadu NEET counselling" and "Odisha NEET counselling" stay apart).

Normalization makes outlets' wording comparable: "SC" → "supreme court", "Class VI" → "class 6",
"3rd" → "3". Each story keeps a stable id and the number of distinct outlets reporting it,
which reports show as corroboration.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone

ROMAN = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6", "vii": "7", "viii": "8", "ix": "9",
         "x": "10", "xi": "11", "xii": "12"}
NORMALIZE = [
    (re.compile(r"\bsc\b"), "supreme court"),
    (re.compile(r"\bhc\b"), "high court"),
    (re.compile(r"\bapex court\b"), "supreme court"),
    (re.compile(r"\b(three|third|3rd)\b"), "3"),
    (re.compile(r"\b(second|2nd)\b"), "2"),
    (re.compile(r"\b(first|1st)\b"), "1"),
    (re.compile(r"\bclass(?:es)?\s+(i{1,3}|iv|v|vi{0,3}|ix|x|xi{0,2})\b"), lambda m: "class " + ROMAN[m.group(1)]),
    (re.compile(r"\bstd\.?\s*(\d+)"), r"class \1"),
    (re.compile(r"(\d+)(st|nd|rd|th)\b"), r"\1"),
    (re.compile(r"[-–—]"), " "),
]


def normalize_title(title: str) -> str:
    text = (title or "").lower()
    for pattern, replacement in NORMALIZE:
        text = pattern.sub(replacement, text)
    return text


def cluster_items(rows: list[dict], threshold: float = 0.4) -> dict[str, str]:
    """rows: dicts with item_key, title, language, states (list), final_score, first_seen, story_id.

    Returns item_key → story_id. Leaders are the highest-scored items; a story keeps an id one
    of its members already had, so ids stay stable across runs.
    """
    if not rows:
        return {}
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    matrix = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, token_pattern=r"(?u)\b\w+\b") \
        .fit_transform([normalize_title(r["title"]) for r in rows])
    sim = cosine_similarity(matrix)
    order = sorted(range(len(rows)), key=lambda i: (-(rows[i]["final_score"] or 0), rows[i]["first_seen"]))
    members: dict[int, list[int]] = {}
    for i in order:
        best, leader = 0.0, None
        for j in members:
            if rows[j]["language"] != rows[i]["language"]:
                continue
            si, sj = set(rows[i]["states"]), set(rows[j]["states"])
            if si and sj and si != sj:
                continue
            if sim[i, j] > best:
                best, leader = sim[i, j], j
        if leader is not None and best >= threshold:
            members[leader].append(i)
        else:
            members[i] = [i]

    assignment: dict[str, str] = {}
    for leader, group in members.items():
        existing = Counter(rows[i]["story_id"] for i in group if rows[i]["story_id"])
        story_id = existing.most_common(1)[0][0] if existing else rows[leader]["item_key"]
        for i in group:
            assignment[rows[i]["item_key"]] = story_id
    return assignment


def update_stories(conn: sqlite3.Connection, window_hours: int = 72, threshold: float = 0.4,
                   now: datetime | None = None) -> int:
    """Cluster recent items in the database; set story_id and sources_count. Returns story count."""
    now = now or datetime.now(timezone.utc)
    since = (now - timedelta(hours=window_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = [dict(r) for r in conn.execute(
        "SELECT item_key, title, language, states, final_score, first_seen, story_id, source_name, feed_id "
        "FROM items WHERE first_seen >= ? AND band != 'not_relevant'", (since,))]
    for row in rows:
        row["states"] = json.loads(row["states"] or "[]")
    assignment = cluster_items(rows, threshold)
    outlets: dict[str, set[str]] = {}
    for row in rows:
        outlets.setdefault(assignment[row["item_key"]], set()).add(row["source_name"] or row["feed_id"])
    conn.executemany("UPDATE items SET story_id = ?, sources_count = ? WHERE item_key = ?",
                     [(sid, len(outlets[sid]), key) for key, sid in assignment.items()])
    conn.commit()
    return len(outlets)
