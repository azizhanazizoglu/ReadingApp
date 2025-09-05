from __future__ import annotations
from typing import Any, Callable, Dict, Optional
from backend.features.tsx_impl.core import TsxCore
from backend.features.tsx_impl.types import StepResult

class TsxOrchestrator:
    """Thin facade preserving original import path; delegates all logic to TsxCore."""
    def __init__(self, map_form_fields_llm: Callable[[str, Dict[str, Any]], Dict[str, Any]], analyze_selectors: Callable[[str, Dict[str, Any]], Dict[str, int]], workspace_tmp: Optional[str] = None) -> None:
        self._core = TsxCore(map_form_fields_llm, analyze_selectors, workspace_tmp)

    def run_step(
        self,
        user_command: str,
        html: str,
        ruhsat_json: Dict[str, Any],
        prev_html: Optional[str] = None,
        executed_action: Optional[str] = None,
        current_url: Optional[str] = None,
    ) -> StepResult:
        return self._core.run(
            user_command,
            html,
            ruhsat_json,
            prev_html=prev_html,
            executed_action=executed_action,
            current_url=current_url,
        )

    def _hard_reset(self) -> None:
        self._core.hard_reset()

