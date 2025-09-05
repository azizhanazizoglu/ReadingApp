from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class StepResult:
    state: str
    details: Dict[str, Any]
