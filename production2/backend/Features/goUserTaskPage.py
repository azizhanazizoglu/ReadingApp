from __future__ import annotations

"""goUserTaskPage feature orchestrator.

Provides planning (no direct execution) for three actions:
  - openSideMenu: click hamburger / side menu toggle (static mapping)
  - goUserPage: navigate to a specific user task button (static first, LLM fallback)
  - checkPageChanged: detect if raw HTML changed (hash / normalized)

Also exposes plan_full_user_task_flow utility to chain openSideMenu + goUserPage.
"""

from typing import Any, Dict, Optional
from dataclasses import asdict
from pathlib import Path as _Path
import sys
import hashlib

_this = _Path(__file__).resolve()
_root = _this.parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from Components.mappingStaticSideMenu import map_side_menu_static  # type: ignore
from Components.mappingStaticUserTask import find_best_user_task_button  # type: ignore
from Components.fillPageFromMapping import fill_and_go  # type: ignore
from Components.letLLMMapUserTaskPage import build_llm_prompt_user_task  # type: ignore
from Components.detectWepPageChange import detect_web_page_change  # type: ignore
from memory import MappingJson  # type: ignore


def _fingerprint(html: Optional[str]) -> Optional[str]:
    if not html:
        return None
    try:
        return hashlib.sha256(html.encode("utf-8")).hexdigest()
    except Exception:
        return None


# ------------------------- openSideMenu -------------------------

def plan_open_side_menu(filtered_html: Optional[str]) -> Dict[str, Any]:
    """Return a plan to click side menu (hamburger) if detectable statically."""
    if not filtered_html:
        return {"ok": False, "error": "no_filtered_html"}

    mapping: MappingJson = map_side_menu_static(filtered_html, name="side_menu")  # type: ignore
    primary = getattr(mapping.mapping, "primary_selector", None)
    if not primary:
        return {
            "ok": False,
            "error": "no_primary_selector",
            "candidates": [asdict(c) for c in mapping.candidates],
        }

    plan = fill_and_go(mapping={}, action_button_selector=primary)
    return {
        "ok": True,
        "planType": "fillPlan",
        "action": "openSideMenu",
        "fingerprint": _fingerprint(filtered_html),
        "mapping": {
            "primary": primary,
            "alternatives": getattr(mapping.mapping, "alternatives", []),
            "candidateCount": len(mapping.candidates),
        },
        "plan": asdict(plan),
    }


# ------------------------- goUserPage -------------------------

def plan_go_user_page(
    filtered_html: Optional[str],
    task_label: str,
    use_llm_fallback: bool = True,
    force_llm: bool = False,
    llm_feedback: Optional[str] = None,
    llm_attempt_index: Optional[int] = None,
) -> Dict[str, Any]:
    if not filtered_html:
        return {"ok": False, "error": "no_filtered_html"}

    static_button = find_best_user_task_button(task_label)

    if static_button and not force_llm:
        selectors = static_button.get("selectors", [])
        chosen: Optional[str] = None
        for s in selectors:
            if isinstance(s, dict) and s.get("type") in ("text", "xpath", "css"):
                val = s.get("value")
                if isinstance(val, str) and val.strip():
                    t = s.get("type")
                    if t == "text":
                        chosen = f"text:{val}"
                    elif t == "xpath":
                        chosen = f"xpath:{val}"
                    else:
                        chosen = f"css:{val}"
                    break
        if chosen:
            plan = fill_and_go(mapping={}, action_button_selector=chosen)
            return {
                "ok": True,
                "planType": "fillPlan",
                "action": "goUserPage",
                "strategy": "static",
                "taskLabel": task_label,
                "match": {
                    "id": static_button.get("id"),
                    "score": static_button.get("matchScore"),
                    "priority": static_button.get("priority"),
                },
                "selector": chosen,
                "plan": asdict(plan),
            }

    if use_llm_fallback:
        llm_plan = build_llm_prompt_user_task(
            filtered_html=filtered_html,
            task_label=task_label,
            llm_feedback=llm_feedback,
            llm_attempt_index=llm_attempt_index,
        )
        return {
            "ok": True,
            "planType": "llmPrompt",
            "action": "goUserPage",
            "strategy": "llm" if not static_button or force_llm else "static+llm",
            "taskLabel": task_label,
            "staticMatched": bool(static_button),
            "llmPlan": llm_plan.get("planLetLLMMapUserTask"),
        }

    return {"ok": False, "error": "no_static_match_and_llm_disabled"}


# ------------------------- checkPageChanged -------------------------

def plan_check_page_changed(
    current_raw_html: Optional[str],
    prev_raw_html: Optional[str],
    use_normalized_compare: bool = True,
) -> Dict[str, Any]:
    result = detect_web_page_change(
        current_raw_html=current_raw_html,
        prev_raw_html=prev_raw_html,
        use_normalized_compare=use_normalized_compare,
    )
    return {"ok": True, "action": "checkPageChanged", "result": asdict(result)}


# --------------- Combined flow ---------------

def plan_full_user_task_flow(
    filtered_html: str,
    task_label: str,
    open_menu_first: bool = True,
    llm_feedback: Optional[str] = None,
    llm_attempt_index: Optional[int] = None,
) -> Dict[str, Any]:
    steps: Dict[str, Any] = {}
    if open_menu_first:
        steps["openSideMenu"] = plan_open_side_menu(filtered_html)
    steps["goUserPage"] = plan_go_user_page(
        filtered_html=filtered_html,
        task_label=task_label,
        use_llm_fallback=True,
        llm_feedback=llm_feedback,
        llm_attempt_index=llm_attempt_index,
    )
    return {"ok": True, "flow": steps, "taskLabel": task_label}


if __name__ == "__main__":  # smoke test
    demo_filtered = """
    <div>
      <button><span>Yeni Trafik</span></button>
      <button class='inline-flex'><svg class='lucide lucide-menu'></svg></button>
    </div>
    """
    import json as _json
    print("-- openSideMenu --")
    print(_json.dumps(plan_open_side_menu(demo_filtered), indent=2, ensure_ascii=False)[:500])
    print("-- goUserPage (static) --")
    print(_json.dumps(plan_go_user_page(demo_filtered, "Yeni Trafik"), indent=2, ensure_ascii=False)[:500])
    print("-- goUserPage (force LLM) --")
    print(_json.dumps(plan_go_user_page(demo_filtered, "Yeni Trafik", force_llm=True), indent=2, ensure_ascii=False)[:500])
