from tracker.config import PROJECT_ROOT, LLMSettings, ModelSettings
from tracker.db import connect, utcnow
from tracker.learn import RelevanceModel, client_labels, seed_labels, text_of, train
from tracker.process import combine

CONFIG = PROJECT_ROOT / "config"


def trained(tmp_path, extra_labels=()):
    conn = connect(tmp_path / "t.db")
    for key, title, value in extra_labels:
        conn.execute("INSERT INTO feedback(item_key, title, label, value, created_at) VALUES(?,?,?,?,?)",
                     (key, title, "relevant" if value else "not_relevant", value, utcnow()))
    conn.commit()
    info = train(conn, CONFIG, tmp_path / "m.joblib", tmp_path / "m.json")
    return conn, info


def test_seed_labels_load_with_both_classes():
    labels, weight = seed_labels(CONFIG)
    assert len(labels) >= 40 and weight == 0.5
    assert {label for _, label in labels} == {0, 1}


def test_train_and_rank_unseen_headlines(tmp_path):
    _, info = trained(tmp_path)
    assert info is not None and info.seed_labels >= 40 and info.cv_accuracy is not None
    model = RelevanceModel.load(ModelSettings(min_labels=1), tmp_path / "m.joblib", tmp_path / "m.json")
    wanted, unwanted = model.probabilities([
        text_of("Punjab transfers 9 IAS officers, new education secretary named"),
        text_of("Cricket: India beat Australia in the final over thriller"),
    ])
    assert wanted > unwanted


def test_latest_client_label_wins(tmp_path):
    conn, _ = trained(tmp_path, [("k1", "University fee hike protest", 1), ("k1", "University fee hike protest", 0)])
    assert client_labels(conn) == [(text_of("University fee hike protest"), 0)]


def test_model_weight_grows_with_labels(tmp_path):
    _, info = trained(tmp_path)
    settings = ModelSettings(min_labels=20, full_weight_at=200, max_weight=0.7)
    model = RelevanceModel.load(settings, tmp_path / "m.joblib", tmp_path / "m.json")
    assert 0 < model.weight < 0.2  # seeds alone give the model a light touch
    model.info.labels = 400
    assert RelevanceModel(model.model, model.info, settings).weight == 0.7


def test_blend_is_neutral_when_unsure(tmp_path):
    _, info = trained(tmp_path)
    model = RelevanceModel.load(ModelSettings(min_labels=1, full_weight_at=1, max_weight=0.7),
                                tmp_path / "m.joblib", tmp_path / "m.json")
    assert model.blend(62, 0.5) == (62, False)
    assert model.blend(62, 1.0) == (97, True)
    assert model.blend(62, 0.0) == (27, True)


def test_combine_layers():
    llm = LLMSettings(uncertain_low=40, uncertain_high=65)

    class Model:
        weight = 0.5

        def blend(self, rule, p):
            final = round(0.5 * rule + 0.5 * 100 * p)
            return final, abs(final - rule) >= 10

    assert combine(70, None, None, None, llm) == (70, "rules")
    assert combine(30, 0.9, None, Model(), llm) == (60, "model")
    assert combine(50, None, 0.9, None, llm) == (70, "llm")       # engine AI settles the uncertain band
    assert combine(20, None, 0.95, None, llm) == (65, "llm")      # engine AI strongly flags a miss
    assert combine(90, None, 0.2, None, llm) == (90, "rules")     # confident rules are left alone
