# Sample outputs (real data, 28–29 September 2026)

Everything here was produced by the pipeline from live sources: 54 feeds plus 8 watched
official pages, in 9 languages. Nothing was edited by hand. Open the `.html` files in any
browser.

| File | What it is | Who it's for |
|---|---|---|
| [daily-2026-09-29/executive-brief.html](daily-2026-09-29/executive-brief.html) | One-page brief: top developments, transfers, elections, court rulings, states | Leadership (the "boss") |
| [daily-2026-09-29/analyst-digest.html](daily-2026-09-29/analyst-digest.html) | Every Core/Relevant story, sector → state, with "why" reasons and outlet counts | The client / analysts |
| [daily-2026-09-29/stories.xlsx](daily-2026-09-29/stories.xlsx) | Excel: state × sector pivot, all stories, transfer / election / court / policy sheets | Analysts |
| [daily-2026-09-29/telegram-brief.txt](daily-2026-09-29/telegram-brief.txt) | The morning message the Telegram bot posts (HTML formatting) before the item cards | Everyone, on the phone |
| [weekly-2026-09-29/](weekly-2026-09-29/) | The weekly versions. Collection began on 28 Sep, so this week matches the daily. | Leadership, analysts |
| [dashboard/index.html](dashboard/index.html) | The mobile-first dashboard with data embedded: filters, trackers, insights, run log | Everyone |

## Numbers behind these samples

| Measure | Value |
|---|---|
| Items collected and tagged | 1,996 from 53 feeds |
| Relevant items (Core + Relevant) | 655, grouped into 469 stories |
| Stories reported by 3+ outlets | 24 |
| Languages | English 393 · Hindi 153 · Tamil 35 · Bengali 20 · Malayalam 17 · Marathi 14 · Gujarati 11 · Telugu 10 · Punjabi 2 |
| States / UTs covered | 27 (top: Delhi, Uttar Pradesh, Maharashtra, Haryana, Tamil Nadu) |
| Categories | Sector news 378 · Court 142 · Election 56 · Policy 35 · Transfer 30 · Statement 11 · Political 3 |
| Pipeline runs | 8 of 8 succeeded |

## A Telegram item card looks like this

```
Mandeep Bhandari Appointed New CBSE Chairperson
boldnewsonline.com · 3 outlets · National · School education · Transfer / posting · core 100
Open
[ 👍 ] [ 👎 ] [ ⭐ ] [ 🔇 ]
```

Each tap is stored as a training label; 🔇 also mutes that source. Forwarding any link, PDF or
text to the bot adds it to the tracker.
