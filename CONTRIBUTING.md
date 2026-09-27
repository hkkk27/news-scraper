# How we work

Small, reviewable steps. Every piece of work is planned in the [SOW](docs/SOW.md),
done on its own branch, committed in logical pieces, logged in the
[WORKLOG](docs/WORKLOG.md), and merged through a pull request.

## 1. The flow for every task

```
SOW task (e.g. M1-04)
   │
   ├─ 1. branch      git checkout main && git pull
   │                 git checkout -b feat/m1-04-rss-adapters
   │
   ├─ 2. commit      one logical change per commit (code + its tests together)
   │                 git add -p   → review what you stage
   │                 git commit   → Conventional Commit message (below)
   │
   ├─ 3. push        git push -u origin feat/m1-04-rss-adapters   (push early, push often)
   │
   ├─ 4. log         add a WORKLOG entry in the same branch
   │
   ├─ 5. PR          open a pull request → review the diff → merge (merge commit, keep history)
   │
   └─ 6. tidy        delete the branch; mark the task Done in the SOW table
```

`main` is always working and deployable, and nobody commits to it directly after setup.
The scheduled pipeline runs from `main`.

## 2. Branch names

`<type>/<task-id>-<short-description>`, lowercase, words joined with hyphens:

| Type | Use for | Example |
|---|---|---|
| `feat/` | New functionality | `feat/m1-08-dedup-clustering` |
| `fix/` | Bug fixes | `fix/m3-03-pib-date-parsing` |
| `docs/` | Documentation only | `docs/m0-scope-of-work` |
| `chore/` | Tooling, CI, dependencies | `chore/m1-12-actions-schedule` |
| `refactor/` | Restructuring without behaviour change | `refactor/m1-09-tagger-rules` |

## 3. Commit messages (Conventional Commits)

```
<type>(<scope>): <what changed, imperative, ≤ 72 chars>

<why this change was needed and anything non-obvious>

Refs: <task-id>
```

- **Types:** `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`.
- **Scopes:** `ingest`, `extract`, `dedup`, `classify`, `learn`, `db`, `report`, `web`, `ci`, `config`.
- **Example:** `feat(ingest): add Google News search adapter with language packs`.
- Keep one logical change per commit. If the message needs "and", it is probably two commits.
- Never commit secrets. Keys go in `.env` locally and in GitHub Actions secrets in CI. Copy `.env.example` to start.

## 4. Versions and releases

Tag each milestone on `main` when its deliverable is accepted:

| Tag | Milestone |
|---|---|
| `v0.1.0` | M1 Backend & training platform (D1) |
| `v0.2.0` | M2 Frontend & reporting (D2) |
| `v1.0.0` | M4 Handover (D4) |

## 5. Documentation rules

- **WORKLOG:** one entry per task or session: date, task ID, branch, what was done, commits, and what is next.
- **Decisions:** any choice between real alternatives gets a short record in `docs/decisions/NNNN-title.md`.
- **SOW:** update the status column when a task starts or finishes; scope changes get a new version in its change log.
