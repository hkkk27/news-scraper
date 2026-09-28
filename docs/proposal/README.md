# Approach & Methodology Proposal (M0-03)

- **Due:** 29 September 2026, 23:59, by email to the client.
- **Format asked for:** a slide deck of 3–5 slides, a brief about the individual(s), and details of prior work of a similar nature.
- **Deck:** [News & Election Tracker — Approach & Methodology](https://claude.ai/artifact/KHNo1cwwFzs2QZPRDUHYnA). It is private; download it as PPTX or PDF from the page to attach to the email.

## Slide outline

Each slide is mapped to the brief's evaluation areas.

| # | Slide | Covers | Evaluation area |
|---|---|---|---|
| 1 | **Cover:** "Every signal that matters for Indian education — collected, ranked and reported by state and sector" | Understanding of the brief; 7 streams, ₹260–410/month estimate, live by 5 Oct | Clarity & understanding |
| 2 | **Seven stages from raw feed to report** | Collect → Extract → Organise → Relevant? → Degree → Tag → Report; five source types; 14 feeds verified live | Content quality |
| 3 | **Tagged, scored, and learning from feedback** | Tagging rubric (8 dimensions); relevance bands; rules → local model → LLM cascade; phone-based training and Telegram feed-in | Taxonomy |
| 4 | **Built on free tiers, measured for reliability** | Architecture stack; 3-level de-duplication; run log and alerts; 95% / 6-hour targets; monthly cost table | Architecture, reliability |
| 5 | **Who is delivering, and how** | Team, prior work, delivery plan by deliverable | Team, prior work |

Every slide has speaker notes.

## Placeholders to fill before sending

| Where | Placeholder |
|---|---|
| Slide 1 footer line | `[College, batch]` |
| Slide 5, team | `[College, programme and batch]` |
| Slide 5, team | `[Second team member, if any: name and one line]` (delete the line if working solo) |
| Slide 5, footer | `[phone]` |

## Prior work cited (slide 5)

| Work | Relevance to this project |
|---|---|
| **Education-sector data pipeline:** schools and NGOs across India, the Gulf and South-East Asia | Same shape of problem: collects from several sources (OpenStreetMap, Google Maps through Apify, and the NGO Darpan government portal), then merges, de-duplicates and confidence-scores |
| **Automated clipping pipeline:** long video to captioned short clips | End-to-end automated pipeline, with rule-based selection of what matters |
| **Automated explainer-video generator** | Scripted, repeatable content automation |
| **This project** | Scope of work, three decision records and 14 verified sources already in this repository |

## Submission checklist

- [ ] Fill the placeholders above.
- [ ] Download the deck as PPTX and as PDF.
- [ ] Write a short email: one-line summary, the deck attached, and a link to the repository if it is to be shared (it is currently private).
- [ ] Send before 29 Sep, 23:59 (the team sends this; it is not automated).
