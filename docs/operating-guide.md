# Operating guide

How to actually run work through the team. Pair this with
[architecture.md](architecture.md) (the design) and [../CLAUDE.md](../CLAUDE.md)
(session bootstrap).

## Prerequisites

- **Antigravity CLI** installed and authenticated. Check:
  ```bash
  agy --version
  agy models
  ```
  If `agy` is not found, it installs to `%LOCALAPPDATA%\agy\bin\agy.exe`; add that
  to PATH (`agy install`) and restart the terminal.
- **Python venv** for the bridge tests (optional, only if touching `bridge/`):
  ```bash
  python -m venv bridge/.venv
  ./bridge/.venv/Scripts/python.exe -m pip install -r bridge/requirements.txt pytest
  ```
- **GitHub CLI** (optional but recommended, for PRs/CI):
  ```bash
  winget install --id GitHub.cli --source winget
  gh auth login
  ```
  Without `gh`, `git push` prints a "create a pull request" URL to click.

## The task lifecycle, step by step

### 1. Architect writes the task contract (Claude)
Ask the main session to use the architect subagent. A contract must include:
`task_id`, `title`, `objective`, `context_refs`, `allowed_paths`,
`interfaces_frozen`, `acceptance` (Given/When/Then), `definition_of_done`,
`branch`, `budget`, `assignee`, and the escalation rule. Hand over risks and edge
cases up front.

### 2. Branch
```bash
git checkout main && git pull
git checkout -b feat/T-xxx-<slug>
```

### 3. Developer implements (Antigravity / agy)
Because workspace skills do not auto-load headless, **inject the role + rules into
the prompt**. Then:
```bash
agy -p "<prompt>" --dangerously-skip-permissions --output-format json --model gemini-3.1-pro-high
```
- `--dangerously-skip-permissions` is required headless or `agy` hangs waiting for
  approval. It is contained by the branch + `allowed_paths`.
- On Windows cmd/PowerShell, **avoid inner double-quotes** in the prompt (describe
  JSON in words, e.g. "a key named status with value ok").
- The JSON result has `conversation_id`, `status`, `response`,
  `usage.total_tokens`.

Prompt skeleton for the developer:
```
You are a developer agent for task T-xxx. Follow AGENTS.md.
Objective: <...>
Only modify/create: <allowed_paths>. Never touch: <interfaces_frozen>.
Write tests. Do not run git. If anything is ambiguous, print a line starting with
BRIDGE_QUESTION: and stop.
```

### 4. Review (Claude — different vendor than the author)
Delegate to the Claude subagents and run tests yourself:
- `qa-reviewer` — acceptance criteria, edge/negative/e2e, coverage, guardrails.
- `security-engineer` — threat model, OWASP/ASVS, secrets, supply chain.
```bash
# run the relevant tests, e.g. for the bridge:
cd bridge && ./.venv/Scripts/python.exe -m pytest -q
```
If changes are requested, resume the same developer session:
```bash
agy -p "<feedback>" --conversation <conversation_id> --dangerously-skip-permissions --output-format json
```

### 5. Commit, push, PR
Commit **only the task's files** (not stray/generated files):
```bash
git add <the task files>
git commit -m "feat: <summary> (T-xxx)"
git push -u origin feat/T-xxx-<slug>
```
With `gh`: `gh pr create --fill`. Without: open the printed URL.

### 6. Merge + gates
Architect makes the merge decision on a green, QA+Security-approved PR. The human
verifies (gate 2) before anything is published.

## agy quick reference

| Need | Command |
|---|---|
| One-shot prompt, JSON | `agy -p "<prompt>" --output-format json` |
| Headless (no hang) | add `--dangerously-skip-permissions` |
| Pick a model | `--model gemini-3.1-pro-high` (list: `agy models`) |
| Resume a conversation | `--conversation <conversation_id>` |
| Plan only, no edits | `--mode plan` |

## Troubleshooting

- **agy did nothing / garbled prompt** → shell quoting. Re-run with no inner
  double-quotes; verify you were in the repo root.
- **agy hangs** → missing `--dangerously-skip-permissions`.
- **A subagent's tools list makes agy hang** → an unknown/misspelled Antigravity
  tool name. Use only real names (`view_file`, `grep_search`, `write_to_file`,
  `replace_file_content`, `run_command`).
- **Claude subagent not available** → open the session in this repo folder; it
  loads `.claude/agents/` at startup. New files need a session reload.
- **Workspace skills not applied on agy** → expected headless; inject the role text
  into the prompt instead.
