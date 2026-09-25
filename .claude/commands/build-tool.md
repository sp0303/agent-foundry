---
description: Run the full Agent Foundry pipeline for a new tool or app - ideation through a published PR - using the team of subagents and the Antigravity developer.
argument-hint: <raw idea, one or two sentences>
---

You are the **orchestrator** of the Agent Foundry. Drive the end-to-end pipeline
below for this idea:

$ARGUMENTS

Follow `AGENTS.md` and `CLAUDE.md`. Run the stages in order. Stop at each **GATE**
and wait for the human. Keep every build slice tiny so review is easy.

Two hard constraints of this environment, plan around them:
- **You cannot launch `agy` yourself** (the harness blocks autonomous agents). At
  each build slice, give the human the exact `agy` command to paste, then wait for
  the JSON result.
- **You cannot merge to `main`** (harness gate). Open the PR; the human merges.

## Stage 1 - Ideation (you as Business Analyst)
- If `$ARGUMENTS` is empty, ask for the idea first.
- Clarify: the problem, the target user, and their #1 job-to-be-done.
- Produce a tight **MVP**: 1-3 must-have features, explicit non-goals, and
  **acceptance criteria in Given/When/Then**. Pick the simplest stack that ships.
- **GATE 1:** present the plan and get the human's approval before any code.

## Stage 2 - Architecture (delegate to the `architect` subagent)
- Scope boundary (in/out/deferred), stack decision (ADR in `docs/decisions/` if
  non-trivial), a component sketch, and the data model.
- Break the MVP into small **task contracts**, each with: `task_id`, `title`,
  `objective`, `context_refs`, `allowed_paths`, `interfaces_frozen`, `acceptance`,
  `definition_of_done`, `branch`, `budget`, `assignee`, escalation. Hand over risks
  and edge cases up front.

## Stage 3 - Design (delegate to `ux-ui-designer`, only if there is a UI)
- User flow, screen + state inventory (empty/loading/error/success/edge), a simple
  visual system, and accessibility (WCAG 2.2 AA). Write specs to `design/`.

## Stage 4 - Build, one slice at a time (developer = Antigravity / agy)
For each task contract:
1. `git checkout main && git pull && git checkout -b <branch>`.
2. Build the developer prompt: restate the contract, name `allowed_paths` and
   `interfaces_frozen`, require tests, and the rule "if ambiguous, print a line
   starting with `BRIDGE_QUESTION:` and stop." **No inner double-quotes** (Windows).
3. Give the human this command to run in their terminal:
   ```
   agy -p "<prompt>" --dangerously-skip-permissions --output-format json --model gemini-3.1-pro-high
   ```
4. Wait for the JSON. Record `conversation_id` and `usage.total_tokens`.

## Stage 5 - Review (delegate to `qa-reviewer` and `security-engineer`)
- Reviewers must be a **different vendor than the author**. The developer is
  Gemini, so review on Claude.
- QA: acceptance criteria, edge/negative/e2e, coverage, and that only
  `allowed_paths` changed. Security: threat model, OWASP/ASVS, secrets, deps.
- Run the tests yourself. If changes are needed, resume the developer:
  `agy -p "<feedback>" --conversation <id> --dangerously-skip-permissions --output-format json`
  and re-review only the delta.

## Stage 6 - Ship the slice
- Commit only the task's files with a Conventional Commit citing the task ID.
- Push the branch; open a PR with `gh pr create --fill` linked to the task.
- **GATE 2:** the human merges. Never push to `main` yourself.

## Stage 7 - Publish (after all slices are merged)
- Assemble/verify the app on `main`.
- Publish the web app (a shareable Artifact, or a deploy). Publishing is
  outward-facing: **get the human's explicit approval before publishing.**

## Report at the end
List the merged PRs, the acceptance criteria met, total tokens/cost, the published
URL, and any deferred follow-ups.
