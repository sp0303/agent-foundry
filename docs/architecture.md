# Agent Foundry architecture

Status: living document · Last updated: 2026-09-25

This is the whole system in one place: the team, which vendor runs each role, how
boundaries are enforced, the task lifecycle, and the known limits. For commands,
see [operating-guide.md](operating-guide.md). For session bootstrap, see
[../CLAUDE.md](../CLAUDE.md).

## 1. Idea

One human talks to one agent (the BA). Work flows through an architect to a team
of specialist agents that run across **two vendors** — Claude and Antigravity
(Gemini) — using **Git as the shared workspace**. Cheaper/faster hands write code;
independent, different-vendor eyes review it. Two human gates bracket the work:
approve the plan, verify the result.

## 2. The team and where each role runs

| # | Role | Runtime / vendor | Built |
|---|---|---|---|
| 1 | Business analyst | Claude | charter only |
| 2 | Architect | Claude subagent | yes |
| 3 | UX / UI designer | Claude subagent | yes |
| 4 | Developer | **Antigravity (agy / Gemini)** | yes (proven) |
| 5 | QA reviewer | Claude subagent | yes |
| 6 | Security engineer | Claude subagent | yes |
| 7 | Skill curator | Claude subagent | yes |
| 8 | DevOps | Claude | charter only |

Plus two non-agent players: the **human sponsor** (two approval gates) and the
**orchestrator** (currently the live Claude session; the `bridge/` server is the
coded-but-not-running upgrade for 24/7 / parallel operation).

The pattern: **thinking and reviewing run on Claude; code-writing runs on
Antigravity.** The reviewer is therefore always a different vendor than the author.

## 3. Boundary enforcement — the key asymmetry

Each role is meant to use only its own tools. How real that is depends on runtime:

- **Claude subagents** (`.claude/agents/*.md`): the `tools:` allowlist is **hard-
  enforced** by Claude Code. Examples that matter: the architect has no `Edit`/
  `Bash` (cannot write or run feature code); QA and Security have no `Edit`/
  `Write` (can run tests, cannot fix code).
- **Antigravity developer** (`.agents/*`): the declared tool allowlist is **not
  enforced in headless `agy -p`**, and workspace skills are **not auto-discovered**
  headless (verified). So the developer's boundary is enforced by **containment**
  instead: the role + `allowed_paths` are injected into the prompt, work happens on
  an isolated branch, and every change passes review before merge.

This is the single most important truth about the current system: **Claude roles
are fenced by tools; the Antigravity role is fenced by scope + review.**

## 4. Shared rules and skills

- `AGENTS.md` (repo root) — vendor-neutral rules every agent obeys. Auto-loaded by
  both Claude Code and `agy`.
- `.claude/agents/*` — Claude subagents (auto-load, enforced).
- `.agents/skills/*`, `.agents/agents/*` — Antigravity skills/agent files (correct
  format; inert in headless mode; kept for the Antigravity IDE and for the injected
  role text).
- `agents/*` — human-readable role charters (the source of truth for each role's
  authority).

## 5. Task lifecycle

```
Human idea → BA (PRD) → [GATE 1: approve plan]
  → Architect: scope, ADRs, interface contracts, task graph, task contracts
  → UX/UI (if a user surface): flows + specs
  → Developer (agy/Gemini): implement one contract on feat/T-xxx, with tests
  → QA (Claude) + Security (Claude): review — independent, different vendor
     ├─ changes requested → back to the developer (resume via --conversation)
     └─ approved + green → Architect merge decision
  → DevOps: deploy → [GATE 2: verify] → publish
  ↺ Skill curator keeps agents/skills/rules and the MCP tool registry healthy
```

A worker that hits ambiguity must **exit with a question** (`BRIDGE_QUESTION:`),
never guess.

## 6. Direct vs bridge orchestration

- **Direct (current):** the live Claude session calls `agy` and git itself. Proven
  end-to-end. Zero infra; ideal for one person, one project at a time.
- **Bridge (`bridge/`, coded skeleton):** an always-on state machine that spawns
  workers, listens to GitHub webhooks, and calls LLMs only at judgement points.
  Adds durability, 24/7 webhook-driven operation, parallelism, and enforced
  budgets. It is the upgrade path, not required yet.

## 7. Security posture

In place: per-task `allowed_paths` + frozen interfaces; branch isolation + review;
a dedicated Security role; secrets scoped out of prompts; sandboxed command
execution policy on Antigravity agents.

Open risks: `agy --dangerously-skip-permissions` auto-approves all writes/commands
(safe inside a scoped branch, dangerous pointed broader); prompt injection via repo
files/dependencies read by the developer (mitigated by the Security role + review,
not yet automated); no CI wired up, so "green CI" is currently manual.

## 8. Maturity

- Proven: build→review→test→push loop; cross-vendor review; Claude-side tool
  scoping; `agy` headless connection + JSON contract.
- Written, not functional headless: Antigravity `.agents/` skills.
- Planned: BA and DevOps subagents; bridge in production; MCP tool registry;
  automated CI; budget enforcement.

## 9. Top risks / where it breaks

1. Antigravity skill discovery does not fire headless — rely on injection + review.
2. The developer is the one role without hard tool-locking — keep it fenced by
   `allowed_paths` + review.
3. No `gh`/CI yet — PR creation and checks are manual.
4. Cost — pro-model runs are minutes and tens of thousands of tokens each; no
   budget guard is active in direct mode.
