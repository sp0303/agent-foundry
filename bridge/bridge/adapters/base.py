"""Worker adapter interface.

One adapter per vendor. Each starts a headless run from a task contract, waits
for the process/API to finish, and reports a WorkerResult. The bridge — never
the agent — decides the task is done from that result (docs/bridge-design.md).

Adapters must NOT put secrets in prompts; secrets are injected into the child
environment by the caller and referenced by the worker, per the design's rules.
"""

from __future__ import annotations

import abc
from typing import Optional

from ..models import TaskContract, WorkerResult


class WorkerAdapter(abc.ABC):
    """Base class for all vendor workers."""

    #: vendor key, e.g. "anthropic" | "openai" | "google"
    vendor: str = ""
    #: harness key, e.g. "claude" | "codex" | "antigravity" | "gemini"
    harness: str = ""

    @abc.abstractmethod
    def start(
        self,
        contract: TaskContract,
        env: dict[str, str],
        resume_session_id: Optional[str] = None,
    ) -> WorkerResult:
        """Run the task to a natural stopping point and report the result.

        `resume_session_id` continues a prior run (answering a question or
        applying review feedback). Implementations must enforce the contract's
        budget with a hard timeout so a hung worker cannot block the loop.
        """
        raise NotImplementedError

    def available(self) -> bool:
        """Whether this adapter's CLI/API is usable on this machine right now."""
        return True
