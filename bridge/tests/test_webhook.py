import hashlib
import hmac
import importlib
import json

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("BRIDGE_DB", str(tmp_path / "wh.sqlite"))
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "s3cret")
    import bridge.webhook as wh

    importlib.reload(wh)  # pick up patched env
    # Seed a task whose branch the webhook will reference.
    from bridge.models import Assignee, Budget, TaskContract

    wh._store.create(
        TaskContract(
            task_id="T-001", title="t", objective="o",
            branch="feat/T-001", budget=Budget(max_tokens=1, max_minutes=1),
            assignee=Assignee(vendor="openai", harness="codex"),
        ),
        trace_id="tr-1",
    )
    return TestClient(wh.app), "s3cret", wh


def _sig(secret, body):
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_rejects_missing_signature(client):
    c, _secret, _wh = client
    r = c.post("/webhook/github", json={}, headers={"X-GitHub-Event": "push"})
    assert r.status_code == 401


def test_rejects_bad_signature(client):
    c, _secret, _wh = client
    body = json.dumps({"ref": "refs/heads/feat/T-001"}).encode()
    r = c.post(
        "/webhook/github",
        content=body,
        headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": "sha256=deadbeef"},
    )
    assert r.status_code == 401


def test_pull_request_opened_records_pr_url(client):
    c, secret, wh = client
    payload = {
        "action": "opened",
        "pull_request": {"head": {"ref": "feat/T-001"}, "html_url": "http://x/pr/7"},
    }
    body = json.dumps(payload).encode()
    r = c.post(
        "/webhook/github",
        content=body,
        headers={"X-GitHub-Event": "pull_request", "X-Hub-Signature-256": _sig(secret, body)},
    )
    assert r.status_code == 200
    assert r.json()["task_id"] == "T-001"
    assert wh._store.get("T-001").pr_url == "http://x/pr/7"


def test_unknown_branch_is_noop(client):
    c, secret, _wh = client
    payload = {"ref": "refs/heads/feat/UNKNOWN"}
    body = json.dumps(payload).encode()
    r = c.post(
        "/webhook/github",
        content=body,
        headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": _sig(secret, body)},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "no-task"
