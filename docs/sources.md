# Source Registry

Sources are verified before they go into `config/sources/`. Re-run the check whenever a
source is added or goes silent. (In M1 the check becomes a `tracker sources check`
command.)

**Verification of 27 September 2026:** HTTP status and number of items returned, fetched
with a desktop browser User-Agent.

## Working

| ID | Source | Type | Language | URL | HTTP | Items |
|---|---|---|---|---|---|---|
| `thehindu_edu` | The Hindu — Education | national_media | en | `https://www.thehindu.com/education/feeder/default.rss` | 200 | 60 |
| `ie_edu` | Indian Express — Education | national_media | en | `https://indianexpress.com/section/education/feed/` | 200 | 200 |
| `theprint_edu` | ThePrint — Education | national_media | en | `https://theprint.in/category/india/education/feed/` | 200 | 20 |
| `edexlive` | EdexLive (New Indian Express) | national_media | en | `https://www.edexlive.com/feed` | 200 | 15 |
| `livelaw` | LiveLaw | legal_media | en | `https://www.livelaw.in/google_feeds.xml` | 200 | 60 |
| `pib_en` | Press Information Bureau (English) | official | en | `https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3` | 200 | 20 |
| `bhaskar` | Dainik Bhaskar | regional_media | hi | `https://www.bhaskar.com/rss-v1--category-1061.xml` | 200 | 54 |
| `amarujala_edu` | Amar Ujala — Education | regional_media | hi | `https://www.amarujala.com/rss/education.xml` | 200 | 40 |
| `gn_en` | Google News search: `"higher education"`, last day | aggregator | en | `news.google.com/rss/search?q=…&hl=en-IN&gl=IN&ceid=IN:en` | 200 | 69 |
| `gn_hi` | Google News search: शिक्षा, last day | aggregator | hi | `…&hl=hi&gl=IN&ceid=IN:hi` | 200 | 100 |
| `gn_mr` | Google News search: शिक्षण, last day | aggregator | mr | `…&hl=mr&gl=IN&ceid=IN:mr` | 200 | 46 |
| `gn_ta` | Google News search: கல்வி, last day | aggregator | ta | `…&hl=ta&gl=IN&ceid=IN:ta` | 200 | 56 |
| `gn_transfer` | Google News search: `IAS officers transferred`, last day | aggregator | en | `…q=IAS+officers+transferred+when:1d…` | 200 | 9 |
| `gn_sec` | Google News search: `"state election commission" municipal`, last 7 days | aggregator | en | `…q="state election commission"+municipal+when:7d…` | 200 | 16 |

Google News search RSS is the backbone of vernacular and stream coverage. Each query pack
(sector × stream × language) becomes one feed. Links are Google redirect URLs, which the
normalizer decodes to the publisher URL before de-duplication.

## Not working, or needs a different method

| Source | Result | Next step |
|---|---|---|
| Times of India — Education `rssfeeds/913168846.cms` | 200, 1 item | Find the current section feed ID, or cover through Google News |
| Hindustan Times — Education `feeds/rss/education/rssfeed.xml` | 200, 0 items | Check the new feed path |
| NDTV Education (Feedburner) | 404 | Retired; use Google News |
| Scroll `scroll.in/feed` | 200, 0 items | Non-standard format; recheck |
| Bar & Bench `barandbench.com/feed` | 200, 1 item | Find the correct feed path |
| Dainik Jagran — Education | 404 | Find the current path |
| Lokmat | 403 | Blocks bots; cover through Google News (`mr`) |

## To add and verify in M1-05 (official pages and PDFs)

| Body | Page to watch | Stream |
|---|---|---|
| Ministry of Education | education.gov.in (what's new, notifications) | policy |
| Ministry of Skill Development and Entrepreneurship (MSDE) | msde.gov.in (notifications) | policy |
| University Grants Commission (UGC) | ugc.gov.in (public notices) | policy |
| All India Council for Technical Education (AICTE) | aicte.gov.in (circulars) | policy |
| National Council of Educational Research and Training (NCERT) and National Council for Teacher Education (NCTE) | notices | policy |
| Central Board of Secondary Education (CBSE) | cbse.gov.in (circulars) | policy |
| National Council for Vocational Education and Training (NCVET) and National Skill Development Corporation (NSDC) | notices | policy |
| Department of Personnel and Training (DoPT) | dopt.gov.in (orders; Appointments Committee of Cabinet appointments) | transfer |
| Election Commission of India | eci.gov.in (press notes) | election |
| State Election Commissions (36) | press notes and notifications | election |
| State General Administration Departments (GAD) | transfer orders | transfer |
| State school and higher education departments | circulars and orders | policy |
| Supreme Court | sci.gov.in (judgments) | court |

## X.com handles (to confirm with the client)

These are candidate groups; the handle list is still to be confirmed:

- Ministry of Education, MSDE and PIB.
- Education ministers (central and states).
- UGC, AICTE, NCERT, CBSE and NTA.
- Chief Minister offices.
- State Election Commissions and ECI.
