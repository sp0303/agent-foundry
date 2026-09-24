"""Adapter registry: pick the worker for a task's assignee.

Keyed by (vendor, harness). The scheduler asks for an adapter by the contract's
assignee and gets back a ready instance, or a clear error if that worker is not
available on this machine.
"""

from __future__ import annotations

from ..models import Assignee
from .antigravity import AntigravityAdapter
from .base import WorkerAdapter
from .claude import ClaudeAdapter
from .codex import CodexAdapter
from .gemini import GeminiAdapter


def build_registry(repo_dir: str = ".") -> dict[tuple[str, str], WorkerAdapter]:
    adapters: list[WorkerAdapter] = [
        ClaudeAdapter(repo_dir=repo_dir),
        CodexAdapter(repo_dir=repo_dir),
        AntigravityAdapter(repo_dir=repo_dir),
        GeminiAdapter(),
    ]
    return {(a.vendor, a.harness): a for a in adapters}


class NoAdapterError(RuntimeError):
    pass


def resolve(
    registry: dict[tuple[str, str], WorkerAdapter], assignee: Assignee
) -> WorkerAdapter:
    key = (assignee.vendor, assignee.harness)
    adapter = registry.get(key)
    if adapter is None:
        raise NoAdapterError(f"no adapter registered for {key}")
    if not adapter.available():
        raise NoAdapterError(
            f"adapter {key} is registered but not available on this machine"
        )
    return adapter
