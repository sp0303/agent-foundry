#!/usr/bin/env bash
# Pull the latest Agent Foundry team layer from the template repo into this repo.
#
# The template (sp0303/agent-foundry-template) is the single source of truth for
# the paths in SYNCED_PATHS. Change them in the template, then run this script in
# each project. Everything not listed here belongs to the project and is never
# touched.
#
# Usage (from anywhere inside the project; Git Bash on Windows):
#   bash scripts/sync-foundry.sh            # sync from the template's main
#   bash scripts/sync-foundry.sh <branch>   # sync from a branch or tag
#
# Requires: git, and gh logged in (the template repo is private).
set -euo pipefail

TEMPLATE="${FOUNDRY_TEMPLATE:-sp0303/agent-foundry-template}"
REF="${1:-main}"

# Paths owned by the template. Keep this list in sync with .claude/foundry.md.
SYNCED_PATHS=(
  AGENTS.md
  .claude/foundry.md
  .claude/agents
  .claude/commands
  .agents
  agents
  docs/architecture.md
  docs/operating-guide.md
  docs/release-checklist.md
  scripts/sync-foundry.sh
)

root="$(git rev-parse --show-toplevel)"
cd "$root"

# Refuse to overwrite local, uncommitted edits to foundry-owned files.
if [ -n "$(git status --porcelain -- "${SYNCED_PATHS[@]}")" ]; then
  echo "Uncommitted changes in foundry-owned paths - commit or stash them first:" >&2
  git status --short -- "${SYNCED_PATHS[@]}" >&2
  exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

gh repo clone "$TEMPLATE" "$tmp/template" -- --quiet --depth 1 --branch "$REF"
sha="$(git -C "$tmp/template" rev-parse --short HEAD)"

for p in "${SYNCED_PATHS[@]}"; do
  src="$tmp/template/$p"
  if [ ! -e "$src" ]; then
    echo "skip (not in template): $p"
    continue
  fi
  if [ -d "$src" ]; then
    mkdir -p "$p"
    cp -R "$src/." "$p/"
  else
    mkdir -p "$(dirname "$p")"
    cp "$src" "$p"
  fi
done

echo "$TEMPLATE@$sha" > .foundry-version

echo "Synced the foundry layer from $TEMPLATE@$sha ($REF)."
if git diff --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  echo "Already up to date - nothing changed."
else
  echo "Review with 'git status' / 'git diff', then commit on a branch, e.g.:"
  echo "  git checkout -b chore/sync-foundry-$sha"
  echo "  git add -A && git commit -m \"chore: sync foundry layer ($sha)\""
fi
