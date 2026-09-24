"""Google / Antigravity CLI worker adapter — UNVERIFIED.

The design doc flags that `agy -p` has been reported to hang in non-TTY
subprocesses and says to check current docs. We therefore:
  * mark this adapter unavailable unless an `agy` binary is actually found, and
  * always run under a hard timeout so a hang cannot stall the loop.

Prefer GeminiAdapter (the API path) until the CLI's headless behaviour is
verified on this machine. Do not trust this in production without a test run.
"""

from __future__ import annotations

from typing import Optional

from ..models import TaskContract, WorkerResult
from .base import WorkerAdapter
from .cli import run_cli, which
from .prompt import build_worker_prompt


class AntigravityAdapter(WorkerAdapter):
    vendor = "google"
    harness = "antigravity"

    def __init__(self, binary: str = "agy", repo_dir: str = ".") -> None:
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
        if not self.available():
            return WorkerResult(
                task_id=contract.task_id,
                exit_code=127,
                error=f"'{self._binary}' not found; install Antigravity CLI or use GeminiAdapter",
            )
        prompt = build_worker_prompt(contract, resume_session_id is not None)
        argv = [self._binary, "-p", prompt, "--output-format", "json"]
        # TODO: run under a pseudo-terminal (pty) to work around the -p hang.
        run = run_cli(
            argv,
            cwd=self._repo_dir,
            env=env,
            timeout_seconds=contract.budget.max_minutes * 60,
        )
        err = run.stderr.strip() or None
        if run.timed_out:
            err = (err or "") + " (likely the known non-TTY hang; needs a pty)"
        return WorkerResult(
            task_id=contract.task_id,
            exit_code=run.exit_code,
            error=err if run.exit_code != 0 else None,
        )
