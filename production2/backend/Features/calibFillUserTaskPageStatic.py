from __future__ import annotations

"""Calibration feature: backend-heavy orchestration for static mapping calibration.

Ops:
  - startSession(html, url, task): detect host, load existing draft, scan DOM, extract ruhsat JSON
  - scanDom(html): return candidates of inputs/actions
  - saveDraft(host, task, draft): persist calibration draft
  - list(host?): list sites or tasks
  - load(host, task): load draft
  - finalizeToConfig(host, task): merge draft into config.json
"""

from typing import Any, Dict, Optional
from pathlib import Path as _Path
import sys as _sys
from urllib.parse import urlparse

_THIS = _Path(__file__).resolve()
_ROOT = _THIS.parents[2]
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

try:
    from backend.logging_utils import log  # type: ignore
except Exception:
    def log(*args, **kwargs):
        pass

from backend.Components.calibDomScan import extract_form_elements, detect_actions  # type: ignore
from backend.Components.calibStorage import (
    load as calib_load,
    save as calib_save,
    list_sites as calib_list_sites,
    list_tasks as calib_list_tasks,
    finalize_to_config as calib_finalize_to_config,
)  # type: ignore
from backend.Components.uploadToSystemData import ensure_f3_data_ready  # type: ignore
from backend.Components.readInputConvertJson import read_input_and_convert_to_json  # type: ignore
from backend.Components.calibActionsPlanner import build_fill_plan  # type: ignore


def _host_from_url(u: Optional[str]) -> str:
    try:
        return urlparse(u or "").hostname or "unknown"
    except Exception:
        return "unknown"


def plan_calib_start_session(html: Optional[str], url: Optional[str], task: Optional[str]) -> Dict[str, Any]:
    t = task or "Yeni Trafik"
    host = _host_from_url(url)
    log("INFO", "CALIB-START", f"startSession host={host} task={t}", component="Calib", extra={
        "html_len": len(html or ""),
        "url": url,
    })

    # Load existing calibration draft if any
    existing = calib_load(host, t)

    # Scan DOM candidates
    inputs = extract_form_elements(html or "")
    actions = detect_actions(html or "")

    # Reuse F3 ingest pipeline to get ruhsat JSON from latest staged image
    prep = ensure_f3_data_ready()
    ruhsat_res = read_input_and_convert_to_json()
    ruhsat_ok = isinstance(ruhsat_res, dict) and ruhsat_res.get("ok")
    ruhsat = ruhsat_res.get("data", {}) if ruhsat_ok else (ruhsat_res if isinstance(ruhsat_res, dict) else {})

    log("INFO", "CALIB-START-RES", f"candidates={len(inputs)} actions={len(actions)} ruhsat_keys={list((ruhsat or {}).keys())}", component="Calib")
    return {
        "ok": True,
        "host": host,
        "task": t,
        "existing": existing or None,
        "candidates_preview": inputs[:50],
        "inputs_found": len(inputs),
        "actions": actions[:10],
        "ruhsat": ruhsat,
        "prep": prep,
    }


def plan_calib_scan_dom(html: Optional[str]) -> Dict[str, Any]:
    inputs = extract_form_elements(html or "")
    actions = detect_actions(html or "")
    return {"ok": True, "inputs": inputs, "count": len(inputs), "actions": actions}


def plan_calib_save_draft(host: str, task: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    res = calib_save(host, task, draft or {})
    log("INFO", "CALIB-SAVE", f"saved draft for {host}/{task}", component="Calib", extra={"path": res.get("path")})
    return {"ok": True, **res}


def plan_calib_list(host: Optional[str] = None) -> Dict[str, Any]:
    if host:
        return {"ok": True, "host": host, "items": calib_list_tasks(host)}
    return {"ok": True, "sites": calib_list_sites()}


def plan_calib_load(host: str, task: str) -> Dict[str, Any]:
    data = calib_load(host, task)
    return {"ok": True, "data": data, "exists": bool(data)}


def plan_calib_finalize_to_config(host: str, task: str) -> Dict[str, Any]:
    res = calib_finalize_to_config(host, task)
    log("INFO", "CALIB-FINALIZE", f"finalized {host}/{task} -> config", component="Calib", extra=res)
    return res


def plan_calib_test_fill_plan(host: str, task: str) -> Dict[str, Any]:
    """Build a dry-run fill plan from current draft + ruhsat JSON without executing UI actions."""
    draft = calib_load(host, task)
    if not draft:
        return {"ok": False, "error": "no_draft"}
    field_selectors = draft.get("fieldSelectors") or {}
    if not isinstance(field_selectors, dict) or not field_selectors:
        return {"ok": False, "error": "no_field_selectors"}
    execution_order = draft.get("executionOrder") or []

    # Reuse F3 ingest to source ruhsat
    _ = ensure_f3_data_ready()
    ruhsat_res = read_input_and_convert_to_json()
    ruhsat_ok = isinstance(ruhsat_res, dict) and ruhsat_res.get("ok")
    ruhsat = ruhsat_res.get("data", {}) if ruhsat_ok else (ruhsat_res if isinstance(ruhsat_res, dict) else {})

    plan = build_fill_plan(field_selectors, ruhsat, list(execution_order) if isinstance(execution_order, list) else [])
    return {"ok": True, "plan": plan, "ruhsat_keys": list((ruhsat or {}).keys())}
