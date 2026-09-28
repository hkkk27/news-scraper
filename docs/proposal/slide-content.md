# Slide content for the A/M proposal (for Claude Design)

**Deck:** "News & Election Tracker — Approach & Methodology". 5 slides, due 29 Sep 2026, 23:59.

**Audience:** Siddharth Sachdev (AIIB social-infrastructure work), reading on screen.

**Tone:** confident, specific, evidence-led. Every claim below is backed by the working system
in this repository.

**The one message:** *It already works: ₹0 to run, live on real Indian news in 9 languages,
learning from your taps on Telegram.*

## Design direction

- **Palette** (matches the reports and dashboard, so screenshots sit naturally):
  - Ink `#1B2433`, paper `#F6F4EE`, card `#FFFDF8`.
  - Accent (burnt orange) `#B34A1F`; secondary (teal) `#17565D`.
  - Charts: blue `#2a78d6`, orange `#eb6834`.
- **Type:** a serif for headings (Source Serif 4 or Georgia) and a clean sans for body (IBM Plex Sans).
- **Layout:** one idea per slide, a big number or a real screenshot on each, no bullet walls.
- **Screenshots to take** (open the files in `samples/`):
  1. `samples/daily-2026-09-29/executive-brief.html`: top of page (stat tiles + Top developments).
  2. `samples/dashboard/index.html`: the Feed tab on desktop, and the same page at phone width (browser dev tools → 375 px).
  3. `samples/dashboard/index.html` → **Insights** tab (charts).
  4. `samples/daily-2026-09-29/stories.xlsx`: the Summary sheet (state × sector pivot).
  5. Optional, once the bot token is set: a Telegram card with 👍/👎 buttons, from your phone.

## Slide 1 — Understanding: one feed for everything that moves the sector

**Headline:** Every signal that matters for Indian education: collected, ranked and reported by
state and sector.

**Three big numbers:**

| Number | Label |
|---|---|
| ₹0–150 | Running cost per month (ceiling ₹500) |
| 9 | Languages read, including Hindi, Tamil, Bengali and Marathi |
| 7 | Streams: sector news, transfers, elections (to municipal level), politics, courts, policy, statements |

**Sub-line:** School education · Higher education · Skill development, with healthcare or any
new sector added by configuration.

**Speaker notes:**
- The brief asks for more than a news feed. It wants the governance signals around the sector: who was transferred, which elections are coming, what courts ruled, which policies changed, all tagged by state and sector, with daily and weekly reporting.
- The system is built, running and costs nothing to operate.

## Slide 2 — Approach: seven stages from raw feed to report

**Visual:** a horizontal flow of seven numbered steps.

| # | Stage | What happens |
|---|---|---|
| 1 | **Collect** | 54 news feeds, 8 government notice pages, Telegram forwards (X.com optional) |
| 2 | **Extract** | Clean text, language, date; PDF text |
| 3 | **Organise** | Remove duplicates; group outlets' reports into one story |
| 4 | **Relevant?** | Multilingual rules drop noise (sports, SEO pages, foreign news) |
| 5 | **Degree** | Score 0–100 from rules + a model that learns from you |
| 6 | **Tag** | Sector · state/UT · category · actor · priority |
| 7 | **Report** | Daily / weekly brief, analyst digest, Excel, dashboard, Telegram |

**Proof strip:** "Live on 28–29 Sep: 1,996 items from 53 feeds → 469 relevant stories in 24 hours."

**Speaker notes:**
- Sources run cheapest and most reliable first: publisher RSS, then Google News search in 9 language editions (vernacular coverage without a scraper per paper), then watchers on UGC, AICTE, CBSE, NTA, DoPT, the Supreme Court, DGT and the Maharashtra SEC pages.
- Anything the client forwards to the Telegram bot joins the feed.

## Slide 3 — Taxonomy and learning: explainable scores that improve with every tap

**Visual (left):** the tagging rubric as a compact table.

| Tag | Values |
|---|---|
| Sector | School · Higher education · Skills (+ healthcare later) |
| Category | Policy · Court · Transfer · Election · Political · Statement · News |
| Geography | National → 36 states/UTs → district → municipal |
| Actor | UGC, AICTE, CBSE, NTA…, 25 High Courts (each mapped to its state), ECI/SECs, parties |
| Relevance | Core ≥ 80 · Relevant 60–79 · Peripheral 40–59 · Not relevant |
| Priority | High · Medium · Low (written rubric) |

**Visual (right):** three stacked layers.

1. **Rules (free):** keywords and place names in 9 languages. Every point is shown as "why this score".
2. **Local model (free):** retrained nightly from 👍/👎 on Telegram and forwarded items.
3. **AI filter (optional, free tier):** only for items the first two are unsure about.

**Example callout:** "Bombay HC quashes fee hike order for unaided schools" → Court ruling ·
Maharashtra (from the court's seat) · School education · Core.

**Speaker notes:**
- Nothing is a black box: the client sees why each item scored what it did.
- Tapping 👎 on a few items retrains the model the same night.
- Publisher names like "Punjab Kesari" are never mistaken for states, and "New Delhi" datelines are not read as Delhi news.

## Slide 4 — Architecture, reliability and cost: built on free tiers, measured every run

**Visual (left):** architecture stack.

- **GitHub Actions** runs every 2 h.
- **India layer** (runs today) plus the **TrendRadar engine** (open source, 62k★; integration is the next step).
- **SQLite database**, saved in the repository.
- **Outputs:** Telegram bot · email brief · Excel · dashboard (Cloudflare Pages + email login).

**Visual (middle):** reliability measures.

- De-duplication in 3 levels: canonical link → story clusters across outlets → across languages (with the engine's AI translation, planned).
- Run log on the dashboard; alert when a source goes quiet.
- **Target for the 14-day run:** ≥ 95% of runs succeed, no gap over 6 h.
- 68 automated tests run on every change.

**Visual (right):** cost table.

| Item | ₹/month |
|---|---|
| Pipeline, storage, bot, dashboard, model | 0 |
| AI filter (free tier) | 0 |
| X.com collection (optional) | 0–150 |
| **Total** | **0–150** |

**Speaker notes:**
- The project is built on proven open source rather than from scratch: TrendRadar's collection, alerts, AI filter and translation, plus standard Python libraries.
- Our India layer is what's running today: state/sector tagging, government-page watching, the Telegram training loop and the reports. It reads the engine's output once the engine is switched on.
- Everything is portable to a small server if free tiers ever change.

## Slide 5 — Who is delivering, and how

**Left: team and prior work.**

- **Harshit Singh** · `[College, programme and batch]` · Python, data pipelines, scraping and automation.
- `[Second team member, if any]`
- **Prior work:**
  - An education-sector data pipeline (schools and NGOs across India, the Gulf and South-East Asia, from OpenStreetMap, Google Maps and the NGO Darpan portal: merged, de-duplicated, confidence-scored).
  - A video clipping pipeline.
  - An explainer-video generator.
- **This project is already running:** repository, scope of work, 5 decision records, 68 tests, live data.

**Right: delivery plan.**

| Dates | Deliverable |
|---|---|
| 29 Sep | Proposal; working prototype on live data ✅ |
| 30 Sep – 4 Oct | D1 Backend & training: tokens, Telegram bot live, engine AI filter on |
| 5 – 12 Oct | D2 Frontend & reporting: dashboard online, reports tuned with feedback |
| 5 – 19 Oct | D3 14 days of uninterrupted processing, with a public run log |
| 16 – 19 Oct | D4 Handover: runbook, methodology, 2-hour hands-on session |

**Footer:** Harshit Singh · harshitkumarsingh04@gmail.com · `[phone]`

**Speaker notes:**
- Most of D1 and D2 already exist.
- The remaining weeks go to connecting the client's accounts (Telegram, email, dashboard login), tuning relevance with his feedback, and the two-week reliability run.

## Placeholders to fill

- `[College, programme and batch]`
- `[Second team member, if any]` (delete the line if working solo)
- `[phone]`

## If a sixth slide is allowed (appendix)

**"What a morning looks like":** a phone mockup of the Telegram brief, with the executive-brief
screenshot beside it. Caption: "07:30 IST: the brief arrives; tap 👍/👎 to train; forward
anything to add it."
