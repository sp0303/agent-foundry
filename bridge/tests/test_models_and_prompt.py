import pytest
from pydantic import ValidationError

from bridge.adapters.prompt import build_worker_prompt, extract_question
from bridge.models import Budget, TaskContract


def test_budget_must_be_positive():
    with pytest.raises(ValidationError):
        Budget(max_tokens=0, max_minutes=10)


def test_contract_roundtrip(contract):
    data = contract.model_dump_json()
    again = TaskContract.model_validate_json(data)
    assert again == contract


def test_prompt_includes_rules_and_paths(contract):
    p = build_worker_prompt(contract, resuming=False)
    assert "src/middleware/**" in p
    assert "Never push to main" in p
    assert "api/openapi.yaml" in p  # frozen interface
    assert "BRIDGE_QUESTION:" in p


def test_prompt_marks_resume(contract):
    p = build_worker_prompt(contract, resuming=True)
    assert "resuming" in p.lower()


def test_extract_question():
    out = "doing work\nBRIDGE_QUESTION: which auth header carries the key?\nmore"
    assert extract_question(out) == "which auth header carries the key?"
    assert extract_question("no question here") is None
