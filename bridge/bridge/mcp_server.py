"""MCP server: the tools the architect agent calls.

Exposes dispatch_task, task_status, answer_question, list_tasks, cancel_task
(bridge-design.md, Components). dispatch_task returns an ID immediately and never
blocks for the whole run.

Run with:  python -m bridge.mcp_server   (stdio transport)
"""

from __future__ import annotations

from typing import Any, Optional

from .config import load_config
from .models import TaskContract
from .scheduler import Scheduler
from .store import TaskStore

try:
    # mcp 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:
    try:
        # mcp 1.x
        from mcp.server.fastmcp import FastMCP as _Server  # type: ignore
    except ImportError as e:  # pragma: no cover - clearer than a raw ImportError
        raise SystemExit(
            "The 'mcp' package is required to run the MCP server. "
            "Install it with: pip install -r bridge/requirements.txt"
        ) from e


_config = load_config()
_store = TaskStore(_config.db_path)
_scheduler = Scheduler(_store, _config)

mcp = _Server("agent-foundry-bridge")


@mcp.tool()
def dispatch_task(contract: dict[str, Any]) -> dict[str, str]:
    """Queue a task for a worker. Returns immediately with the task id.

    `contract` must match the task contract schema (see docs/bridge-design.md).
    """
    parsed = TaskContract.model_validate(contract)
    task_id = _scheduler.dispatch_task(parsed)
    return {"task_id": task_id, "state": "submitted"}


@mcp.tool()
def task_status(task_id: str) -> dict[str, Any]:
    """Return the current state, sub-state, branch, PR and cost of a task."""
    row = _store.get(task_id)
    if row is None:
        return {"error": f"unknown task {task_id}"}
    return {
        "task_id": row.task_id,
        "state": row.state.value,
        "sub_state": row.sub_state.value if row.sub_state else None,
        "branch": row.branch,
        "pr_url": row.pr_url,
        "tokens_used": row.tokens_used,
        "vendor": row.vendor,
    }


@mcp.tool()
def answer_question(task_id: str, answer: str) -> dict[str, str]:
    """Answer a task that is in input_required and resume it."""
    _scheduler.answer_question(task_id, answer)
    return {"task_id": task_id, "state": "working"}


@mcp.tool()
def list_tasks(state: Optional[str] = None) -> list[dict[str, Any]]:
    """List tasks, optionally filtered by top-level state."""
    from .models import TaskState

    filt = TaskState(state) if state else None
    return [
        {
            "task_id": r.task_id,
            "state": r.state.value,
            "sub_state": r.sub_state.value if r.sub_state else None,
            "vendor": r.vendor,
        }
        for r in _store.list(filt)
    ]


@mcp.tool()
def cancel_task(task_id: str) -> dict[str, str]:
    """Cancel a task."""
    _scheduler.cancel_task(task_id)
    return {"task_id": task_id, "state": "canceled"}


if __name__ == "__main__":
    mcp.run()
