import json
import re

from tracker.site import build_site
from tests.test_reports import NOW, cfg  # noqa: F401  (reuse the report fixture)


def test_dashboard_embeds_data(cfg, tmp_path):  # noqa: F811
    path = build_site(cfg, out_dir=tmp_path / "site", now=NOW)
    html = path.read_text(encoding="utf-8")
    assert "/*__TRACKER_DATA__*/" not in html
    blob = re.search(r"const DATA = (\{.*?\});\n", html, re.S).group(1)
    data = json.loads(blob)
    assert data["profile"] and data["states"]["MH"] == "Maharashtra"
    titles = {s["t"] for s in data["stories"]}
    assert "SC directs CBSE to extend third-language exemption to Class 6" in titles
    assert "Cricket final tonight" not in titles
    assert data["runs"][0]["status"] == "ok"
