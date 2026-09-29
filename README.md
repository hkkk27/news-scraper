# News & Election Tracker (India)

An intelligence tracker for **school education, higher education and skill development** in
India. Alongside sector news it tracks:

- Officer **transfers and postings**.
- **Elections**, down to municipal and panchayat level.
- **Supreme Court and High Court** rulings.
- **Policy decisions**, **political developments** and **statements**.

Every item is tagged by **state** and **sector**, scored for relevance, grouped into stories,
and delivered as a daily and weekly brief, an analyst digest, Excel, a Telegram bot and a
dashboard.

- **Running cost:** ₹0–150/month (ceiling ₹500).
- **Status:** live since 28 Sep 2026 on GitHub Actions. Evening and early-morning sweeps; the brief PDF reaches Telegram by 10:00 IST. 74 tests.

```
54 news feeds (9 languages) ─┐
8 government notice pages ───┼─► collect ─► organise ─► relevant? ─► degree ─► tag ─► report
Telegram forwards ───────────┘   (RSS,       (dedupe,    (rules)      (rules +   (sector, state,   (brief, digest,
                                  watchers)   stories)                 model, AI)  category, actor)  Excel, bot, dashboard)
```

## Quick start

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Windows (use .venv/bin on macOS/Linux)
.venv/Scripts/python -m tracker run              # collect, tag, score, cluster; builds output/site/index.html
.venv/Scripts/python -m tracker report daily     # output/reports/daily-<date>/ (brief, digest, Excel, Telegram text)
```

See real outputs in **[samples/](samples/README.md)**. To connect Telegram, email and the
online dashboard, see **[docs/SETUP.md](docs/SETUP.md)**.

## Documentation

| Document | For |
|---|---|
| [docs/SETUP.md](docs/SETUP.md) | Connecting Telegram, email, dashboard login, AI filter |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | Operating, monitoring and fixing it |
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | How items are collected, de-duplicated, tagged, scored and reported |
| [docs/EXTENDING.md](docs/EXTENDING.md) | Adding feeds, pages, vocabulary, sectors (e.g. healthcare), states, countries, clients |
| [docs/SOW.md](docs/SOW.md) | Scope of work, deliverables, timeline, task status |
| [docs/decisions/](docs/decisions/) | Why each major choice was made (ADR-0001…0005) |
| [docs/WORKLOG.md](docs/WORKLOG.md) | Dated log of every piece of work |
| [docs/sources.md](docs/sources.md) | Source registry with verification results |
| [docs/proposal/](docs/proposal/README.md) | Proposal: slide content for Claude Design, demo script |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Branch, commit and release conventions |

## Layout

| Path | Contents |
|---|---|
| `tracker/` | The India layer: sources, watcher, tagger, stories, learning, reports, bot, dashboard, CLI |
| `config/` | The client profile: settings, sources, taxonomy, geography, scoring, seed labels, engine overlay |
| `.github/workflows/` | Scheduled pipeline (`tracker.yml`) and tests (`tests.yml`) |
| `scripts/data_branch.sh` | Saves and restores the database on the `data` branch |
| `tests/` | 68 automated tests |
| `samples/` | Real outputs from the live run |

## Credits

The collection, alerting and AI-filter engine planned for `engine/` is
[TrendRadar](https://github.com/sansan0/TrendRadar) (GPL-3.0), per ADR-0005; its import is
pending. The India layer uses feedparser, trafilatura, scikit-learn, pypdf, openpyxl, Jinja2
and httpx.
