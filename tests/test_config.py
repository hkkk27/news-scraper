from pathlib import Path

from tracker.config import Bands, Secrets, load_config


def test_loads_default_profile():
    cfg = load_config()
    assert cfg.settings.profile.country == "IN"
    assert cfg.db_path.name == "tracker.db"


def test_bands_classify_scores():
    bands = Bands(core=80, relevant=60, peripheral=40)
    assert bands.band(95) == "core"
    assert bands.band(60) == "relevant"
    assert bands.band(45) == "peripheral"
    assert bands.band(10) == "not_relevant"


def test_missing_settings_file_uses_defaults(tmp_path: Path):
    cfg = load_config(tmp_path)
    assert cfg.settings.relevance.bands.core == 80


def test_secrets_parse_lists(monkeypatch):
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123, -100456 ,abc")
    monkeypatch.setenv("REPORT_EMAIL_TO", "a@x.in,b@y.in")
    secrets = Secrets.from_env()
    assert secrets.telegram_allowed_chat_ids == [123, -100456]
    assert secrets.report_email_to == ["a@x.in", "b@y.in"]
