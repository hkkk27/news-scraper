import json

from tracker.config import PROJECT_ROOT, load_config
from tracker.db import connect, kv_get
from tracker.items import Item
from tracker.llm import AIScore, OpenRouterScorer, load_brief, parse_scores
from tracker.process import ai_scores


class Resp:
    def __init__(self, status, content=None):
        self.status_code = status
        self._body = {"choices": [{"message": {"content": content}}], "model": "m"} if content else {"error": {}}

    def json(self):
        return self._body


class FakeHTTP:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def post(self, url, headers=None, json=None):
        self.calls.append((headers["Authorization"], json["model"]))
        return self.replies.pop(0)


def test_parse_scores_tolerates_fences_and_prose():
    text = 'Sure!\n```json\n[{"i": 1, "score": 88, "why": "transfer"}, {"i": 2, "score": "7"}]\n```'
    assert parse_scores(text) == {1: (0.88, "transfer"), 2: (0.07, "")}
    assert parse_scores("no json here") == {}


def test_busy_model_falls_back_and_bad_key_rotates(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    answer = json.dumps([{"i": 1, "score": 90, "why": "IAS transfer"}])
    http = FakeHTTP([Resp(429), Resp(429), Resp(401), Resp(200, answer)])
    scorer = OpenRouterScorer(["k1", "k2"], ["busy/model", "good/model"], "brief", http=http)
    result = scorer.score([("a", "Rajasthan transfers 14 IAS officers")])
    assert result == {"a": AIScore(0.9, "IAS transfer", "m")}
    assert [c[1] for c in http.calls] == ["busy/model", "busy/model", "good/model", "good/model"]
    assert http.calls[-1][0] == "Bearer k2"  # k1 refused, rotated to k2
    assert scorer.requests_made == 1


def test_brief_comes_from_engine_interests():
    assert "transfers" in load_brief(PROJECT_ROOT / "config").lower()


def test_ai_scores_only_uncertain_uncached_and_counts_requests(tmp_path, monkeypatch):
    cfg = load_config(PROJECT_ROOT / "config")
    monkeypatch.setattr(cfg.secrets, "openrouter_api_keys", ["k"])
    conn = connect(tmp_path / "t.db")

    class Scorer:
        requests_made = 0

        def score(self, items, batch_size, max_requests, max_seconds=150):
            self.requests_made += 1
            self.sent = [k for k, _ in items]
            return {k: AIScore(0.8, "fits brief", "m") for k, _ in items}

    items = [Item(url=f"https://e.com/{n}", title=t, feed_id="x") for n, t in enumerate(["a", "b", "c"])]
    scorer = Scorer()
    out = ai_scores(cfg, conn, [(items[0], 50), (items[1], 90), (items[2], 10)], scorer=scorer)
    assert scorer.sent == [items[0].key]            # only the uncertain one was sent
    assert out == {items[0].key: (0.8, "fits brief")}
    assert int(next(v for k, v in [(r["key"], r["value"]) for r in conn.execute("SELECT * FROM kv")])) == 1
    again = Scorer()
    ai_scores(cfg, conn, [(items[0], 50)], scorer=again)
    assert again.requests_made == 0                 # cached: not sent twice
