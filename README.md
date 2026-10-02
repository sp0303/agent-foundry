# Agent Foundry

A multi-vendor team of AI agents that builds tools. You talk to one agent (the business analyst); it hands work to an architect, who runs developer, QA and DevOps agents across Claude, Gemini (Antigravity) and OpenAI (Codex). A small bridge server automates the repetitive loop between them, using Git as the shared workspace.

## Status

The team is built and in use (first project: sarey.tech). The `bridge/` server is
a tested walking skeleton, not yet the live orchestrator.

## Where things live

**The foundry team layer is owned by the template repo,
[sp0303/agent-foundry-template](https://github.com/sp0303/agent-foundry-template).**
It is the single source of truth for `AGENTS.md`, `.claude/foundry.md`,
`.claude/agents/`, `.claude/commands/`, `.agents/`, `agents/`, and the shared docs
(`docs/architecture.md`, `docs/operating-guide.md`, `docs/release-checklist.md`).
This repo holds synced copies — change them in the template, then run
`bash scripts/sync-foundry.sh` here. `.foundry-version` records which template
commit this repo is on.

This repo owns:

| Path | What it is |
|---|---|
| `bridge/` | The bridge server (always-on orchestrator, walking skeleton + tests). |
| `docs/research.html` | Research and concept sheet: topology, lifecycle, roles, model routing, landscape, risks, roadmap. Open in a browser. |
| `docs/bridge-design.md` | Design of the bridge server that connects the vendors. |
| `docs/decisions/` | Architecture decision records (ADRs) for this repo. |
| `CLAUDE.md` | This repo's own session notes (imports the shared foundry rules). |

## Core ideas

1. **One front door.** You only talk to the BA agent.
2. **Architect is the hub.** All engineering traffic goes through it; it decides, it does not write feature code.
3. **Deterministic loop, LLM judgement.** Plain code runs "push → CI → QA → merge". Models are called only for planning, answering questions, review, merge decisions and reports.
4. **Git is the source of truth** shared by every vendor.
5. **Two human gates:** approve the plan before code, verify the result before production.
6. **Tool registry.** Every finished tool is published as an MCP server so later projects reuse it.

## Roadmap

1. Single-vendor walking skeleton on Claude Code.
2. Freeze templates: PRD, ADR, task contract, role charters.
3. Add Codex as a developer and cross-vendor reviewer.
4. Add Antigravity/Gemini and the DevOps agent with staging deploys.
5. Tool registry.
