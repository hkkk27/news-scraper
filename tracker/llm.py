"""L3: an AI relevance check for the items rules and the model are unsure about.

Uses OpenRouter's free models (OpenAI-compatible chat API), so it costs nothing. Only items in
the uncertain band are sent, 20 per request, with a daily request cap; answers are cached per
item so an item is never scored twice. Several API keys and models can be listed: a key that
is rate-limited or out of quota moves to the next key, a model that is busy moves to the next
model. With no key configured the layer is simply skipped.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

from tracker.log import get_logger

log = get_logger("tracker.llm")

API = "https://openrouter.ai/api/v1/chat/completions"
PROMPT = """You score Indian news items for a client's tracker. The client's brief:

{brief}

Score each numbered item 0-100 for relevance to the brief:
80-100 core (a decision, order, ruling, transfer or election notice squarely in scope),
60-79 relevant, 40-59 peripheral, 0-39 not relevant.
Items may be in English, Hindi, Marathi, Tamil, Telugu, Bengali, Gujarati, Malayalam or Punjabi:
judge the meaning, not the language. Foreign news with no Indian angle is not relevant.

Return ONLY a JSON array, one object per item, no prose:
[{{"i": 1, "score": 85, "why": "IAS transfers incl. education secretary"}}]

Items:
{items}"""


class _Failed:
    """Stands in for a response when the request itself failed (timeout, network)."""
    status_code = 599

    def json(self):
        return {}


@dataclass
class AIScore:
    score: float        # 0-1
    reason: str
    model: str


def load_brief(config_dir: Path) -> str:
    path = config_dir / "engine" / "ai_interests.txt"
    if not path.exists():
        return "School education, higher education and skill development in India; officer transfers; elections; court rulings; policy."
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("#")]
    return "\n".join(lines).strip()


def parse_scores(text: str) -> dict[int, tuple[float, str]]:
    """Pull the JSON array out of a model reply (tolerates code fences and stray prose)."""
    match = re.search(r"\[.*\]", text or "", re.S)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
    out = {}
    for row in data if isinstance(data, list) else []:
        try:
            out[int(row["i"])] = (max(0.0, min(100.0, float(row["score"])) / 100), str(row.get("why", ""))[:120])
        except (KeyError, TypeError, ValueError):
            continue
    return out


class OpenRouterScorer:
    def __init__(self, keys: list[str], models: list[str], brief: str, timeout: float = 45, http=None):
        import httpx

        self.keys = [k for k in keys if k]
        self.models = models
        self.brief = brief
        self.http = http or httpx.Client(timeout=timeout)
        self._key = 0
        self.requests_made = 0

    def _post(self, model: str, prompt: str):
        for _ in range(len(self.keys)):
            key = self.keys[self._key % len(self.keys)]
            try:
                response = self.http.post(API, headers={"Authorization": f"Bearer {key}", "X-Title": "News Tracker"},
                                          json={"model": model, "temperature": 0,
                                                "messages": [{"role": "user", "content": prompt}]})
            except Exception as exc:  # timeout or network error: let the caller try the next model
                log.warning("OpenRouter %s: %s", model, type(exc).__name__)
                return _Failed()
            if response.status_code in (401, 402, 403):  # bad key or no quota: next key
                log.warning("OpenRouter key #%d refused (%s); trying the next key", self._key + 1, response.status_code)
                self._key += 1
                continue
            return response
        return None

    def score_batch(self, texts: list[str]) -> tuple[dict[int, tuple[float, str]], str]:
        """Scores for one batch (keys are 1-based positions in `texts`) and the model that answered."""
        numbered = "\n".join(f"{i}. {t}" for i, t in enumerate(texts, 1))
        prompt = PROMPT.format(brief=self.brief, items=numbered)
        for model in self.models:
            for attempt in range(2):
                response = self._post(model, prompt)
                if response is None:
                    return {}, ""
                if response.status_code == 429 or response.status_code >= 500:
                    time.sleep(2 * (attempt + 1))  # busy upstream: brief back-off, then next model
                    continue
                if response.status_code != 200:
                    break
                body = response.json()
                content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content", "")
                scores = parse_scores(content)
                if scores:
                    return scores, body.get("model", model)
                break  # unparseable answer: try the next model
        return {}, ""

    def score(self, items: list[tuple[str, str]], batch_size: int = 20, max_requests: int = 10,
              max_seconds: float = 150) -> dict[str, AIScore]:
        """items: (item_key, text). Returns AI scores by item key. Stops at the request or time budget;
        anything left over is scored on a later run."""
        results: dict[str, AIScore] = {}
        requests = 0
        started = time.monotonic()
        for start in range(0, len(items), batch_size):
            if requests >= max_requests or time.monotonic() - started > max_seconds:
                break
            batch = items[start:start + batch_size]
            scores, model = self.score_batch([text for _, text in batch])
            requests += 1
            self.requests_made += 1
            for position, (key, _) in enumerate(batch, 1):
                if position in scores:
                    value, why = scores[position]
                    results[key] = AIScore(value, why, model)
        log.info("AI scored %d of %d uncertain items in %d request(s)", len(results), len(items), requests)
        return results
