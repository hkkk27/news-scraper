# ADR-0003: Collection methods and AI relevance engine within ₹500/month

- **Status:** Proposed
- **Date:** 27 September 2026
- **Task:** M0-02

## Context

The whole platform must run for under ₹500 a month. Two questions decide most of that
cost:

1. **How do we collect?** RSS, scraping, bots or paid APIs.
2. **How do we judge relevance and tag items?** A local model, an AI API, or rules.

The workflow we must support is:

**Collect → scrape (extract text) → organise (clean, de-duplicate) → is it relevant? →
degree of relevance → tag → report**

Government notifications are one of the sources, and the client can also feed items in
by hand.

### Volume assumption (to be measured in M1)

| Stage | Items per day |
|---|---|
| Raw items from about 25 feeds and 30 Google News query packs × 3 languages | 2,000–3,000 |
| Unique items after de-duplication | about 1,500 |

## Decision 1: Collection is a ladder, cheapest and most reliable first

| Rung | Method | Used for | Cost |
|---|---|---|---|
| 1 | **RSS/Atom feeds** | Publishers, PIB, LiveLaw | ₹0; stable and legal |
| 2 | **Google News search RSS** (per sector × stream × language) | Vernacular coverage, transfers, local elections, court news | ₹0 |
| 3 | **Targeted scraping** (HTTP and HTML parsing, link-diff) | Official pages without RSS: ministries, UGC, AICTE, CBSE, ECI, State Election Commissions, state GAD and education departments; new PDFs downloaded and text extracted | ₹0 |
| 4 | **Headless browser** | Only for JavaScript-only official pages; kept to a few sources because it is slow on CI | ₹0 (uses Actions minutes) |
| 5 | **Apify actor** (pay-per-result) | X.com handles; the official X API is too expensive | ₹0 within the free monthly credit; capped |
| — | **Manual feed-in (bot and form)** | Client forwards a link, PDF or text to a **Telegram bot**, or uses the web form. These items are also strong training labels. | ₹0 |

The Telegram bot needs no server. Each scheduled run collects pending messages through
the Bot API (`getUpdates`), which holds messages for 24 hours. A Supabase Edge Function
webhook is the alternative if instant intake is wanted.

We don't use paid news APIs (NewsAPI, GDELT resellers and similar) or the WhatsApp
Business API, because they are over budget.

## Decision 2: Relevance runs as a cascade, where cheap layers decide most items

| Layer | What it does | Where it runs | Cost |
|---|---|---|---|
| **L1 Rules** | Multilingual keyword and gazetteer match (sector terms, regulators, states and districts, officer titles), source prior and blocklist. Drops obvious noise (sports, cinema…) and tags obvious items. | Pipeline (GitHub Actions) | ₹0 |
| **L2 Local ML model** | Small multilingual embedding model (for example `paraphrase-multilingual-MiniLM-L12-v2`, about 120 MB, CPU) + logistic-regression classifier trained on our feedback labels. Outputs the relevance probability. | Pipeline; about 1–2 minutes of CPU for 1,500 items | ₹0 |
| **L3 LLM API** | Only for the **uncertain band** (L2 probability 0.35–0.65) and for tags that L1 and L2 cannot fill (category, officer name, district). Sends 20 items per request with a fixed, cached instruction block and returns strict JSON. | API call | ≤ ₹300 cap |

The expected split is L1 and L2 deciding about 80% of items, leaving about 300 items a
day for L3.

**Degree of relevance** is a score from 0 to 100: 100 × the L2 probability, overridden by
L3 where L3 ran. The score maps to bands:

| Band | Score | Treatment |
|---|---|---|
| Core | 80 or above | Always in the report |
| Relevant | 60–79 | In the report |
| Peripheral | 40–59 | Feed only |
| Not relevant | below 40 | Hidden, but kept for training and audit |

### Options considered for L3 (the LLM)

**Workload:** about 300 items a day in batches of 20, so 15 requests a day.

- Each request: about 2,000 tokens of instructions plus 20 × 250 tokens of items (Indic scripts tokenize longer than English).
- Output: about 60 tokens of JSON per item.
- Totals: about 105k input and 18k output tokens a day.

| Option | Estimated monthly cost | Quality in Indian languages | Reliability | Verdict |
|---|---|---|---|---|
| **Local LLM on GitHub Actions** (1.5–3B model on a 2-vCPU runner) | ₹0 cash, but about 85 min of runner time a day (~2,500 min a month), over the 2,000-minute budget | Weak on Hindi, Marathi and Tamil nuance | Slow; jobs time out | **Rejected** |
| Local LLM on a home PC | ₹0 | Depends on the model | Fails the 14-day uninterrupted run whenever the PC is off | **Rejected** |
| Free-tier APIs (for example Google Gemini, Groq) | ₹0 | Good | Rate limits and free quotas change without notice; free-tier prompts may be used by the provider | **Fallback only** |
| **Claude Haiku 4.5 through the Message Batches API** ($1 / $5 per million input/output tokens, 50% batch discount) | About US$3 a month, roughly ₹260 at about ₹88/US$ | Good | Paid tier; asynchronous batch results are collected on the next run | **Chosen** |
| Claude Haiku 4.5 standard (not batched) | About US$6 a month, roughly ₹520 | Good | — | Over budget on its own |
| Larger models (Sonnet or Opus class) | 2–5× Haiku | Better | — | Over budget for bulk tagging; possible for the weekly narrative summary only |

The chosen design is **provider-agnostic**: one `LLMTagger` interface, with the provider,
model and monthly cap set in config. If prices or quotas change we switch provider in
config, not code.

## Guardrails

- **Hard cap.** Before each call the pipeline sums month-to-date token spend in the `runs` table. At the cap it stops calling L3, and uncertain items stay in the "needs review" queue in the app.
- **Truncation.** Excerpts are truncated to 400 characters. Full text is only fetched for Core and Relevant items.
- **Asynchronous batches.** A batch submitted in run *N* is collected in run *N+1*. Items appear immediately with L1 and L2 tags and are refined when L3 returns.

## Consequences

- Expected operating cost:
  - LLM about ₹260 a month.
  - Infrastructure ₹0 (see ADR-0002).
  - X.com collection ₹0–150 a month.
  - **Total: ₹260–410 a month, under the ₹500 ceiling.**
- As labels accumulate, L2 gets more confident and fewer items reach L3, so LLM cost falls over time.
- Every relevance decision records which layer made it (`decided_by = rules | model | llm | human`), so accuracy per layer can be measured and explained at handover.
