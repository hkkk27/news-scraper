# Meeting cheat sheet (10-minute read)

## 1. One line

"It reads the news and government notices for you every morning, keeps only what matters for
education and skills, sorts it by state and sector, and sends a short report."

## 2. Their problem

Siddharth works on social-infrastructure projects (AIIB). Every morning someone spends about
40 minutes scanning papers, regional-language dailies, department websites and PDFs to find
the few items that matter, then sorts them by state and sector. It is slow, and things get
missed.

## 3. What they asked for (the brief)

- **Track:** school education, higher education and skill development.
- **Also track:**
  - Officer transfer orders.
  - Elections and political developments, down to municipal level.
  - Supreme Court and High Court decisions.
  - Policy decisions and statements.
- **Sources:** department websites, official PDFs, vernacular papers, X.com handles.
- **A system that learns** what is relevant, trainable from a phone, for 3–5 users.
- **Reports:** daily and weekly, by state and sector, plus a dashboard.
- **Extensible** later to healthcare, more states, other countries.
- **Cost:** under ₹500 a month. Fee ₹15,000. Completion 19 October.
- **Four paid milestones:**
  1. Backend and training.
  2. Frontend and reporting.
  3. Two weeks of uninterrupted running.
  4. Handover with a 2-hour training.

## 4. What is already built and running

- **Live since 28 Sep.** 23 of 23 automatic runs have succeeded since the 29 Sep fix. The first 4 runs failed on a login bug, now fixed.
- **Sources:** 61, in 9 languages. 53 news feeds plus 8 government notice pages: UGC, AICTE, CBSE, NTA, DoPT, Supreme Court, DGT, Maharashtra State Election Commission.
- **Dashboard:** https://hkkk27.github.io/news-scraper/ currently holds about 3,200 stories, filterable by state, sector, category, language and date.
- **Daily report:** a PDF on Telegram, a weekly Excel, and thumbs-up/down buttons to train it.
- **Running cost:** ₹0.

## 5. How it works

Seven steps. Say it in this order.

1. **Collect.** A program pulls headlines from news feeds (RSS), from Google News searches in 9 languages, and from government pages. For government pages it compares today's links with yesterday's and keeps the new ones.
2. **Clean.** Standardise the text, detect the language, and read the first page of PDFs.
3. **Remove duplicates.** The same link is stored once. The same event from many outlets is grouped into one item ("reported by 14 outlets").
4. **Is it relevant?** Word lists in 9 languages for the sectors, places, courts and so on. Sports, ads and foreign news are dropped.
5. **How relevant (0–100).** Three layers, cheapest first:
   - **Rules:** points for matching words; every point is shown as "why this score".
   - **A small learning model:** learns from thumbs-up/down.
   - **Free AI:** only for items the first two are unsure about.
6. **Tag.** Sector, category (policy, court, transfer, election, political, statement, news), state, priority.
7. **Report.** PDF brief, dashboard, weekly Excel.

## 6. Tech stack

Each line is a plain answer to "what are you using?".

| Part | What | Why |
|---|---|---|
| Language | Python | Standard for data and scraping |
| Scheduler and server | GitHub Actions (runs the program on a timer) | Free, no server to maintain |
| Database | SQLite (a single file), saved in the GitHub repository | Free, simple, portable |
| Collection | RSS feeds, Google News search feeds, a page watcher for government sites | Reliable, legal, no paid APIs |
| Learning model | scikit-learn (TF-IDF + logistic regression) | Tiny, runs free, learns from few examples |
| AI | Free models through OpenRouter | Zero cost; only for borderline items |
| Report | HTML turned into PDF by headless Chrome; Excel via openpyxl | Proper formatting, Indian scripts render correctly |
| Delivery | Telegram bot (demo); email or WhatsApp possible | Free, works on a phone |
| Dashboard | A static web page on GitHub Pages | Free hosting, fast on mobile |
| Quality | 74 automated tests; every decision documented | Reliability, easy handover |

Also imported but not yet switched on: TrendRadar, an open-source news-monitoring engine
(62k stars). The plan is to use it for collection, alerts and translation.

## 7. How I used AI

Be straightforward about this.

- **Inside the product:** AI is the third scoring layer only. It reads borderline headlines against the client's brief and gives a score and a reason. Rules and the learning model decide most items, which keeps it free and explainable.
- **In building it:** "I used an AI coding assistant to write the code quickly. I defined the requirements, the scoring logic, the sources and the checks, and reviewed what it produced. There are 74 automated tests and written decision records, so it is maintainable."

## 8. How we proceed

- **Week 1 (now):** take their scoring criteria (which topics, states and signals matter; what to ignore) and their source list and X handles. Put these into the config and the AI brief.
- **Next:** add X.com handles, agree the report format and delivery channel, and put a login in front of the dashboard for their 3–5 users.
- **5–19 Oct:** two-week uninterrupted run, with the run log as evidence.
- **16–19 Oct:** handover. Runbook, methodology document, and the 2-hour training.

**What I need from them:** scoring criteria, priority states, sources and handles, report format,
and who the users are.

## 9. Honest gaps

Say these yourself; it builds trust.

- **X.com handles:** not built yet (planned; X is expensive to access officially).
- **Some government sites** (Ministry of Education, MSDE, ECI) load by JavaScript, so they are covered through PIB and news reports, not directly.
- **Scanned PDFs:** tagged by their titles; text extraction (OCR) is a later addition.
- **Report timing:** GitHub starts scheduled jobs late, so until 4 Oct the brief arrived in the afternoon. Fixed on 4 Oct: the morning job is now attempted several times and sends once, at the first run after 8:45 AM. Tomorrow's delivery time will confirm it.
- **Learning:** nobody has rated items yet (0 ratings), so the model is running on 60 starter examples. It improves as they rate.
- **Dashboard:** currently a public page. A login for 3–5 users is to be added.

## 10. Likely questions

| Question | Answer |
|---|---|
| How accurate is it? | Clear items are handled by rules. For borderline ones the free AI reviews, and your ratings teach it. Every score shows its reason, so mistakes are easy to spot and correct. |
| How will it use my criteria? | Your criteria become word lists, weights and a plain-English brief for the AI. Changing them is a config edit, not new code. |
| How do you add healthcare or a new state? | Add a word list and sources for it in the config. Same engine. |
| What does it cost to run? | ₹0 now. X.com collection could add up to about ₹150 a month. |
| Where is the data? | In the GitHub repository: news headlines and links only, no personal data. It can move to your account at handover. |
| What if a source breaks? | Each source is checked every run; failures show in the run log and the report footer. One broken source never stops the rest. |
| Why Telegram? | Free and good on phones, for the demo. It can be email or WhatsApp. |
| Who owns it? | You do, after handover: code, data and accounts. |
