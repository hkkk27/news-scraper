# Methodology

How the tracker decides what to show, in the order an item travels through it. Every number
below lives in a config file and can be tuned without code changes.

## 1. Collect: cheapest and most reliable first

| Rung | Source | Details |
|---|---|---|
| 1 | Publisher RSS | The Hindu, Indian Express, ThePrint, EdexLive (education sections), LiveLaw, PIB, Dainik Bhaskar, Amar Ujala |
| 2 | Google News search RSS | 7 query packs (school, higher education, skills, transfers, elections, courts, policy) × 9 language editions (en, hi, mr, ta, te, bn, gu, ml, pa). This gives vernacular coverage without a scraper per newspaper. Bengali queries require West Bengal context, because that edition mixes in Bangladeshi publishers |
| 3 | Government page watchers | UGC, AICTE, CBSE, NTA, DoPT, Supreme Court, DGT, Maharashtra SEC. Each page's links are compared with those already seen; new ones become items. The first visit is only a baseline; at most 15 new per run. PDF first-page text is read when present (scanned PDFs are labelled) |
| 4 | Telegram intake | Anything a user forwards (link, PDF, text) becomes an item and a positive training label |
| — | X.com | Planned (M1-06) |

Config: `config/sources/`. Verification history: `docs/sources.md`.

## 2. Organise: de-duplication in three levels

1. **Same link:** URLs are canonicalised (tracking parameters, AMP/mobile variants and fragments removed), so one article is stored once.
2. **Same event, different outlets.** Titles are normalised ("SC" → "supreme court", "Class VI" → "class 6", "3rd" → "3") and compared with TF-IDF cosine similarity (≥ 0.4). Grouping is limited to one language and 72 hours, and to items whose states agree, so "Tamil Nadu NEET counselling" and "Odisha NEET counselling" stay apart. The group becomes a **story**; the number of outlets reporting it is shown as corroboration.
3. **Same event, different languages:** planned, using the engine's AI translation.

## 3. Tag: the rubric

| Tag | How it is decided |
|---|---|
| **Sector** | Evidence from sector vocabularies in 9 languages (`config/taxonomy/sectors.yaml`): a strong term in the title counts most, a normal term in the summary least |
| **Category** | court > transfer > election > policy > political > statement > news (first match by precedence; the runner-up is kept as secondary). Transfers must name a cadre or senior post (IAS, secretary, collector, VC…); election announcements are marked separately from coverage |
| **State / UT** | State names in their own scripts; High Court seats (Bombay HC → Maharashtra); cities; the source's own state (e.g. Maharashtra SEC). "New Delhi" datelines and publisher names ("Punjab Kesari") are ignored |
| **Level** | Municipal / district / state / national, from terms like "municipal corporation", "zilla parishad", "the Centre" |
| **Actor** | Ministries, regulators (UGC, AICTE, CBSE, NTA…), courts, election bodies, parties (`actors.yaml`) |
| **Language** | From the script (Devanagari from a Marathi source → Marathi) |

## 4. Relevance: is it relevant, and how much?

The score runs from 0 to 100 and is built in three layers:

1. **Rules (L1).** `config/taxonomy/scoring.yaml`:
   - Best sector evidence (up to 55).
   - Plus a stream base: transfers 55, election announcements 58, election coverage 40, politics 35, court 15, policy 10.
   - Plus a sector bonus when both apply: court or transfer +30, policy +25, …
   - Plus +10 when a regulator, court or election body is named, plus the source's prior (education sections +20, official +10–15).
   - Minus penalties: off-topic −45 (−15 if education is also mentioned); round-up/SEO pages −45; foreign news with no Indian link −40; muted source −30.
   - Every step is written into the item's reasons ("Why this score" on the dashboard and in the digest).
2. **Model (L2).** A TF-IDF (character + word n-grams) logistic regression trained on the client's labels (👍 / ⭐ / 👎 on Telegram, forwarded items) plus 60 seed labels at half weight:
   - `final = rule + w × (100 × P(relevant) − 50)`. This is neutral when the model is unsure.
   - The weight `w` grows with the number of labels, up to 0.7.
   - It retrains nightly and reports cross-validated accuracy.
3. **AI (L3, optional).** The engine's AI filter scores titles against the plain-English brief in `config/engine/ai_interests.txt`. It only settles items in the uncertain band (40–65), or rescues a miss it is very sure about (≥ 0.85).

A **human label always wins**: 👍 → 95, 👎 → 10.

**Bands:** Core ≥ 80 · Relevant 60–79 · Peripheral 40–59 · Not relevant < 40. Not-relevant items are kept 30 days, for training, then purged.

**Priority:**
- **High:** score ≥ 80 and a policy / court / transfer / election item tied to a sector (transfers always qualify).
- **Medium:** score ≥ 60.
- **Low:** everything else.

## 5. Report

| Output | Contents |
|---|---|
| **Executive brief** | Top developments, ranked by priority, then score, then outlets. Kept varied: at most 3 per category, and other outlets' takes on the same event are skipped. Plus transfers, elections and court rulings, and a state table |
| **Analyst digest** | Every Core/Relevant story, sector → state, with reasons |
| **Excel** | State × sector pivot, all stories, a sheet per tracker |
| **Telegram** | The brief text plus item cards with training buttons |
| **Dashboard** | Filters, trackers, insights, run log |

## 6. Reliability

- **Steps are isolated.** A failing source or service never stops a run.
- **Every run is logged** (`runs` table → dashboard Run log). Report footers name failing sources.
- **One writer at a time** (workflow concurrency), so the database is never written twice at once.
- **Backups:** the database is saved to the `data` branch every run, and a copy is kept in 14 days of artifacts.
- **Tests:** 68 automated tests run on every push.

## Known limitations

- **JavaScript-only government sites** (Ministry of Education, MSDE, ECI) are covered indirectly through PIB and Google News.
- **Scanned PDFs** have no text layer. Tagging uses their titles; OCR (OCRmyPDF with Indian-language packs) is a possible addition.
- **Cross-language grouping and English translations** need the engine's AI step.
- **Telegram feedback is processed every 2 hours** on GitHub. For instant replies, run `bot listen` on an always-on machine.
