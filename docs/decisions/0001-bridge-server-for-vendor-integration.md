# ADR 0001: Bridge server for cross-vendor integration

- Status: proposed
- Date: 2026-09-24

## Context

Agents run on Claude Code, Antigravity and Codex. They cannot call each other, and a chat session cannot listen for events. Browser automation of vendor web UIs was considered.

## Options

1. Drive vendor web UIs through a browser agent.
2. Implement full A2A servers for every vendor now.
3. A small bridge server using headless CLIs/APIs, GitHub webhooks, and A2A-shaped task states.

## Decision

Option 3.

## Consequences

- Fast to build; every vendor already offers a headless CLI or API.
- Browser automation rejected: fragile, slow, hard to audit, and a likely terms-of-service problem.
- Keeping A2A task states and message shapes makes a later move to real A2A a swap, not a rewrite.
- The bridge becomes a critical component and needs its own tests, logging and restarts.
