from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict
from backend.logging_utils import log_backend


@dataclass
class ErrorState:
    counts: Dict[str, int] = field(default_factory=dict)
    limits: Dict[str, int] = field(default_factory=lambda: {
        "capture": 3,
        "mapping": 3,
        "fillNoChange": 3,
        "homeNav": 3,
        "sideMenu": 3,
        "userTaskNav": 3,
        "pageHop": 5,
        "controller": 1,
        "processData": 1,
    })


class ErrorManager:
    def __init__(self, state: ErrorState | None = None) -> None:
        self.state = state or ErrorState()

    def error_tick_and_decide(self, context: str) -> str:
        count = self.state.counts.get(context, 0) + 1
        self.state.counts[context] = count
        limit = self.state.limits.get(context, 3)
        decision = "retry" if count < limit else "abort"
        log_backend(
            "[INFO] [BE-2401] Error tick",
            code="BE-2401",
            component="ErrorManager",
            extra={"context": context, "count": count, "limit": limit, "decision": decision}
        )
        return decision
