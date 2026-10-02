# Agent Foundry

**A team of eight AI agents, across two vendors, that turns an idea into a
reviewed, tested pull request.** You talk to one agent. The plan, the design, the
code, the review and the release are handled by specialists — each with a written
charter, hard boundaries, and its own tools. You keep the two decisions that
matter: approve the plan, and merge the result.

## Meet the team

| Name | Role | Runs on | What they own |
|---|---|---|---|
| **Jacobin** | Business analyst | Claude | Your idea → scope, user stories, Given/When/Then acceptance criteria |
| **Arjun** | Architect | Claude | Stack, ADRs, interface contracts, one task contract per slice |
| **Sparsha** | UX / UI designer | Claude | Flows, screens and states, visual system, accessibility (WCAG 2.2 AA) |
| **Vaka** | Developer | Gemini, via Antigravity CLI | The code — one task at a time, with tests |
| **Tara** | QA reviewer | Claude | Review against acceptance criteria, edge cases, coverage |
| **Kara** | Security engineer | Claude | Threat model, OWASP/ASVS, secrets, supply chain |
| **Ira** | Skill curator | Claude | The agents, skills and rules themselves |
| **Vihaan** | DevOps | Claude | CI, release checklist, deploys, rollback |

## How a build runs

```
You ─ idea ─▶ Jacobin (scope) ─▶ [Gate 1: you approve the plan]
          ─▶ Arjun (architecture + task contracts) ─▶ Sparsha (design, if there's a UI)
          ─▶ Vaka builds one small slice ─▶ run it and look
          ─▶ Tara + Kara review ─▶ pull request ─▶ [Gate 2: you merge]
          ─▶ Vihaan (release checklist) ─▶ publish, with your OK
```

One command starts it: `/build-tool <your idea>`.

## The design choices that make it work

- **Different vendor writes vs. reviews.** Vaka (Gemini) writes the code; Tara
  and Kara (Claude) review it. A model never grades its own homework.
- **Boundaries are enforced by tools, not promises.** Each Claude agent gets only
  the tools its job needs: Tara and Kara have no file-writing tools, so they can't
  "just fix it"; Arjun can't edit or run code. Vaka is fenced by the task
  contract's allowed paths, its own branch, and review.
- **Task contracts, not vibes.** Every slice is a written contract — objective,
  allowed paths, frozen interfaces, acceptance criteria, Definition of Done. If
  anything is ambiguous, the developer stops and asks instead of guessing.
- **The orchestrator never writes product code.** Every change, however small,
  goes through the developer and review.
- **Git is the shared workspace.** Agents from different vendors don't talk to
  each other directly; they meet in branches and pull requests.
- **Humans hold two gates.** Approve the plan before any code; merge before
  anything ships.

## What's real today

- The full loop has run end to end: Gemini wrote the code, Claude reviewed it, the
  tests passed, and it landed as a pull request.
- All eight roles are defined; seven run as tool-scoped agents (the business
  analyst is played by the main session).
- First real project: a product landing page, built through this pipeline with
  design, QA and security review.
- The process improves from real use. Lessons from that first project became
  rules: the orchestrator never writes product code, design specs must match the
  code, every UI is previewed before review, and releases go through a DevOps
  checklist.

## Use it for your own project

The team lives in a template:
[agent-foundry-template](https://github.com/sp0303/agent-foundry-template).

```
gh repo create <owner>/<name> --template sp0303/agent-foundry-template --private --clone
```

Open the new folder in Claude Code, fill in `CLAUDE.md`, and run
`/build-tool <your idea>`. Projects stay current with
`bash scripts/sync-foundry.sh`.

You'll need [Claude Code](https://claude.com/claude-code), the Antigravity CLI
(`agy`), and the GitHub CLI (`gh`).

## What's in this repo

This repo is the workshop: research, design history, and the bridge server. The
team itself is owned by the template and synced here.

| Path | What it is |
|---|---|
| `bridge/` | The bridge server — a future always-on orchestrator (task state machine, GitHub webhooks, per-vendor workers). Walking skeleton with tests. |
| `docs/architecture.md` | The full design: team, boundaries, lifecycle, security posture, risks. |
| `docs/operating-guide.md` | Step-by-step commands for running a build. |
| `docs/release-checklist.md` | What DevOps checks before anything is published. |
| `docs/research.html` | The original research and concept sheet. Open in a browser. |
| `docs/bridge-design.md`, `docs/decisions/` | Bridge server design and decision records. |
| `.claude/agents/`, `.claude/commands/`, `.agents/`, `agents/`, `AGENTS.md`, `.claude/foundry.md` | The team — synced from the template (see `.foundry-version`). |

## Roadmap

1. Business analyst as a dedicated agent.
2. Bridge server in production: always-on, webhook-driven, parallel tasks, budgets.
3. Automated CI on every pull request.
4. A tool registry: every finished tool published as an MCP server so later
   projects can reuse it.
