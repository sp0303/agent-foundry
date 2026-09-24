"""Anthropic / Claude Code worker adapter.

Headless entry point:  claude -p "<prompt>" --output-format json
Resume:                claude --resume <session_id> -p "<prompt>" ...
Tools are scoped with --allowedTools to the contract's allowed_paths.
"""

from __future__ import annotations

import json
from typing import Optional

from ..models import TaskContract, WorkerResult
from .base import WorkerAdapter
from .cli import run_cli, which
from .prompt import build_worker_prompt


class ClaudeAdapter(WorkerAdapter):
    vendor = "anthropic"
    harness = "claude"

    def __init__(self, binary: str = "claude", repo_dir: str = ".") -> None:
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
        argv = [self._binary, "-p", prompt, "--output-format", "json"]
        if resume_session_id:
            argv += ["--resume", resume_session_id]

        run = run_cli(
            argv,
            cwd=self._repo_dir,
            env=env,
            timeout_seconds=contract.budget.max_minutes * 60,
        )
        return _parse(contract, run.exit_code, run.stdout, run.stderr, run.timed_out)


def _parse(
    contract: TaskContract, code: int, stdout: str, stderr: str, timed_out: bool
) -> WorkerResult:
    session_id: Optional[str] = None
    tokens = 0
    try:
        payload = json.loads(stdout)
        session_id = payload.get("session_id")
        tokens = int(payload.get("usage", {}).get("total_tokens", 0))
    except (json.JSONDecodeError, ValueError, AttributeError):
        pass
    return WorkerResult(
        task_id=contract.task_id,
        exit_code=code,
        session_id=session_id,
        tokens_used=tokens,
        error=stderr.strip() or None if code != 0 else None,
    )
