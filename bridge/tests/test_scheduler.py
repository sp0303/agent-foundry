import pytest

from bridge.adapters.base import WorkerAdapter
from bridge.config import Config
from bridge.models import TaskState, WorkerQuestion, WorkerResult, WorkingSubState
from bridge.scheduler import Scheduler
from bridge.store import TaskStore
from bridge.trace import Tracer
import io


class FakeAdapter(WorkerAdapter):
    vendor = "openai"
    harness = "codex"

    def __init__(self, result: WorkerResult):
        self._result = result

    def available(self) -> bool:
        return True

    def start(self, contract, env, resume_session_id=None):
        return self._result


def _make(store, result):
    cfg = Config(db_path=store._path)
    reg = {("openai", "codex"): FakeAdapter(result)}
    tracer = Tracer(stream=io.StringIO())
    return Scheduler(store, cfg, tracer=tracer, registry=reg, inline=True)


@pytest.fixture
def store(tmp_path):
    s = TaskStore(tmp_path / "t.sqlite")
    yield s
    s.close()


def test_clean_run_reaches_pr_open(store, contract):
    result = WorkerResult(task_id="T-001", exit_code=0)
    sched = _make(store, result)
    sched.dispatch_task(contract)
    row = store.get("T-001")
    assert row.state is TaskState.working
    assert row.sub_state is WorkingSubState.pr_open


def test_worker_question_moves_to_input_required(store, contract):
    result = WorkerResult(
        task_id="T-001",
        exit_code=0,
        question=WorkerQuestion(task_id="T-001", question="which header?"),
    )
    sched = _make(store, result)
    sched.dispatch_task(contract)
    assert store.get("T-001").state is TaskState.input_required


def test_nonzero_exit_fails(store, contract):
    result = WorkerResult(task_id="T-001", exit_code=1, error="boom")
    sched = _make(store, result)
    sched.dispatch_task(contract)
    assert store.get("T-001").state is TaskState.failed


def test_answer_question_resumes(store, contract):
    q = WorkerResult(
        task_id="T-001", exit_code=0,
        question=WorkerQuestion(task_id="T-001", question="which header?"),
    )
    sched = _make(store, q)
    sched.dispatch_task(contract)
    assert store.get("T-001").state is TaskState.input_required
    # Swap the adapter to a clean result for the resume.
    sched._registry[("openai", "codex")] = FakeAdapter(
        WorkerResult(task_id="T-001", exit_code=0)
    )
    sched.answer_question("T-001", "the X-Api-Key header")
    row = store.get("T-001")
    assert row.state is TaskState.working
    assert row.sub_state is WorkingSubState.pr_open


def test_dispatch_unknown_vendor_raises(store, contract):
    from bridge.adapters.registry import NoAdapterError

    sched = _make(store, WorkerResult(task_id="T-001", exit_code=0))
    bad = contract.model_copy(update={"assignee": contract.assignee.model_copy(update={"harness": "nope"})})
    with pytest.raises(NoAdapterError):
        sched.dispatch_task(bad)
