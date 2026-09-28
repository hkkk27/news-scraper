import json
from datetime import datetime, timezone

from tracker.db import connect
from tracker.stories import cluster_items, normalize_title, update_stories


def row(key, title, states=(), score=70, lang="en", story=None, seen="2026-09-28T05:00:00Z"):
    return {"item_key": key, "title": title, "language": lang, "states": list(states), "final_score": score,
            "first_seen": seen, "story_id": story}


def test_normalization_aligns_outlet_wording():
    assert normalize_title("SC extends exemption to Class VI") == "supreme court extends exemption to class 6"
    assert normalize_title("3rd-language rule") == "3 language rule"


def test_same_event_different_wording_forms_one_story():
    rows = [
        row("a", "Supreme Court directs CBSE to extend 3rd language policy exemption to Class 6 students", score=100),
        row("b", "SC directs CBSE to extend third language policy exemption to class VI students", score=90),
        row("c", "Extend same third-language policy relief to Class 6 students: SC directs CBSE", score=80),
        row("d", "UGC notifies new rules for foreign university campuses", score=95),
    ]
    stories = cluster_items(rows)
    assert stories["a"] == stories["b"] == stories["c"] == "a"
    assert stories["d"] == "d"


def test_different_states_and_languages_stay_apart():
    rows = [
        row("tn", "Tamil Nadu NEET UG Round 3 Counselling 2026: Registration Open", states=["TN"]),
        row("od", "Odisha NEET UG Round 3 Counselling 2026: Registration Open", states=["OD"]),
        row("hi", "Tamil Nadu NEET UG Round 3 Counselling 2026: Registration Open", states=["TN"], lang="hi"),
    ]
    stories = cluster_items(rows)
    assert len(set(stories.values())) == 3


def test_existing_story_ids_are_kept_stable():
    rows = [row("new", "SC directs CBSE to extend third language exemption to class VI", score=100),
            row("old", "Supreme Court directs CBSE to extend 3rd language exemption to class 6", score=60, story="old")]
    assert cluster_items(rows) == {"new": "old", "old": "old"}


def test_update_stories_sets_ids_and_outlet_counts(tmp_path):
    conn = connect(tmp_path / "t.db")
    for key, title, source in [("a", "SC directs CBSE to extend third language exemption to class VI", "The Hindu"),
                               ("b", "Supreme Court directs CBSE to extend 3rd language exemption to class 6", "NDTV"),
                               ("c", "Rajasthan transfers 14 IAS officers", "Patrika")]:
        conn.execute("INSERT INTO items(item_key, url, title, source_name, first_seen, final_score, band, states, "
                     "updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                     (key, f"https://e.com/{key}", title, source, "2026-09-28T05:00:00Z", 80, "core", json.dumps([]),
                      "2026-09-28T05:00:00Z"))
    conn.commit()
    assert update_stories(conn, now=datetime(2026, 9, 28, 8, tzinfo=timezone.utc)) == 2
    rows = {r["item_key"]: (r["story_id"], r["sources_count"]) for r in conn.execute("SELECT * FROM items")}
    assert rows["a"][0] == rows["b"][0] and rows["a"][1] == 2
    assert rows["c"] == ("c", 1)
