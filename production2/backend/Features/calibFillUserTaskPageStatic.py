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


def plan_calib_llm_feedback_update(
    llm_session_results: list,
    host: str,
    task: str = "Yeni Trafik",
    auto_save: bool = True
) -> Dict[str, Any]:
    """
    Process LLM feedback session and update calibration automatically.
    
    Flow:
    1. Capture LLM mappings from session results
    2. Convert to calibration format  
    3. Update calib.json preserving other domains
    4. Optionally create draft for manual review
    
    Args:
        llm_session_results: List of F3 LLM page results from successful session
        host: Extracted from URLs  
        task: Domain task name
        auto_save: If True, directly update calib.json. If False, create draft only.
        
    Returns:
        {
            "ok": True,
            "method": "llm_feedback_auto_update",
            "pages_captured": 3,
            "fields_updated": ["plaka_no", "motor_no", "sasi_no", "model_yili"],
            "actions_updated": ["Devam", "Poliçeyi Aktifleştir"],
            "backup_path": "calib_backup_20250921_120530.json",
            "calib_updated": True
        }
    """
    try:
        from backend.Components.captureLLMFeedbackUserTaskStaticMap import (
            capture_llm_session_data,
            convert_to_calib_format,
            validate_llm_capture_data
        )  # type: ignore
        from backend.Components.updateCalibUserTaskStaticLLMFeedback import (
            update_calib_with_llm_feedback,
            preview_calib_update
        )  # type: ignore
        
        log("INFO", "CALIB-LLM-FEEDBACK", f"Processing LLM feedback for {host}/{task}", component="Calib", extra={
            "session_results_count": len(llm_session_results) if llm_session_results else 0,
            "auto_save": auto_save
        })
        
        # Validate LLM session results
        validation_result = validate_llm_capture_data(llm_session_results)
        if not validation_result["ok"]:
            log("ERROR", "CALIB-LLM-VALIDATION", f"LLM session validation failed: {validation_result.get('error')}", component="Calib")
            return validation_result
        
        if validation_result.get("warnings"):
            log("WARNING", "CALIB-LLM-WARNINGS", f"LLM session has warnings", component="Calib", extra={
                "warnings": validation_result["warnings"]
            })
        
        # Capture LLM mappings
        capture_result = capture_llm_session_data(llm_session_results, task)
        if not capture_result["ok"]:
            log("ERROR", "CALIB-LLM-CAPTURE", f"Failed to capture LLM data: {capture_result.get('error')}", component="Calib")
            return capture_result
        
        log("INFO", "CALIB-LLM-CAPTURED", f"LLM data captured successfully", component="Calib", extra={
            "pages_captured": capture_result.get("pages_captured", 0),
            "global_fields": len(capture_result.get("global_fields", [])),
            "global_actions": len(capture_result.get("global_actions", []))
        })
        
        # Convert to calibration format
        convert_result = convert_to_calib_format(capture_result, host, task)
        if not convert_result["ok"]:
            log("ERROR", "CALIB-LLM-CONVERT", f"Failed to convert to calib format: {convert_result.get('error')}", component="Calib")
            return convert_result
        
        log("INFO", "CALIB-LLM-CONVERTED", f"LLM data converted to calibration format", component="Calib", extra={
            "fields_captured": convert_result.get("fields_captured", 0),
            "actions_captured": convert_result.get("actions_captured", 0),
            "pages_processed": convert_result.get("pages_processed", 0)
        })
        
        if auto_save:
            # Update calib.json directly
            calib_path = str(_ROOT / "calib.json")
            update_result = update_calib_with_llm_feedback(
                convert_result,
                host,
                task,
                calib_path
            )
            
            if update_result["ok"]:
                log("INFO", "CALIB-LLM-UPDATED", f"calib.json updated with LLM feedback", component="Calib", extra={
                    "backup_path": update_result.get("backup_path"),
                    "fields_updated": len(update_result.get("fields_updated", [])),
                    "actions_updated": len(update_result.get("actions_updated", [])),
                    "pages_updated": update_result.get("pages_updated", 0)
                })
                
                return {
                    "ok": True,
                    "method": "llm_feedback_auto_update",
                    "pages_captured": capture_result.get("pages_captured", 0),
                    "fields_updated": update_result.get("fields_updated", []),
                    "actions_updated": update_result.get("actions_updated", []),
                    "backup_path": update_result.get("backup_path"),
                    "calib_updated": True,
                    "host": host,
                    "task": task
                }
            else:
                log("ERROR", "CALIB-LLM-UPDATE-FAILED", f"Failed to update calib.json: {update_result.get('error')}", component="Calib")
                return update_result
        else:
            # Save as draft only for manual review
            calib_structure = convert_result["calib_structure"]
            draft_result = plan_calib_save_draft(host, task, calib_structure)
            
            if draft_result["ok"]:
                log("INFO", "CALIB-LLM-DRAFT", f"LLM feedback saved as draft", component="Calib", extra={
                    "draft_path": draft_result.get("path")
                })
                
                return {
                    "ok": True,
                    "method": "llm_feedback_draft_only",
                    "pages_captured": capture_result.get("pages_captured", 0),
                    "fields_captured": convert_result.get("fields_captured", 0),
                    "actions_captured": convert_result.get("actions_captured", 0),
                    "draft_saved": True,
                    "draft_path": draft_result.get("path"),
                    "calib_updated": False,
                    "host": host,
                    "task": task
                }
            else:
                log("ERROR", "CALIB-LLM-DRAFT-FAILED", f"Failed to save LLM feedback as draft: {draft_result.get('error')}", component="Calib")
                return draft_result
        
    except Exception as e:
        error_msg = f"LLM feedback processing failed: {str(e)}"
        log("ERROR", "CALIB-LLM-EXCEPTION", error_msg, component="Calib")
        return {"ok": False, "error": error_msg}


def plan_calib_capture_llm_mappings(
    llm_results: list,
    task: str = "Yeni Trafik"  
) -> Dict[str, Any]:
    """
    Pure capture function - extract LLM mappings without updating files.
    Used for validation and preview.
    
    Returns:
        {
            "ok": True,
            "captured_data": {...},
            "preview": {...},
            "fields": [...],
            "actions": [...],
            "pages": 3
        }
    """
    try:
        from backend.Components.captureLLMFeedbackUserTaskStaticMap import (
            capture_llm_session_data,
            validate_llm_capture_data
        )  # type: ignore
        
        # Validate input
        validation_result = validate_llm_capture_data(llm_results)
        if not validation_result["ok"]:
            return validation_result
        
        # Capture mappings
        capture_result = capture_llm_session_data(llm_results, task)
        if not capture_result["ok"]:
            return capture_result
        
        return {
            "ok": True,
            "captured_data": capture_result,
            "fields": capture_result.get("global_fields", []),
            "actions": capture_result.get("global_actions", []),
            "pages": capture_result.get("pages_captured", 0),
            "host": capture_result.get("host"),
            "task": task,
            "validation": validation_result
        }
        
    except Exception as e:
        return {"ok": False, "error": f"Failed to capture LLM mappings: {str(e)}"}


def plan_calib_preview_llm_update(
    llm_session_results: list,
    host: str,
    task: str = "Yeni Trafik"
) -> Dict[str, Any]:
    """
    Preview what changes would be made by LLM feedback without updating files.
    
    Returns:
        {
            "ok": True,
            "changes": {
                "fields_added": ["motor_no", "sasi_no"],
                "fields_updated": ["plaka_no"], 
                "actions_added": ["Poliçeyi Aktifleştir"],
                "pages_added": 1,
                "pages_updated": 2
            },
            "current_calib": {...},
            "proposed_calib": {...}
        }
    """
    try:
        from backend.Components.captureLLMFeedbackUserTaskStaticMap import (
            capture_llm_session_data,
            convert_to_calib_format
        )  # type: ignore
        from backend.Components.updateCalibUserTaskStaticLLMFeedback import (
            preview_calib_update
        )  # type: ignore
        
        # Capture and convert LLM data
        capture_result = capture_llm_session_data(llm_session_results, task)
        if not capture_result["ok"]:
            return capture_result
        
        convert_result = convert_to_calib_format(capture_result, host, task)
        if not convert_result["ok"]:
            return convert_result
        
        # Preview changes
        calib_path = str(_ROOT / "calib.json")
        preview_result = preview_calib_update(convert_result, host, task, calib_path)
        
        return preview_result
        
    except Exception as e:
        return {"ok": False, "error": f"Failed to preview LLM update: {str(e)}"}
