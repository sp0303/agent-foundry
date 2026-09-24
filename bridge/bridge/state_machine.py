"""The deterministic task loop as an explicit state machine.

The bridge decides a task is finished from process exit or API status, never
from an agent remembering to call back (docs/bridge-design.md rules). This
module owns the *allowed* transitions; callers (scheduler, webhook handlers)
apply them. It contains no I/O so it is trivially testable.
"""

from __future__ import annotations

from .models import TERMINAL_STATES, TaskState, WorkingSubState

# Allowed top-level transitions. Anything not listed is rejected.
_ALLOWED: dict[TaskState, frozenset[TaskState]] = {
    TaskState.submitted: frozenset({TaskState.working, TaskState.canceled}),
    TaskState.working: frozenset(
        {
            TaskState.input_required,
            TaskState.completed,
            TaskState.failed,
            TaskState.canceled,
        }
    ),
    TaskState.input_required: frozenset({TaskState.working, TaskState.canceled}),
    # terminal states intentionally have no outgoing edges
    TaskState.completed: frozenset(),
    TaskState.failed: frozenset(),
    TaskState.canceled: frozenset(),
}

# Allowed sub-state progression while `working`. `dispatched` is the entry point.
_SUB_ORDER: list[WorkingSubState] = [
    WorkingSubState.dispatched,
    WorkingSubState.pr_open,
    WorkingSubState.ci_running,
    WorkingSubState.in_review,
    WorkingSubState.ready_to_merge,
]


class TransitionError(ValueError):
    """Raised when a caller attempts a transition that is not allowed."""


def can_transition(src: TaskState, dst: TaskState) -> bool:
    return dst in _ALLOWED.get(src, frozenset())


def assert_transition(src: TaskState, dst: TaskState) -> None:
    if not can_transition(src, dst):
        raise TransitionError(f"illegal transition {src.value} -> {dst.value}")


def is_terminal(state: TaskState) -> bool:
    return state in TERMINAL_STATES


def can_substep(src: WorkingSubState, dst: WorkingSubState) -> bool:
    """Sub-states move forward one step, or jump back to changes_requested.

    `changes_requested` can be entered from `in_review` and always returns to
    `pr_open` when the dev pushes a fix.
    """
    if dst is WorkingSubState.changes_requested:
        return src is WorkingSubState.in_review
    if src is WorkingSubState.changes_requested:
        return dst is WorkingSubState.pr_open
    try:
        return _SUB_ORDER.index(dst) == _SUB_ORDER.index(src) + 1
    except ValueError:
        return False
