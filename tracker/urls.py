"""URL helpers: canonical form (for de-duplication) and a short stable key per item."""

from __future__ import annotations

import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "utm_id",
                   "fbclid", "gclid", "igshid", "ref", "ref_src", "ocid", "cmpid", "s", "from"}


def canonical_url(url: str) -> str:
    """Lower-case host, no tracking params, no fragment, no AMP/mobile variants, no trailing slash."""
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        return url
    parts = urlsplit(url)
    host = parts.netloc.lower()
    for prefix in ("www.", "m.", "amp."):
        if host.startswith(prefix):
            host = host[len(prefix):]
    path = parts.path
    for suffix in ("/amp", "/amp/", ".amp"):
        if path.endswith(suffix):
            path = path[: -len(suffix)]
    path = path.rstrip("/") or "/"
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                       if k.lower() not in TRACKING_PARAMS])
    return urlunsplit(("https", host, path, query, ""))


def item_key(url: str) -> str:
    """12-character key used in Telegram callback data and the feedback table."""
    return hashlib.sha1(canonical_url(url).encode("utf-8")).hexdigest()[:12]
