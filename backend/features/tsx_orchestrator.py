from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, List

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
from backend.features.find_llm_home_button import FindLLMHomePageButton
from backend.logging_utils import log_backend
from backend.memory_store import memory
from pathlib import Path
import hashlib


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
        self.find_llm_home = FindLLMHomePageButton()
        # Dev controls
        self.force_llm = False
        # Do not simulate static success by default; allow natural fallback
        try:
            setattr(self.find_home, 'simulate_success', False)
        except Exception:
            pass

    def run_step(self, user_command: str, html: str, ruhsat_json: Dict[str, Any], prev_html: Optional[str] = None, executed_action: Optional[str] = None) -> StepResult:
        log_backend("[INFO] [BE-3201] TsxOrchestrator: run_step called", code="BE-3201", component="TsxOrchestrator", extra={"user_command": user_command, "html_len": len(html) if isinstance(html, str) else 0})
        # Page hash to correlate attempts on same page across runs
        try:
            page_hash = hashlib.md5((html or "").encode("utf-8", errors="ignore")).hexdigest()
        except Exception:
            page_hash = str(len(html) if isinstance(html, str) else 0)
        try:
            hist_root = memory.setdefault('llm_nav_history', {})
            hist = hist_root.setdefault(page_hash, {"failed": [], "last_proposed": [], "tries": 0})
            prev_hash = memory.get('last_page_hash')
            # Feedback: only mark the executed action as failed (if provided) instead of whole proposal batch
            if prev_hash == page_hash:
                failed: List[str] = hist.setdefault('failed', [])
                if executed_action:
                    if executed_action not in failed:
                        failed.append(executed_action)
                    # increment tries only when the executed action failed to change DOM
                    hist['tries'] = int(hist.get('tries', 0)) + 1
                elif hist.get('last_proposed'):
                    # legacy fallback: if we don't know which one was executed, mark all
                    for a in hist['last_proposed']:
                        if a not in failed:
                            failed.append(a)
                    hist['tries'] = int(hist.get('tries', 0)) + 1
                hist['last_proposed'] = []
            # Update last seen page hash for subsequent runs
            memory['last_page_hash'] = page_hash
        except Exception:
            pass
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
                details={"changed": mf.changed, "is_final": mf.is_final, "attempts": mf.attempts, "attempted_nav": False, "llm_used": True},
            )
        if cls.is_final:
            # Note: Even if page looks final, for navigation commands (e.g., 'Yeni Trafik')
            # we still attempt static navigation first per TSX_MAIN.
            log_backend("[INFO] [BE-3203] TsxOrchestrator: page appears final, proceeding with static-first due to user command", code="BE-3203", component="TsxOrchestrator")

        # Always try static navigation first when not final, regardless of kind
        attempted_nav = True
        log_backend(
            "[INFO] [BE-3204] TsxOrchestrator: try static navigation first",
            code="BE-3204",
            component="TsxOrchestrator",
            extra={"route": "static_nav", "kind": getattr(cls, 'kind', None)},
        )
        # Static: try only once; if unchanged, fallback to LLM
        r = self.find_home.run(user_command, html, max_attempts=1)
        log_backend(
            "[INFO] [BE-3205] TsxOrchestrator: navigation result",
            code="BE-3205",
            component="TsxOrchestrator",
            extra={"success": r.success, "attempts": r.attempts},
        )
        if r.success:
            return StepResult(
                state="navigated",
                details={
                    "success": r.success,
                    "attempts": r.attempts,
                    "attempted_nav": attempted_nav,
                    "actions": getattr(r, 'actions', []),
                    "llm_used": False,
                },
            )

        # If we've already tried LLM nav suggestions 3+ times on the same DOM, skip proposing again
        try:
            hist_root = memory.get('llm_nav_history') or {}
            hist = hist_root.get(page_hash) or {}
            tries = int(hist.get('tries', 0))
        except Exception:
            tries = 0

        # Fallback A → try to propose LLM-based navigation actions (visible buttons)
        if tries >= 3:
            log_backend(
                "[INFO] [BE-3206X] TsxOrchestrator: LLM nav attempts exhausted for this page",
                code="BE-3206X",
                component="TsxOrchestrator",
                extra={"llm": True, "tries": tries}
            )
            # Do not fall back to TS2 mapping on TsX nav flow; signal navigation failure
            return StepResult(
                state="nav_failed",
                details={"attempted_nav": True, "llm_used": True, "tries": tries, "reason": "llm_nav_exhausted"},
            )
        else:
            llm_actions = self.find_llm_home.run(html, user_command).actions
            # Filter out actions already failed
            try:
                failed_set = set((memory.get('llm_nav_history') or {}).get(page_hash, {}).get('failed', []) or [])
            except Exception:
                failed_set = set()
            filtered = [a for a in llm_actions if a not in failed_set]
            if llm_actions and len(filtered) != len(llm_actions):
                log_backend(
                    "[INFO] [BE-3206F] TsxOrchestrator: filtered failed actions",
                    code="BE-3206F",
                    component="TsxOrchestrator",
                    extra={"original": len(llm_actions), "filtered": len(filtered), "failed": len(failed_set), "tries": tries, "llm": True}
                )
            if filtered:
                log_backend(
                    "[INFO] [BE-3206] TsxOrchestrator: LLM home candidates",
                    code="BE-3206",
                    component="TsxOrchestrator",
                    extra={"llm": True, "count": len(filtered), "tries": tries}
                )
                # Remember proposals for this page; if the page doesn't change on next run, we'll exclude these
                try:
                    hist_root = memory.setdefault('llm_nav_history', {})
                    hist = hist_root.setdefault(page_hash, {"failed": [], "last_proposed": [], "tries": tries})
                    hist['last_proposed'] = list(filtered)
                    memory['last_page_hash'] = page_hash
                except Exception:
                    pass
                # Return actions for FE to execute; defer mapping to next step after navigation
                return StepResult(
                    state="navigated",
                    details={
                        "attempted_nav": attempted_nav,
                        "actions": filtered,
                        "llm_used": True,
                        "tries": tries,
                    },
                )
            # If all actions are exhausted
            if llm_actions and not filtered:
                log_backend(
                    "[INFO] [BE-3206E] TsxOrchestrator: all LLM actions exhausted",
                    code="BE-3206E",
                    component="TsxOrchestrator",
                    extra={"llm": True, "failed": len(failed_set), "tries": tries}
                )
                return StepResult(
                    state="nav_failed",
                    details={"attempted_nav": attempted_nav, "llm_used": True, "reason": "all_actions_failed", "tries": tries},
                )
        # No LLM nav actions were found; treat as navigation failure for TsX
        log_backend(
            "[INFO] [BE-3208] TsxOrchestrator: no LLM nav actions; nav_failed",
            code="BE-3208",
            component="TsxOrchestrator",
            extra={"attempted_nav": attempted_nav, "fallback_reason": "no_llm_actions", "llm": True}
        )
        return StepResult(
            state="nav_failed",
            details={"attempted_nav": attempted_nav, "llm_used": True, "reason": "no_llm_actions", "tries": tries},
        )

