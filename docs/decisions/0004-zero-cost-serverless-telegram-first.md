# ADR-0004: ₹0 serverless design, SQLite-first and Telegram-first

- **Status:** Accepted (28 September 2026)
- **Supersedes:** the Supabase choice in [ADR-0002](0002-stack-and-hosting.md), and the paid-LLM default in [ADR-0003](0003-collection-and-ai-within-budget.md)
- **Task:** M0-04

## Context

The team reviewed ADR-0002 and ADR-0003 and raised four concerns.

- **Supabase free tier.** It costs ₹0, but its next tier (Pro) is about ₹2,100 a month, four times the whole budget. Free projects also pause after a week without activity. We should not depend on a service whose only upgrade path breaks the budget.
- **Paid LLM.** A paid LLM for relevance (about ₹260 a month) uses half the budget and grows with news volume.
- **Not just a website.** The client and his leadership should get the tracker where they already work (phone, email, Excel), rather than having to remember to open a website.
- **Resale.** If this client passes, the product should be sellable to other people who spend hours searching for sector news. That means configuration-driven profiles, not hard-coded logic.

Five options were compared, recorded in the 27 September session:

| Option | What it is |
|---|---|
| A | Serverless |
| B | One free cloud VM |
| C | The client's own computer |
| D | Google Sheets-native |
| E | Low-code n8n |

The team chose **Option A**.

## Decision

| Concern | Decision |
|---|---|
| **Compute** | Scheduled Python pipeline on GitHub Actions: collection every 2 hours, reports at 07:30 IST and on Monday, retraining nightly. |
| **Storage** | **SQLite is the single source of truth.** In CI the database file lives on an orphan `data` branch of the repository (fetched at the start of each run, force-pushed at the end), so the only account needed is GitHub. The storage layer is an interface, so Cloudflare D1 (hosted SQLite, 5 GB free), or a local machine running the same file, is a configuration change. |
| **Mobile app and training** | **A Telegram bot.** It sends the morning brief with buttons on every item (Relevant / Not relevant / wrong tag), accepts forwarded links, PDFs and text as manual feed-in, and answers `/today`, `/state`, `/sector` and `/search`. Access is limited to an allowlist of chat IDs. |
| **Leadership and analysts** | Executive brief and analyst digest as HTML email and saved files; weekly Excel workbook split by state and sector. |
| **Dashboard** | A static, mobile-first site generated each run (filters, trackers for transfers, elections and courts, charts). It is hosted on Cloudflare Pages behind Cloudflare Access email login (free for up to 50 users), or served locally. |
| **Relevance** | L1 multilingual rules → L2 local model trained on feedback labels (TF-IDF character n-grams + logistic regression, which needs no downloads; multilingual embeddings optional) → L3 LLM **only if configured**. The default L3 is the free Gemini API tier (about 15 batched requests a day against a quota of roughly 500–1,000). Paid providers are off by default. |
| **X.com** | Apify pay-per-result actor, within its free monthly credit; disabled until a token is configured. |
| **Resale** | Everything client-specific lives under `config/`: sectors, streams, geography, sources and recipients. A new customer is a new config profile. |

## Cost

| Item | ₹/month |
|---|---|
| GitHub Actions, data branch, Telegram, Cloudflare Pages and Access, local models, free Gemini tier | 0 |
| X.com collection (optional, capped) | 0–150 |
| **Total** | **0–150** |

## Consequences

- **Feedback timing.** Telegram button presses are processed at the next scheduled run, not instantly. The bot confirms them then. If instant confirmation is wanted later, a Cloudflare Worker webhook can be added without changing the pipeline.
- **One writer at a time.** SQLite allows one writer, so all workflows share one concurrency group and never run in parallel.
- **Runners are outside India.** Some Indian government sites block foreign IP addresses. Per-source health logging shows this quickly. The mitigation is a self-hosted runner, for example on an office PC, which the same workflow supports.
- **Free-tier changes.** GitHub, Cloudflare and Google change free tiers from time to time. Every one of them is optional or swappable, and the pipeline degrades gracefully: with no LLM, uncertain items wait in a review queue.
- **Retired option.** GitHub Models, a free LLM API noted during research, was retired on 30 July 2026 and is not used.
