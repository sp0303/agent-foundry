"""Google / Gemini API worker adapter (the reliable Google path).

Uses the Gemini API (google-genai) rather than a headless IDE CLI. The design
doc lists the Interactions API with background=True and polling; the google-genai
SDK is imported lazily so the rest of the bridge runs without it installed.

This is a skeleton: it proves the shape (build prompt -> call model -> result).
Turning a model response into an actual branch+PR is done by a code-execution
tool loop, tracked as a follow-up in bridge/README.md.
"""

from __future__ import annotations

from typing import Optional

from ..models import TaskContract, WorkerResult
from .base import WorkerAdapter
from .prompt import build_worker_prompt


class GeminiAdapter(WorkerAdapter):
    vendor = "google"
    harness = "gemini"

    def __init__(self, model: str = "gemini-2.5-pro", api_key_env: str = "GEMINI_API_KEY") -> None:
        self._model = model
        self._api_key_env = api_key_env

    def available(self) -> bool:
        try:
            import google.genai  # noqa: F401
        except ImportError:
            return False
        return True

    def start(
        self,
        contract: TaskContract,
        env: dict[str, str],
        resume_session_id: Optional[str] = None,
    ) -> WorkerResult:
        api_key = env.get(self._api_key_env)
        if not api_key:
            return WorkerResult(
                task_id=contract.task_id,
                exit_code=2,
                error=f"{self._api_key_env} not set in worker env",
            )
        try:
            from google import genai
        except ImportError:
            return WorkerResult(
                task_id=contract.task_id,
                exit_code=127,
                error="google-genai not installed (pip install google-genai)",
            )

        client = genai.Client(api_key=api_key)
        prompt = build_worker_prompt(contract, resume_session_id is not None)
        try:
            resp = client.models.generate_content(model=self._model, contents=prompt)
        except Exception as e:  # network/quota/etc. — report, never crash the loop
            return WorkerResult(
                task_id=contract.task_id, exit_code=1, error=f"{type(e).__name__}: {e}"
            )
        usage = getattr(resp, "usage_metadata", None)
        tokens = getattr(usage, "total_token_count", 0) if usage else 0
        return WorkerResult(
            task_id=contract.task_id,
            exit_code=0,
            session_id=resume_session_id,
            tokens_used=int(tokens or 0),
        )
