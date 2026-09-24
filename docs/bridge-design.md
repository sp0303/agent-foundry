# Bridge server design

Status: draft · Owner: architect

## Problem

Claude Code, Antigravity CLI and Codex cannot call each other directly, and a chat session cannot listen for events. Something always-on has to receive "task finished" signals and wake the right agent with the right context.

## Decision

Build a small bridge server that owns the task loop as a state machine. It spawns vendor workers headlessly, listens to GitHub webhooks, and calls LLM agents only at judgement points. It borrows the A2A task model so it can be swapped for real A2A later.

## Flow

```
You ⇄ BA (Claude chat)
        │ approved plan
        ▼
Architect (Claude Code) ──MCP──▶ Bridge server (task queue)
                                   │ spawns one worker per task:
                                   │   claude -p … | codex exec … | agy -p … / Gemini Interactions API
                                   ▼
                              worker pushes feat/T-xxx and opens a PR
GitHub webhook (PR opened) ──▶ Bridge ──▶ CI runs
CI result ──▶ Bridge ──▶ QA agent (different vendor from author) reviews
  ├─ changes requested ──▶ resume dev session with feedback
  ├─ worker exits with a question ──▶ architect answers ──▶ resume session
  └─ approved + green ──▶ architect merge decision ──▶ DevOps ──▶ BA report ──▶ You
```

## Task states (borrowed from A2A)

`submitted → working → input_required → working → completed | failed | canceled`

Plus bridge-specific sub-states on `working`: `pr_open`, `ci_running`, `in_review`, `changes_requested`, `ready_to_merge`.

## Components

| Component | Responsibility |
|---|---|
| Task store | SQLite (Postgres later). One row per task: contract, state, vendor, session ID, branch, PR, cost. |
| Worker adapters | One per vendor. Start a run, stream logs, detect exit, capture session ID, resume with new input. |
| Webhook receiver | GitHub `pull_request`, `push`, `check_suite` events, signature-verified. |
| MCP server | Tools the architect calls: `dispatch_task`, `task_status`, `answer_question`, `list_tasks`, `cancel_task`. `dispatch_task` returns an ID immediately; it never blocks for the whole run. |
| Scheduler | Enforces per-task token and time budgets, retries, max review rounds. |
| Trace log | One trace ID per user request; cost per agent. |

## Worker adapters

| Vendor | Headless entry point | Resume | Notes |
|---|---|---|---|
| Claude | `claude -p "<prompt>" --output-format json` | `--resume <session_id>` | Scope tools with `--allowedTools`. |
| Codex | `codex exec "<prompt>"` or Codex SDK | SDK sessions | Codex MCP server was removed Sep 2026; use CLI or SDK. |
| Antigravity CLI | `agy -p "<prompt>" --output-format json` | check current docs | Known reports of `-p` hanging in non-TTY subprocesses: run under a pseudo-terminal, with timeouts. |
| Gemini API | Interactions API, `background=True` | multi-turn interactions | Poll interaction ID until completed or failed. |

## Rules

- The bridge decides a task is finished from process exit or API status, never from the agent remembering to send a callback.
- Workers run on API keys, not personal OAuth subscriptions (quota limits).
- A worker that hits ambiguity must exit with a structured question, not guess. The bridge moves the task to `input_required`.
- Workers get only the paths in their task contract; secrets come through a proxy, never in prompts.
- Production deploys require a recorded human approval.

## Task contract (sent to every worker)

```json
{
  "task_id": "T-014",
  "title": "Rate-limit middleware for /v1/convert",
  "objective": "Reject >60 req/min per API key with HTTP 429",
  "context_refs": ["docs/decisions/0007-rate-limiting.md", "api/openapi.yaml"],
  "allowed_paths": ["src/middleware/**", "tests/middleware/**"],
  "interfaces_frozen": ["api/openapi.yaml"],
  "acceptance": [
    "Given 61 requests in 60s with one key, the 61st returns 429 with Retry-After",
    "Given two keys, limits are independent"
  ],
  "definition_of_done": ["unit tests pass", "coverage >= 85% on changed files", "no new high SAST findings"],
  "branch": "feat/T-014-rate-limit",
  "budget": { "max_tokens": 400000, "max_minutes": 45 },
  "assignee": { "vendor": "openai", "harness": "codex", "model": "from-routing-table" },
  "escalation": "exit with a question; do not guess"
}
```

## Open questions

- Where the bridge runs: laptop, single VM, or container on a cloud host.
- Postgres vs SQLite once more than one project runs at a time.
- When to replace the internal protocol with real A2A servers per vendor.
