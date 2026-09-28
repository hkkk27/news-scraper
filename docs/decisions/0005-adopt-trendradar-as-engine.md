# ADR-0005: Adopt TrendRadar as the base engine and add an India layer

- **Status:** Accepted (28 September 2026); amended the same day to keep the India layer outside `engine/`
- **Supersedes:** [ADR-0001](0001-build-lean-core-not-fork.md) ("build a lean core, don't fork")
- **Task:** M0-05

## Context

On 28 September the team asked us to build on existing open-source projects rather than
write everything from scratch. Licensing is not a constraint, because this is a personal
project.

ADR-0001 rejected forking TrendRadar when the target was still an open question. Since then
ADR-0004 fixed the design:

- RSS-first collection.
- An AI relevance filter.
- Telegram and email alerts.
- HTML reports.
- A GitHub Actions schedule.
- ₹0 hosting.

That is close to what [TrendRadar](https://github.com/sansan0/TrendRadar) already does
(62.5k★, GPL-3.0, Python, release 6.10.0 of 13 September 2026). We reviewed its code on
28 September:

| Needed | TrendRadar module | Fit |
|---|---|---|
| Fetch RSS/Atom, freshness filter, per-feed limits | `trendradar/crawler/rss/` | ✅ as is; Google News search feeds work as plain RSS URLs |
| Store items; de-duplicate by URL/GUID per feed | `trendradar/storage/` (one SQLite file per day, local or S3/R2) | ✅ |
| Keyword word groups with required (`+`) and exclude (`!`) words, global filter | `trendradar/core/frequency.py`, `config/frequency_words.txt` | ✅ becomes our sector/stream groups |
| AI relevance: plain-English interests → tags → batch scoring 0–1 | `trendradar/ai/filter*.py`, `config/ai_interests.txt` | ✅ becomes our "is it relevant / degree / tag" step |
| Any LLM provider, including the free Gemini tier | `trendradar/ai/client.py` via LiteLLM | ✅ |
| Translate titles (Hindi and others to English) | `trendradar/ai/translator.py` | ✅ |
| Telegram, email and 8 other channels; batching; schedules | `trendradar/notification/`, `core/scheduler.py`, `config/timeline.yaml` | ✅ |
| HTML report; Cloudflare Pages deploy step | `trendradar/report/`, `.github/workflows/crawler.yml` | ✅ |
| Query the data with AI | `mcp_server/` | ✅ bonus |

What it does not have, and we add as an **India layer**:

- State/UT, sector, category and actor tagging, using our M1-02 taxonomy and gazetteer.
- A government page and PDF watcher.
- Telegram feedback buttons and forward-to-add intake.
- A learned relevance model trained on that feedback.
- Cross-feed story clustering.
- The analyst digest, executive brief and Excel reports by state and sector.
- A dashboard with trackers.
- Persistence on a `data` branch.

## Decision

1. **Import TrendRadar with `git subtree` into `engine/`,** squashed to one commit. Our edits are ordinary commits on top. Upstream fixes can later be pulled with `git subtree pull --prefix=engine https://github.com/sansan0/TrendRadar.git master --squash`.
2. **Configure rather than rewrite.**
   - `engine/config/config.yaml` in English: Chinese hot-list platforms off, our Indian feeds and Google News query packs on, timezone Asia/Kolkata.
   - `frequency_words.txt` holds the multilingual sector and stream groups.
   - `ai_interests.txt` holds the relevance brief.
   - The AI prompts are translated to English.
3. **Every new collector writes an RSS file** (`feeds/*.xml`), which TrendRadar ingests like any feed. This covers the government watcher, Telegram intake and X. The one engine edit this needs is `file://` URL support in the RSS fetcher, so the whole pipeline (filters, AI, alerts, reports) applies to them unchanged.
4. **The India layer is the `tracker/` package at the repository root, outside `engine/`.** It runs after each TrendRadar pass: it reads the engine's SQLite output, tags and scores items, clusters stories, learns from feedback, and builds reports and the dashboard. Keeping it outside the subtree means upstream pulls never touch our code, and the engine is patched only where a hook is unavoidable (for example `file://` feeds).
5. **Our M1-01/M1-02 code stays:** the settings loader and CLI become the India layer's own command line (`python -m tracker ...`), and the taxonomy, gazetteer and matcher are its tagging core. TrendRadar keeps its own config and entry point for the engine.
6. **The ₹0 design of ADR-0004 stands.** No S3/R2: `output/` persists on the repository's `data` branch. The 7-day "check-in" trial step in TrendRadar's workflow is not used; our own workflow at the repository root runs the engine.

## Consequences

- **Less to build.** Collection, storage, the AI filter, translation, alerts and HTML reports already exist and are tested by a large user base.
- **Division of labour.** TrendRadar handles collection, filtering and real-time alerts. The India layer handles structure (state × sector), reporting and learning.
- **Python 3.12.** TrendRadar requires it and installs with `uv`. CI uses 3.12.
- **Upstream updates.** Most of our changes live in config files and the separate `tracker/` package, so a `git subtree pull` should mostly merge cleanly.
- **License.** GPL-3.0: TrendRadar's LICENSE stays in `engine/`, and the README credits the project.
