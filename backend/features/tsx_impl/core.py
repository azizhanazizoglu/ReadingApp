from __future__ import annotations
from typing import Any, Callable, Dict, Optional, List
from pathlib import Path
import hashlib
import json
from datetime import datetime

from backend.components.ensure_inputs import EnsureInputs
from backend.components.html_capture_service import HtmlCaptureService
from backend.components.classify_page import ClassifyPage
from backend.components.navigator import Navigator
from backend.components.diff_service import DiffService
from backend.components.mapping_validator import MappingValidator
from backend.components.script_filler import ScriptFiller
from backend.components.finalization import FinalDetector, Finalizer
from backend.components.error_manager import ErrorManager, ErrorState
from backend.features.find_home_page import FindHomePage
from backend.features.map_and_fill import MapAndFill, MapFillResult
from backend.features.find_llm_home_button import FindLLMHomePageButton
from backend.features.find_llm_task_button import FindLLMTaskPageButton
from backend.logging_utils import log_backend
from backend.memory_store import memory

from .types import StepResult
from .constants import (
    PHASE_TO_HOME, PHASE_TO_TASK, PHASE_FILLING, PHASE_FINAL, NAV_LLM_MAX_TRIES
)
from .fallbacks import LLMNavigatorHelpers

class TsxCore:
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
        self.find_llm_task = FindLLMTaskPageButton()
        self.llm_helpers = LLMNavigatorHelpers(self)
        self.force_llm = False
        try:
            setattr(self.find_home, 'simulate_success', False)
        except Exception:
            pass

    def get_phase(self) -> str:
        return memory.get('tsx_phase') or PHASE_TO_HOME

    def set_phase(self, phase: str) -> None:
        prev = memory.get('tsx_phase')
        memory['tsx_phase'] = phase
        if prev != phase:
            log_backend('[INFO] [BE-3211] TsxOrchestrator phase change', code='BE-3211', component='TsxOrchestrator', extra={'from': prev, 'to': phase})

    def hard_reset(self) -> None:
        for k in ['tsx_phase', 'llm_nav_history', 'last_page_hash']:
            try:
                if k in memory:
                    del memory[k]
            except Exception:
                pass
        self.set_phase(PHASE_TO_HOME)
        log_backend('[INFO] [BE-3212] TsxOrchestrator hard reset', code='BE-3212', component='TsxOrchestrator', extra={'reset': True})

    # --- public single step orchestrator ---
    def run(self, user_command: str, html: str, ruhsat_json: Dict[str, Any], prev_html: Optional[str] = None, executed_action: Optional[str] = None, current_url: Optional[str] = None) -> StepResult:
        log_backend('[INFO] [BE-3201] TsxOrchestrator: run_step called', code='BE-3201', component='TsxOrchestrator', extra={'user_command': user_command, 'html_len': len(html) if isinstance(html, str) else 0})
        page_hash = self._hash(html)
        prev_hash_before = memory.get('last_page_hash')
        if current_url:
            memory['last_url_prev'] = memory.get('last_url')
            memory['last_url'] = current_url
        self._update_history(page_hash, executed_action, html)
        try:
            if executed_action:
                memory['last_executed_action'] = executed_action
        except Exception:
            pass
        if memory.get('tsx_phase') == PHASE_FINAL:
            self.hard_reset()
        cls = self.classifier.classify(html)
        phase = self.get_phase()
        log_backend('[INFO] [BE-3210] TsxOrchestrator phase', code='BE-3210', component='TsxOrchestrator', extra={'phase': phase})

        # Final detection
        if phase in (PHASE_FILLING, PHASE_FINAL):
            if getattr(cls, 'is_final', False) or phase == PHASE_FINAL:
                self.set_phase(PHASE_FINAL)
                return StepResult(state='final', details={'attempted_nav': False, 'llm_used': False, 'phase': PHASE_FINAL})

        if phase == PHASE_TO_HOME:
            return self._phase_home(cls, user_command, html, ruhsat_json, prev_html, executed_action, prev_hash_before, page_hash)
        if phase == PHASE_TO_TASK:
            return self._phase_task(user_command, html, ruhsat_json, prev_html, executed_action, page_hash)
        if phase == PHASE_FILLING:
            return self._phase_filling(user_command, html, ruhsat_json, prev_html, page_hash)
        return StepResult(state='unknown_phase', details={'phase': phase})

    # --- phase handlers ---
    def _phase_home(self, cls, user_command: str, html: str, ruhsat_json: Dict[str, Any], prev_html: Optional[str], executed_action: Optional[str], prev_hash_before: Optional[str], page_hash: str) -> StepResult:
        kind = getattr(cls, 'kind', None)
        if kind in ('dashboard', 'home', 'homepage') and executed_action:
            if prev_hash_before == page_hash:
                log_backend('[INFO] [BE-3216] Executed home action but DOM unchanged → not advancing phase yet', code='BE-3216', component='TsxOrchestrator', extra={'executed_action': executed_action})
            else:
                # Stricter home arrival check: no visible "home" buttons on dashboard and URL not task-like
                current_url: Optional[str] = memory.get('last_url')
                home_btns = self._count_home_buttons(html)
                url_task_like = False
                try:
                    url_l = (current_url or '').lower()
                    url_task_like = any(t in url_l for t in ('insurance-quote', '/quote', '/form'))
                except Exception:
                    pass
                ok_home = (home_btns == 0) and (not url_task_like)
                log_backend(
                    '[INFO] [BE-3216H] Home arrival check',
                    code='BE-3216H',
                    component='TsxOrchestrator',
                    extra={'dashboard_like': True, 'home_buttons_found': home_btns, 'url': current_url, 'url_task_like': url_task_like, 'ok': ok_home}
                )
                if ok_home:
                    task_actions: List[str] = []
                    try:
                        menu_plan = self.navigator.navigator_open_menu_candidates(html)
                        task_plan = self.navigator.navigator_go_to_task_candidates(user_command, html)
                        for src_plan in (menu_plan.candidates, task_plan.candidates):
                            for act in src_plan:
                                if act.selector:
                                    sel = f'css#{act.selector}'
                                    if sel not in task_actions:
                                        task_actions.append(sel)
                    except Exception:
                        pass
                    self.set_phase(PHASE_TO_TASK)
                    return StepResult(state='navigated_home', details={'success': True, 'attempts': 0, 'attempted_nav': False, 'actions': task_actions, 'llm_used': False, 'phase': PHASE_TO_TASK, 'home_achieved': True, 'executed_action': executed_action, 'dom_changed': True, 'task_actions_seeded': len(task_actions) > 0})
                else:
                    # Stay in to_home; do not advance phase yet
                    log_backend('[INFO] [BE-3216B] Home check failed; staying in to_home', code='BE-3216B', component='TsxOrchestrator', extra={'executed_action': executed_action})
        # static attempt
        r = self.find_home.run(user_command, html, max_attempts=1)
        if r.success:
            self.set_phase(PHASE_TO_TASK)
            return StepResult(state='navigated_home', details={'success': True, 'attempts': r.attempts, 'attempted_nav': True, 'actions': getattr(r, 'actions', []), 'llm_used': False, 'phase': PHASE_TO_TASK})
        return self.llm_helpers.home_llm_fallback(page_hash, html, user_command, True)

    def _phase_task(self, user_command: str, html: str, ruhsat_json: Dict[str, Any], prev_html: Optional[str], executed_action: Optional[str], page_hash: str) -> StepResult:
        mf_preview = self.map_and_fill.run(html, ruhsat_json, prev_html=prev_html, max_map_attempts=1)
        if mf_preview.mapping_valid:
            self.set_phase(PHASE_FILLING)
            return StepResult(state='navigated_task', details={'phase': PHASE_FILLING, 'mapping_ready': True})
        # no DOM change fast fallback
        try:
            task_hash = self._hash(html)
            prev_task_hash = memory.get('tsx_task_prev_hash')
            if executed_action and prev_task_hash == task_hash:
                log_backend('[INFO] [BE-3215] No DOM change after task action -> forcing LLM fallback', code='BE-3215', component='TsxOrchestrator', extra={'executed_action': executed_action})
                return self.llm_helpers.task_llm_fallback(task_hash, html, user_command)
            memory['tsx_task_prev_hash'] = task_hash
        except Exception:
            pass
        actions, task_actions, menu_actions = self._gather_task_actions(user_command, html, executed_action)
        # Write a step debug snapshot for analysis
        try:
            self._dump_step_debug(PHASE_TO_TASK, user_command, html, actions, task_actions, menu_actions, executed_action)
        except Exception:
            pass
        if actions:
            return StepResult(state='navigated_task', details={'phase': PHASE_TO_TASK, 'actions': actions, 'llm_used': False})
        return self.llm_helpers.task_llm_fallback(page_hash, html, user_command)

    def _phase_filling(self, user_command: str, html: str, ruhsat_json: Dict[str, Any], prev_html: Optional[str], page_hash: str) -> StepResult:
        mf: MapFillResult = self.map_and_fill.run(html, ruhsat_json, prev_html=prev_html)
        if mf.mapping_valid:
            if mf.is_final:
                self.set_phase(PHASE_FINAL)
                return StepResult(state='fill_complete', details={'phase': PHASE_FINAL, 'changed': mf.changed, 'is_final': True})
            return StepResult(state='fill_progress', details={'phase': PHASE_FILLING, 'changed': mf.changed, 'is_final': False})
        return self.llm_helpers.fill_llm_fallback(page_hash, html, user_command)

    # --- helpers ---
    def _gather_task_actions(self, user_command: str, html: str, executed_action: Optional[str]):
        actions: List[str] = []
        task_actions: List[str] = []
        menu_actions: List[str] = []
        try:
            if not executed_action:
                try:
                    executed_action = memory.get('last_executed_action')
                except Exception:
                    pass
            menu_plan = self.navigator.navigator_open_menu_candidates(html)
            task_plan = self.navigator.navigator_go_to_task_candidates(user_command, html)
            llm_task = self.find_llm_task.run(html, user_command).actions
            for act in menu_plan.candidates:
                if act.selector:
                    sel = f'css#{act.selector}'
                    if sel not in menu_actions:
                        menu_actions.append(sel)
            for act in task_plan.candidates:
                if act.selector:
                    sel = f'css#{act.selector}'
                    if sel not in task_actions:
                        task_actions.append(sel)
            for sel in llm_task:
                if sel not in task_actions:
                    task_actions.append(sel)
            executed_lower = (executed_action or '').lower()
            if executed_action and (self._is_menu_action(executed_lower)) and task_actions:
                filtered = [m for m in menu_actions if not ('menu' in m.lower() or 'aria-label=menu' in m.lower())]
                if len(filtered) != len(menu_actions):
                    log_backend('[INFO] [BE-3218] Suppressing repeated menu toggles', code='BE-3218', component='TsxOrchestrator', extra={'removed': len(menu_actions)-len(filtered)})
                menu_actions = filtered
            uc = (user_command or '').strip().lower()
            def score(sel: str) -> int:
                s = sel.lower(); sc = 0
                # Strongly prefer exact task text matches
                if uc and uc in s:
                    sc += 20
                # Prefer human-readable text selectors
                if 'text=' in s or ':contains(' in s or ':has-text(' in s:
                    sc += 10
                # Prefer precise attribute selectors by lov id (strong)
                if "[data-lov-id='" in s:
                    sc += 36
                # Prefer menu items when present
                if 'menuitem' in s:
                    sc += 5
                # Slight preference for button/anchor semantics
                if 'button' in s or 'a:' in s:
                    sc += 2
                # Push xpath-like selectors to the end (unsupported in runner)
                if 'xpath=' in s:
                    sc -= 20
                return -sc
            prioritized_task = sorted(task_actions, key=score)
            # As an extra guard, move any xpath entries to the very end
            if prioritized_task:
                non_xpath = [a for a in prioritized_task if 'xpath=' not in a.lower()]
                only_xpath = [a for a in prioritized_task if 'xpath=' in a.lower()]
                prioritized_task = non_xpath + only_xpath

            # Token-aware primary selection (e.g., "yeni trafik" → prefer chain Yeni then Trafik)
            tokens = [t for t in (uc.split() if uc else []) if t]
            def pick_first(pred):
                for cand in prioritized_task:
                    if pred(cand.lower()):
                        return cand
                return None
            primary_task = None
            if len(tokens) >= 2:
                t1, t2 = tokens[0], tokens[1]
                # If last action was menu → click first token (Yeni) first
                if executed_action and self._is_menu_action(executed_lower):
                    primary_task = pick_first(lambda s: (f"text={t1}" in s) or (f"'{t1}'" in s and t2 not in s)) or pick_first(lambda s: t1 in s and t2 not in s)
                # If last action already clicked first token → click second token
                if not primary_task and executed_action and (t1 in executed_lower) and (t2 not in executed_lower):
                    primary_task = pick_first(lambda s: (f"text={t2}" in s) or (f"'{t2}'" in s and t1 not in s)) or pick_first(lambda s: t2 in s and t1 not in s)
            # Default: precise lov-id or whole phrase
            if not primary_task:
                for cand in prioritized_task:
                    c = cand.lower()
                    if ("[data-lov-id='" in c) or (uc and uc in c) or ('text=' in c):
                        primary_task = cand
                        break
            menu_open_variants = [m for m in menu_actions if any(k in m.lower() for k in (
                "[data-lov-id='src/pages/dashboard.tsx:40:10']", "data-lov-name='menu", "aria-label='menu", 'lucide-menu', "button:has([data-lov-name='menu']"
            ))]
            paired: List[str] = []
            if primary_task and menu_open_variants:
                # If last action was a menu toggle, don't lead with menu again; try task first
                if executed_action and self._is_menu_action(executed_lower):
                    paired = [primary_task]
                    log_backend('[INFO] [BE-3217A] Pairing (skip menu due to prior menu click) → task', code='BE-3217A', component='TsxOrchestrator', extra={'task': primary_task})
                else:
                    # Add first viable menu open + primary task
                    paired = [menu_open_variants[0], primary_task]
                    log_backend('[INFO] [BE-3217] Pairing menu→task', code='BE-3217', component='TsxOrchestrator', extra={'menu': menu_open_variants[0], 'task': primary_task})

            # Final actions: pair first, then prioritized task, then remaining menu
            actions = []
            seen_set = set()
            def _add(x: str):
                lx = x.lower()
                if lx not in seen_set:
                    actions.append(x); seen_set.add(lx)
            for x in paired:
                _add(x)
            for x in prioritized_task:
                _add(x)
            for x in menu_actions:
                _add(x)
            if not any((user_command or '').lower() in a.lower() for a in prioritized_task) and llm_task:
                forced = [a for a in llm_task if a not in actions]
                if forced:
                    actions = forced + actions
                    log_backend('[INFO] [BE-3219] Forcing LLM task selectors to front (no direct match yet)', code='BE-3219', component='TsxOrchestrator', extra={'added': len(forced)})
            if actions:
                log_backend('[INFO] [BE-3214] TsxOrchestrator task/menu actions', code='BE-3214', component='TsxOrchestrator', extra={'count': len(actions), 'task': len(task_actions), 'menu': len(menu_actions)})
        except Exception:
            pass
        return actions, task_actions, menu_actions

    def _is_menu_action(self, action_str: str) -> bool:
        try:
            s = (action_str or '').lower()
            keys = [
                "[data-lov-id='src/pages/dashboard.tsx:40:10']",
                "aria-label='menu'",
                'aria-label="menu"',
                'button[aria-label=\'menu\']',
                'button:has([data-lov-name=\'menu\'])',
                "button:has([data-lov-name='menu'])",
                'lucide-menu',
                'open side menu',
            ]
            return any(k in s for k in keys)
        except Exception:
            return False

    def _dump_step_debug(self, phase: str, user_command: str, html: str, actions: List[str], task_actions: List[str], menu_actions: List[str], executed_action: Optional[str]) -> None:
        try:
            seq = int(memory.get('tsx_seq', 0)) + 1
            memory['tsx_seq'] = seq
            ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            last_url = memory.get('last_url')
            page_hash = self._hash(html)
            llm_props = []
            try:
                llm_props = self.find_llm_task.run(html, user_command).actions[:20]
            except Exception:
                pass
            data = {
                'seq': seq,
                'phase': phase,
                'user_command': user_command,
                'last_url': last_url,
                'page_hash': page_hash,
                'executed_action': executed_action,
                'actions': actions,
                'task_actions': task_actions,
                'menu_actions': menu_actions,
                'llm_task_sample': llm_props,
            }
            out_dir = Path(self.capture.base_dir if hasattr(self.capture, 'base_dir') else 'webbot2html') / 'tsx_debug'
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f'step_{seq:04d}_{ts}.json'
            out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            # Also dump HTML snapshot for this step for offline analysis
            try:
                html_file = out_dir / f'step_{seq:04d}_{ts}.html'
                html_file.write_text(html or '', encoding='utf-8')
                data['html_file'] = str(html_file)
                out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            except Exception:
                pass
            log_backend('[INFO] [BE-3220] Tsx debug dump', code='BE-3220', component='TsxOrchestrator', extra={'file': str(out_file), 'seq': seq})
        except Exception:
            pass

    def _hash(self, html: str) -> str:
        try:
            return hashlib.md5((html or '').encode('utf-8', errors='ignore')).hexdigest()
        except Exception:
            return str(len(html) if isinstance(html, str) else 0)

    def _update_history(self, page_hash: str, executed_action: Optional[str], html: str) -> None:
        try:
            hist_root = memory.setdefault('llm_nav_history', {})
            hist = hist_root.setdefault(page_hash, {'failed': [], 'last_proposed': [], 'tries': 0})
            prev_hash = memory.get('last_page_hash')
            if prev_hash == page_hash:
                failed: List[str] = hist.setdefault('failed', [])
                if executed_action and executed_action not in failed:
                    failed.append(executed_action)
                    hist['tries'] = int(hist.get('tries', 0)) + 1
                elif hist.get('last_proposed'):
                    for a in hist['last_proposed']:
                        if a not in failed:
                            failed.append(a)
                    hist['tries'] = int(hist.get('tries', 0)) + 1
                hist['last_proposed'] = []
            memory['last_page_hash'] = page_hash
        except Exception:
            pass

    def _count_home_buttons(self, html: str) -> int:
        """Heuristic: count visible controls that look like 'Home/Ana Sayfa' buttons.
        If count > 0, we likely are NOT on the dashboard yet.
        """
        try:
            from bs4 import BeautifulSoup as _BS
            soup = _BS(html or '', 'html.parser')
            def norm(s: str) -> str:
                return ' '.join((s or '').split()).strip().lower()
            tokens = [
                'ana sayfa', 'anasayfa', 'ana sayfaya', 'anasayfaya',
                'home', 'go home', 'back to home', 'ana sayfaya dön', 'ana sayfaya don', 'anasayfaya dön'
            ]
            cnt = 0
            for el in soup.select("a, button, [role='button']"):
                label = norm(el.get_text(' ') or '')
                if any(t in label for t in tokens):
                    cnt += 1
            return cnt
        except Exception:
            # Fallback: simple substring scan
            h = (html or '').lower()
            simple_hits = sum(h.count(t) for t in ('ana sayfa', 'anasayfa', 'home'))
            return simple_hits
