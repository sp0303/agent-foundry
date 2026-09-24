"""Shared helper for adapters that shell out to a headless vendor CLI."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class CliRun:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool


def which(binary: str) -> Optional[str]:
    return shutil.which(binary)


def run_cli(
    argv: list[str],
    *,
    cwd: str,
    env: dict[str, str],
    timeout_seconds: int,
    stdin: Optional[str] = None,
) -> CliRun:
    """Run a CLI worker with a hard timeout.

    The timeout is the bridge's guarantee that a hung worker (e.g. the known
    `agy -p` non-TTY hang noted in the design) cannot stall the task loop.
    """
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return CliRun(proc.returncode, proc.stdout, proc.stderr, timed_out=False)
    except subprocess.TimeoutExpired as e:
        return CliRun(
            exit_code=124,
            stdout=e.stdout or "" if isinstance(e.stdout, str) else "",
            stderr=(e.stderr or "" if isinstance(e.stderr, str) else "")
            + f"\n[bridge] worker exceeded {timeout_seconds}s timeout",
            timed_out=True,
        )
