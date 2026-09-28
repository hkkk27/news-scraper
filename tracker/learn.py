"""L2: a relevance model that learns from the client's labels.

Labels come from Telegram (👍 relevant / ⭐ key / 👎 not relevant), forwarded items (positive)
and a small seed file for day one (half weight). The model is a TF-IDF (character n-grams, which
work across Indian scripts without a tokenizer, plus word 1-2 grams) + logistic regression
pipeline: no GPU, no downloads, trains in seconds, and runs inside the scheduled pipeline.

Blending: final = rule score + w × (100 × P(relevant) − 50). The adjustment is neutral when the
model is unsure (P ≈ 0.5), so a young model cannot drag scores around; w grows with the number
of labels (0 below `min_labels`, `max_weight` at `full_weight_at`), giving at most ±w×50 points.
A human label on the item itself always wins.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from tracker.config import PROJECT_ROOT, ModelSettings, read_yaml
from tracker.log import get_logger

log = get_logger("tracker.learn")

MODEL_PATH = PROJECT_ROOT / "data" / "models" / "relevance.joblib"
META_PATH = PROJECT_ROOT / "data" / "models" / "relevance.json"


@dataclass
class ModelInfo:
    trained_at: str
    labels: int            # client labels (Telegram, forwarded items)
    seed_labels: int
    positives: int
    negatives: int
    cv_accuracy: float | None = None
    cv_precision: float | None = None


def text_of(title: str, summary: str = "") -> str:
    return f"{title}. {summary[:300]}".strip()


def client_labels(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    """(text, label) for the latest relevance label of each item, joined with its text."""
    rows = conn.execute("""
        SELECT f.item_key, f.value, COALESCE(i.title, f.title) AS title, COALESCE(i.summary, '') AS summary
        FROM feedback f LEFT JOIN items i ON i.item_key = f.item_key
        WHERE f.value IS NOT NULL
          AND f.id = (SELECT MAX(id) FROM feedback g WHERE g.item_key = f.item_key AND g.value IS NOT NULL)
    """).fetchall()
    return [(text_of(r["title"], r["summary"]), int(r["value"])) for r in rows if r["title"]]


def seed_labels(config_dir: Path) -> tuple[list[tuple[str, int]], float]:
    path = config_dir / "training" / "seed_labels.yaml"
    if not path.exists():
        return [], 0.0
    data = read_yaml(path)
    labels = [(text_of(x["title"]), int(x["label"])) for x in data.get("labels") or []]
    return labels, float(data.get("weight", 0.5))


def build_pipeline():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import FeatureUnion, Pipeline

    features = FeatureUnion([
        ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=1, max_features=60000)),
        ("words", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), sublinear_tf=True, token_pattern=r"(?u)\b\w+\b")),
    ])
    return Pipeline([("features", features),
                     ("clf", LogisticRegression(C=2.0, class_weight="balanced", max_iter=2000))])


def train(conn: sqlite3.Connection, config_dir: Path, model_path: Path = MODEL_PATH,
          meta_path: Path = META_PATH) -> ModelInfo | None:
    import joblib
    import numpy as np

    client = client_labels(conn)
    seeds, seed_weight = seed_labels(config_dir)
    data = client + seeds
    y = np.array([label for _, label in data])
    if len(data) < 6 or len(set(y)) < 2:
        log.info("not enough labels to train (%d, classes=%s)", len(data), sorted(set(y)))
        return None
    X = [text for text, _ in data]
    weights = np.array([1.0] * len(client) + [seed_weight] * len(seeds))

    info = ModelInfo(trained_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), labels=len(client),
                     seed_labels=len(seeds), positives=int(y.sum()), negatives=int(len(y) - y.sum()))
    if min(info.positives, info.negatives) >= 5:
        from sklearn.model_selection import StratifiedKFold, cross_val_predict

        folds = min(5, info.positives, info.negatives)
        predicted = cross_val_predict(build_pipeline(), X, y, cv=StratifiedKFold(folds, shuffle=True, random_state=0),
                                      params={"clf__sample_weight": weights})
        info.cv_accuracy = round(float((predicted == y).mean()), 3)
        flagged = predicted == 1
        info.cv_precision = round(float((y[flagged] == 1).mean()), 3) if flagged.any() else None

    model = build_pipeline()
    model.fit(X, y, clf__sample_weight=weights)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    meta_path.write_text(json.dumps(asdict(info), indent=2), encoding="utf-8")
    log.info("trained relevance model: %s", info)
    return info


class RelevanceModel:
    """Loaded model plus the blending weight derived from how many client labels it has seen."""

    def __init__(self, model, info: ModelInfo, settings: ModelSettings):
        self.model = model
        self.info = info
        effective = info.labels + info.seed_labels * 0.5
        if not settings.enabled or effective < settings.min_labels:
            self.weight = 0.0
        else:
            self.weight = settings.max_weight * min(1.0, effective / max(1, settings.full_weight_at))

    @classmethod
    def load(cls, settings: ModelSettings, model_path: Path = MODEL_PATH, meta_path: Path = META_PATH):
        if not (settings.enabled and model_path.exists() and meta_path.exists()):
            return None
        import joblib

        info = ModelInfo(**json.loads(meta_path.read_text(encoding="utf-8")))
        return cls(joblib.load(model_path), info, settings)

    def probabilities(self, texts: list[str]) -> list[float]:
        if not texts:
            return []
        return [float(p) for p in self.model.predict_proba(texts)[:, 1]]

    def blend(self, rule_score: int, probability: float) -> tuple[int, bool]:
        """Final score and whether the model moved it materially (≥ 10 points)."""
        delta = self.weight * (100 * probability - 50)
        final = int(max(0, min(100, round(rule_score + delta))))
        return final, abs(final - rule_score) >= 10
