# Slide content for the A/M proposal (for Claude Design)

**Format:** 3 slides as the brief asks (approach and methodology, plus a brief about the
individual and prior work), and a 4th slide with the demo links. Due 29 Sep 2026, 23:59.

**The one message:** *It already runs: ₹0/month, live on Indian news in 9 languages, reports on
Telegram, and it learns from your taps.*

## Style

- **Colours:** ink `#1B2433`, paper `#F6F4EE`, accent `#B34A1F`, teal `#17565D`.
- **Type:** serif headings (Source Serif 4 or Georgia), sans body (IBM Plex Sans).
- **Layout:** one idea per slide, a big number or a real screenshot, short lines.
- **Screenshots** (from `output/` or `samples/`):
  - The executive brief, top of the page.
  - The dashboard's Feed tab and its Insights tab.
  - Your Telegram chat showing the daily brief and a card with 👍 👎 ⭐ 🔇.

## Slide 1 — Understanding and approach

**Title:** Every signal that matters for Indian education, collected, ranked and reported by
state and sector.

**Left: what it tracks.**

- School education · Higher education · Skill development. New sectors (e.g. healthcare) are added by configuration.
- Officer transfers · Elections down to municipal level · SC/HC rulings · Policy decisions · Political changes · Statements.

**Right: seven-step flow** (draw as a horizontal pipeline):

Collect → Extract → De-duplicate → Is it relevant? → How relevant (0–100) → Tag → Report

**Sources strip:**
- 55 feeds in 9 languages (publisher RSS plus Google News in en, hi, mr, ta, te, bn, gu, ml, pa).
- 8 government notice pages: UGC, AICTE, CBSE, NTA, DoPT, Supreme Court, DGT, Maharashtra SEC.
- Anything forwarded to the Telegram bot.

**Proof line:** Live on 28–29 Sep: 2,865 items tagged → 671 relevant stories across 28
states/UTs.

## Slide 2 — Methodology: tagging, learning, reliability, cost

**Tagging rubric (small table):**

| Tag | Values |
|---|---|
| Sector | School · Higher · Skills |
| Category | Policy · Court · Transfer · Election · Political · Statement · News |
| Geography | National → state/UT → district → municipal |
| Relevance | Core ≥80 · Relevant 60–79 · Peripheral 40–59 |
| Priority | High · Medium · Low |

Example: "Bombay HC quashes fee hike for unaided schools" → Court · Maharashtra · School ·
Core.

**How the score is decided** (three stacked boxes):

1. **Rules:** keywords and places in 9 languages, with every point shown as "why".
2. **Learning model:** retrains nightly from 👍/👎 in Telegram.
3. **Free AI** (OpenRouter free models): only for unsure items. It rejected Bangladeshi, UK and coaching-ad items with a stated reason.

**Reliability:**
- Duplicate articles merged into one story with an "N outlets" count.
- Runs every 2 hours on GitHub Actions, and every run is logged.
- 72 automated tests.

**Cost:** ₹0 per month. GitHub Actions, Telegram, GitHub Pages and free AI models, well under
the ₹500 ceiling.

## Slide 3 — About me, prior work, plan

**Harshit Singh:** `[college, programme, batch]` · Python, data pipelines, scraping,
automation.

**Prior work:**
- Education-sector data pipeline (schools and NGOs, India/Gulf/SE Asia; OpenStreetMap, Google Maps, NGO Darpan; merged, de-duplicated, scored).
- Video clipping pipeline.
- Explainer-video generator.

**Built on open source:** TrendRadar (62k★) is imported as the collection and alert engine,
plus our India layer.

**Plan:**

| Dates | Deliverable |
|---|---|
| Now | Prototype live ✅ |
| 30 Sep – 4 Oct | D1 backend and training |
| 5–12 Oct | D2 frontend and reporting |
| 5–19 Oct | D3 14-day run with a public run log |
| 16–19 Oct | D4 handover and 2-hour session |

## Slide 4 — See it live

- **Demo video:** `[paste your video link]`
- **Live dashboard:** https://hkkk27.github.io/news-scraper/ (once the repo is public and Pages is on)
- **Telegram bot:** @newsscrapereduction_bot (access on request)
- **Code:** https://github.com/hkkk27/news-scraper

**Contact:** harshitkumarsingh04@gmail.com · `[phone]`

## Placeholders

- `[college, programme, batch]`
- `[paste your video link]`
- `[phone]`
