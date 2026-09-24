"""SQLite task store. One row per task (docs/bridge-design.md, Components).

Postgres is a later swap; the interface here is deliberately small so that swap
stays cheap. All state changes go through `set_state`, which enforces the
state machine, so no caller can write an illegal transition.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import state_machine as sm
from .models import TaskContract, TaskState, WorkingSubState

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id      TEXT PRIMARY KEY,
    contract     TEXT NOT NULL,          -- JSON TaskContract
    state        TEXT NOT NULL,
    sub_state    TEXT,
    vendor       TEXT NOT NULL,
    session_id   TEXT,
    branch       TEXT NOT NULL,
    pr_url       TEXT,
    tokens_used  INTEGER NOT NULL DEFAULT 0,
    trace_id     TEXT NOT NULL,
    created_at   REAL NOT NULL,
    updated_at   REAL NOT NULL
);
"""


@dataclass
class TaskRow:
    task_id: str
    contract: TaskContract
    state: TaskState
    sub_state: Optional[WorkingSubState]
    vendor: str
    session_id: Optional[str]
    branch: str
    pr_url: Optional[str]
    tokens_used: int
    trace_id: str
    created_at: float
    updated_at: float


class TaskStore:
    def __init__(self, db_path: str | Path = "bridge.sqlite") -> None:
        self._path = str(db_path)
        # Workers run on background threads and the webhook runs in a threadpool,
        # so the connection is shared across threads and every access is
        # serialised by `_lock`. SQLite in WAL mode handles this fine in-process.
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # --- writes -----------------------------------------------------------
    def create(self, contract: TaskContract, trace_id: str) -> TaskRow:
        now = time.time()
        with self._lock:
            self._conn.execute(
                "INSERT INTO tasks (task_id, contract, state, sub_state, vendor, "
                "branch, trace_id, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    contract.task_id,
                    contract.model_dump_json(),
                    TaskState.submitted.value,
                    None,
                    contract.assignee.vendor,
                    contract.branch,
                    trace_id,
                    now,
                    now,
                ),
            )
            self._conn.commit()
            row = self.get(contract.task_id)
        assert row is not None
        return row

    def set_state(
        self,
        task_id: str,
        new_state: TaskState,
        sub_state: Optional[WorkingSubState] = None,
    ) -> TaskRow:
        with self._lock:
            row = self.get(task_id)
            if row is None:
                raise KeyError(task_id)
            sm.assert_transition(row.state, new_state)
            self._conn.execute(
                "UPDATE tasks SET state=?, sub_state=?, updated_at=? WHERE task_id=?",
                (
                    new_state.value,
                    sub_state.value if sub_state else None,
                    time.time(),
                    task_id,
                ),
            )
            self._conn.commit()
            updated = self.get(task_id)
        assert updated is not None
        return updated

    def set_substate(self, task_id: str, sub_state: WorkingSubState) -> TaskRow:
        with self._lock:
            row = self.get(task_id)
            if row is None:
                raise KeyError(task_id)
            if row.state is not TaskState.working:
                raise sm.TransitionError("sub-states only apply while working")
            if row.sub_state is not None and not sm.can_substep(row.sub_state, sub_state):
                raise sm.TransitionError(
                    f"illegal sub-step {row.sub_state.value} -> {sub_state.value}"
                )
            self._conn.execute(
                "UPDATE tasks SET sub_state=?, updated_at=? WHERE task_id=?",
                (sub_state.value, time.time(), task_id),
            )
            self._conn.commit()
            updated = self.get(task_id)
        assert updated is not None
        return updated

    def update_fields(self, task_id: str, **fields: object) -> None:
        allowed = {"session_id", "pr_url", "tokens_used"}
        bad = set(fields) - allowed
        if bad:
            raise ValueError(f"cannot update fields: {bad}")
        if not fields:
            return
        cols = ", ".join(f"{k}=?" for k in fields)
        with self._lock:
            self._conn.execute(
                f"UPDATE tasks SET {cols}, updated_at=? WHERE task_id=?",
                (*fields.values(), time.time(), task_id),
            )
            self._conn.commit()

    # --- reads ------------------------------------------------------------
    def get(self, task_id: str) -> Optional[TaskRow]:
        with self._lock:
            cur = self._conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,))
            r = cur.fetchone()
        return _row_to_task(r) if r else None

    def list(self, state: Optional[TaskState] = None) -> list[TaskRow]:
        with self._lock:
            if state is None:
                cur = self._conn.execute("SELECT * FROM tasks ORDER BY created_at")
            else:
                cur = self._conn.execute(
                    "SELECT * FROM tasks WHERE state=? ORDER BY created_at",
                    (state.value,),
                )
            rows = cur.fetchall()
        return [_row_to_task(r) for r in rows]

    def find_by_branch(self, branch: str) -> Optional[TaskRow]:
        with self._lock:
            cur = self._conn.execute("SELECT * FROM tasks WHERE branch=?", (branch,))
            r = cur.fetchone()
        return _row_to_task(r) if r else None


def _row_to_task(r: sqlite3.Row) -> TaskRow:
    return TaskRow(
        task_id=r["task_id"],
        contract=TaskContract.model_validate(json.loads(r["contract"])),
        state=TaskState(r["state"]),
        sub_state=WorkingSubState(r["sub_state"]) if r["sub_state"] else None,
        vendor=r["vendor"],
        session_id=r["session_id"],
        branch=r["branch"],
        pr_url=r["pr_url"],
        tokens_used=r["tokens_used"],
        trace_id=r["trace_id"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )
