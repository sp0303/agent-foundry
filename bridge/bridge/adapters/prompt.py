"""Build the worker prompt from a task contract.

The prompt is vendor-neutral: it restates the contract, the repo rules, and the
one non-negotiable behaviour — exit with a structured question instead of
guessing. Secrets are never interpolated here.
"""

from __future__ import annotations

from ..models import TaskContract

_QUESTION_SENTINEL = "BRIDGE_QUESTION:"


def build_worker_prompt(contract: TaskContract, resuming: bool) -> str:
    c = contract
    lines = [
        f"You are a {c.assignee.harness} developer agent working on task {c.task_id}.",
        "Follow AGENTS.md in the repo root. Key rules:",
        "- Work only inside these paths: " + ", ".join(c.allowed_paths or ["(none)"]),
        "- Never modify: " + ", ".join(c.interfaces_frozen or ["(none)"]),
        f"- Never push to main. Work on branch {c.branch} and open a PR for {c.task_id}.",
        "- Write tests with the code and meet the Definition of Done before the PR.",
        "",
        f"# Objective\n{c.objective}",
    ]
    if c.context_refs:
        lines.append("\n# Context (read these)\n- " + "\n- ".join(c.context_refs))
    if c.acceptance:
        lines.append("\n# Acceptance criteria\n- " + "\n- ".join(c.acceptance))
    if c.definition_of_done:
        lines.append("\n# Definition of Done\n- " + "\n- ".join(c.definition_of_done))
    lines += [
        "",
        "# If anything is ambiguous",
        f"Do NOT guess. Print a single line starting with '{_QUESTION_SENTINEL}' "
        "followed by your question, then stop. The bridge will get you an answer "
        "and resume this session.",
    ]
    if resuming:
        lines.insert(
            0, "You are resuming an earlier session; new input follows.\n"
        )
    return "\n".join(lines)


def extract_question(text: str) -> str | None:
    """Pull a structured question out of worker output, if present."""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(_QUESTION_SENTINEL):
            return line[len(_QUESTION_SENTINEL):].strip()
    return None
