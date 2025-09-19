from __future__ import annotations

"""fillFormsUserTaskPageStatic feature orchestrator (STATIC ONLY).

Provides planning for static-only actions:
  - loadRuhsatFromTmp: ingest ruhsat JSON (prepared or via Vision LLM on latest image)
  - analyzePageStaticFillForms: static heuristic field mapping and action suggestion per page
  - detectFinalPage: static detection of final activation CTAs (e.g., "Poliçeyi Aktifleştir")
  - detectFormsFilled: check if critical fields were filled
  - validateCriticalFields: check if critical fields from config were successfully filled

This is a pure static implementation without any LLM calls.
"""

from typing import Any, Dict, Optional, List
import sys
import hashlib
import json as _json
from pathlib import Path as _Path

_this = _Path(__file__).resolve()
_root = _this.parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from backend.Components.readInputConvertJson import read_input_and_convert_to_json  # type: ignore
from backend.Components.detectFinalPageArrivedinUserTask import detect_final_page_arrived  # type: ignore
from backend.Components.detectFormsAreFilled import detect_forms_filled  # type: ignore
from backend.Components.uploadToSystemData import ensure_f3_data_ready  # type: ignore
from backend.Components.mappingStaticFillForms import static_analyze_page  # type: ignore


def _fingerprint(html: Optional[str]) -> Optional[str]:
    if not html:
        return None
    try:
        return hashlib.sha256(html.encode("utf-8")).hexdigest()
    except Exception:
        return None


# ------------------------- loadRuhsatFromTmp -------------------------

def plan_load_ruhsat_json() -> Dict[str, Any]:
    """Return ruhsat JSON via ingest pipeline with richer diagnostics.

    Always returns a structured { ok, data?, error?, meta? } object – never raises – so
    the /api/f3-static caller should not surface http_500 unless FastAPI itself fails.
    """
    from backend.logging_utils import log  # type: ignore
    try:
        log("INFO", "RUHSAT-LOAD", "starting ensure_f3_data_ready", component="F3-Static")
        prep = ensure_f3_data_ready()  # { ok, prepared, meta?, error? }
        log("INFO", "RUHSAT-LOAD", "ensure_f3_data_ready done", component="F3-Static", extra={
            "prepared": prep.get("prepared"),
            "meta": prep.get("meta"),
            "error": prep.get("error")
        })
        res = read_input_and_convert_to_json()  # { ok, data?, error, meta }
        # Normalise legacy structure
        ok = bool(res.get("ok")) if isinstance(res, dict) else False
        error = res.get("error") if isinstance(res, dict) else "unknown"
        data = res.get("data") if isinstance(res, dict) else None
        meta = res.get("meta") if isinstance(res, dict) else {}
        if ok and not data:
            # Unexpected – treat as error
            ok = False
            error = error or "no_data"
        out: Dict[str, Any] = {"ok": ok, "data": data, "error": error if not ok else None, "meta": meta, "prep": prep}
        code = "RUHSAT-OK" if ok else "RUHSAT-ERR"
        log("INFO" if ok else "WARN", code, "ruhsat load result", component="F3-Static", extra={
            "ok": ok,
            "error": error,
            "source": (meta or {}).get("source"),
            "ingest_error": error,
            "has_keys": list((data or {}).keys())[:10] if isinstance(data, dict) else [],
        })
        # Provide explicit error codes UI can branch on instead of generic http_500
        if not ok and isinstance(error, str):
            # Map underlying errors to stable short codes
            if error.startswith("no_image_dir"):
                out["error_code"] = "no_image_dir"
            elif error.startswith("no_images_found"):
                out["error_code"] = "no_images"
            elif error.startswith("no_key_for_vision"):
                out["error_code"] = "missing_api_key"
            elif "vision_extract_failed" in error:
                out["error_code"] = "vision_failed"
            else:
                out["error_code"] = "ingest_failed"
        return out
    except Exception as e:  # Final safety net – never raise
        log("ERROR", "RUHSAT-EXC", f"unexpected exception: {e}", component="F3-Static")
        return {"ok": False, "error": f"ingest_exception: {e}", "error_code": "ingest_exception"}


# ------------------------- analyzePageStaticFillForms (STATIC ONLY) -------------------------

def plan_analyze_page_static_fill_forms(filtered_html: Optional[str], url: Optional[str] = None, task: Optional[str] = None) -> Dict[str, Any]:
    """Static-only page analysis. No LLM calls."""
    from backend.logging_utils import log  # type: ignore
    
    if not filtered_html:
        log("ERROR", "STATIC-NO-HTML", "No HTML provided for static analysis", component="StaticAnalyze")
        return {"ok": False, "error": "no_filtered_html"}
    try:
        u = url or ""
        t = task or "Yeni Trafik"
        
        log("INFO", "STATIC-START", f"Static analysis starting: {len(filtered_html)} chars", component="StaticAnalyze", extra={
            "url": u,
            "task": t
        })
        
        import config  # type: ignore
        cfg = config.load_config()
        out = static_analyze_page(filtered_html, u, t, cfg)
        fp = _fingerprint(filtered_html)
        out["fingerprint"] = fp
        
        field_mapping = out.get("field_mapping", {})
        actions = out.get("actions", [])
        
        log("INFO", "STATIC-RESULT", f"Static analysis complete: {len(field_mapping)} fields, {len(actions)} actions", component="StaticAnalyze", extra={
            "field_mapping": field_mapping,
            "actions": actions[:3] if actions else [],  # First 3 actions only
            "mapping_sources": out.get("mapping_sources", {}),
            "contexts": out.get("contexts", {})
        })
        
        return out
    except Exception as e:
        log("ERROR", "STATIC-ERROR", f"Static analysis failed: {e}", component="StaticAnalyze")
        return {"ok": False, "error": f"analyze_static_failed: {e}"}


def plan_validate_critical_fields(field_mapping: Dict[str, str], ruhsat_json: Dict[str, Any], task: Optional[str] = None, critical_fields_override: Optional[List[str]] = None) -> Dict[str, Any]:
    """Validate that critical fields from config were successfully mapped and have data.
    
    Args:
        field_mapping: Field to selector mapping from static analysis
        ruhsat_json: Extracted ruhsat data
        task: Task name (e.g., "Yeni Trafik")
        critical_fields_override: Dynamic critical fields from calib.json page (preferred over config)
    """
    from backend.logging_utils import log  # type: ignore
    
    try:
        import config  # type: ignore
        cfg = config.load_config()
        t = task or "Yeni Trafik"
        
        # Use dynamic critical fields from calib.json if provided, otherwise fall back to config
        if critical_fields_override:
            critical_fields = critical_fields_override
            source = "calib_page"
        else:
            critical_fields = cfg.get("goFillForms", {}).get("static", {}).get("criticalFields", {}).get(t, [])
            source = "config"
            if not critical_fields:
                # Default critical fields
                critical_fields = ["plaka_no", "model_yili", "sasi_no", "motor_no"]
                source = "default"
        
        log("INFO", "CRITICAL-VALIDATION", f"Validating critical fields from {source}", component="F3-Static", extra={
            "critical_fields": critical_fields,
            "field_mapping_keys": list(field_mapping.keys()),
            "ruhsat_keys": list(ruhsat_json.keys()),
            "source": source
        })
        
        mapped_critical = []
        missing_critical = []
        unmapped_critical = []
        
        for field in critical_fields:
            has_data = field in ruhsat_json and str(ruhsat_json.get(field, "")).strip() != ""
            has_mapping = field in field_mapping and field_mapping[field]
            
            log("INFO", "CRITICAL-FIELD-CHECK", f"Field {field}: data={has_data}, mapping={has_mapping}", component="F3-Static", extra={
                "field": field,
                "has_data": has_data,
                "has_mapping": has_mapping,
                "data_value": str(ruhsat_json.get(field, ""))[:50] if has_data else "",
                "mapping_selector": field_mapping.get(field, "") if has_mapping else ""
            })
            
            if has_data and has_mapping:
                mapped_critical.append(field)
            elif not has_data:
                missing_critical.append(field) 
            elif not has_mapping:
                unmapped_critical.append(field)
        
        success_rate = len(mapped_critical) / len(critical_fields) if critical_fields else 1.0
        is_success = success_rate >= 0.75  # 75% of critical fields must be mapped
        
        result = {
            "ok": True,
            "is_success": is_success,
            "success_rate": success_rate,
            "critical_fields": critical_fields,
            "mapped_critical": mapped_critical,
            "missing_critical": missing_critical,
            "unmapped_critical": unmapped_critical,
            "total_critical": len(critical_fields),
            "total_mapped": len(mapped_critical),
            "source": source
        }
        
        log("INFO", "CRITICAL-VALIDATION-RESULT", f"Critical validation: {len(mapped_critical)}/{len(critical_fields)} success={is_success}", component="F3-Static", extra=result)
        
        return result
    except Exception as e:
        log("ERROR", "CRITICAL-VALIDATION-ERROR", f"Critical validation failed: {e}", component="F3-Static")
        return {"ok": False, "error": f"validation_failed: {e}"}


def plan_detect_final_page(filtered_html: Optional[str]) -> Dict[str, Any]:
    if not filtered_html:
        return {"ok": True, "is_final": False, "reason": "no_html"}
    try:
        out = detect_final_page_arrived(filtered_html)
        return {"ok": True, **out, "fingerprint": _fingerprint(filtered_html)}
    except Exception as e:
        return {"ok": False, "error": f"detect_failed: {e}"}


def plan_detect_forms_filled(details: Optional[Dict[str, Any]] = None, html: Optional[str] = None, min_filled: int = 2) -> Dict[str, Any]:
    """Check if at least min_filled inputs are filled."""
    try:
        det_list = None
        if isinstance(details, dict) and isinstance(details.get("details"), list):
            det_list = details.get("details")
        out = detect_forms_filled(det_list, html, min_filled=min_filled)
        return {"ok": True, **out}
    except Exception as e:
        return {"ok": False, "error": f"detect_forms_failed: {e}"}


def plan_check_should_fallback_to_llm(validation_result: Dict[str, Any], task: Optional[str] = None) -> Dict[str, Any]:
    """Determine if we should fall back to LLM due to insufficient static mapping."""
    try:
        import config  # type: ignore
        cfg = config.load_config()
        t = task or "Yeni Trafik"
        
        # Get fallback threshold from config
        fallback_threshold = cfg.get("goFillForms", {}).get("static", {}).get("fallbackThreshold", 0.75)
        
        should_fallback = False
        reason = "success"
        
        if not validation_result.get("ok"):
            should_fallback = True
            reason = "validation_error"
        elif not validation_result.get("is_success"):
            should_fallback = True
            reason = "insufficient_critical_fields"
        elif validation_result.get("success_rate", 0) < fallback_threshold:
            should_fallback = True
            reason = "below_threshold"
        
        return {
            "ok": True,
            "should_fallback": should_fallback,
            "reason": reason,
            "threshold": fallback_threshold,
            "success_rate": validation_result.get("success_rate", 0)
        }
    except Exception as e:
        return {"ok": False, "error": f"fallback_check_failed: {e}"}


if __name__ == "__main__":  # smoke test
    demo_filtered = """
    <form>
      <label for="plk">Plaka</label>
      <input id="plk" />
      <button>Devam</button>
    </form>
    """
    print("-- analyzePageStaticFillForms --")
    print(_json.dumps(plan_analyze_page_static_fill_forms(demo_filtered), indent=2, ensure_ascii=False)[:500])
    print("-- detectFinalPage --")
    print(_json.dumps(plan_detect_final_page('<button>Poliçeyi Aktifleştir</button>'), indent=2, ensure_ascii=False))