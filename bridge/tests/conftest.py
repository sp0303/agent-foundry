import pytest

from bridge.models import Assignee, Budget, TaskContract


@pytest.fixture
def contract() -> TaskContract:
    return TaskContract(
        task_id="T-001",
        title="Rate-limit middleware",
        objective="Reject >60 req/min per API key with HTTP 429",
        context_refs=["api/openapi.yaml"],
        allowed_paths=["src/middleware/**", "tests/middleware/**"],
        interfaces_frozen=["api/openapi.yaml"],
        acceptance=["61st request in 60s returns 429"],
        definition_of_done=["unit tests pass", "coverage >= 85%"],
        branch="feat/T-001-rate-limit",
        budget=Budget(max_tokens=400000, max_minutes=45),
        assignee=Assignee(vendor="openai", harness="codex"),
    )
