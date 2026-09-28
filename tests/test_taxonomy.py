import pytest

from tracker.config import PROJECT_ROOT
from tracker.taxonomy import TermMatcher, flatten_terms, load_taxonomy


@pytest.fixture(scope="module")
def tax():
    return load_taxonomy(PROJECT_ROOT / "config")


def test_flatten_terms_accepts_language_maps():
    assert flatten_terms({"en": ["a", "b"], "hi": ["b", "c"]}) == ["a", "b", "c"]
    assert flatten_terms(None) == []


def test_acronyms_are_case_sensitive_and_whole_word():
    m = TermMatcher(["ITI", "CBSE"])
    assert m.terms_in("ITI admissions open") == ["ITI"]
    assert m.terms_in("politics and utility") == []
    assert m.terms_in("cbse in lower case") == []


def test_latin_terms_are_whole_word_case_insensitive():
    m = TermMatcher(["school", "board exam"])
    assert m.terms_in("School shut; Board Exam postponed") == ["school", "board exam"]
    assert m.terms_in("schooling abroad") == []


def test_devanagari_allows_inflection_but_not_longer_words():
    m = TermMatcher(["छात्र", "कहा"])
    assert m.terms_in("छात्रों ने प्रदर्शन किया") == ["छात्र"]
    assert m.terms_in("यह एक कहानी है") == []
    assert m.terms_in("मंत्री ने कहा कि") == ["कहा"]


def test_tamil_allows_attached_suffixes():
    m = TermMatcher(["பள்ளி"])
    assert m.terms_in("அரசுப் பள்ளிகளில் சேர்க்கை") == ["பள்ளி"]


def test_payloads_and_order():
    m = TermMatcher({"Mumbai": "MH", "Lucknow": "UP"})
    assert m.find("From Lucknow to Mumbai") == [("Lucknow", "UP"), ("Mumbai", "MH")]


def test_taxonomy_loads_all_parts(tax):
    assert {"school_education", "higher_education", "skill_development"} <= set(tax.sectors)
    assert {"court", "transfer", "election", "policy", "political", "statement", "news"} <= set(tax.categories)
    assert len(tax.gazetteer.states) == 36
    assert tax.actors["hc_bombay"].state == "MH"


def test_gazetteer_maps_names_and_cities(tax):
    gz = tax.gazetteer
    assert gz.names.find("Uttar Pradesh govt")[0][1] == "UP"
    assert gz.names.find("उत्तर प्रदेश सरकार")[0][1] == "UP"
    assert gz.cities.find("Pune college fee hike")[0][1] == "MH"
    assert gz.names.find("தமிழ்நாடு அரசு")[0][1] == "TN"
    # "New Delhi" is only a weak (dateline) signal
    assert gz.names.find(gz.strip_weak("New Delhi: The Centre said")) == []
    assert gz.names.find(gz.strip_weak("Delhi government schools"))[0][1] == "DL"
    assert gz.weak.find("New Delhi: The Centre said")[0][1] == "DL"


def test_sector_terms_multilingual(tax):
    school = tax.sectors["school_education"]
    assert school.strong.terms_in("CBSE Class 10 board exam dates") == ["CBSE", "Class 10", "board exam"]
    assert school.strong.terms_in("बोर्ड परीक्षा की तारीख") == ["बोर्ड परीक्षा"]
    skill = tax.sectors["skill_development"]
    assert "ITI" in skill.strong.terms_in("Govt ITI seats increased")


def test_actor_aliases(tax):
    hits = dict(tax.actor_matcher.find("Madras High Court directs UGC"))
    assert hits == {"Madras High Court": "hc_madras", "UGC": "ugc"}
