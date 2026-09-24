"""Structured trace logging: one trace ID per user request, cost per agent.

Deliberately tiny (stdlib only). Emits JSON lines so a later log pipeline can
aggregate cost by trace, task and vendor without reparsing prose.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from typing import Any, TextIO


def new_trace_id() -> str:
    return "tr-" + uuid.uuid4().hex[:12]


class Tracer:
    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream or sys.stdout

    def emit(self, trace_id: str, event: str, **fields: Any) -> None:
        record = {"ts": round(time.time(), 3), "trace_id": trace_id, "event": event}
        record.update(fields)
        self._stream.write(json.dumps(record) + "\n")
        self._stream.flush()
