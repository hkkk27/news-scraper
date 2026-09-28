# ADR-0001: Build a lean core from proven libraries instead of forking an existing product

- **Status:** Accepted
- **Date:** 27 September 2026
- **Task:** M0-02

## Context

We want to reuse open-source work rather than start from zero. The needs from the brief
are:

- India-specific sources: government sites and PDFs, vernacular papers, X.com.
- Special streams: transfers, elections down to municipal level, court rulings, policy.
- Tagging by state and sector.
- A mobile training loop for 3–5 users.
- Daily and weekly reports.
- Running cost under ₹500/month, delivered by 19 October.

The candidates below were evaluated on 27 September 2026 (GitHub stars, license and last
push date as of that day).

| Project | Stars | License | Last push | What it is | Fit |
|---|---|---|---|---|---|
| sansan0/TrendRadar | 62.5k | GPL-3.0 | 2026-09-13 | Trending-news monitor: keyword and AI filtering, HTML reports, push alerts, runs on GitHub Actions | Closest in spirit, poor fit in detail (see below) |
| dgtlmoon/changedetection.io | 34.6k | Apache-2.0 | 2026-09-25 | Website change monitor | The right idea for government pages, but needs an always-on server |
| DIYgod/RSSHub | 46.3k | AGPL-3.0 | 2026-09-27 | RSS for sites without feeds, including X routes | Use as an external service when needed |
| miniflux/v2 | 9.7k | Apache-2.0 | 2026-09-23 | Multi-user RSS reader | Needs an always-on server and Postgres; no tagging, training or reports |
| samuelclay/NewsBlur | 7.6k | MIT | 2026-09-24 | RSS reader with an "intelligence trainer" | Training concept matches; stack of about 10 services, far over budget |
| FreshRSS | 16.2k | AGPL-3.0 | 2026-09-27 | PHP RSS reader | Same limits as Miniflux |
| finaldie/auto-news | 0.9k | MIT | 2025-07-19 | LLM news aggregator (RSS, tweets, Reddit) | Heavy stack (Airflow, Milvus, MySQL), Notion UI, inactive for over a year |
| yinan-c/RSSbrew | 0.3k | — | 2026-08-29 | Django feed aggregator with AI digests | Small; needs hosting and has no geography or streams |
| Indian-specific repositories (PIB, ECI, Indian Kanoon scrapers) | < 10 each | mixed | — | One-off scripts | Useful as references only |

### Why not fork TrendRadar

- **Different data model.** It is built around Chinese "hot list" rankings (Weibo, Zhihu and others, collected through the newsnow API) and headline-level alerts. We need article-level items with state, sector and category tags, story clusters and feedback.
- **Missing pieces.** It has no multi-user app, feedback training loop, geography tagging, government page and PDF watcher, or database-backed dashboard. Those pieces make up most of our scope.
- **Size.** About 34,500 lines of Python with Chinese prompts and comments. Understanding it and removing what we don't need would take longer than building our own core, and D4 requires us to explain the methodology in depth.
- **Deployment.** Its GitHub Actions mode is a 7-day trial that asks users to check in; long-term use is expected to run on Docker.

## Decision

Write our own small, modular core, about 2–3k lines, and reuse proven components as
**dependencies**, not forks:

| Need | Reused component |
|---|---|
| Feed parsing | `feedparser` |
| Full text from articles, including Indian languages | `trafilatura` (Apache-2.0) |
| HTTP | `httpx` |
| Near-duplicate detection | `rapidfuzz` / MinHash; multilingual `sentence-transformers` embeddings (stretch) |
| Learned relevance model | `scikit-learn` |
| Storage and auth | Supabase (Postgres) through `SQLAlchemy` |
| PDF text | `pypdf` / `pdfplumber`; OCR best-effort |
| X.com | Apify tweet scraper (pay-per-result), with `twscrape` or RSSHub as fallback |

We also borrow design ideas, not code, from:

- **TrendRadar:** a plain-English "interests" file that drives AI filtering with a minimum score, and keyword word-groups.
- **changedetection.io:** snapshot and diff the list of links on notice/order pages, then fetch only what is new.
- **NewsBlur:** the per-item and per-source training interactions.

## Consequences

- We own every line, which keeps the handover and methodology explanation simple.
- The core is small enough to fit the 5 October go-live.
- All code is Apache-2.0 or MIT compatible. We avoid GPL and AGPL obligations by not copying from TrendRadar, RSSHub or FreshRSS.
- We must write adapters for India-specific sources ourselves. That work is needed in any case.
