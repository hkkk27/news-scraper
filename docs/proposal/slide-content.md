# Deck content for Claude Design (4 slides)

**Style:** black, blue and white (`#0B1220` · `#1D4ED8` · white), clean sans-serif, one idea
per slide, real screenshots.

**Tone:** "I was already building this, so I made a small working demo. I'd love your
feedback to shape it for you."

---

## Slide 1 — Your 40-minute morning news scan, done by 10 AM

**Headline:** From 40 minutes of searching to a 2-minute brief on your phone.

**The problem:** tracking school education, higher education and skill development across
India means checking dozens of sites, papers in regional languages, government notices,
transfers, elections and court rulings, every morning.

**What the tracker does:**
- Reads **61 sources in 9 Indian languages**: national and regional papers, Google News, and government notice pages (UGC, AICTE, CBSE, NTA, DoPT, Supreme Court, DGT, State Election Commission).
- Picks what matters, tags it by **state, sector and category**, and removes duplicates.
- Sends a **formatted PDF brief to Telegram before 10 AM**, and keeps a live dashboard.

**Visual:** a phone showing the Telegram PDF brief, next to the dashboard.

## Slide 2 — How it works

**Visual:** a flow of 7 steps: Collect → Clean → Remove duplicates → Is it relevant? → How relevant (0–100) → Tag → Brief.

- **Collect:** RSS feeds, Google News in 9 languages, government notice pages, and anything you forward to the bot.
- **Score:**
  1. Keyword rules in 9 languages, with every point explained ("why this score").
  2. A model that **learns from your 👍 / 👎** in Telegram.
  3. Free AI for items the first two are unsure about.
- **Tag:** sector (school / higher / skills) · category (policy, court, transfer, election, political, statement, news) · state/UT · priority.
- **One card per event:** 14 outlets reporting the same Supreme Court order appear as one item marked "reported by 14 outlets".
- **Deliver:** a Telegram PDF brief (daily at about 9:45 AM; weekly with Excel), a live dashboard, and filters by state, sector and category.
- **Cost:** ₹0 per month (GitHub Actions, Telegram and free AI models).

**Proof line:** On 29 Sep it scanned 1,488 items from 61 sources and found 671 relevant reports on 521 distinct events across 28 states. The brief leads with the top 8.

## Slide 3 — About me, and next steps

**Harshit Singh:** `[college, programme, batch]` · Python, data pipelines, automation.

**Prior work:**
- An education-sector data pipeline for schools and NGOs across India, the Gulf and South-East Asia (multi-source, de-duplicated, scored).
- A video clipping pipeline.
- An explainer-video generator.

**How I built this:** on open source (the TrendRadar engine, 62k★) plus an India-specific layer.

**Next steps:**
- I was already working on this, so this is a small demo of what it does.
- I'd like your feedback on sources, topics, states and the brief format.
- It is ready to tune to your preferences: tap 👍 / 👎 and it adapts.

## Slide 4 — See it live

- **Demo video:** `[your video link]`
- **Live dashboard:** https://hkkk27.github.io/news-scraper/
- **Telegram bot:** @newsscrapereduction_bot (access on request)

**Contact:** harshitkumarsingh04@gmail.com · `[phone]`
