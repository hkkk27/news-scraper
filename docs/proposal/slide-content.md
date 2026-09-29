# A/M proposal — slide content (5 slides)

---

## Slide 1 — Understanding the ask
*Clarity & Understanding*

**Title:** One daily read for India's education, skills and governance news

Every morning someone has to scan national papers, regional-language dailies, department
websites, official PDFs and social media to find the few items that matter, then sort them
by state and sector. That takes 40 minutes on a good day, and things still get missed.

This platform does that work before the day starts:

- **Sectors:** school education, higher education, skill development
- **Governance signals around them:** transfer orders for central and state officers;
  election announcements and political developments down to the municipal level; Supreme
  Court and High Court decisions; policy decisions and statements
- **Output:** a daily and weekly report by state and sector, and a live dashboard
- **Room to grow:** healthcare or any other sector, more states, other geographies
- **Running cost:** under ₹500 a month (the working demo runs at ₹0)

---

## Slide 2 — What it delivers every day
*Content Quality · Reliability*

**Title:** From hundreds of headlines to the ones that matter, by 10 AM

**Where it reads from**
- 61 sources in 9 Indian languages: national and regional papers, including vernacular
  dailies in Hindi, Marathi, Tamil, Telugu, Bengali, Gujarati, Malayalam and Punjabi
- Department and regulator websites and their official PDFs: UGC, AICTE, CBSE, NTA, DoPT,
  Supreme Court, DGT, State Election Commission; more can be added any time
- X.com handles of ministries, regulators and election bodies (added during the build)

**What it does with them**
- **Relevance, scored your way:** each item gets a 0–100 score against the criteria you set.
  You tell us what matters and how much; those rules go straight into the scoring model, and
  it keeps learning from the items you mark as useful or not
- **AI as a second opinion:** a free AI service reviews the borderline items alongside the
  news itself, so nothing important slips through and nothing irrelevant gets in
- **No duplicates:** the same event reported by 14 outlets shows up once, with a note of how
  widely it was covered
- **Always current:** refreshed in the evening and early morning, with the report ready
  before 10 AM

**From the demo, 29 September:** 1,488 items read from 61 sources became 521 distinct
events across 28 states, ranked by relevance.

---

## Slide 3 — How items are classified, and how it scales
*Taxonomy · Architecture*

**Title:** Every item tagged the same way, every time

| Tag | What it captures |
|---|---|
| Sector | School education · Higher education · Skill development |
| Category | Policy decision · Court ruling · Transfer or posting · Election · Political development · Statement · Sector news |
| Geography | National · State or UT · District · Municipal |
| Who is involved | Ministries, regulators, courts, election bodies, parties, officers |
| Relevance | Core · Relevant · Peripheral, from the 0–100 score |
| Priority | High · Medium · Low |

**Example:** "Bombay High Court quashes fee hike for unaided schools" is tagged as Court
ruling · Maharashtra · School education · Core · High priority.

**Built to be extended, not rebuilt**
- A new feed, keyword, state or district is a one-line configuration change
- A new sector such as healthcare, or a new country, uses the same structure with its own
  word lists and sources
- 3–5 users on phone and desktop, with the dashboard filterable by state, sector, category,
  language and date

---

## Slide 4 — About me, prior work and delivery
*Brief about the individual · Prior work*

**Harshit Singh**
[College, programme, batch]
Python, data pipelines, web scraping and automation

**Similar work**
- **Education-sector data pipeline:** collected and merged records of schools and NGOs across
  India, the Gulf and South-East Asia from OpenStreetMap, Google Maps and the NGO Darpan
  government portal, with de-duplication and confidence scoring
- **Automated video pipeline:** turns long recordings into short captioned clips, choosing
  the key moments by rule
- **This tracker:** already running on live data (see the next slide)

**Delivery plan**

| Milestone | Dates |
|---|---|
| Backend and training platform, tuned to your criteria | 30 Sep – 4 Oct |
| Frontend and reporting structure | 5 – 12 Oct |
| Two weeks of uninterrupted processing, with a run log | 5 – 19 Oct |
| Handover and 2-hour hands-on training | 16 – 19 Oct |

---

## Slide 5 — A working demo, and your input
*Next steps*

I was already working on this problem, so I built a small working version to show what it
can do. It is running on live news today.

- **Demo video:** [video link]
- **Live dashboard:** https://hkkk27.github.io/news-scraper/

**What I need from you**
- Your scoring criteria: which topics, states and signals matter most, and what to ignore.
  These go directly into the model.
- The sources and X.com handles you already follow
- How you want the report delivered and formatted

For the demo, the daily report is delivered on Telegram because it is free and works well on
a phone. It can go to email, WhatsApp or any channel you prefer.

**Harshit Singh**
+91 95035 60489 · harshitkumarsingh04@gmail.com
