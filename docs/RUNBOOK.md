# Runbook — operate, monitor, fix

## What runs, and when

All times are IST. Everything runs from `.github/workflows/tracker.yml`.

| When | Job | What it does |
|---|---|---|
| Every 2 hours (at :40 past odd hours IST) | `run` | Watch 8 government pages → read Telegram → collect 54 feeds → tag, score, cluster → rebuild dashboard |
| 07:30 daily | `daily` | `run`, then the daily report to email and Telegram |
| 08:00 Monday | `weekly` | Weekly report; the analyst email carries the Excel |
| 03:10 daily | `train` | Retrain the relevance model on the day's feedback, re-score |

Each job restores the database from the `data` branch at the start and saves it back at the
end. Reports, the dashboard and a database copy are kept as artifacts for 14 days.

## Daily check (1 minute)

1. **Dashboard → Run log.** Runs should be green, and "longest gap" should stay under 6 hours. The two-week acceptance target is ≥ 95% success and no gap over 6 h.
2. **Report footer.** It lists any sources that errored in the last run.

## Where to look when something is wrong

- **GitHub → Actions → tracker:** every run's log. Red means that run failed.
- **`python -m tracker sources check`:** which feeds are failing (`!!`) or quiet (`~~`).
- **Dashboard → Insights → "Who decided the score":** the mix of rules, model, AI and human decisions.

## Common problems

| Symptom | Likely cause | Fix |
|---|---|---|
| A feed shows `!!` for days | Publisher moved or blocked the feed | Find the new URL (see `docs/sources.md`) or set `enabled: false` in `config/sources/feeds.yaml` |
| An official page stops producing items | Site redesign or JavaScript-only page | Run `python -m tracker watch --only <id>`; adjust `include` in `watch.yaml`, or rely on PIB/Google News |
| A burst of old notices from one page | The site renamed all its links | Temporary: `max_new` caps it at 15 per run. To reset the baseline, delete that page's entry in `data/state/watch_seen.json` |
| Bot silent | Token or allowlist wrong | Check the secrets; `/start` from an unknown chat returns its ID; run `python -m tracker bot poll` locally |
| Bot replies late | Expected on GitHub | Updates are read every 2 hours. For instant replies, run `python -m tracker bot listen` on an always-on machine |
| No email | App password or recipients missing | See `docs/SETUP.md` §3. The run log shows "email not configured" |
| Irrelevant items in Core | Rules too generous for a pattern | Tap 👎 on them (the model learns overnight); for a whole pattern add a term to `negative` (sectors.yaml) or `noise_terms` (scoring.yaml) |
| Relevant items missed | Vocabulary gap (often a regional language) | Tap 👍 or forward the item; add the missing term to `config/taxonomy/sectors.yaml` |
| Workflow disabled | GitHub disables schedules after 60 days without repository activity | Actions → tracker → Enable workflow (any commit also keeps it alive) |
| Database lost or corrupted | Rare | Download `data/tracker.db` from a recent run's artifact, then save it back: `bash scripts/data_branch.sh save` with that file in `data/` |

## Manual operations

- **Run now:** Actions → tracker → Run workflow → task `run`, `daily`, `weekly` or `train`.
- **Pause everything:** Actions → tracker → ⋯ → Disable workflow.
- **Retrain after bulk feedback:** Run workflow → `train`.
- **Change schedule times:** edit the `cron` lines in `tracker.yml` (they are in UTC).

## Costs to watch

| Item | Limit | Our use |
|---|---|---|
| GitHub Actions (private repository) | 2,000 min/month free | About 1,000 |
| Cloudflare Pages / Access | Free for up to 50 users | Within limits |
| Gemini free tier (once the engine AI filter is on) | Roughly 500–1,000 requests/day | About 15 a day |
