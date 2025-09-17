from __future__ import annotations

"""Calibration actions planner.

Turns a dict of fieldSelectors + ruhsat JSON into a sequence of set_value
actions ordered by executionOrder (when provided).
"""

from typing import Any, Dict, List


def build_fill_plan(field_selectors: Dict[str, str], ruhsat_json: Dict[str, Any], execution_order: List[str]) -> Dict[str, Any]:
    order = list(execution_order or [])
    if not order:
        order = list(field_selectors.keys())
    details: List[Dict[str, Any]] = []
    for key in order:
        sel = field_selectors.get(key)
        if not sel:
            continue
        val = ruhsat_json.get(key)
        if val is None:
            continue
        details.append({
            "kind": "set_value",
            "selector": sel,
            "value": str(val),
            "field": key,
        })
    return {"ok": True, "details": details, "count": len(details)}
