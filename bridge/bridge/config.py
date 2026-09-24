"""Bridge configuration, loaded from environment / .env.

Secrets live only here and in the worker environment the bridge builds — never
in prompts, logs or commits (AGENTS.md / bridge-design.md).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _worker_secret_env() -> dict[str, str]:
    """The subset of the environment workers are allowed to receive.

    Only API keys the workers need. Everything else is withheld so a worker
    cannot read unrelated secrets from the bridge's own environment.
    """
    keys = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY")
    return {k: os.environ[k] for k in keys if k in os.environ}


@dataclass
class Config:
    repo_dir: str = field(default_factory=lambda: os.getenv("BRIDGE_REPO_DIR", "."))
    db_path: str = field(default_factory=lambda: os.getenv("BRIDGE_DB", "bridge.sqlite"))
    github_webhook_secret: str = field(
        default_factory=lambda: os.getenv("GITHUB_WEBHOOK_SECRET", "")
    )
    max_review_rounds: int = field(
        default_factory=lambda: int(os.getenv("BRIDGE_MAX_REVIEW_ROUNDS", "3"))
    )
    worker_env: dict[str, str] = field(default_factory=_worker_secret_env)

    def base_worker_env(self) -> dict[str, str]:
        """A minimal PATH-preserving env plus the allowed secrets."""
        env = {
            k: v
            for k, v in os.environ.items()
            if k in ("PATH", "PATHEXT", "SYSTEMROOT", "HOME", "USERPROFILE", "TEMP", "TMP")
        }
        env.update(self.worker_env)
        return env


def load_config() -> Config:
    return Config()
