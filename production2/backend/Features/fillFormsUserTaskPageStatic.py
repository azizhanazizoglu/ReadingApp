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
    """Return ruhsat JSON via ingest pipeline."""
    try:
        prep = ensure_f3_data_ready()
        res = read_input_and_convert_to_json()
        if isinstance(res, dict):
            res.setdefault("prep", prep)
        return res
    except Exception as e:
        return {"ok": False, "error": f"ingest_failed: {e}"}


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


def plan_validate_critical_fields(field_mapping: Dict[str, str], ruhsat_json: Dict[str, Any], task: Optional[str] = None) -> Dict[str, Any]:
    """Validate that critical fields from config were successfully mapped and have data."""
    try:
        import config  # type: ignore
        cfg = config.load_config()
        t = task or "Yeni Trafik"
        
        # Get critical fields from config
        critical_fields = cfg.get("goFillForms", {}).get("static", {}).get("criticalFields", {}).get(t, [])
        if not critical_fields:
            # Default critical fields
            critical_fields = ["plaka_no", "model_yili", "sasi_no", "motor_no"]
        
        mapped_critical = []
        missing_critical = []
        unmapped_critical = []
        
        for field in critical_fields:
            has_data = field in ruhsat_json and str(ruhsat_json.get(field, "")).strip() != ""
            has_mapping = field in field_mapping and field_mapping[field]
            
            if has_data and has_mapping:
                mapped_critical.append(field)
            elif not has_data:
                missing_critical.append(field) 
            elif not has_mapping:
                unmapped_critical.append(field)
        
        success_rate = len(mapped_critical) / len(critical_fields) if critical_fields else 1.0
        is_success = success_rate >= 0.75  # 75% of critical fields must be mapped
        
        return {
            "ok": True,
            "is_success": is_success,
            "success_rate": success_rate,
            "critical_fields": critical_fields,
            "mapped_critical": mapped_critical,
            "missing_critical": missing_critical,
            "unmapped_critical": unmapped_critical,
            "total_critical": len(critical_fields),
            "total_mapped": len(mapped_critical)
        }
    except Exception as e:
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