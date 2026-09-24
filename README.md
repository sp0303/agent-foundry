# Agent Foundry

A multi-vendor team of AI agents that builds tools. You talk to one agent (the business analyst); it hands work to an architect, who runs developer, QA and DevOps agents across Claude, Gemini (Antigravity) and OpenAI (Codex). A small bridge server automates the repetitive loop between them, using Git as the shared workspace.

## Status

Research and design. No code yet.

## Repository layout

| Path | What it is |
|---|---|
| `docs/research.html` | Research and concept sheet: topology, lifecycle, roles, model routing, landscape, risks, roadmap. Open in a browser. |
| `docs/bridge-design.md` | Design of the bridge server that connects the vendors. |
| `docs/decisions/` | Architecture decision records (ADRs). |
| `agents/` | Role charters, one file per agent. These become system prompts. |
| `AGENTS.md` | Rules every coding agent reads, whatever the vendor. |

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
