"""Dispatch and drive tasks.

`dispatch_task` returns immediately with a task ID and never blocks for the whole
run (bridge-design.md, MCP server). The worker runs on a background thread; when
it finishes, the bridge — not the agent — records the outcome and advances the
state machine.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

from .adapters import registry as reg
from .config import Config
from .models import TaskContract, TaskState, WorkerResult, WorkingSubState
from .store import TaskStore
from .trace import Tracer, new_trace_id


class Scheduler:
    def __init__(
        self,
        store: TaskStore,
        config: Config,
        tracer: Tracer | None = None,
        registry: dict | None = None,
        inline: bool = False,
    ) -> None:
        self._store = store
        self._config = config
        self._tracer = tracer or Tracer()
        self._registry = registry if registry is not None else reg.build_registry(config.repo_dir)
        # `inline` runs workers synchronously — used by tests for determinism.
        self._inline = inline
        self._pool = None if inline else ThreadPoolExecutor(max_workers=4)
        self._lock = threading.Lock()

    def _submit(self, *args) -> None:
        if self._inline:
            self._run(*args)
        else:
            self._pool.submit(self._run, *args)

    def dispatch_task(self, contract: TaskContract) -> str:
        """Queue a task and return its ID immediately."""
        trace_id = new_trace_id()
        # Fail fast if we cannot even run this assignee.
        reg.resolve(self._registry, contract.assignee)  # raises NoAdapterError
        self._store.create(contract, trace_id)
        self._tracer.emit(
            trace_id, "task_submitted", task_id=contract.task_id,
            vendor=contract.assignee.vendor, harness=contract.assignee.harness,
        )
        self._submit(contract, trace_id)
        return contract.task_id

    def answer_question(self, task_id: str, answer: str) -> None:
        """Resume a task that is waiting on input_required."""
        row = self._store.get(task_id)
        if row is None:
            raise KeyError(task_id)
        if row.state is not TaskState.input_required:
            raise ValueError(f"task {task_id} is not waiting for input")
        # `_run` performs the input_required -> working transition itself, so we
        # do not pre-transition here (that would double-move to working).
        # Fold the answer into a fresh contract objective for the resumed run.
        contract = row.contract.model_copy(
            update={"objective": row.contract.objective + f"\n\n# Answer to your question\n{answer}"}
        )
        self._submit(contract, row.trace_id, row.session_id)

    def cancel_task(self, task_id: str) -> None:
        row = self._store.get(task_id)
        if row is None:
            raise KeyError(task_id)
        self._store.set_state(task_id, TaskState.canceled)
        self._tracer.emit(row.trace_id, "task_canceled", task_id=task_id)

    # --- internals --------------------------------------------------------
    def _run(self, contract: TaskContract, trace_id: str, resume_session: str | None = None) -> None:
        task_id = contract.task_id
        self._store.set_state(task_id, TaskState.working, WorkingSubState.dispatched)
        adapter = reg.resolve(self._registry, contract.assignee)
        env = self._config.base_worker_env()
        self._tracer.emit(trace_id, "worker_started", task_id=task_id)
        try:
            result = adapter.start(contract, env, resume_session)
        except Exception as e:  # never let a worker crash the loop
            self._store.set_state(task_id, TaskState.failed)
            self._tracer.emit(trace_id, "worker_crashed", task_id=task_id, error=str(e))
            return
        self._record(contract, trace_id, result)

    def _record(self, contract: TaskContract, trace_id: str, result: WorkerResult) -> None:
        task_id = contract.task_id
        if result.session_id:
            self._store.update_fields(task_id, session_id=result.session_id)
        if result.tokens_used:
            self._store.update_fields(task_id, tokens_used=result.tokens_used)
        self._tracer.emit(
            trace_id, "worker_finished", task_id=task_id,
            exit_code=result.exit_code, tokens=result.tokens_used,
        )
        if result.question is not None:
            self._store.set_state(task_id, TaskState.input_required)
            self._tracer.emit(trace_id, "question_raised", task_id=task_id, question=result.question.question)
            return
        if result.exit_code != 0:
            self._store.set_state(task_id, TaskState.failed)
            return
        # Worker exited cleanly. Real completion is confirmed later by the CI +
        # review path (webhook -> ready_to_merge -> architect). For the skeleton
        # we advance the sub-state to pr_open and wait for the webhook.
        self._store.set_substate(task_id, WorkingSubState.pr_open)
