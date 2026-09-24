# Bridge server

The always-on component that connects the vendors. It owns the task loop as a
state machine, spawns vendor workers headlessly, listens to GitHub webhooks, and
calls LLM agents only at judgement points. Design: [../docs/bridge-design.md](../docs/bridge-design.md).

This is a **walking skeleton**: the deterministic core (task store, state
machine, task contract, dispatch loop, webhook receiver, MCP tool surface) is
real and tested. The worker adapters shell out to each vendor's headless CLI/API;
only the ones whose CLI is installed are "available".

## Layout

| Path | What it is |
|---|---|
| `bridge/models.py` | Task contract + A2A task states (pydantic). |
| `bridge/state_machine.py` | Allowed transitions. Pure, no I/O. |
| `bridge/store.py` | SQLite task store; every write goes through the state machine. |
| `bridge/scheduler.py` | `dispatch_task` (non-blocking), question/resume, cancel. |
| `bridge/adapters/` | One worker adapter per vendor + a registry. |
| `bridge/mcp_server.py` | MCP tools the architect calls. |
| `bridge/webhook.py` | Signature-verified GitHub webhook receiver. |
| `bridge/config.py` | Env/`.env` config; scopes which secrets reach workers. |
| `bridge/trace.py` | JSON-line trace log (one trace id per request). |

## Setup

```bash
python -m venv .venv && . .venv/Scripts/activate   # Windows Git Bash
pip install -r bridge/requirements.txt
cp bridge/.env.example bridge/.env                 # then fill in keys
```

## Run

```bash
# MCP server (stdio) — register this with the architect agent
python -m bridge.mcp_server

# Webhook receiver
uvicorn bridge.webhook:app --port 8000
```

## Test

```bash
cd bridge && pytest
```

The tests cover the state machine, store, contract/prompt, scheduler loop
(with a fake worker) and webhook signature verification — none require a vendor
CLI or network.

## Worker availability

| Vendor | Harness | How it runs | Status |
|---|---|---|---|
| Anthropic | `claude` | `claude -p … --output-format json`, `--resume` | needs `claude` on PATH |
| OpenAI | `codex` | `codex exec …` | **installed on this machine** |
| Google | `gemini` | Gemini API (`google-genai`) | needs `pip install google-genai` + key |
| Google | `antigravity` | `agy -p …` | **unverified** — see below |

## Known follow-ups (not yet done)

- **Antigravity `agy` CLI is unverified.** The design flags a non-TTY hang; the
  adapter is guarded by a hard timeout and marks itself unavailable when `agy`
  is absent. Prefer the Gemini API path until the CLI is verified with a real run.
- **Gemini/Codex → branch+PR.** The adapters run the model/CLI; turning output
  into an actual branch push + PR (tool loop for Gemini, SDK sessions for Codex
  resume) is the next increment.
- **Scheduler budgets/retries/max-review-rounds** are configured but not yet
  enforced end to end.
- **Merge decision, QA cross-vendor routing, DevOps + BA report** stages exist
  in the design but not yet in code.
