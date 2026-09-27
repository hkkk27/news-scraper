# Work Log

Newest entries at the top. One entry per task or working session. Format rules are in
[CONTRIBUTING.md](../CONTRIBUTING.md#5-documentation-rules).

---

## 2026-09-27 — M0-01 Repository setup, M0-02 Scope of work and decisions

**Branch:** `main` (initial setup), then `docs/m0-scope-of-work`

### Done

- **Repository.** Cloned the empty private repo `hkkk27/news-scraper`. Added the README, a `.gitignore` for Python, Node, secrets and local data, and a `.gitattributes` that stores LF line endings because the pipeline runs on Linux.
- **Open-source survey.** Evaluated 8 candidate projects, plus the small India-specific scrapers, from GitHub. Decision: build a lean core and reuse libraries as dependencies rather than fork a product ([ADR-0001](decisions/0001-build-lean-core-not-fork.md)).
- **Stack and cost.** Chose GitHub Actions, Supabase and Cloudflare Pages on free tiers, with a VPS as the fallback. Budgeted Actions minutes for a private repo at about 1,230 of 2,000 a month ([ADR-0002](decisions/0002-stack-and-hosting.md)).
- **Source verification.** Tested 21 feeds:
  - 14 work, including Hindi publisher feeds and Google News search in `en`, `hi`, `mr` and `ta`.
  - 7 need another method, recorded in [sources.md](sources.md).
- **Scope of work.** Wrote the [SOW](SOW.md): deliverables with acceptance criteria, taxonomy and priority rubric, three-level de-duplication protocol, training loop, timeline and a 29-task work breakdown.
- **Git conventions.** Wrote [CONTRIBUTING.md](../CONTRIBUTING.md): branch per task, Conventional Commits, PR merges and milestone tags.

### Commits

| Hash | Message |
|---|---|
| `61f1652` | chore: initialize repository with README and .gitignore |
| `c7e2cda` | chore: normalize line endings with .gitattributes |
| `5f577db` | docs: add scope of work with milestones, taxonomy and WBS |
| `841d1fe` | docs: add ADR-0001 build a lean core instead of forking |
| `7b8043e` | docs: add ADR-0002 stack and hosting within Rs 500/month |
| `e1f8aba` | docs: add source registry with 27 Sep verification results |
| `8c8aebe` | docs: add contributing guide with branch, commit and release rules |

### Key finding

The 14-day uninterrupted run (D3) has to end by 19 October, so **the pipeline must be live
by 5 October**, before the selection outcome is fully settled. Backend work therefore
starts immediately after M0.

### Next

- Review and merge `docs/m0-scope-of-work` into `main`.
- M0-03: build the A/M proposal deck (3–5 slides), due 29 Sep 23:59.
- M1-01: Python package skeleton, config loader and CLI.
