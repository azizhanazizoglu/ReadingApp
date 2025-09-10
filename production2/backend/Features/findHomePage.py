"""FindHomePage feature (production2)

Minimal dev helper to integrate with getHtml component and test HTML capture.
Later, expand with Navigator/Diff/LLM orchestration.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path as _Path
from dataclasses import asdict
import json
import sys

from Components.getHtml import get_save_Html, get_Html, filter_Html
from Components.mappingStatic import map_home_page_static
from Components.fillPageFromMapping import fill_and_go
from Components.detectWepPageChange import detect_web_page_change
from Components.letLLMMap import def_let_llm_map
import time
from config import (  # type: ignore
    get_llm_prompt_find_home_page_default,
    get_llm_max_attempts_find_home_page,
    get_static_max_candidates_find_home_page,
)
from logging_utils import log

# Ensure project root (production2) is importable for memory access
_this = _Path(__file__).resolve()
_root = _this.parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from memory import HtmlCaptureResult  # type: ignore


def FindHomePage(
    html: str,
    name: Optional[str] = None,
    debug: bool = False,
    # MANDATORY op: 'allPlanHomePageCandidates' | 'planCheckHtmlIfChanged' | 'planLetLLMMap'
    op: str = "allPlanHomePageCandidates",
    clean_tmp: bool = False,
    save_on_nochange: bool = False,
    save_label: Optional[str] = None,
    # Preferred from UI: raw HTMLs; backend will filter for detection
    prev_html: Optional[str] = None,
    current_html: Optional[str] = None,
    # Back-compat: already-filtered HTMLs (legacy callers)
    prev_filtered_html: Optional[str] = None,
    current_filtered_html: Optional[str] = None,
    wait_ms: int = 200,
    # LLM planning
    llm_feedback: Optional[str] = None,
    llm_attempt_index: Optional[int] = None,
) -> Dict[str, Any]:
    """Stateless: compute mapping from in-memory HTML; save to tmp only for debug.

    Flow:
    - Normalize raw HTML -> filter in-memory -> build mapping (no disk dependency)
    - Additionally save filtered snapshot under tmp/html for debugging (optional)
    """
    # In-memory processing (stateless)
    # Planning: compute mapping and ordered candidate selectors from CURRENT page
    # (UI will use these to try clicks in order until a change is detected.)
    raw_res = get_Html(html)
    f_res = filter_Html(raw_res.html)
    mapping = map_home_page_static(f_res.html, name="findHome_mapping")
    try:
        cnt_candidates = len(getattr(mapping, "candidates", []) or [])
    except Exception:
        cnt_candidates = 0
    log("DEBUG", "F1-MAP", f"filtered_len={len(f_res.html or '')} candidates={cnt_candidates}", component="FindHomePage", extra={"op": op})

    # Optional: persist snapshots for debugging/inspection
    cap_raw: Optional[HtmlCaptureResult] = None
    cap_filtered: Optional[HtmlCaptureResult] = None
    if debug:
        try:
            # Optionally clean tmp folder for fresh session
            if clean_tmp:
                # Attempt to clear tmp dir under Components.getHtml default path; ignore errors
                tmp_dir = _root / "tmp" / "html"
                if tmp_dir.exists():
                    for p in tmp_dir.glob("*"):
                        try:
                            if p.is_file() or p.is_symlink():
                                p.unlink(missing_ok=True)  # type: ignore[arg-type]
                            elif p.is_dir():
                                # Shallow remove (no recursion expected), else skip
                                for c in p.glob("*"):
                                    try:
                                        if c.is_file() or c.is_symlink():
                                            c.unlink(missing_ok=True)  # type: ignore[arg-type]
                                    except Exception:
                                        pass
                                try:
                                    p.rmdir()
                                except Exception:
                                    pass
                        except Exception:
                            pass
                else:
                    try:
                        tmp_dir.mkdir(parents=True, exist_ok=True)
                    except Exception:
                        pass
        except Exception:
            pass
        # Save initial snapshots with a friendly label when provided
        cap_raw = get_save_Html(html, stage="nonfiltered", name=(save_label or name))
        cap_filtered = get_save_Html(f_res, stage="filtered", name=(save_label or name))
        # Optional debug prints
        print(f"[FindHomePage] saved nonfiltered -> {cap_raw.html_path}")
        print(f"[FindHomePage] saved filtered    -> {cap_filtered.html_path}")

    # Build an ordered list of selectors exactly as delivered:
    # 1) primary selector (if any)
    # 2) all alternatives from mapping in given order
    # 3) for each candidate: all css selectors in order, then all heuristic selectors in order
    candidate_selectors_in_order: list[str] = []
    try:
        primary = (mapping.mapping.primary_selector or "").strip()
        if primary:
            candidate_selectors_in_order.append(primary)
        # alternatives
        alts = getattr(mapping.mapping, "alternatives", []) or []
        candidate_selectors_in_order.extend([s for s in alts if isinstance(s, str)])
    except Exception:
        pass

    try:
        for cand in getattr(mapping, "candidates", []) or []:
            sels = getattr(cand, "selectors", {}) or {}
            css_list = sels.get("css") or []
            heur_list = sels.get("heuristic") or []
            candidate_selectors_in_order.extend([s for s in css_list if isinstance(s, str)])
            candidate_selectors_in_order.extend([s for s in heur_list if isinstance(s, str)])
    except Exception:
        pass

    # Cap how many static selectors we expose, configurable via config
    try:
        static_cap = int(get_static_max_candidates_find_home_page())
    except Exception:
        static_cap = 40
    if static_cap and static_cap > 0:
        candidate_selectors_in_order = candidate_selectors_in_order[:static_cap]
    log("DEBUG", "F1-STATIC-LIMIT", f"exposing_selectors={len(candidate_selectors_in_order)} cap={static_cap}", component="FindHomePage")

    # Build plans for all selectors in order (UI tries sequentially until page changes)
    all_candidate_plans: list[Dict[str, Any]] = []
    for sel in candidate_selectors_in_order:
        p = fill_and_go(mapping={}, action_button_selector=sel)
        # Ensure actions are present (ordered) in the plan dict
        plan_dict = asdict(p)
        all_candidate_plans.append({"selector": sel, "plan": plan_dict})

    # Detection: Only when UI provides prev/current snapshots.
    # UI sends RAW HTMLs (preferred); backend filters both via filter_Html and compares.
    # Frontend never filters.
    changed_info: Dict[str, Any] | None = None
    # Normalize detection inputs
    det_prev_filtered: Optional[str] = None
    det_curr_filtered: Optional[str] = None
    if prev_html is not None and current_html is not None:
        # Filter the raw inputs internally
        try:
            det_prev_filtered = filter_Html(prev_html).html
            det_curr_filtered = filter_Html(current_html).html
        except Exception:
            det_prev_filtered = prev_html
            det_curr_filtered = current_html
    elif prev_filtered_html is not None and current_filtered_html is not None:
        det_prev_filtered = prev_filtered_html
        det_curr_filtered = current_filtered_html

    if det_prev_filtered is not None and det_curr_filtered is not None:
        if wait_ms and wait_ms > 0:
            time.sleep(max(0, wait_ms) / 1000.0)
        dres = detect_web_page_change(
            current_raw_html=det_curr_filtered,
            prev_raw_html=det_prev_filtered,
        )
        changed_info = {
            "changed": dres.changed,
            "reason": dres.reason,
            "before_hash": dres.before_hash,
            "after_hash": dres.after_hash,
        }
        log("INFO", "F1-DET", f"changed={dres.changed} reason={dres.reason}", component="FindHomePage")
        # Optionally save detection snapshots with '-nochange' suffix
        if debug and (dres.changed or save_on_nochange):
            try:
                lbl = (save_label or name or "F1").strip()
                lbl = lbl or "F1"
                suffix = "" if dres.changed else "_nochange"
                get_save_Html(det_prev_filtered, stage=f"det-prev{suffix}", name=lbl)
                get_save_Html(det_curr_filtered, stage=f"det-curr{suffix}", name=lbl)
            except Exception:
                pass
    # Shape the response based on op for clarity/decoupling.
    # - 'allPlanHomePageCandidates': return full list + traceability
    # - 'planCheckHtmlIfChanged': return only detection result
    # - 'planLetLLMMap': return LLM mapping prompt/context for fallback planning
    op_l = (op or "").strip()
    if op_l == "planCheckHtmlIfChanged":
        log("DEBUG", "F1-RET-DET", "returning detection only", component="FindHomePage")
        return {"ok": True, "checkHtmlIfChanged": changed_info}
    if op_l == "planLetLLMMap":
        log("INFO", "F1-LLM", f"building LLM prompt attempt={llm_attempt_index}", component="FindHomePage", extra={"fb_len": len((llm_feedback or '').strip())})
        return def_let_llm_map(
            filtered_html=f_res.html,
            mapping=mapping,
            llm_feedback=llm_feedback,
            llm_attempt_index=llm_attempt_index,
        )
    # Default to allPlanHomePageCandidates
    log("DEBUG", "F1-RET-PLANS", f"plans={len(all_candidate_plans)}", component="FindHomePage")
    return {
        "ok": True,
        "allPlanHomePageCandidates": all_candidate_plans,
        "createCandidates": {
            "selectorsInOrder": candidate_selectors_in_order,
            "mapping": asdict(mapping),
        },
    "capture": (
            {
                "nonfiltered": {
                    "path": str(cap_raw.html_path),
                    "fingerprint": cap_raw.fingerprint,
                    "timestamp": cap_raw.timestamp,
                    "name": cap_raw.name,
                },
                "filtered": {
                    "path": str(cap_filtered.html_path),
                    "fingerprint": cap_filtered.fingerprint,
                    "timestamp": cap_filtered.timestamp,
                    "name": cap_filtered.name,
                },
            }
            if cap_raw and cap_filtered
            else None
        ),
    }


# TODO: Reintroduce full class-based flow once Navigator/Diff/Error types are ready.
# class FindHomePage:
#     def __init__(self, navigator: Navigator, diff: DiffService, capture: HtmlCaptureService, errors: Optional[ErrorManager] = None) -> None:
#         ...
#     def run(self, user_command: str, html_before: str, max_attempts: int = 3) -> FindResult:
#         ...

