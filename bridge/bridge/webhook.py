"""GitHub webhook receiver.

Signature-verified `pull_request`, `push` and `check_suite` events drive the
task loop's sub-states (bridge-design.md). This module verifies the HMAC and
maps events onto store transitions; the review/merge decisions themselves are
made by LLM agents elsewhere and are out of scope for this receiver.

Run with:  uvicorn bridge.webhook:app --port 8000
"""

from __future__ import annotations

import hashlib
import hmac

from fastapi import FastAPI, Header, HTTPException, Request

from .config import load_config
from .models import WorkingSubState
from .store import TaskStore

_config = load_config()
_store = TaskStore(_config.db_path)

app = FastAPI(title="agent-foundry bridge webhook")


def _verify(secret: str, body: bytes, signature: str | None) -> bool:
    if not secret:
        # No secret configured: refuse rather than accept unverified events.
        return False
    if not signature or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str | None = Header(default=None),
) -> dict[str, str]:
    body = await request.body()
    if not _verify(_config.github_webhook_secret, body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="bad or missing signature")

    payload = await request.json()
    handler = {
        "pull_request": _on_pull_request,
        "check_suite": _on_check_suite,
        "push": _on_push,
    }.get(x_github_event)
    if handler is None:
        return {"status": "ignored", "event": x_github_event}
    return handler(payload)


def _branch_task(branch: str):
    return _store.find_by_branch(branch)


def _on_pull_request(payload: dict) -> dict[str, str]:
    action = payload.get("action")
    branch = payload.get("pull_request", {}).get("head", {}).get("ref", "")
    row = _branch_task(branch)
    if row is None:
        return {"status": "no-task", "branch": branch}
    if action == "opened":
        pr_url = payload.get("pull_request", {}).get("html_url")
        if pr_url:
            _store.update_fields(row.task_id, pr_url=pr_url)
        return {"status": "ok", "task_id": row.task_id, "sub_state": "pr_open"}
    return {"status": "ok", "task_id": row.task_id, "action": action or ""}


def _on_check_suite(payload: dict) -> dict[str, str]:
    suite = payload.get("check_suite", {})
    branch = suite.get("head_branch", "")
    row = _branch_task(branch)
    if row is None:
        return {"status": "no-task", "branch": branch}
    if suite.get("status") == "completed":
        # green CI advances toward review; red is handled by the review path.
        try:
            _store.set_substate(row.task_id, WorkingSubState.ci_running)
        except Exception:
            pass
    return {"status": "ok", "task_id": row.task_id, "conclusion": suite.get("conclusion", "")}


def _on_push(payload: dict) -> dict[str, str]:
    ref = payload.get("ref", "")
    branch = ref.removeprefix("refs/heads/")
    row = _branch_task(branch)
    if row is None:
        return {"status": "no-task", "branch": branch}
    return {"status": "ok", "task_id": row.task_id}
