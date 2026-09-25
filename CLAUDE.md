# CLAUDE.md — project context for every session

This file is auto-loaded by Claude Code at the start of any session opened in this
repo. It is the bootstrap: read it, and you know the team and how to operate it.

**What this repo is:** a multi-vendor team of AI agents that builds tools. The
thinking/reviewing roles run on **Claude**; the code-writing role runs on
**Antigravity (agy / Gemini)**. Git is the shared workspace. See
[docs/architecture.md](docs/architecture.md) for the full design and
[docs/operating-guide.md](docs/operating-guide.md) for step-by-step commands.

## The team

| Role | Runtime | How to invoke | Status |
|---|---|---|---|
| Business analyst | Claude | played live by the main session | charter only |
| Architect | Claude subagent | "use the architect subagent…" | built (`.claude/agents/architect.md`) |
| UX / UI designer | Claude subagent | "use the ux-ui-designer subagent…" | built |
| Developer | **Antigravity (agy)** | `agy -p "<task>"` (see recipe) | proven |
| QA reviewer | Claude subagent | "use the qa-reviewer subagent…" | built |
| Security engineer | Claude subagent | "use the security-engineer subagent…" | built |
| Skill curator | Claude subagent | "use the skill-curator subagent…" | built |
| DevOps | Claude | (design only) | charter only |

Claude subagents in `.claude/agents/` load automatically — no slash command
needed; just ask the main session to delegate to them by name.

## The rule that protects quality

**The reviewer must be a different vendor than the author.** The developer is
Gemini (agy), so **QA and Security stay on Claude.** Never let the same vendor
write and review the same code.

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
4. Review: delegate to the `qa-reviewer` and `security-engineer` Claude subagents;
   run the tests.
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
- Follow [AGENTS.md](AGENTS.md): never push to `main`, open a PR per task, never
  edit `interfaces_frozen`, never commit secrets.

## Repo

- Remote: `origin` = https://github.com/sp0303/agent-foundry.git
- Bridge server (coded skeleton, not the current orchestrator): `bridge/`.
