from urllib.parse import parse_qs, urlparse

import yaml

from tracker.config import PROJECT_ROOT
from tracker.sources import engine_feed_entries, export_engine_feeds, google_news_url, load_sources

CONFIG = PROJECT_ROOT / "config"


def test_google_news_url_encodes_query_and_edition():
    url = google_news_url('CBSE OR "board exam"', "hi", "hi", "when:1d")
    qs = parse_qs(urlparse(url).query)
    assert qs["q"] == ['CBSE OR "board exam" when:1d']
    assert qs["hl"] == ["hi"] and qs["gl"] == ["IN"] and qs["ceid"] == ["IN:hi"]


def test_registry_expands_packs_and_keeps_direct_feeds():
    specs = load_sources(CONFIG)
    ids = {s.id for s in specs}
    assert "thehindu-education" in ids
    assert "gn-school-en" in ids and "gn-transfers-hi" in ids
    assert all(s.enabled for s in specs)
    # disabled languages (kn, or) and disabled feeds (x-handles) are excluded by default
    assert not any(s.id.endswith("-kn") for s in specs)
    assert "x-handles" not in ids
    assert "x-handles" in {s.id for s in load_sources(CONFIG, include_disabled=True)}


def test_pack_metadata_flows_to_specs():
    specs = {s.id: s for s in load_sources(CONFIG)}
    assert specs["gn-higher-ta"].sector == "higher_education"
    assert specs["gn-courts-en"].stream == "court"
    assert specs["manual-feed-in"].is_local
    assert specs["official-mahasec"].state == "MH" and specs["official-mahasec"].type == "official"


def test_engine_export_shape(tmp_path):
    specs = load_sources(CONFIG)
    out = export_engine_feeds(specs, tmp_path / "feeds.yaml")
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert len(data["feeds"]) == len(specs)
    assert set(data["feeds"][0]) >= {"id", "name", "url", "enabled"}
    assert engine_feed_entries(specs[:1])[0]["id"] == specs[0].id
