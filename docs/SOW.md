# Scope of Work — News & Election Tracker (India)

| | |
|---|---|
| **Version** | 0.1 (draft) |
| **Date** | 27 September 2026 |
| **Prepared by** | Harshit Singh |
| **Prepared for** | Siddharth Sachdev (personal initiative) |
| **Target completion** | 19 October 2026 |
| **Budget** | ₹15,000 fixed fee; running cost ceiling ₹500/month |

---

## 1. Objective

Build an online intelligence platform that tracks and curates news relevant to **school
education, higher education and skill development** in India. On top of general sector
news it tracks five special streams:

1. **Transfer and posting orders** for central and state government officers.
2. **Election announcements** and results, from national elections down to municipal bodies.
3. **Political developments** relevant to the sectors (cabinet and portfolio changes, and similar).
4. **Supreme Court and High Court decisions**.
5. **Policy decisions and statements** by ministries, regulators, state governments and political leaders.

All data feeds a customizable reporting structure (daily and weekly) and a dashboard,
segregated at minimum by **state** and **sector**. The design must allow new sectors
(such as healthcare), states and geographies to be added later without rewriting the
system.

## 2. Scope

### 2.1 In scope (v1)

| Area | Included |
|---|---|
| Sectors | School education, higher education, skill development |
| Geography | India: national, 28 states and 8 union territories, with district and municipal tagging where the text names them |
| Source types | Department websites, official PDFs, national media, vernacular (regional-language) papers, legal media, X.com handles |
| Streams | Sector news, transfers, elections, political developments, court decisions, policy and statements |
| Curation | Automatic tagging, relevance scoring, de-duplication, and a training loop that learns from user feedback |
| Users | 3–5 concurrent users with login; mobile-friendly training mode |
| Reporting | Daily and weekly reports by state, sector and category, plus an interactive dashboard |
| Operations | Two weeks of uninterrupted processing, with evidence (run logs) |
| Handover | Runbook, methodology document, a 2-hour hands-on session, and transfer of all accounts |

### 2.2 Out of scope (v1)

- Other sectors and countries. The architecture supports them (see §10), but only the three sectors above are populated.
- Native Android and iOS apps. The web app is mobile-first and installable as a PWA instead.
- Paid news or data APIs, including the official X API (too expensive for the budget).
- Bulk historical backfill. v1 starts from go-live, plus up to 7 days of look-back where sources allow.
- Guaranteed OCR of scanned regional-language PDFs. This is best-effort, and failures are flagged for manual review.
- Bypassing CAPTCHAs, logins or paywalls on any source.

## 3. Deliverables, milestones and acceptance criteria

The four deliverables follow the brief's payment schedule.

### D1 — Backend & Training Platform (₹4,000)

- An ingestion pipeline running on a schedule across all source types in §7.
- Every stored item is tagged with sector(s), geography (state/UT or "National"), category, priority and a relevance score (taxonomy in §6).
- De-duplication and story clustering (§8).
- Feedback capture and a relevance model that learns from it (§9).
- Sources, sectors, states and keywords live in configuration, not code.

**Acceptance:** the scheduled pipeline has run unattended for 48 hours; at least 25 sources are active across at least 4 source types; exact duplicates are 0%; a feedback label given in the app changes the next run's scores; a new RSS feed can be added by editing config only.

### D2 — Frontend & Reporting Structure (₹4,000)

- A web app with login for up to 5 users: a filterable feed (state, sector, category, date, source type, language, priority), a mobile training mode, and source and keyword management.
- A daily report (07:30 IST) and a weekly report (Monday), shown in the app and sent by email.
- Tracker views for transfers, elections (with a calendar) and court rulings.
- A dashboard with volumes and trends by state and sector.

**Acceptance:** all views work on a 375 px phone screen; the daily and weekly reports generate automatically; filters combine correctly.

### D3 — Two Weeks of Uninterrupted Processing (₹4,000)

- 14 consecutive days in production.
- A public run log showing each scheduled run, items collected and errors.
- A weekly accuracy review based on sampled precision of relevance tagging.

**Acceptance:** at least 95% of scheduled runs succeed; no gap between successful runs exceeds 6 hours; a daily report goes out on all 14 days.

### D4 — Handover & Hands-on Training (₹3,000)

- A runbook (operate, monitor, fix), a methodology document (how collection, tagging, de-duplication and learning work) and an extension guide (add a feed, sector, state or geography).
- A 2-hour hands-on training and walkthrough session.
- Transfer of ownership of the repository, database, hosting and secrets.

**Acceptance:** after the session the client adds a new source and a new keyword, and retrains the model, without help.

## 4. Timeline

The brief's dates impose one hard constraint. **Two weeks of uninterrupted processing
must finish by 19 October, so the system has to be live by 5 October.** That is why
backend work starts now rather than after selection.

| Dates (2026) | Milestone | Key output |
|---|---|---|
| Sun 27 Sep – Tue 29 Sep | **M0 Planning** | SOW, repository, source verification, A/M deck (due **29 Sep 23:59**) |
| Wed 30 Sep – Sun 4 Oct | **M1 Backend & training** (D1) | Pipeline live on schedule by 4 Oct |
| Fri 2 Oct | Selection call | Confirm open questions (§15) |
| Mon 5 Oct – Mon 12 Oct | **M2 Frontend & reporting** (D2) | Built while the pipeline runs |
| Mon 5 Oct – Mon 19 Oct | **M3 Uninterrupted processing** (D3) | 14-day run log |
| Fri 16 Oct – Mon 19 Oct | **M4 Handover** (D4) | Documents, session, ownership transfer |

## 5. Solution overview

```
 SOURCES                  PIPELINE (scheduled, GitHub Actions)              STORAGE & APPS
 ───────                  ─────────────────────────────────────             ──────────────
 RSS feeds          ┐
 Google News search ┤     ┌──────────┐  ┌───────────┐  ┌─────────┐  ┌──────────────┐
 Vernacular RSS     ┼───▶ │ Adapters │─▶│ Normalise │─▶│ De-dup  │─▶│  Classify    │
 Official pages/PDF ┤     │ (one per │  │ + extract │  │ + story │  │ rules → model│
 X.com handles      ┘     │  type)   │  │   text    │  │ cluster │  │ → LLM (if    │
                          └──────────┘  └───────────┘  └─────────┘  │  uncertain)  │
                                                                     └──────┬───────┘
                                                                            ▼
                    ┌──────────────────────────────────────────────────────────────┐
                    │ Postgres (Supabase): items, stories, tags, sources, feedback,│
                    │ runs, reports                                                 │
                    └───────┬───────────────────────────────┬──────────────────────┘
                            ▼                               ▼
                 Web app (mobile-first PWA)        Report generator
                 feed · training · trackers ·      daily 07:30 IST · weekly Mon
                 dashboard · settings              → app + email
                            │
                            └── feedback (👍/👎, re-tag, mute) ──▶ nightly retrain
```

Each box is a separate module with a small interface, so a new source type, sector or
report can be added without touching the rest.

## 6. Taxonomy (classification and tagging rubric)

Every item carries the following tags. The vocabularies live in `config/taxonomy/` and
can be extended without code changes.

| Dimension | Values | Cardinality |
|---|---|---|
| **Sector** | `school_education`, `higher_education`, `skill_development` (future: `healthcare`, …) | one or more |
| **Category** | `policy` · `statement` · `court` · `transfer` · `election` · `political` · `news` | one primary, optional secondary |
| **Geography level** | `national` · `state` · `district` · `municipal` | one |
| **State/UT** | ISO 3166-2:IN code (for example `IN-MH`, `IN-UP`); "National" if none | zero or more |
| **District / local body** | Free text normalized against a gazetteer | optional |
| **Actor** | Central ministry, state department, regulator (UGC, AICTE, NCTE, NCERT, CBSE, NTA, NCVET, NSDC…), court (SC or a named HC), election body (ECI or a State Election Commission), political party, officer | zero or more |
| **Source type** | `official` · `national_media` · `regional_media` · `legal_media` · `social` | one |
| **Language** | ISO 639-1 (`en`, `hi`, `mr`, `ta`, `te`, `bn`, …) | one |
| **Priority** | `high` · `medium` · `low` (rubric below) | one |
| **Relevance score** | 0.00–1.00, learned (§9) | one |

**Category definitions**

| Category | Includes | Example |
|---|---|---|
| `policy` | Government decisions, schemes, regulations, circulars, notifications, budgets | "UGC notifies draft regulations on foreign university campuses" |
| `statement` | On-record statements by ministers, officials, regulators or party leaders | "Education Minister says NEP rollout in states to finish by 2027" |
| `court` | SC/HC judgments, orders, notices and hearings | "Bombay HC quashes fee hike order for unaided schools" |
| `transfer` | Transfers, postings, appointments and repatriations of officers, including VCs and regulator heads | "Maharashtra transfers 12 IAS officers; new School Education Secretary named" |
| `election` | Schedules, notifications, polling, results, by-polls, and local-body and university/teacher-constituency polls | "SEC announces municipal corporation polls in 5 cities" |
| `political` | Government formation, cabinet or portfolio changes, and alliance shifts affecting sector governance | "New Higher Education Minister sworn in in Karnataka" |
| `news` | Other sector news: exams, admissions, results, protests, infrastructure, data and reports | "Board exam results declared; pass rate 88%" |

**Priority rubric**

| Priority | Rule of thumb |
|---|---|
| `high` | An official decision, order, judgment or election notification that directly affects a tracked sector, or the transfer of an officer holding a sector portfolio |
| `medium` | Statements, announcements, reports and data releases; elections and political changes not specific to the sector |
| `low` | Opinion and explainers, generic coverage, and items outside tracked states |

## 7. Source strategy

Full list and test results: [sources.md](sources.md).

| Source type | Method | Notes |
|---|---|---|
| National media (education sections) | RSS | The Hindu, Indian Express, ThePrint, EdexLive and others (verified 27 Sep) |
| Vernacular media | Publisher RSS, plus Google News search RSS per language | Google News search verified for `en`, `hi`, `mr` and `ta`; gives vernacular coverage without a scraper per paper |
| Legal media | RSS plus keyword filter | LiveLaw verified; court-stream queries through Google News |
| Official (PIB, ministries, regulators, ECI, State Election Commissions, state departments) | PIB RSS, plus **page watchers** that diff the list of links on notice/order pages and download new PDFs | PDF text extraction; OCR for scanned files is best-effort |
| X.com | Configured list of handles (ministers, ministries, regulators, Chief Minister offices, State Election Commissions), collected with a pay-per-result scraper (Apify) within the free monthly credit | The official X API is excluded on cost; fallbacks are RSSHub and twscrape |
| Transfers | Google News query packs ("IAS officers transferred", "reshuffle", state-language equivalents), plus page watchers on DoPT and state General Administration Department (GAD) order pages | |
| Elections | ECI and State Election Commission press-note pages, plus query packs for "municipal", "panchayat", "by-poll" and "local body" | |

## 8. De-duplication and reliability

**De-duplication (three levels)**

1. **Exact:** hash of the canonical URL, after stripping tracking parameters, AMP and mobile variants, and decoding Google News redirects.
2. **Near-duplicate:** normalized-title and text similarity within a 72-hour window. Near-duplicates join the same *story cluster*.
3. **Semantic / cross-language:** multilingual embedding similarity above a threshold, so that a Hindi and an English report of the same order form one story. This is an M1 stretch goal.

A story cluster shows one canonical item and lists all outlets. The number of independent
sources counts as corroboration and raises confidence.

**Update frequency** (tunable in config)

| Stream | Frequency |
|---|---|
| News and Google News queries | Every 2 hours |
| Official pages and PDFs | 4 times a day |
| X.com | Every 6 hours (bounded by scraper credit) |
| Model retrain | Nightly |

**Reliability measures**

- Idempotent upserts, so reruns never create duplicates.
- Retries with back-off.
- A `runs` table logging every run.
- Per-source health (last success, items per run, consecutive failures), with an alert when a source goes silent for 48 hours.
- A daily health line in the report.

## 9. Training mechanism (learning relevance)

Users train the system from their phone while reading:

- **👍 / 👎** marks an item relevant or not relevant.
- **Re-tag** corrects the sector, state or category.
- **Mute / boost** acts on a source or keyword.

The feedback improves three layers, from cheapest to most expensive:

1. **Rules:** keyword and source weights, editable in the app and adjusted by mute and boost.
2. **Learned model:** a small classifier (TF-IDF or multilingual embeddings with logistic regression), retrained nightly from labels. It needs no GPU and runs in seconds.
3. **LLM:** called only for items the first two layers are unsure about. The prompt carries a plain-English relevance brief plus recent labelled examples (few-shot), with a hard monthly spending cap.

**Measurement:** the dashboard shows weekly precision on sampled items and the number of
labels collected.

## 10. Extensibility

| To add | Change |
|---|---|
| A feed | One entry in `config/sources/*.yaml` |
| A keyword or query pack | Edit `config/taxonomy/sectors/*.yaml` or `config/sources/google_news.yaml` |
| A sector (for example healthcare) | New file `config/taxonomy/sectors/healthcare.yaml` with keywords per language; it then appears in filters and reports |
| A state, district or municipality | Add aliases in `config/geography/india.yaml` |
| A country or geography | New gazetteer `config/geography/<country>.yaml` plus source files |
| A source type | New adapter class implementing the `Source` interface; register it in config |

## 11. Technology and running cost

| Component | Choice | Monthly cost |
|---|---|---|
| Pipeline and scheduler | Python 3.11 on GitHub Actions cron (private repo: 2,000 free minutes a month; the planned load is about 1,200) | ₹0 |
| Database and auth | Supabase free tier (Postgres, email login, row-level security) | ₹0 |
| Web app | Static PWA on Cloudflare Pages free tier | ₹0 |
| Email reports | Gmail SMTP or Resend free tier | ₹0 |
| LLM tagging | Only for uncertain items; hard cap in config | ≤ ₹300 |
| X.com collection | Apify free monthly credit; capped | ₹0–150 |
| Domain (optional) | .in domain | ~₹70 |
| **Total** | | **≤ ₹500** |

Free-tier limits and prices are to be re-verified at M1-03. The fallback is a small VPS at
about ₹400 a month, since all components are portable. Rationale:
[ADR-0002](decisions/0002-stack-and-hosting.md).

## 12. Work breakdown structure

Each task gets its own branch and a WORKLOG entry (see [CONTRIBUTING.md](../CONTRIBUTING.md)).

| ID | Task | Deliverable | Status |
|---|---|---|---|
| **M0** | **Planning** | | |
| M0-01 | Repository setup, git conventions | — | Done |
| M0-02 | Scope of work, decisions, source verification | — | In review |
| M0-03 | A/M proposal: 3–5 slides, profile, prior work (due 29 Sep 23:59) | Application | To do |
| **M1** | **Backend & training platform** | D1 | |
| M1-01 | Python package skeleton, config loader, logging, CLI | D1 | To do |
| M1-02 | Taxonomy and geography config (sectors, categories, 36 states/UTs with multilingual aliases) | D1 | To do |
| M1-03 | Storage schema (Supabase Postgres, SQLite for local dev), migrations | D1 | To do |
| M1-04 | RSS and Google News source adapters | D1 | To do |
| M1-05 | Official website and PDF watcher | D1 | To do |
| M1-06 | X.com adapter | D1 | To do |
| M1-07 | Normalization and full-text extraction | D1 | To do |
| M1-08 | De-duplication and story clustering | D1 | To do |
| M1-09 | Rule-based tagger (sector, geography, category, priority) | D1 | To do |
| M1-10 | LLM tagger for uncertain items, with cost cap | D1 | To do |
| M1-11 | Feedback store and learned relevance model | D1 | To do |
| M1-12 | Scheduled workflows, run log, source-health alerts; go-live | D1 | To do |
| **M2** | **Frontend & reporting** | D2 | |
| M2-01 | Web app skeleton, login (up to 5 users) | D2 | To do |
| M2-02 | Feed view with combined filters | D2 | To do |
| M2-03 | Mobile training mode (rate, re-tag, mute and boost) | D2 | To do |
| M2-04 | Settings: sources, keywords, taxonomy | D2 | To do |
| M2-05 | Daily report (app and email) | D2 | To do |
| M2-06 | Weekly report | D2 | To do |
| M2-07 | Dashboard metrics and charts | D2 | To do |
| M2-08 | Trackers: transfers, elections calendar, court rulings | D2 | To do |
| **M3** | **Uninterrupted processing** | D3 | |
| M3-01 | Go-live checklist and monitoring | D3 | To do |
| M3-02 | Daily run log and weekly accuracy review | D3 | To do |
| M3-03 | Tuning and fixes (`fix/` branches) | D3 | To do |
| **M4** | **Handover** | D4 | |
| M4-01 | Runbook, methodology and extension guide | D4 | To do |
| M4-02 | 2-hour training session and materials | D4 | To do |
| M4-03 | Ownership transfer (repo, Supabase, hosting, secrets) | D4 | To do |

## 13. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| The 14-day run window compresses if go-live slips past 5 October | D3 fails | Build before selection; go live on our own accounts and transfer ownership at handover |
| X.com access or pricing changes | Loss of the social stream | Pay-per-result scraper within credit; fallbacks (RSSHub, twscrape); X treated as supplementary, never the only source for a stream |
| Government sites that are JavaScript-heavy, slow or blocking | Missed official orders | Headless fetch only where needed; polite rate limits; news coverage of the same order as backup; CAPTCHAs are never bypassed |
| Scanned PDFs in regional languages | Missing text | OCR best-effort; flag untagged PDFs for manual review in the app |
| Free-tier limits change | Cost over ceiling | Portable Postgres and Python; VPS fallback at about ₹400 a month |
| LLM cost overrun | Budget breach | Rules and model first; LLM only when uncertain; hard monthly cap |
| Storage fills the 500 MB free database | Writes fail | Store excerpts and links, not full pages; retention policy for low-relevance items |
| Copyright and terms of use | Legal exposure | Store headline, short excerpt and link only; respect robots.txt and rate limits |

## 14. Documentation and change control

- Every task is logged in [WORKLOG.md](WORKLOG.md) with its date, branch, commits and outcome.
- Every significant choice gets an architecture decision record in [decisions/](decisions/).
- Changes to this SOW are versioned in the table below and agreed with the client.

## 15. Open questions for the client (for the 2 October call)

1. Should v1 cover all 36 states and UTs equally, or a priority shortlist?
2. Which officers count for the transfer stream: IAS only, or also state education department officers, vice-chancellors and regulator heads?
3. Who receives the reports, and on which channel (email, WhatsApp, both)?
4. Is there an existing list of X handles to track?
5. Which regional languages matter most beyond Hindi?
6. At handover, should accounts move to the client's GitHub, Supabase and Cloudflare, or stay with us under a maintenance arrangement?

## Change log

| Version | Date | Change |
|---|---|---|
| 0.1 | 27 Sep 2026 | First draft |
