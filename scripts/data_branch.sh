#!/usr/bin/env bash
# Persist the tracker's runtime data between CI runs on an orphan `data` branch.
#
#   scripts/data_branch.sh restore   # copy data/ from origin/data into the working tree (if the branch exists)
#   scripts/data_branch.sh save      # replace origin/data with a single commit holding data/
#
# The branch always holds exactly one commit, so the repository does not grow with every run.
# Requires push access (GITHUB_TOKEN with contents: write in Actions).
set -euo pipefail

BRANCH="${DATA_BRANCH:-data}"
action="${1:-}"

case "$action" in
  restore)
    if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
      git fetch --depth=1 origin "$BRANCH"
      rm -rf data
      git archive FETCH_HEAD data | tar -x
      echo "restored data/ from origin/$BRANCH ($(du -sh data | cut -f1))"
    else
      echo "no $BRANCH branch yet; starting with an empty data/"
      mkdir -p data
    fi
    ;;
  save)
    tmp="$(mktemp -d)"
    cp -r data "$tmp/"
    remote="$(git remote get-url origin)"
    # The temporary repository does not inherit actions/checkout's credentials: use the token.
    if [ -n "${GITHUB_TOKEN:-}" ] && [ -n "${GITHUB_REPOSITORY:-}" ]; then
      remote="https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
    fi
    (
      cd "$tmp"
      git init -q
      git checkout -q -b "$BRANCH"
      git config user.name "tracker-bot"
      git config user.email "tracker-bot@users.noreply.github.com"
      git add -A
      git commit -q -m "data snapshot $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      git push -q -f "$remote" "$BRANCH"
    )
    rm -rf "$tmp"
    echo "saved data/ to origin/$BRANCH"
    ;;
  *)
    echo "usage: $0 restore|save" >&2
    exit 2
    ;;
esac
