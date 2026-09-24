"""OpenAI / Codex worker adapter.

Headless entry point:  codex exec "<prompt>"
The Codex MCP server was removed in Sep 2026, so we use the CLI (docs/bridge-design.md).
Codex is the vendor already installed on this machine, so it is the default
worker for the walking skeleton.
"""

from __future__ import annotations

from typing import Optional

from ..models import TaskContract, WorkerResult
from .base import WorkerAdapter
from .cli import run_cli, which
from .prompt import build_worker_prompt, extract_question
from ..models import WorkerQuestion


class CodexAdapter(WorkerAdapter):
    vendor = "openai"
    harness = "codex"

    def __init__(self, binary: str = "codex", repo_dir: str = ".") -> None:
        self._binary = binary
        self._repo_dir = repo_dir

    def available(self) -> bool:
        return which(self._binary) is not None

    def start(
        self,
        contract: TaskContract,
        env: dict[str, str],
        resume_session_id: Optional[str] = None,
    ) -> WorkerResult:
        prompt = build_worker_prompt(contract, resume_session_id is not None)
        # `codex exec` runs non-interactively; resume support is via the SDK and
        # is left as a follow-up (tracked in bridge/README.md).
        argv = [self._binary, "exec", prompt]
        run = run_cli(
            argv,
            cwd=self._repo_dir,
            env=env,
            timeout_seconds=contract.budget.max_minutes * 60,
        )
        question_text = extract_question(run.stdout)
        question = (
            WorkerQuestion(task_id=contract.task_id, question=question_text)
            if question_text
            else None
        )
        return WorkerResult(
            task_id=contract.task_id,
            exit_code=run.exit_code,
            question=question,
            error=run.stderr.strip() or None if run.exit_code != 0 else None,
        )
