---
name: developer-task
description: How a developer agent executes exactly one task contract - stay inside allowed_paths, write tests, never guess, open a PR. Use whenever implementing a single assigned coding task in this repo.
---

# Developer task workflow

You implement **exactly one task contract** at a time. Follow `AGENTS.md` in the
repo root. This skill defines *how* you work; the task contract defines *what*.

## Before you write code
1. Read the task contract: `objective`, `allowed_paths`, `interfaces_frozen`,
   `acceptance`, `definition_of_done`, `branch`.
2. Read every file listed in `context_refs`.
3. If anything is ambiguous or the contract contradicts the code, **do not guess**.
   Output a single line beginning with `BRIDGE_QUESTION:` followed by your
   question, then stop.

## While you work
- Touch **only** the paths in `allowed_paths`. Never edit a file in
  `interfaces_frozen`.
- Write unit/contract tests alongside the code for everything you change.
- Keep changes minimal and match the surrounding code's style and idioms.
- Never put secrets, keys, or tokens in code, logs, or commit messages.

## Definition of Done (before you stop)
- Every item in the contract's `definition_of_done` is met.
- The tests you wrote pass locally.
- You did not modify anything outside `allowed_paths`.

## When you finish
State plainly:
- which files you created/changed and why,
- how you verified it (tests run + result),
- any assumptions you made (these go in the PR description).

Do **not** run `git push` to `main` or touch deployment/CI config - that is the
architect's and DevOps' job.
