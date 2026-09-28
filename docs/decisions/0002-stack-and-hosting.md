# ADR-0002: Stack and hosting within ₹500/month

- **Status:** Proposed
- **Date:** 27 September 2026
- **Task:** M0-02

## Context

The platform must cost less than ₹500 a month (about US$6) to operate, serve 3–5
concurrent users with login, and run scheduled collection several times a day. Traffic is
tiny, but collection must be reliable for the 14-day run (D3).

## Options considered

| Option | Monthly cost | Pros | Cons |
|---|---|---|---|
| **A. Serverless free tiers:** GitHub Actions + Supabase + Cloudflare Pages | ₹0 infrastructure | No servers to maintain; auth, row-level security and Postgres built in; easy to hand over | Free-tier limits: Actions minutes, 500 MB database, a project pauses after 7 days of inactivity |
| B. One small VPS (Hetzner, Oracle Free, or similar) running everything | ₹0–400 | Full control; no job-time limits | A server to patch and monitor; Oracle Free sign-up is unreliable; handover is harder |
| C. Render or Railway free web service + managed database | ₹0 → paid | Simple deploys | Free services sleep, and free databases expire, so it is not reliable for a 14-day run |

## Decision

Choose **Option A**, with Option B as the documented fallback.

| Layer | Service | Why |
|---|---|---|
| Scheduler and compute | GitHub Actions cron | Free minutes (2,000 a month for private repositories), logs per run, secrets store |
| Database, auth, API | Supabase (Postgres) | Email login for up to 5 users, row-level security, and an auto-generated REST API, so the web app needs no custom backend |
| Web app | Static PWA on Cloudflare Pages | Free, fast in India, allows commercial use. Vercel's Hobby plan is non-commercial only. |
| Email | Gmail SMTP or Resend free tier | Daily and weekly reports |
| LLM | Called only for uncertain items, behind a hard monthly cap in config | Keeps spending predictable |

**Actions-minute budget (private repository):**

| Job | Schedule | Minutes/month |
|---|---|---|
| News collection | 12 runs/day × ~2 min | ~720 |
| Official pages | 4 runs/day × ~3 min | ~360 |
| X.com collection, nightly retrain, reports | | ~150 |
| **Total** | | **~1,230 of 2,000** |

Making the repository public would remove the minute limit, but it would expose the
configuration. That is the client's call.

## Consequences

- Supabase pauses a free project after 7 days without activity. Our pipeline writes every 2 hours, so this should not trigger. We will verify this during M3.
- The 500 MB database means we store metadata, excerpts and links, not full HTML, and we purge low-relevance items after 90 days.
- Everything is standard Python plus Postgres, so moving to a VPS takes about an hour if free tiers change.
