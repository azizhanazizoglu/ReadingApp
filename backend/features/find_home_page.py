from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from backend.components.navigator import Navigator
from backend.components.diff_service import DiffService
from backend.components.html_capture_service import HtmlCaptureService
from backend.components.error_manager import ErrorManager, ErrorState
from backend.logging_utils import log_backend


@dataclass
class FindResult:
    success: bool
    attempts: int
    actions: List[str]


class FindHomePage:
    def __init__(self, navigator: Navigator, diff: DiffService, capture: HtmlCaptureService, errors: Optional[ErrorManager] = None) -> None:
        self.navigator = navigator
        self.diff = diff
        self.capture = capture
        self.errors = errors or ErrorManager(ErrorState())
        # Dev: allow toggling simulation of success; default False so fallback can occur naturally
        self.simulate_success = False

    def run(self, user_command: str, html_before: str, max_attempts: int = 3) -> FindResult:
        try:
            log_backend(
                "[INFO] [BE-2700] FindHomePage start",
                code="BE-2700",
                component="FindHomePage",
                extra={"user_command": user_command, "html_len": len(html_before) if isinstance(html_before, str) else 0, "max_attempts": max_attempts}
            )
        except Exception:
            pass
        attempts = 0
        prev = html_before
        actions: List[str] = []
        while attempts < max_attempts:
            attempts += 1
            log_backend(
                "[INFO] [BE-270A] FindHomePage attempt",
                code="BE-270A",
                component="FindHomePage",
                extra={"attempt": attempts}
            )
            # Emit candidates: explicit Home first, then menu and user task
            home_plan = self.navigator.navigator_home_candidates(prev)
            menu_plan = self.navigator.navigator_open_menu_candidates(prev)
            task_plan = self.navigator.navigator_go_to_task_candidates(user_command, prev)
            # Build action list in deterministic order
            for act in home_plan.candidates:
                if act.selector:
                    actions.append(f"css#{act.selector}")
            for act in menu_plan.candidates:
                if act.selector:
                    actions.append(f"css#{act.selector}")
            for act in task_plan.candidates:
                if act.selector:
                    actions.append(f"css#{act.selector}")
            # Try direct 'Ana Sayfa' button/link first if present
            try:
                from bs4 import BeautifulSoup as _BS
                _soup = _BS(prev or "", "html.parser")
                def _norm(s: str) -> str:
                    return " ".join((s or "").split()).strip().lower()
                home_btn = None
                for tag in _soup.select("a, button, [role='button']"):
                    txt = _norm(tag.get_text(" "))
                    if txt == _norm("Ana Sayfa"):
                        home_btn = tag
                        break
                if home_btn is not None and 'click#Ana Sayfa' not in actions:
                    actions.append('click#Ana Sayfa')
                # Also try to find the task by user_command text directly
                ulabel = _norm(user_command or '')
                if ulabel:
                    task_btn = None
                    for tag in _soup.select("a, button, [role='button']"):
                        txt = _norm(tag.get_text(" "))
                        if txt == ulabel:
                            task_btn = tag
                            break
                    if task_btn is not None:
                        act = f"click#{user_command}"
                        if act not in actions:
                            actions.append(act)
            except Exception:
                pass
            # Assume a click happened and capture new html (in prod, TS3 executes)
            # For testability, mimic a change only when simulate_success is True.
            if getattr(self, 'simulate_success', True):
                simulated_new_html = prev + f"<!--attempt:{attempts}-->"
            else:
                simulated_new_html = prev  # no change => forces fallback path
            diff_res = self.diff.diff(prev, simulated_new_html)
            log_backend(
                "[INFO] [BE-270B] FindHomePage actions",
                code="BE-270B",
                component="FindHomePage",
                extra={"attempt": attempts, "actions_len": len(actions)}
            )
            if diff_res.changed:
                self.capture.persist_html(simulated_new_html, name=f"after_nav_{attempts}")
                log_backend("[INFO] [BE-2701] FindHomePage success", code="BE-2701", component="FindHomePage", extra={"attempts": attempts})
                return FindResult(success=True, attempts=attempts, actions=actions)
            # else tick error
            if self.errors.error_tick_and_decide("homeNav") == "abort":
                log_backend("[WARN] [BE-2702] FindHomePage abort", code="BE-2702", component="FindHomePage", extra={"attempts": attempts})
                break
            prev = simulated_new_html
        log_backend(
            "[INFO] [BE-270C] FindHomePage fallback to LLM",
            code="BE-270C",
            component="FindHomePage",
            extra={"attempts": attempts, "llm": True}
        )
        return FindResult(success=False, attempts=attempts, actions=actions)
