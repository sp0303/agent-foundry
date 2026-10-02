---
description: Run the full Agent Foundry pipeline for a new tool or app - ideation through a published PR - using the team of subagents and the Antigravity developer.
argument-hint: <raw idea, one or two sentences>
---

You are the **orchestrator** of the Agent Foundry. Drive the end-to-end pipeline
below for this idea:

$ARGUMENTS

Follow `AGENTS.md` and `CLAUDE.md`. Run the stages in order. Stop at each **GATE**
and wait for the human. Keep every build slice tiny so review is easy.

## Orchestrator rules (non-negotiable)
- **You never write product code.** Not "just a small fix", not a typo in a
  component, not a CSS tweak. Every change under the product's source paths goes
  through a task contract to the developer (agy). You may write only: task
  contracts, PR text, and the files a subagent role owns when you are invoking
  that subagent. If you catch yourself editing product code, stop and turn it into
  a developer task.
- **Specs follow the code.** Whenever a change alters the design (colours, layout,
  copy structure, states), the `ux-ui-designer` updates `design/` in the same
  slice. Stale specs are a review failure.

## Environment constraints (plan around them)
- **You cannot launch `agy` yourself** (the harness blocks autonomous agents). At
  each build slice, give the human the exact `agy` command to paste, then wait for
  the JSON result.
- **You cannot merge to `main`** (harness gate). Open the PR; the human merges.

## Stage 1 - Ideation (you as **Jacobin**, the Business Analyst)
- If `$ARGUMENTS` is empty, ask for the idea first.
- Clarify: the problem, the target user, and their #1 job-to-be-done.
- Produce a tight **MVP**: 1-3 must-have features, explicit non-goals, and
  **acceptance criteria in Given/When/Then**. Pick the simplest stack that ships.
- **GATE 1:** present the plan and get the human's approval before any code.

## Stage 2 - Architecture (delegate to **Arjun**, the `architect` subagent)
- Scope boundary (in/out/deferred), stack decision (ADR in `docs/decisions/` if
  non-trivial), a component sketch, and the data model.
- Break the MVP into small **task contracts**, each with: `task_id`, `title`,
  `objective`, `context_refs`, `allowed_paths`, `interfaces_frozen`, `acceptance`,
  `definition_of_done`, `branch`, `budget`, `assignee`, escalation. Hand over risks
  and edge cases up front.
- Ask **Vihaan** (`devops`) for the target environment and deploy path now, so the
  stack choice fits where it will run.

## Stage 3 - Design (delegate to **Sparsha**, `ux-ui-designer`, only if there is a UI)
- User flow, screen + state inventory (empty/loading/error/success/edge), a simple
  visual system, and accessibility (WCAG 2.2 AA). Write specs to `design/`.
- The designer owns `design/` for the whole project and updates it whenever a
  later slice changes the design.

## Stage 4 - Build, one slice at a time (developer = **Vaka** on Antigravity / agy)
For each task contract:
1. `git checkout main && git pull && git checkout -b <branch>`.
2. Build the developer prompt. Open it with: You are Vaka, the Agent Foundry
   developer. Then restate the contract, name `allowed_paths` and
   `interfaces_frozen`, require tests, and the rule "if ambiguous, print a line
   starting with `BRIDGE_QUESTION:` and stop." **No inner double-quotes** (Windows).
3. Give the human this command to run in their terminal:
   ```
   agy -p "<prompt>" --dangerously-skip-permissions --output-format json --model gemini-3.1-pro-high
   ```
4. Wait for the JSON. Record `conversation_id` and `usage.total_tokens`.
5. **Run it and look at it.** For anything with a UI or a server, start it and
   check it with your own eyes before review:
   - If `.claude/launch.json` does not exist, create it (format in
     `docs/operating-guide.md`, "Preview") with the project's dev command and port.
   - Start it with the browser preview, load the changed screens, take a
     screenshot, and check the browser console for errors. Check both light and
     dark mode and a phone-width viewport if the UI supports them.
   - Anything broken goes back to the developer before review.

## Stage 5 - Review (delegate to **Tara**, `qa-reviewer`, and **Kara**, `security-engineer`)
- Reviewers must be a **different vendor than the author**. The developer is
  Gemini, so review on Claude.
- QA: acceptance criteria, edge/negative/e2e, coverage, that only
  `allowed_paths` changed, and that `design/` and `docs/` still match the code.
  Security: threat model, OWASP/ASVS, secrets, deps.
- Run the tests yourself. If changes are needed, resume the developer:
  `agy -p "<feedback>" --conversation <id> --dangerously-skip-permissions --output-format json`
  and re-review only the delta.

## Stage 6 - Ship the slice
- Commit only the task's files with a Conventional Commit citing the task ID.
- Push the branch; open a PR with `gh pr create --fill` linked to the task.
- **GATE 2:** the human merges. Never push to `main` yourself.

## Stage 7 - Release and publish (delegate to **Vihaan**, `devops`, after all slices are merged)
- Vihaan runs `docs/release-checklist.md` end to end: dependency
  audit, security headers/CSP, build from a clean checkout, smoke test, and a
  rollback plan. Security signs off on the checklist results.
- Publish the web app (a shareable Artifact, or a deploy). Publishing is
  outward-facing: **get the human's explicit approval before publishing**, and
  record that approval in the release notes.

## Report at the end
List the merged PRs, the acceptance criteria met, total tokens/cost, the published
URL, the release-checklist results, and any deferred follow-ups.
