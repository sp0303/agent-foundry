# Agent Foundry — shared rules

> **Synced file — do not edit in a project.** This file comes from
> `sp0303/agent-foundry-template`, the single source of truth for the foundry team
> layer. Change it there, then run `bash scripts/sync-foundry.sh` in each project.

This project is built with the **Agent Foundry**: a multi-vendor team of AI
agents. The thinking/reviewing roles run on **Claude**; the code-writing role runs
on **Antigravity (agy / Gemini)**. Git is the shared workspace. See
[docs/architecture.md](../docs/architecture.md) for the design and
[docs/operating-guide.md](../docs/operating-guide.md) for step-by-step commands.

## The team

| Role | Runtime | How to invoke | Status |
|---|---|---|---|
| Business analyst | Claude | played live by the main session | charter only |
| Architect | Claude subagent | "use the architect subagent…" | built |
| UX / UI designer | Claude subagent | "use the ux-ui-designer subagent…" | built |
| Developer | **Antigravity (agy)** | `agy -p "<task>"` (see recipe) | built |
| QA reviewer | Claude subagent | "use the qa-reviewer subagent…" | built |
| Security engineer | Claude subagent | "use the security-engineer subagent…" | built |
| Skill curator | Claude subagent | "use the skill-curator subagent…" | built |
| DevOps | Claude subagent | "use the devops subagent…" | built |

Claude subagents in `.claude/agents/` load automatically — just ask the main
session to delegate to them by name. Run the whole pipeline with
**`/build-tool <idea>`** (`.claude/commands/build-tool.md`).

## The rule that protects quality

**The reviewer must be a different vendor than the author.** The developer is
Gemini (agy), so **QA and Security stay on Claude.** Never let the same vendor
write and review the same code.

## Orchestrator rules

- **The orchestrator never writes product code** — not even a one-line fix. Every
  product change goes through a task contract to the developer (agy) and then
  review. The orchestrator writes only contracts, PR text, and files owned by a
  subagent it is invoking.
- **Specs follow the code.** If a change alters the design, the `ux-ui-designer`
  updates `design/` in the same slice; QA fails the review if specs are stale.
- **Look before review.** Run anything with a UI or server via the browser
  preview (`.claude/launch.json`, see the operating guide) and check it before
  handing it to QA.
- **Release through DevOps.** Nothing is published until the `devops` subagent has
  run [docs/release-checklist.md](../docs/release-checklist.md), Security has
  signed off, and the human has approved.
- **Foundry files are synced, not edited.** The paths listed in
  `scripts/sync-foundry.sh` belong to the template. To improve the process, change
  the template (the `skill-curator` subagent owns this) and sync — never edit
  those files inside a project.

## Running a task (direct orchestration)

The main Claude session is the orchestrator. For one task:

1. Architect (Claude) writes a **task contract**: objective, `allowed_paths`,
   `interfaces_frozen`, acceptance (Given/When/Then), Definition of Done, branch.
2. Create the branch `feat/T-xxx-<slug>`.
3. Dispatch the developer to Antigravity:
   ```bash
   agy -p "<contract, written out as a prompt>" --dangerously-skip-permissions --output-format json --model gemini-3.1-pro-high
   ```
   (On Windows cmd/PowerShell, avoid inner double-quotes in the prompt.)
4. Preview it (UI/server), then review: delegate to the `qa-reviewer` and
   `security-engineer` Claude subagents; run the tests.
5. Commit only the task's files, push the branch, open a PR linked to the task ID.
6. Merge decision (architect) → human verifies → merge.

## Gotchas (learned the hard way)

- **Antigravity workspace skills do NOT auto-load in headless `agy -p`.** The
  files in `.agents/skills/` are correct but inert headless; the developer's role
  is enforced by **injecting the role text into the prompt** plus `allowed_paths`
  + branch + review. (Claude subagents, by contrast, DO auto-load and enforce.)
- `agy` without `--dangerously-skip-permissions` **hangs** waiting for a human to
  approve file writes. Use the flag for headless runs (it is scoped by the branch).
- `agy` returns JSON: `conversation_id`, `status`, `response`,
  `usage.total_tokens`. Resume with `--conversation <id>`.
- The harness blocks the session from launching `agy` itself and from merging to
  `main`: the human runs `agy` commands and merges PRs.
- Follow [AGENTS.md](../AGENTS.md): never push to `main`, open a PR per task,
  never edit `interfaces_frozen`, never commit secrets.

## One-time machine setup (not per project)

- `agy` (Antigravity CLI) installed and logged in — `agy --version`, `agy models`.
- `gh` (GitHub CLI) installed and logged in — `gh auth status`.
