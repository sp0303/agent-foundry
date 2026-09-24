from bridge import state_machine as sm
from bridge.models import TaskState, WorkingSubState


def test_happy_path_transitions():
    assert sm.can_transition(TaskState.submitted, TaskState.working)
    assert sm.can_transition(TaskState.working, TaskState.completed)
    assert sm.can_transition(TaskState.working, TaskState.input_required)
    assert sm.can_transition(TaskState.input_required, TaskState.working)


def test_illegal_transitions_rejected():
    assert not sm.can_transition(TaskState.submitted, TaskState.completed)
    assert not sm.can_transition(TaskState.completed, TaskState.working)
    assert not sm.can_transition(TaskState.failed, TaskState.working)


def test_terminal_states_have_no_exit():
    for s in (TaskState.completed, TaskState.failed, TaskState.canceled):
        assert sm.is_terminal(s)
        for dst in TaskState:
            assert not sm.can_transition(s, dst)


def test_assert_transition_raises():
    import pytest

    with pytest.raises(sm.TransitionError):
        sm.assert_transition(TaskState.submitted, TaskState.completed)


def test_substate_progression():
    assert sm.can_substep(WorkingSubState.dispatched, WorkingSubState.pr_open)
    assert sm.can_substep(WorkingSubState.pr_open, WorkingSubState.ci_running)
    assert sm.can_substep(WorkingSubState.in_review, WorkingSubState.changes_requested)
    assert sm.can_substep(WorkingSubState.changes_requested, WorkingSubState.pr_open)


def test_substate_cannot_skip():
    assert not sm.can_substep(WorkingSubState.dispatched, WorkingSubState.in_review)
    assert not sm.can_substep(WorkingSubState.ready_to_merge, WorkingSubState.pr_open)
