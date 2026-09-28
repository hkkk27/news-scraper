# Work Log

Newest entries at the top. One entry per task or working session. Format rules are in
[CONTRIBUTING.md](../CONTRIBUTING.md#5-documentation-rules).

---

## 2026-09-28 â€” M1-04 India sources and engine relevance config

**Branch:** `feat/m1-04-india-sources`

### Done

- **Source registry.** `config/sources/feeds.yaml` has 8 verified direct feeds plus 3 local feeds that the India layer will write: official pages, Telegram feed-in and X.
- **Google News packs.** `config/sources/google_news.yaml` has 7 query packs across 9 language editions. With the direct feeds, 54 sources in total.
- **Engine overlay** in `config/engine/`, in TrendRadar format:
  - `frequency_words.txt`: multilingual keyword groups. Transfers require an officer term; court rulings require an education term; short acronyms use word-boundary regexes.
  - `ai_interests.txt`: the plain-English, priority-ordered relevance brief.
- **Code.** `tracker/sources.py` plus `tracker sources list | check | export`. Export writes the engine's `rss.feeds` block to `build/`.
- **Live check.** 50/54 sources returned items; 4 were quiet streams. `kn` and `or` Google News editions returned nothing and are disabled.
- **Tests:** 18 passing.

### Blocked

- The TrendRadar import into `engine/` (M1-03) was stopped by the assistant's safety check on bringing third-party code into the repository. It needs the owner's approval, or the owner can run the `git subtree add` command.

### Next

- M1-05: official page and PDF watcher that writes `feeds/official.xml`.

---

## 2026-09-28 â€” M0-05 Decision to build on TrendRadar

**Branch:** `docs/m0-05-adopt-trendradar`

### Input from the team

- Don't build everything from scratch: download the open-source projects, integrate and edit them.
- Licensing is not a concern for this personal project.

### Done

- **Code review.** Read TrendRadar 6.10.0 (released 13 Sep 2026): RSS crawler, per-day SQLite storage, keyword word groups, the AI filter (interests â†’ tags â†’ 0â€“1 scores in batches of 200 titles), LiteLLM client, translator, 10 notification channels including Telegram and email, HTML report, workflow with a Cloudflare Pages deploy step, MCP server.
- **[ADR-0005](decisions/0005-adopt-trendradar-as-engine.md):**
  - Import TrendRadar into `engine/` with `git subtree`.
  - Configure it for India.
  - Every new collector (government pages, Telegram intake, X) writes an RSS file that the engine ingests.
  - Our additions become an `india` sub-package: tagging, clustering, learning, reports, dashboard.
  - Retire the M1-01 skeleton; move the M1-02 taxonomy into the India layer.
  - ADR-0001 is superseded.
- **SOW v0.4.** Rewrote the M1/M2 task breakdown around the engine.

### Next

- M1-03: import TrendRadar and run it locally on Python 3.12.

---

## 2026-09-28 â€” M1-02 Taxonomy and geography

**Branch:** `feat/m1-02-taxonomy`

### Done

- **Taxonomy files** in `config/taxonomy/`:
  - `sectors.yaml`: 3 sectors, strong and normal terms in 9 languages, plus negative terms.
  - `categories.yaml`: 7 categories. Transfers require an officer mention; election announcements are marked separately.
  - `actors.yaml`: regulators, 25 High Courts mapped to their states, ECI and State Election Commissions, parties, cadres.
- **Gazetteer:** `config/geography/india.yaml` covers 36 states and UTs with ISO codes, native-script names and cities. "New Delhi" is kept as a weak signal because it is usually a dateline.
- **Matcher:** `tracker/taxonomy.py` is an explainable term matcher.
  - Latin-script terms match whole words.
  - ALL-CAPS acronyms are case-sensitive.
  - Indian-language terms accept inflections but not longer words.
- **Removed ambiguous terms:** "à¤—à¤¯à¤¾" (also "went"), "à¤•à¥‹à¤Ÿà¤¾" (also "quota"), "Centre" (also "exam centre"), "Mandi", "block", "ward".
- **Tests:** 14 passing.

### Next

- M1-03: storage (SQLite schema and repository layer).

---

## 2026-09-28 â€” M1-01 Python package skeleton

**Branch:** `feat/m1-01-skeleton`

### Done

- **Packaging:** `pyproject.toml` (package `news-tracker`, console script `tracker`), `requirements.txt` for CI, and `.env.example` listing every optional secret.
- **Settings:** `config/settings.yaml` with typed pydantic settings in `tracker/config.py`, covering storage, collection, dedup, relevance bands, the model and LLM, reports, Telegram, dashboard and retention.
  - Secrets are read only from the environment or `.env`.
  - A profile is a whole config folder, selectable with `--config` or `TRACKER_CONFIG_DIR`, so resale to a new client means a new folder.
- **CLI:** `python -m tracker version | config`. It forces UTF-8 console output so Indian-language headlines print on Windows.
- **Environment:** a project virtual environment in `.venv`. It is git-ignored and keeps the global Python untouched; an accidental global upgrade of `charset-normalizer` was reverted.
- **Tests:** 4 passing.

### Next

- M1-02: taxonomy and geography configuration.

---

## 2026-09-28 — M0-04 Architecture decision (Option A)

**Branch:** `docs/m0-04-option-a`

### Input from the team

- Supabase and a paid API look risky for a ₹500/month ceiling; prefer local storage.
- Build an integrated system, not just a website.
- After ideating five options, the team chose **Option A**: ₹0 serverless, Telegram-first.
- Complete the whole project, including samples and slide content for Claude Design.
- The product may later be sold to other clients.

### Done

- **Merged** `docs/m0-scope-of-work` and `docs/m0-03-proposal` into `main` with `--no-ff`, because `gh` is not logged in and no PR can be opened.
- **[ADR-0004](decisions/0004-zero-cost-serverless-telegram-first.md):**
  - SQLite on an orphan `data` branch (D1 or a local box as swaps).
  - Telegram bot as the mobile app, training mode and feed-in.
  - Email and Excel for leadership; static dashboard behind Cloudflare Access.
  - Local relevance model plus an optional free-tier LLM.
  - Config profiles for resale.
  - Running cost ₹0–150/month.
- **ADR statuses:** 0001 accepted; 0002 and 0003 marked superseded where they conflict.
- **SOW v0.3:** users, D2, stage table, diagram, training, §11 cost, WBS and risks updated; M0-04 and M4-04 added.
- **CONTRIBUTING:** documented the `--no-ff` merge fallback.
- **README:** added a design summary.

### Next

- M1-01 onwards: build the pipeline, one branch per task.

---

## 2026-09-27 (session 2, continued) — M0-03 A/M proposal deck

**Branch:** `docs/m0-03-proposal` (stacked on `docs/m0-scope-of-work`)

### Done

- **Proposal deck.** Built a five-slide deck: [News & Election Tracker — Approach & Methodology](https://claude.ai/artifact/KHNo1cwwFzs2QZPRDUHYnA).
  - Each slide maps to one of the brief's evaluation areas:
    1. Understanding
    2. Seven-stage approach and sources
    3. Taxonomy and learning
    4. Architecture, reliability and cost
    5. Team, prior work and delivery plan
  - Each slide has speaker notes.
- **Prior work.** Drawn from the team's existing projects: the education-sector school/NGO data pipeline (OpenStreetMap, Apify, NGO Darpan), the clipping pipeline and the explainer-video generator.
- **Documentation.** Recorded the outline, placeholders and submission checklist in [proposal/README.md](proposal/README.md). Marked M0-03 as "Draft ready" in the SOW.

### Commits

| Hash | Message |
|---|---|
| `ff1835e` | docs: add A/M proposal outline, placeholders and submission checklist |

### Next

- **Team:** fill the four placeholders (college/batch, second member, phone), download as PPTX/PDF, and email before 29 Sep 23:59.
- Merge `docs/m0-scope-of-work`, then `docs/m0-03-proposal`.
- M1-01: Python package skeleton, config loader and CLI.

---

## 2026-09-27 (session 2) — M0-02 Cost decision and SOW v0.2

**Branch:** `docs/m0-scope-of-work`

### Input from the team

- The ₹500 budget is tight, so we need to decide between a local model, an API, and scraping or bots.
- The workflow is: collect → scrape → reorganise → is it relevant → degree of relevance → tag → report.
- Government notifications are a source.
- The client must be able to feed items into the dataset himself.
- Reports go to the client and to his boss.

### Done

- **[ADR-0003](decisions/0003-collection-and-ai-within-budget.md), collection and AI within budget:**
  - **Collection** is a ladder, cheapest and most reliable first: RSS → Google News search RSS → targeted scraping of official pages and PDFs → headless browser (rare) → Apify for X.
  - **Manual feed-in** comes through a Telegram bot polled by the pipeline (no server) and a web form.
  - **Relevance** is a three-layer cascade: L1 rules, then L2 local embedding model and classifier (free, on CI), then L3 LLM only for the uncertain band.
  - **Rejected:** a local LLM on CI (about 2,500 runner minutes a month, over budget, and weak in Indian languages), and a home PC (can't guarantee the 14-day run).
  - **Chosen for L3:** Claude Haiku 4.5 through the Batches API with a hard cap, estimated at about ₹260 a month. **Total estimated running cost: ₹260–410 a month.**
- **SOW v0.2:**
  - The seven-stage pipeline table (§5).
  - Relevance bands: Core, Relevant, Peripheral, Not relevant.
  - A "decided by" audit tag.
  - Manual feed-in (D1 bot, D2 form).
  - Two report formats: analyst digest and executive brief.
  - New task M1-13 and open questions 7–8.

### Commits

| Hash | Message |
|---|---|
| `a089c80` | docs: add ADR-0003 collection ladder and AI relevance cascade |
| `9a8ea97` | docs: update SOW to v0.2 with pipeline stages and report audiences |

### Next

- M0-03: A/M proposal deck (due 29 Sep 23:59).

---

## 2026-09-27 — M0-01 Repository setup, M0-02 Scope of work and decisions

**Branch:** `main` (initial setup), then `docs/m0-scope-of-work`

### Done

- **Repository.** Cloned the empty private repo `hkkk27/news-scraper`. Added the README, a `.gitignore` for Python, Node, secrets and local data, and a `.gitattributes` that stores LF line endings because the pipeline runs on Linux.
- **Open-source survey.** Evaluated 8 candidate projects, plus the small India-specific scrapers, from GitHub. Decision: build a lean core and reuse libraries as dependencies rather than fork a product ([ADR-0001](decisions/0001-build-lean-core-not-fork.md)).
- **Stack and cost.** Chose GitHub Actions, Supabase and Cloudflare Pages on free tiers, with a VPS as the fallback. Budgeted Actions minutes for a private repo at about 1,230 of 2,000 a month ([ADR-0002](decisions/0002-stack-and-hosting.md)).
- **Source verification.** Tested 21 feeds:
  - 14 work, including Hindi publisher feeds and Google News search in `en`, `hi`, `mr` and `ta`.
  - 7 need another method, recorded in [sources.md](sources.md).
- **Scope of work.** Wrote the [SOW](SOW.md): deliverables with acceptance criteria, taxonomy and priority rubric, three-level de-duplication protocol, training loop, timeline and a 29-task work breakdown.
- **Git conventions.** Wrote [CONTRIBUTING.md](../CONTRIBUTING.md): branch per task, Conventional Commits, PR merges and milestone tags.

### Commits

| Hash | Message |
|---|---|
| `61f1652` | chore: initialize repository with README and .gitignore |
| `c7e2cda` | chore: normalize line endings with .gitattributes |
| `5f577db` | docs: add scope of work with milestones, taxonomy and WBS |
| `841d1fe` | docs: add ADR-0001 build a lean core instead of forking |
| `7b8043e` | docs: add ADR-0002 stack and hosting within Rs 500/month |
| `e1f8aba` | docs: add source registry with 27 Sep verification results |
| `8c8aebe` | docs: add contributing guide with branch, commit and release rules |

### Key finding

The 14-day uninterrupted run (D3) has to end by 19 October, so **the pipeline must be live
by 5 October**, before the selection outcome is fully settled. Backend work therefore
starts immediately after M0.

### Next

- Review and merge `docs/m0-scope-of-work` into `main`.
- M0-03: build the A/M proposal deck (3–5 slides), due 29 Sep 23:59.
- M1-01: Python package skeleton, config loader and CLI.
