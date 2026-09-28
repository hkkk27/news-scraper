# Work Log

Newest entries at the top. One entry per task or working session. Format rules are in
[CONTRIBUTING.md](../CONTRIBUTING.md#5-documentation-rules).

---

## 2026-09-29 — M4-04 Samples, slide content, demo script

**Branch:** `docs/m4-04-samples-and-slides`

### Done

- **Live pass.** Ran a fresh `tracker run` plus daily and weekly reports: 1,996 items stored, 469 relevant stories in 24 h, 111 core, 9 languages, 27 states/UTs, 8/8 runs OK.
- **`samples/`.** Real outputs, unedited: executive brief, analyst digest, Excel, Telegram brief text (daily and weekly), and the dashboard with data embedded. A README explains each file and the numbers behind it.
- **`docs/proposal/slide-content.md`.** The 5-slide content for Claude Design: design direction, real numbers, screenshots to take, speaker notes and placeholders. TrendRadar is described as the next integration step, not as already running.
- **`docs/proposal/demo-script.md`.** A 3-minute demo video script.
- **Proposal README.** Marks the 27 Sep artifact deck as outdated, because it still shows Supabase and a paid LLM.
- **Watcher check.** 15 "new" items per run come from the Supreme Court's daily judgments list. That is genuine churn capped by `max_new`, not a bug.

### Next

- M4-01: setup guide, runbook, methodology, README quickstart.

---

## 2026-09-29 — M1-12 Scheduled pipeline and go-live

**Branch:** `feat/m1-12-scheduler`

### Done

- **`tracker run`.** One scheduled pass: watch official pages → process Telegram updates → gather, tag, score and cluster → rebuild the dashboard. Steps are isolated, and the SQLite write-ahead log is checkpointed before the file is saved.
- **`scripts/data_branch.sh restore|save`.** Keeps `data/` on an orphan `data` branch as a single force-pushed commit. Tested round-trip against a local bare repository.
- **`.github/workflows/tracker.yml`:**
  - Every 2 hours: `run`.
  - 07:30 IST: daily report (email + Telegram).
  - Monday 08:00 IST: weekly report with Excel.
  - 03:10 IST: nightly retrain.
  - One concurrency group (single SQLite writer). Outputs are kept 14 days as artifacts. Cloudflare Pages deploy is optional, when its secrets are set.
- **`.github/workflows/tests.yml`.** Runs pytest on every push and pull request.
- **Local run:** the watcher found 15 new official notices since the baseline; process gave 116 core, 328 relevant.
- **Go-live.** Merging to `main` starts the schedule. It runs without secrets (Telegram and email are skipped) until the owner adds them. Budget: about 1,000 of 2,000 free Actions minutes a month.

### Next

- M4-01: setup guide, runbook, methodology.
- M4-04: sample outputs and slide content.

---

## 2026-09-28 — M2-01/07/08 Dashboard

**Branch:** `feat/m2-01-dashboard`

### Done

- **`tracker site`.** Builds `output/site/index.html`, a single static page with the last 30 days of stories and the run log embedded. It works from disk or any static host (Cloudflare Pages behind Cloudflare Access email login).
- **Filters:** period (today / 7 / 30 days), relevance (core / relevant+ / all), sector, state, category, language, search. They are remembered per browser.
- **Tabs:**
  - Feed, and trackers for transfers, elections, court rulings and policy.
  - Insights: stories per day (stacked core / other), and counts by state (national shown separately), sector, category, language and deciding layer. Hover tooltips, plus a table view.
  - Run log: success rate and the longest gap between successful runs, which is the evidence for D3.
- **Visual checks** in the browser pane: desktop, 375 px phone (no horizontal scroll), dark mode.
  - Chart colors use the validated reference palette. The deck's teal failed the chroma check.
  - Fixed a clipped axis label, and excluded "National" from the state chart because it swamped the states.
- **Tests:** 68 passing.

### Next

- M1-12: GitHub Actions workflow and `data`-branch persistence.

---

## 2026-09-28 — M2-05/06 Reports; M2-03 Telegram commands

**Branch:** `feat/m2-05-reports`

### Done

- **Reports module** (`tracker/reports.py`). Every format is built from the same stories, where a story is the best item in a cluster, with its outlet count:
  - **Analyst digest (HTML):** sector → state → category, with each item's "why" reasons.
  - **Executive brief (HTML):** one page with varied top developments plus trackers for transfers, elections and court rulings.
  - **Excel workbook:** a state × sector pivot, all stories, and a sheet each for transfers, elections, courts and policy.
  - **Telegram brief text** and SMTP email. The footer shows run health (runs OK, failing sources).
- **`tracker report daily|weekly [--send]`.** Writes to `output/reports/<kind>-<date>/`. With `--send`, the brief goes to leadership, the digest (plus Excel weekly) to analysts, and the brief plus top cards (with training buttons) to Telegram.
- **Bot commands** (`tracker/commands.py`): `/today`, `/week`, `/search`, `/state`, `/sector` reply with story cards.
- **Visual check** in the browser pane. Issues found and fixed:
  1. Three outlets' versions of the same Supreme Court CBSE order all made the top list. The brief now skips headlines that share key words with one already chosen.
  2. A CISF security deployment was tagged as a transfer ("नियुक्त" + generic "अधिकारी"). Transfers now need a cadre or senior post.
  3. "Headlines for school assembly" round-ups and SEO pages now get a noise penalty.
- **Live daily report:** 357 stories, 81 core. The top 8 are 8 distinct developments.
- **Tests:** 67 passing.

### Next

- M1-12: GitHub Actions workflow with `data`-branch persistence.
- M2-01: dashboard.

---

## 2026-09-28 — M1-11 Learned relevance model (L2) and layer blending

**Branch:** `feat/m1-11-learning`

### Done

- **Model** (`tracker/learn.py`): TF-IDF (character 2–5-grams, which work across Indian scripts, plus word 1–2-grams) and a balanced logistic regression. It needs no GPU or downloads and trains in seconds.
- **Training data:**
  - The latest label per item from Telegram (👍 / ⭐ / 👎) and forwarded items.
  - 60 bilingual seed labels (`config/training/seed_labels.yaml`) at half weight, for day one.
- **`tracker train`.** Saves the model with cross-validated accuracy and precision. Seed-only run: accuracy 0.67, precision 0.64, weight 0.10.
- **Blending in `process`:** rules → model → engine AI score (L3, uncertain band only). Every item records which layer decided.
- **Fix during the live check.** The first blend (a convex mix) let a weak seed-only model pull every score down, and 91 items fell out of Relevant. It is now neutral when unsure: `rule + w × (100p − 50)`, giving at most ±35 points at full weight.
- **Live run:** 1,352 items → 109 Core, 330 Relevant.
- **Tests:** 62 passing.

### Next

- M2-05/06: daily and weekly analyst digest, executive brief and Excel.

---

## 2026-09-28 — M1-08 Story clustering

**Branch:** `feat/m1-08-story-clustering`

### Done

- **Clustering** (`tracker/stories.py`). This is level-2 de-duplication; level 1 is the canonical-URL key.
  - Titles are normalized before comparing ("SC" → "supreme court", "Class VI" → "class 6", "3rd" → "3").
  - Items are compared with TF-IDF cosine similarity, within one language and a 72-hour window.
  - Two items only group when their states agree, so "Tamil Nadu NEET counselling" and "Odisha NEET counselling" stay apart.
- **Stable ids and corroboration.** Story ids stay stable across runs. Each story stores how many distinct outlets reported it (`sources_count`); reports will show this as corroboration.
- **Threshold choice.** Compared 0.35 / 0.4 / 0.45 / 0.55 on live data and picked 0.4 with state agreement. Without the state rule, different states' NEET counselling notices merged.
- **Process.** Clustering now runs in every `process` pass. The database migrates in place (new `sources_count` column).
- **Live result:** 472 Core/Relevant items → 373 stories. The Supreme Court CBSE three-language order appears as clusters of 4–6 outlets.
- **Tests:** 56 passing.

### Next

- M1-11: the learned relevance model (L2) trained on Telegram labels.

---

## 2026-09-28 — M1-07 India-layer tagging, scoring and item store

**Branch:** `feat/m1-07-india-tagger`

### Done

- **Tagger** (`tracker/tagger.py`). For each item it sets:
  - Sectors, from title and summary evidence.
  - Category by precedence (transfers need an officer term; election announcements are marked separately).
  - Actors, states and geography level. States come from names, High Court seats, cities and the source hint; "New Delhi" datelines are ignored.
  - Language, by script.
  - A 0–100 score, with a `reasons` list naming every point added or removed.
- **Scoring rules.** `config/taxonomy/scoring.yaml` holds all the weights. A category known only from the source's focus counts half.
- **Item model** (`tracker/items.py`). Google News publisher suffixes are split off, so "Punjab Kesari" or "Telangana Today" is never read as a place.
- **Engine reader** (`tracker/engine_store.py`). Reads TrendRadar's SQLite output read-only, including AI-filter scores. `tracker/collect.py` is a direct fallback collector.
- **Processing pass** (`tracker/process.py`, `tracker process`):
  - Tags and scores every item; a human label overrides the models.
  - Sets band and priority and upserts into the new `items` table.
  - Logs each run in the new `runs` table: the evidence for the 14-day run.
- **Quality review on live data.** 1,438 items, sampled by band. Fixes:
  - Bangladeshi news via the Bengali edition: foreign markers, and Bengali queries now require West Bengal context.
  - "SC extends/asks …" is now recognised as a court ruling.
  - Source focus alone no longer lifts an item to Core.
  - A court case about elections counts the stronger stream.
  - The skills query had a bare "ITI" that matched Ilocano text.
  - More Bengali and education terms; UK and Philippines markers.
- **Latest live run:** 1,337 items → 110 Core, 351 Relevant, 237 Peripheral, 639 Not relevant.
- **Tests:** 51 passing.

### Next

- M1-08: story clustering across feeds (e.g. one Supreme Court CBSE order reported by 10+ outlets).

---

## 2026-09-28 — M1-13 Telegram bot

**Branch:** `feat/m1-13-telegram-bot` (work log repaired in `fix/worklog-restore`)

### Done

- **Database.** `tracker/db.py` is the India layer's SQLite store (`data/tracker.db`): feedback, cards, intake, muted sources, key/value state.
- **URL keys.** `tracker/urls.py` does URL canonicalisation (drops tracking params, AMP/mobile variants and fragments) and makes a 12-character item key.
- **API client.** `tracker/telegram.py` is a minimal Bot API client over plain HTTPS, with no framework.
- **Bot** (`tracker/bot.py`):
  - Item cards carry 👍 / 👎 / ⭐ / 🔇 buttons; each press is stored as a training label, and 🔇 also mutes the source.
  - A forwarded link (title taken from the page's `og:title`), PDF (first-page text) or plain text becomes an item in `data/feeds/manual-feed-in.xml` and counts as a positive label.
  - Only allowlisted chats are served; anyone else sending `/start` is told their chat ID for onboarding.
  - Other modules can register commands such as `/search`, `/state` and `/today`.
- **CLI:**
  - `tracker bot poll` processes pending updates once (used by CI).
  - `tracker bot listen` long-polls for instant replies.
  - `tracker bot test-card` sends a sample card.
- **Tests:** 30 passing.

### Incident

- The work-log helper crashed while writing this entry (the shell passed emoji to Python as invalid UTF-8). It had already truncated `WORKLOG.md`, and the empty file was committed in `24d01e4`.
- Restored from `308aa50`. The helper now reads entries from a UTF-8 file and writes atomically, and it refuses to run on an empty log.

### Needs from the owner

- A bot token from @BotFather and the chat IDs to allow. See the setup guide (to be written in M4-01).

### Next

- M1-07: India-layer tagging and relevance bands.

---

## 2026-09-28 â€” M1-05 Official page and PDF watcher

**Branch:** `feat/m1-05-official-watcher`

### Done

- **Watched pages.** `config/sources/watch.yaml` lists 8 official pages verified to serve plain-HTML links: UGC, AICTE, CBSE, NTA, DoPT, the Supreme Court, DGT (skills) and the Maharashtra SEC. JavaScript-rendered sites (MoE, MSDE, ECI) are left to PIB and Google News.
- **Watcher** (`tracker/watch.py`). On each run it:
  1. Fetches the page and lists its links.
  2. Keeps the new links that pass the include/exclude rules.
  3. Writes them to `data/feeds/official-<id>.xml`, which the engine ingests.
  - The first visit only records a baseline; `max_new` caps each run.
  - Generic "Read More" links take their title from the surrounding text. At NTA this raised the captured notices from 2 to 751.
  - File sizes are stripped from titles. First-page PDF text is added when present; scanned PDFs (common for government orders) are labelled.
- **RSS helper.** `tracker/rssfile.py` reads and writes rolling RSS files for all India-layer collectors.
- **Registry.** Watched pages join the source registry as `official-*` feeds carrying their sector, stream and state hints (MahaSEC â†’ MH, elections).
- **Live run.** 8/8 pages reachable and baselined. A simulated second run produced 6 correctly titled items.
- **Tests:** 24 passing.

### Next

- M1-13: Telegram bot (feedback buttons, forward-to-add intake).

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
