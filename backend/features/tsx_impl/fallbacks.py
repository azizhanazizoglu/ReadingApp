from __future__ import annotations
from typing import List, Dict, Any, TYPE_CHECKING
from backend.memory_store import memory
from backend.logging_utils import log_backend
from .types import StepResult
from .constants import PHASE_TO_HOME, PHASE_TO_TASK, PHASE_FILLING, NAV_LLM_MAX_TRIES

if TYPE_CHECKING:  # avoid circular import at runtime
    from .core import TsxCore

class LLMNavigatorHelpers:
    def __init__(self, orchestrator: 'TsxCore') -> None:
        self.o = orchestrator

    def llm_filter(self, page_hash: str, actions: List[str], tries: int) -> List[str]:
        try:
            failed_set = set((memory.get('llm_nav_history') or {}).get(page_hash, {}).get('failed', []) or [])
        except Exception:
            failed_set = set()
        filtered = [a for a in actions if a not in failed_set]
        if actions and len(filtered) != len(actions):
            log_backend(
                "[INFO] [BE-3206F] TsxOrchestrator: filtered failed actions",
                code="BE-3206F",
                component="TsxOrchestrator",
                extra={
                    "original": len(actions),
                    "filtered": len(filtered),
                    "failed": len(actions)-len(filtered),
                    "tries": tries,
                    "llm": True,
                    "failed_set_sample": list(sorted(list(failed_set)))[:5]
                }
            )
        return filtered

    def record_proposals(self, page_hash: str, proposals: List[str], tries: int) -> None:
        try:
            hist_root = memory.setdefault('llm_nav_history', {})
            hist = hist_root.setdefault(page_hash, {"failed": [], "last_proposed": [], "tries": tries})
            hist['last_proposed'] = list(proposals)
            memory['last_page_hash'] = page_hash
        except Exception:
            pass

    def home_llm_fallback(self, page_hash: str, html: str, user_command: str, attempted_nav: bool) -> StepResult:
        tries = self._tries(page_hash)
        if tries >= NAV_LLM_MAX_TRIES:
            log_backend("[INFO] [BE-3206X] TsxOrchestrator: LLM nav attempts exhausted (home)", code="BE-3206X", component="TsxOrchestrator", extra={"llm": True, "tries": tries, "max": NAV_LLM_MAX_TRIES, "phase": PHASE_TO_HOME})
            return StepResult(state="nav_failed_home", details={"attempted_nav": attempted_nav, "llm_used": True, "tries": tries, "reason": "llm_nav_exhausted", "phase": PHASE_TO_HOME})
        llm_actions = self.o.find_llm_home.run(html, user_command).actions
        filtered = self.llm_filter(page_hash, llm_actions, tries)
        if filtered:
            log_backend(
                "[INFO] [BE-3206] TsxOrchestrator: LLM home candidates",
                code="BE-3206",
                component="TsxOrchestrator",
                extra={
                    "llm": True,
                    "count": len(filtered),
                    "tries": tries,
                    "phase": PHASE_TO_HOME,
                    "proposals_sample": filtered[:3],
                    "last_executed": memory.get('last_executed_action')
                }
            )
            self.record_proposals(page_hash, filtered, tries)
            return StepResult(state="navigated_home", details={"attempted_nav": attempted_nav, "actions": filtered, "llm_used": True, "tries": tries, "phase": PHASE_TO_HOME})
        if llm_actions and not filtered:
            log_backend(
                "[INFO] [BE-3206E] TsxOrchestrator: all LLM home actions previously failed",
                code="BE-3206E",
                component="TsxOrchestrator",
                extra={"tries": tries, "phase": PHASE_TO_HOME, "last_executed": memory.get('last_executed_action')}
            )
            return StepResult(state="nav_failed_home", details={"attempted_nav": attempted_nav, "llm_used": True, "reason": "all_actions_failed", "tries": tries, "phase": PHASE_TO_HOME})
        log_backend("[INFO] [BE-3208] TsxOrchestrator: no LLM nav actions (home)", code="BE-3208", component="TsxOrchestrator", extra={"attempted_nav": attempted_nav, "phase": PHASE_TO_HOME, "llm": True})
        return StepResult(state="nav_failed_home", details={"attempted_nav": attempted_nav, "llm_used": True, "reason": "no_llm_actions", "tries": tries, "phase": PHASE_TO_HOME})

    def task_llm_fallback(self, page_hash: str, html: str, user_command: str) -> StepResult:
        tries = self._tries(page_hash)
        if tries >= NAV_LLM_MAX_TRIES:
            return StepResult(state="nav_failed_task", details={"llm_used": True, "tries": tries, "max": NAV_LLM_MAX_TRIES, "reason": "llm_nav_exhausted", "phase": PHASE_TO_TASK})
        # Use task-specific LLM finder
        llm_actions = self.o.find_llm_task.run(html, user_command).actions
        filtered = self.llm_filter(page_hash, llm_actions, tries)
        if filtered:
            log_backend(
                "[INFO] [BE-3206T] TsxOrchestrator: LLM task candidates",
                code="BE-3206T",
                component="TsxOrchestrator",
                extra={
                    "llm": True,
                    "count": len(filtered),
                    "tries": tries,
                    "phase": PHASE_TO_TASK,
                    "proposals_sample": filtered[:4],
                    "failed_so_far": len((memory.get('llm_nav_history') or {}).get(page_hash, {}).get('failed', []) or []),
                    "last_executed": memory.get('last_executed_action')
                }
            )
            self.record_proposals(page_hash, filtered, tries)
            return StepResult(state="navigated_task", details={"phase": PHASE_TO_TASK, "actions": filtered, "llm_used": True, "tries": tries})
        if llm_actions and not filtered:
            log_backend(
                "[INFO] [BE-3206E] TsxOrchestrator: all LLM task actions previously failed",
                code="BE-3206E",
                component="TsxOrchestrator",
                extra={"tries": tries, "phase": PHASE_TO_TASK, "last_executed": memory.get('last_executed_action')}
            )
            return StepResult(state="nav_failed_task", details={"phase": PHASE_TO_TASK, "llm_used": True, "reason": "all_actions_failed", "tries": tries})
        return StepResult(state="nav_failed_task", details={"phase": PHASE_TO_TASK, "llm_used": True, "reason": "no_llm_actions", "tries": tries})

    def fill_llm_fallback(self, page_hash: str, html: str, user_command: str) -> StepResult:
        assist = self.task_llm_fallback(page_hash, html, user_command)
        if assist.state.startswith("nav_failed"):
            return StepResult(state="fill_failed", details={"phase": PHASE_FILLING, "reason": assist.details.get('reason'), "tries": assist.details.get('tries')})
        return StepResult(state="fill_nav", details={"phase": PHASE_FILLING, **assist.details})

    def _tries(self, page_hash: str) -> int:
        try:
            hist_root = memory.get('llm_nav_history') or {}
            hist = hist_root.get(page_hash) or {}
            return int(hist.get('tries', 0))
        except Exception:
            return 0
