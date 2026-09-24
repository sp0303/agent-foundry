import pytest

from bridge import state_machine as sm
from bridge.models import TaskState, WorkingSubState
from bridge.store import TaskStore


@pytest.fixture
def store(tmp_path):
    s = TaskStore(tmp_path / "t.sqlite")
    yield s
    s.close()


def test_create_and_get(store, contract):
    row = store.create(contract, trace_id="tr-abc")
    assert row.state is TaskState.submitted
    assert row.branch == contract.branch
    fetched = store.get("T-001")
    assert fetched is not None
    assert fetched.contract.objective == contract.objective


def test_set_state_enforces_machine(store, contract):
    store.create(contract, trace_id="tr-abc")
    store.set_state("T-001", TaskState.working, WorkingSubState.dispatched)
    with pytest.raises(sm.TransitionError):
        store.set_state("T-001", TaskState.submitted)  # illegal


def test_substate_requires_working(store, contract):
    store.create(contract, trace_id="tr-abc")
    with pytest.raises(sm.TransitionError):
        store.set_substate("T-001", WorkingSubState.pr_open)  # still submitted


def test_find_by_branch(store, contract):
    store.create(contract, trace_id="tr-abc")
    row = store.find_by_branch("feat/T-001-rate-limit")
    assert row is not None and row.task_id == "T-001"


def test_update_fields_whitelist(store, contract):
    store.create(contract, trace_id="tr-abc")
    store.update_fields("T-001", pr_url="http://x/pr/1", tokens_used=1234)
    row = store.get("T-001")
    assert row.pr_url == "http://x/pr/1"
    assert row.tokens_used == 1234
    with pytest.raises(ValueError):
        store.update_fields("T-001", state="hacked")


def test_list_filters_by_state(store, contract):
    store.create(contract, trace_id="tr-abc")
    assert len(store.list(TaskState.submitted)) == 1
    assert len(store.list(TaskState.completed)) == 0
