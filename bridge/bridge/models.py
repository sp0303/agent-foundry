"""Task contract and state definitions.

These mirror the task contract in docs/bridge-design.md and borrow the A2A
task-state vocabulary so the internal protocol can later be swapped for real A2A.
"""

from __future__ import annotations

import enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskState(str, enum.Enum):
    """Top-level A2A task states (docs/bridge-design.md, "Task states")."""

    submitted = "submitted"
    working = "working"
    input_required = "input_required"
    completed = "completed"
    failed = "failed"
    canceled = "canceled"


# States from which the task can never move again.
TERMINAL_STATES: frozenset[TaskState] = frozenset(
    {TaskState.completed, TaskState.failed, TaskState.canceled}
)


class WorkingSubState(str, enum.Enum):
    """Bridge-specific sub-states that refine `working`."""

    dispatched = "dispatched"  # worker spawned, not yet pushed
    pr_open = "pr_open"
    ci_running = "ci_running"
    in_review = "in_review"
    changes_requested = "changes_requested"
    ready_to_merge = "ready_to_merge"


class Budget(BaseModel):
    max_tokens: int = Field(gt=0)
    max_minutes: int = Field(gt=0)


class Assignee(BaseModel):
    vendor: str  # "anthropic" | "openai" | "google"
    harness: str  # "claude" | "codex" | "antigravity" | "gemini"
    model: str = "from-routing-table"


class TaskContract(BaseModel):
    """The contract sent to every worker. See docs/bridge-design.md."""

    task_id: str
    title: str
    objective: str
    context_refs: list[str] = Field(default_factory=list)
    allowed_paths: list[str] = Field(default_factory=list)
    interfaces_frozen: list[str] = Field(default_factory=list)
    acceptance: list[str] = Field(default_factory=list)
    definition_of_done: list[str] = Field(default_factory=list)
    branch: str
    budget: Budget
    assignee: Assignee
    escalation: str = "exit with a question; do not guess"


class WorkerQuestion(BaseModel):
    """Structured question a worker emits instead of guessing.

    A worker that hits ambiguity must exit with one of these; the bridge then
    moves the task to `input_required` (docs/bridge-design.md rules).
    """

    task_id: str
    question: str
    context: Optional[str] = None


class WorkerResult(BaseModel):
    """What an adapter returns after a run finishes."""

    task_id: str
    exit_code: int
    session_id: Optional[str] = None  # for --resume / multi-turn
    branch_pushed: bool = False
    pr_url: Optional[str] = None
    question: Optional[WorkerQuestion] = None
    tokens_used: int = 0
    error: Optional[str] = None
