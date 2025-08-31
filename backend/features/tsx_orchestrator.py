from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from backend.components.ensure_inputs import EnsureInputs
from backend.components.html_capture_service import HtmlCaptureService
from backend.components.classify_page import ClassifyPage
from backend.components.types import PageKind
from backend.components.navigator import Navigator
from backend.components.diff_service import DiffService
from backend.components.mapping_validator import MappingValidator
from backend.components.script_filler import ScriptFiller
from backend.components.finalization import FinalDetector, Finalizer
from backend.components.error_manager import ErrorManager, ErrorState
from backend.features.find_home_page import FindHomePage
from backend.features.map_and_fill import MapAndFill, MapFillResult
from backend.logging_utils import log_backend


@dataclass
class StepResult:
    state: str
    details: Dict[str, Any]


class TsxOrchestrator:
    def __init__(
        self,
        map_form_fields_llm: Callable[[str, Dict[str, Any]], Dict[str, Any]],
        analyze_selectors: Callable[[str, Dict[str, Any]], Dict[str, int]],
        workspace_tmp: Optional[str] = None,
    ) -> None:
        self.ensure = EnsureInputs()
        self.capture = HtmlCaptureService(Path(workspace_tmp) if workspace_tmp else Path("webbot2html"))
        self.classifier = ClassifyPage()
        self.navigator = Navigator()
        self.diff = DiffService()
        self.validator = MappingValidator(analyze_selectors)
        self.filler = ScriptFiller()
        self.final_detector = FinalDetector()
        self.finalizer = Finalizer()
        self.errors = ErrorManager(ErrorState())
        self.find_home = FindHomePage(self.navigator, self.diff, self.capture, self.errors)
        self.map_and_fill = MapAndFill(map_form_fields_llm, self.validator, self.filler, self.diff, self.final_detector, self.finalizer, self.errors)
        # Dev controls
        self.force_llm: bool = False
        # Whether to simulate static nav success inside FindHomePage (dev)
        try:
            setattr(self.find_home, 'simulate_success', True)
        except Exception:
            pass

    def run_step(self, user_command: str, html: str, ruhsat_json: Dict[str, Any], prev_html: Optional[str] = None) -> StepResult:
        log_backend("[INFO] [BE-3201] TsxOrchestrator: run_step called", code="BE-3201", component="TsxOrchestrator", extra={"user_command": user_command, "html_len": len(html) if isinstance(html, str) else 0})
        cls = self.classifier.classify(html)
        log_backend("[INFO] [BE-3202] TsxOrchestrator: page classified", code="BE-3202", component="TsxOrchestrator", extra={"kind": getattr(cls, 'kind', None), "is_final": getattr(cls, 'is_final', False)})
        # Forced LLM fallback (dev)
        if getattr(self, 'force_llm', False):
            log_backend("[INFO] [BE-3207] TsxOrchestrator: forced fallback to LLM (dev)", code="BE-3207", component="TsxOrchestrator", extra={"llm": True})
            mf: MapFillResult = self.map_and_fill.run(html, ruhsat_json, prev_html=prev_html)
            log_backend(
                "[INFO] [BE-3209] TsxOrchestrator: MapAndFill result",
                code="BE-3209",
                component="TsxOrchestrator",
                extra={"mapping_valid": mf.mapping_valid, "changed": mf.changed, "is_final": mf.is_final, "attempts": mf.attempts, "llm": True}
            )
            return StepResult(
                state="mapped" if mf.mapping_valid else "mapping_failed",
                details={"changed": mf.changed, "is_final": mf.is_final, "attempts": mf.attempts, "attempted_nav": False},
            )
        if cls.is_final:
            # Note: Even if page looks final, for navigation commands (e.g., 'Yeni Trafik')
            # we still attempt static navigation first per TSX_MAIN.
            log_backend("[INFO] [BE-3203] TsxOrchestrator: page appears final, proceeding with static-first due to user command", code="BE-3203", component="TsxOrchestrator")

        # Always try static navigation first when not final, regardless of kind
        attempted_nav = True
        log_backend("[INFO] [BE-3204] TsxOrchestrator: try static navigation first", code="BE-3204", component="TsxOrchestrator", extra={"route": "static_nav", "kind": getattr(cls, 'kind', None)})
        r = self.find_home.run(user_command, html)
        log_backend("[INFO] [BE-3205] TsxOrchestrator: navigation result", code="BE-3205", component="TsxOrchestrator", extra={"success": r.success, "attempts": r.attempts})
        if r.success:
            return StepResult(state="navigated", details={"success": r.success, "attempts": r.attempts, "attempted_nav": attempted_nav, "actions": getattr(r, 'actions', [])})

        # Fallback → try map and fill (LLM mapping path)
        log_backend(
            "[INFO] [BE-3208] TsxOrchestrator: falling back to MapAndFill",
            code="BE-3208",
            component="TsxOrchestrator",
            extra={"attempted_nav": attempted_nav, "fallback_reason": "static_nav_exhausted", "llm": True}
        )
        mf: MapFillResult = self.map_and_fill.run(html, ruhsat_json, prev_html=prev_html)
        log_backend(
            "[INFO] [BE-3209] TsxOrchestrator: MapAndFill result",
            code="BE-3209",
            component="TsxOrchestrator",
            extra={"mapping_valid": mf.mapping_valid, "changed": mf.changed, "is_final": mf.is_final, "attempts": mf.attempts, "llm": True}
        )
        return StepResult(
            state="mapped" if mf.mapping_valid else "mapping_failed",
            details={"changed": mf.changed, "is_final": mf.is_final, "attempts": mf.attempts, "attempted_nav": attempted_nav},
        )

from pathlib import Path  # keep import at end to minimize top clutter
