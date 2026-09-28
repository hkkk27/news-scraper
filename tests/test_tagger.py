import pytest

from tracker.config import PROJECT_ROOT, Bands
from tracker.items import Item
from tracker.sources import load_sources
from tracker.tagger import Tagger, detect_language, load_scoring, priority_for
from tracker.taxonomy import load_taxonomy

CONFIG = PROJECT_ROOT / "config"
BANDS = Bands()


@pytest.fixture(scope="module")
def tagger():
    sources = {s.id: s for s in load_sources(CONFIG, include_disabled=True)}
    return Tagger(load_taxonomy(CONFIG), load_scoring(CONFIG), sources)


def tag(tagger, title, feed="gn-higher-en", summary=""):
    return tagger.tag(Item(url="https://example.com/x", title=title, summary=summary, feed_id=feed))


def test_regulator_policy_is_core(tagger):
    t = tag(tagger, "UGC notifies draft regulations for foreign university campuses - The Hindu")
    assert t.sectors[0] == "higher_education"
    assert t.category == "policy"
    assert "ugc" in t.actors
    assert BANDS.band(t.rule_score) == "core"
    assert t.level == "national"


def test_transfer_without_sector_is_relevant_with_state(tagger):
    t = tag(tagger, "Haryana Govt Transfers 3 IAS Officers; Nikhil Gajraj Appointed Director - Punjab Kesari",
            feed="gn-transfers-en")
    assert t.category == "transfer"
    assert t.states == ["HR"]  # "Punjab Kesari" is the publisher, not a place
    assert BANDS.band(t.rule_score) == "relevant"


def test_transfer_of_education_secretary_is_core(tagger):
    t = tag(tagger, "Maharashtra transfers 12 IAS officers; new School Education Secretary named", feed="bhaskar")
    assert t.category == "transfer" and "school_education" in t.sectors
    assert t.states == ["MH"] and BANDS.band(t.rule_score) == "core"


def test_high_court_ruling_on_schools_takes_state_from_court(tagger):
    t = tag(tagger, "Bombay HC quashes fee hike order for unaided schools", feed="livelaw")
    assert t.category == "court" and "school_education" in t.sectors
    assert t.states == ["MH"] and "hc_bombay" in t.actors
    assert BANDS.band(t.rule_score) == "core"


def test_hindi_transfer_headline(tagger):
    t = tag(tagger, "हरियाणा में 3 IAS अधिकारियों के तबादले, निखिल गजराज बने परिवहन निदेशक", feed="gn-transfers-hi")
    assert t.language == "hi" and t.category == "transfer" and t.states == ["HR"]
    assert t.rule_score >= 60


def test_tamil_school_news(tagger):
    t = tag(tagger, "அரசுப் பள்ளிகளில் மாணவர் சேர்க்கை அதிகரிப்பு", feed="gn-school-ta")
    assert t.language == "ta" and "school_education" in t.sectors


def test_election_announcement_beats_coverage(tagger):
    announce = tag(tagger, "State Election Commission announces schedule for municipal polls in 5 cities",
                   feed="gn-elections-en")
    coverage = tag(tagger, "Nandigram bypoll: ballot without the battle", feed="gn-elections-en")
    assert announce.category == coverage.category == "election"
    assert announce.rule_score > coverage.rule_score
    assert BANDS.band(announce.rule_score) in ("relevant", "core")


def test_cricket_is_not_relevant(tagger):
    t = tag(tagger, "India vs Pakistan cricket: Kohli hits century in Asia Cup final", feed="bhaskar")
    assert BANDS.band(t.rule_score) == "not_relevant"


def test_dateline_does_not_make_delhi(tagger):
    t = tag(tagger, "CBSE revises board exam schedule", summary="New Delhi: The Central Board of Secondary Education...",
            feed="gn-school-en")
    assert t.states == [] and t.level == "national"


def test_municipal_level_and_reasons(tagger):
    t = tag(tagger, "Pune Municipal Corporation polls: ward reservation draft published", feed="gn-elections-en")
    assert t.states == ["MH"] and t.level == "municipal"
    assert any(r.startswith("category election") for r in t.reasons)


def test_muted_source_and_manual_items(tagger):
    muted = Tagger(tagger.tax, tagger.cfg, tagger.sources, muted_sources={"gn-higher-en"})
    a = tag(tagger, "University fee hike protest")
    b = muted.tag(Item(url="https://e.com/x", title="University fee hike protest", feed_id="gn-higher-en"))
    assert b.rule_score < a.rule_score
    m = tagger.tag(Item(url="https://e.com/y", title="anything the client forwarded", feed_id="manual-feed-in"))
    assert m.rule_score >= 95


def test_language_detection():
    assert detect_language("मुंबई में स्कूल", hint="mr") == "mr"
    assert detect_language("విద్యా శాఖ") == "te"
    assert detect_language("Plain English") == "en"


def test_priority_rubric(tagger):
    assert priority_for(90, "policy", True, tagger.cfg) == "high"
    assert priority_for(90, "statement", True, tagger.cfg) == "medium"
    assert priority_for(85, "transfer", False, tagger.cfg) == "high"
    assert priority_for(30, "news", False, tagger.cfg) == "low"


def test_bangladesh_news_from_bengali_edition_is_dropped(tagger):
    t = tag(tagger, "জাহাঙ্গীরনগর বিশ্ববিদ্যালয়ে ছাত্রশক্তি নেতা বহিষ্কার, ঢাকা", feed="gn-higher-bn")
    assert BANDS.band(t.rule_score) == "not_relevant"
    kolkata = tag(tagger, "কলকাতা বিশ্ববিদ্যালয়ে নতুন উপাচার্য নিয়োগ", feed="gn-higher-bn")
    assert kolkata.states == ["WB"] and kolkata.rule_score > t.rule_score


def test_indian_students_abroad_are_kept(tagger):
    t = tag(tagger, "Canada caps study permits; Indian students and universities hit", feed="gn-higher-en")
    assert BANDS.band(t.rule_score) != "not_relevant"


def test_sc_shorthand_is_a_court_ruling(tagger):
    t = tag(tagger, "SC extends CBSE third-language exemption to Class 6 students", feed="gn-school-en")
    assert t.category == "court" and BANDS.band(t.rule_score) == "core"


def test_source_focus_alone_is_weak_evidence(tagger):
    t = tag(tagger, "Holiday List for the year", feed="official-dopt")
    assert t.category == "transfer" and BANDS.band(t.rule_score) in ("peripheral", "not_relevant")


def test_court_case_about_elections_counts_as_election(tagger):
    t = tag(tagger, "Supreme Court hears plea on electoral roll revision before assembly polls", feed="livelaw")
    assert {t.category, t.category2} == {"court", "election"}
    assert t.rule_score >= 40


def test_generic_officer_deployment_is_not_a_transfer(tagger):
    t = tag(tagger, "अब NTA ऑफिस की सुरक्षा CISF के हवाले, अधिकारी नियुक्त", feed="bhaskar")
    assert t.category != "transfer"


def test_school_assembly_roundups_are_noise(tagger):
    t = tag(tagger, "Today News Headlines for School Assembly, September 29: SC refuses to stay order", feed="ie-education")
    assert BANDS.band(t.rule_score) in ("peripheral", "not_relevant")
