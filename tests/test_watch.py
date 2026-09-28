from datetime import datetime, timezone

from tracker.config import PROJECT_ROOT
from tracker.rssfile import FeedItem, merge_items, read_feed, write_feed
from tracker.watch import Link, WatchPage, extract_links, load_watch_pages, run_watch, select_links

PAGE_V1 = """<html><body>
<a href="/menu/org-chart.pdf">UGC Organisational Chart</a>
<a href="/pdfnews/notice-1.pdf">Public notice on fake universities 2026</a>
<a href="#top">Top</a>
<a href="https://other.example/a">Short</a>
</body></html>"""

PAGE_V2 = PAGE_V1.replace("</body>", '<a href="/pdfnews/notice-2.pdf">Draft regulations on foreign campuses</a></body>')


class FakeResponse:
    def __init__(self, text, url):
        self.text, self.url, self.status_code, self.content = text, url, 200, text.encode()

    def raise_for_status(self):
        pass


class FakeClient:
    def __init__(self, pages):
        self.pages = pages

    def get(self, url):
        return FakeResponse(self.pages[url], url)


def page(**kw):
    base = dict(id="ugc", name="UGC notices", url="https://www.ugc.gov.in/", include=r"\.pdf",
                exclude="organisation(al)? chart", pdf_text=False, sector="higher_education")
    base.update(kw)
    return WatchPage(**base)


def test_extract_links_absolute_and_deduplicated():
    links = extract_links(PAGE_V1, "https://www.ugc.gov.in/")
    urls = {l.url for l in links}
    assert "https://www.ugc.gov.in/pdfnews/notice-1.pdf" in urls
    assert not any(u.endswith("#top") for u in urls)


def test_generic_link_text_uses_surrounding_block_and_drops_file_size():
    html = """<div><p>Declaration of Results of AIAPGET 2026 – reg. <a href="/a.pdf">Read More</a></p>
    <ul><li><a href="/b.pdf">Extension of last date for LOC submission (1.23 MB)</a> 23/09/2026</li></ul></div>"""
    links = {l.url.rsplit("/", 1)[-1]: l.text for l in extract_links(html, "https://nta.ac.in/")}
    assert links["a.pdf"] == "Declaration of Results of AIAPGET 2026 – reg."
    assert links["b.pdf"] == "Extension of last date for LOC submission"


def test_select_links_applies_include_exclude_and_min_text():
    links = extract_links(PAGE_V1, "https://www.ugc.gov.in/")
    chosen = select_links(links, page())
    assert [l.text for l in chosen] == ["Public notice on fake universities 2026"]
    assert select_links([Link("https://x/a.pdf", "tiny")], page()) == []


def test_first_run_is_baseline_then_new_links_emitted(tmp_path, monkeypatch):
    import tracker.watch as watch

    monkeypatch.setattr(watch, "FEEDS_DIR", tmp_path / "feeds")
    state = tmp_path / "seen.json"
    now = datetime(2026, 9, 28, 6, 0, tzinfo=timezone.utc)
    p = page()

    first = run_watch([p], "UA", state_path=state, now=now, client=FakeClient({p.url: PAGE_V1}))
    assert first[0].baseline and first[0].new == 0
    assert read_feed(p.feed_path) == []  # empty feed file exists for the engine

    second = run_watch([p], "UA", state_path=state, now=now, client=FakeClient({p.url: PAGE_V2}))
    assert second[0].new == 1
    items = read_feed(p.feed_path)
    assert [i.title for i in items] == ["Draft regulations on foreign campuses"]
    assert items[0].categories == ["higher_education"]

    third = run_watch([p], "UA", state_path=state, now=now, client=FakeClient({p.url: PAGE_V2}))
    assert third[0].new == 0 and len(read_feed(p.feed_path)) == 1


def test_rss_roundtrip_and_merge(tmp_path):
    now = datetime(2026, 9, 28, tzinfo=timezone.utc)
    a = FeedItem("A", "https://x/a", now, summary="s", categories=["court"])
    b = FeedItem("B", "https://x/b", now)
    path = write_feed(tmp_path / "f.xml", "Test", [a])
    merged = merge_items(read_feed(path), [a, b])
    assert [i.guid for i in merged] == ["https://x/b", "https://x/a"]
    assert read_feed(path)[0].categories == ["court"]


def test_configured_pages_load():
    pages = {p.id: p for p in load_watch_pages(PROJECT_ROOT / "config")}
    assert {"ugc", "cbse", "nta", "dopt", "mahasec"} <= set(pages)
    assert pages["mahasec"].state == "MH" and pages["cbse"].max_new == 15
