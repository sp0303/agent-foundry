# CLAUDE.md — project context

Auto-loaded by Claude Code in every session opened in this repo. The top part is
**this project's own notes**. The shared foundry rules (team, how to run a task,
gotchas) are imported at the bottom from `.claude/foundry.md`, which is synced from
the template — don't edit that file here.

## This project

- **Product:** the Agent Foundry workshop — research, design history, and the
  `bridge/` server (the future always-on orchestrator).
- **Remote:** https://github.com/sp0303/agent-foundry.git
- **Stack / run commands:** Python 3.13 for `bridge/`:
  `python -m venv bridge/.venv`, `./bridge/.venv/Scripts/python.exe -m pip install -r bridge/requirements.txt pytest`,
  tests: `cd bridge && ./.venv/Scripts/python.exe -m pytest -q`.
- **Notes:**
  - The foundry team layer is **owned by `sp0303/agent-foundry-template`**. To
    change agents, skills, `/build-tool`, `AGENTS.md`, charters, or the shared
    docs, open a PR on the template, then run `bash scripts/sync-foundry.sh` here.
  - Project-only material lives here: `bridge/`, `docs/bridge-design.md`,
    `docs/decisions/`, `docs/research.html`.

## Shared foundry rules

@.claude/foundry.md
