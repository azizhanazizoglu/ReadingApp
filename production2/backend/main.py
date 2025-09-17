from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional, List

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from dataclasses import asdict

# Import capture helper (Components is a sibling folder of this file)
from Components.getHtml import get_save_Html
from Features.findHomePage import FindHomePage
from Components.getHtml import remember_raw_html
from Components.detectWepPageChange import detect_web_page_change
from Features.goUserTaskPage import (
    plan_open_side_menu,
    plan_go_user_page,
    plan_check_page_changed,
    plan_full_user_task_flow,
)
from logging_utils import log, get_log_records, clear_log_records
from config import load_config, get_go_user_task_stateflow
from Features.fillFormsUserTaskPage import (
    plan_load_ruhsat_json,
    plan_analyze_page,
    plan_build_fill_plan,
    plan_detect_final_page,
    plan_check_page_changed as plan_check_page_changed_f3,
)
from Components.uploadToSystemData import stage_uploaded_file  # type: ignore


class TsxRequest(BaseModel):
    user_command: Optional[str] = None
    html: Optional[str] = None
    prev_html: Optional[str] = None
    executed_action: Optional[str] = None
    current_url: Optional[str] = None
    force_llm: Optional[bool] = None
    hard_reset: Optional[bool] = None
    ruhsat_json: Optional[Dict[str, Any]] = None


# Load local .env if present (keep env decoupled from root)
try:
    from dotenv import load_dotenv  # type: ignore
    _here = Path(__file__).resolve().parents[1]
    _env = _here / ".env"
    if _env.exists():
        load_dotenv(dotenv_path=_env)
except Exception:
    pass

app = FastAPI(title="Production2 Backend", version="0.0.1")

# CORS (dev): allow UI/Electron to call the API easily
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, Any]:
    """GET: Sunucunun ayakta olduğunu kontrol etmek için basit sağlık kontrolü.

    GET = veri al (read-only). Sunucu durumunu sorgulama gibi yan etkisiz işlemler.
    """
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}


@app.get("/api/config")
def get_config() -> Dict[str, Any]:
    """Expose relevant config to UI (read-only)."""
    cfg = load_config()
    # Keep it minimal for now
    return {
        "goUserTaskPage": {
            "stateflow": cfg.get("goUserTaskPage", {}).get("stateflow", {}),
            "letLLM": {"maxAttempts": cfg.get("goUserTaskPage", {}).get("letLLMMap_goUserTask", {}).get("maxAttempts", 4)},
        },
        "findHomePage": {
            "letLLM": {"maxAttempts": cfg.get("findHomePage", {}).get("letLLMMap_findHomePage", {}).get("maxAttempts", 3)}
        },
        "goFillForms": {
            "stateflow": cfg.get("goFillForms", {}).get("stateflow", {}),
            "llm": {
                "mappingPrompt": cfg.get("goFillForms", {}).get("llm", {}).get("mappingPrompt", ""),
                "useHeuristics": cfg.get("goFillForms", {}).get("llm", {}).get("useHeuristics", True),
                "mappingModel": cfg.get("goFillForms", {}).get("llm", {}).get("mappingModel", cfg.get("goFillForms", {}).get("llm", {}).get("model", "")),
                "visionModel": cfg.get("goFillForms", {}).get("llm", {}).get("visionModel", cfg.get("goFillForms", {}).get("llm", {}).get("model", ""))
            }
        }
    }


@app.post("/api/tsx/dev-run")
def tsx_dev_run(req: TsxRequest) -> Dict[str, Any]:
    """POST: TsX orchestration - Static-first form filling with LLM fallback.
    
    F3 Button Flow:
    1. Try static form filling first (fast heuristics)
    2. If static succeeds → return success with actions
    3. If static fails critical validation → return should_go_home + use_llm_fallback
    """
    log("INFO", "TSX-START", f"TsX endpoint called", component="TsX", extra={
        "html_len": len(req.html or ""),
        "current_url": req.current_url,
        "user_command": req.user_command,
        "force_llm": req.force_llm,
        "hard_reset": req.hard_reset
    })
    
    if not req.html:
        log("ERROR", "TSX-NO-HTML", "Missing HTML in request", component="TsX")
        return {
            "ok": False,
            "error": "missing html",
            "details": {"message": "HTML required for TsX form filling analysis"}
        }
    
    try:
        # Load ruhsat data first
        log("INFO", "TSX-RUHSAT", "Loading ruhsat data", component="TsX")
        ruhsat_result = f3_static(F3Request(op="loadRuhsatFromTmp"))
        log("INFO", "TSX-RUHSAT-RES", f"Ruhsat result: ok={ruhsat_result.get('ok')}", component="TsX")
        
        if not ruhsat_result.get("ok"):
            log("ERROR", "TSX-RUHSAT-FAIL", f"Failed to load ruhsat: {ruhsat_result}", component="TsX")
            return {
                "ok": False,
                "state": "ruhsat_failed",
                "error": "Failed to load ruhsat data",
                "details": {"ruhsat_error": ruhsat_result}
            }
        
        ruhsat_data = ruhsat_result.get("data", {})
        log("INFO", "TSX-RUHSAT-DATA", f"Ruhsat data keys: {list(ruhsat_data.keys()) if ruhsat_data else 'empty'}", component="TsX")
        
        # Check if final page first
        log("INFO", "TSX-FINAL-CHECK", "Checking for final page", component="TsX")
        final_check = f3_static(F3Request(op="detectFinalPage", html=req.html))
        log("INFO", "TSX-FINAL-RES", f"Final check: ok={final_check.get('ok')} is_final={final_check.get('is_final')}", component="TsX")
        
        if final_check.get("ok") and final_check.get("is_final"):
            log("INFO", "TSX-FINAL-DETECTED", "Final page detected", component="TsX")
            return {
                "ok": True,
                "state": "final_page_detected",
                "details": {
                    "message": "Final activation page detected - ready to click",
                    "phase": "final",
                    "actions": final_check.get("hits", []),
                    "method": "static_detection",
                    "cta_buttons": final_check.get("hits", [])
                }
            }
        
        # Analyze page with static heuristics
        log("INFO", "TSX-ANALYZE", "Starting static page analysis", component="TsX")
        analysis = f3_static(F3Request(
            op="analyzePageStaticFillForms", 
            html=req.html,
            current_url=req.current_url,
            task="Yeni Trafik"
        ))
        log("INFO", "TSX-ANALYZE-RES", f"Analysis result: ok={analysis.get('ok')}", component="TsX")
        
        if not analysis.get("ok"):
            log("ERROR", "TSX-ANALYZE-FAIL", f"Analysis failed: {analysis}", component="TsX")
            return {
                "ok": False,
                "state": "analysis_failed",
                "error": "Static page analysis failed",
                "details": {"analysis_error": analysis}
            }
        
        field_mapping = analysis.get("field_mapping", {})
        log("INFO", "TSX-MAPPING", f"Field mapping: {len(field_mapping)} fields found", component="TsX")
        
        if not field_mapping:
            log("INFO", "TSX-NO-FORMS", "No form fields detected", component="TsX")
            return {
                "ok": True,  # Not an error, just no form fields found
                "state": "no_forms_detected",
                "details": {
                    "message": "No form fields detected on this page",
                    "phase": "skip",
                    "method": "static_detection",
                    "analysis": analysis
                }
            }
        
        # Validate critical fields
        log("INFO", "TSX-VALIDATE", "Validating critical fields", component="TsX")
        validation = f3_static(F3Request(
            op="validateCriticalFields",
            mapping=field_mapping,
            ruhsat_json=ruhsat_data,
            task="Yeni Trafik"
        ))
        log("INFO", "TSX-VALIDATE-RES", f"Validation result: ok={validation.get('ok')}", component="TsX")
        
        if not validation.get("ok"):
            log("ERROR", "TSX-VALIDATE-FAIL", f"Validation failed: {validation}", component="TsX")
            return {
                "ok": False,
                "state": "validation_error",
                "error": "Critical field validation failed",
                "details": {"validation_error": validation}
            }
        
        # Check if should fallback to LLM
        log("INFO", "TSX-FALLBACK-CHECK", "Checking if LLM fallback needed", component="TsX")
        fallback_check = f3_static(F3Request(
            op="checkShouldFallbackToLLM",
            validation_result=validation,
            task="Yeni Trafik"
        ))
        log("INFO", "TSX-FALLBACK-RES", f"Fallback check: ok={fallback_check.get('ok')} should_fallback={fallback_check.get('should_fallback')}", component="TsX")
        
        if fallback_check.get("ok") and fallback_check.get("should_fallback"):
            log("INFO", "TSX-FALLBACK-NEEDED", f"LLM fallback required: {fallback_check.get('reason')}", component="TsX")
            return {
                "ok": True,
                "state": "need_llm_fallback",
                "details": {
                    "message": "Static mapping insufficient - critical fields not met",
                    "phase": "fallback_required",
                    "method": "static_to_llm",
                    "should_go_home": True,
                    "use_llm_fallback": True,
                    "fallback_reason": fallback_check.get("reason"),
                    "success_rate": fallback_check.get("success_rate"),
                    "mapped_critical": validation.get("mapped_critical", []),
                    "missing_critical": validation.get("missing_critical", []),
                    "threshold": fallback_check.get("threshold", 0.75)
                }
            }
        
        # Static approach is sufficient - ready to proceed
        log("INFO", "TSX-READY", f"Static form filling ready: {validation.get('success_rate')}% success", component="TsX")
        return {
            "ok": True,
            "state": "static_ready",
            "details": {
                "message": "Static form filling ready - critical fields satisfied",
                "phase": "ready_to_fill",
                "method": "static_heuristics",
                "field_mapping": field_mapping,
                "actions": analysis.get("actions", []),
                "success_rate": validation.get("success_rate"),
                "mapped_critical": validation.get("mapped_critical", []),
                "total_fields": len(field_mapping),
                "critical_fields": validation.get("critical_fields", [])
            }
        }
        
    except Exception as e:
        log("ERROR", "TSX-EXCEPTION", f"TsX error: {e}", component="TsX")
        return {
            "ok": False,
            "state": "error",
            "error": str(e),
            "details": {
                "message": f"TsX static form filling failed: {e}",
                "phase": "error"
            }
        }

class HtmlCaptureRequest(BaseModel):
    # Operation mode (MANDATORY): 'allPlanHomePageCandidates' | 'planCheckHtmlIfChanged'
    op: str
    html: str
    name: Optional[str] = None
    # Debug/diagnostics
    debug: Optional[bool] = None
    clean_tmp: Optional[bool] = None
    save_on_nochange: Optional[bool] = None
    save_label: Optional[str] = None
    # Prefer raw HTML inputs from UI; backend will filter internally when needed.
    prev_html: Optional[str] = None
    current_html: Optional[str] = None
    # Back-compat: UI used to send already-filtered HTML; still accepted.
    prev_filtered_html: Optional[str] = None
    current_filtered_html: Optional[str] = None
    wait_ms: int = 0
    # LLM fallback fields
    llm_feedback: Optional[str] = None  # UI-provided feedback text about failed candidates/tries
    llm_attempt_index: Optional[int] = None  # 0-based attempt count maintained by UI


class HtmlSaveRequest(BaseModel):
    html: str
    name: Optional[str] = None


class GoUserTaskRequest(BaseModel):
    op: Optional[str] = None  # openSideMenu | goUserPage | checkPageChanged | fullFlow
    html: Optional[str] = None  # current (filtered) html for planning (we accept raw too)
    taskLabel: Optional[str] = None
    # For change detection (raw html snapshots)
    prev_html: Optional[str] = None
    current_html: Optional[str] = None
    # LLM fallback
    llm_feedback: Optional[str] = None
    llm_attempt_index: Optional[int] = None
    force_llm: Optional[bool] = None
    open_menu_first: Optional[bool] = None  # for fullFlow


class F3Request(BaseModel):
    # op: loadRuhsatFromTmp | analyzePage | buildFillPlan | detectFinalPage | analyzePageStaticFillForms | validateCriticalFields | detectFormsFilled | checkShouldFallbackToLLM
    op: Optional[str] = None
    html: Optional[str] = None
    ruhsat_json: Optional[Dict[str, Any]] = None
    # For buildFillPlan
    mapping: Optional[Dict[str, Any]] = None  # expects { field_mapping: {key->selector}, llm_actions?: [str] }
    # For static operations
    current_url: Optional[str] = None
    task: Optional[str] = None
    validation_result: Optional[Dict[str, Any]] = None
    min_filled: Optional[int] = None
    # For page change detection
    current_html: Optional[str] = None
    prev_html: Optional[str] = None


@app.post("/api/f1")
def f1(req: HtmlCaptureRequest) -> Dict[str, Any]:
    """F1: On-demand FindHomePage feature entry.

    UI sends { html, name? } here; calls FindHomePage.
    """
    valid_ops = {"allPlanHomePageCandidates", "planCheckHtmlIfChanged", "planLetLLMMap"}
    if req.op not in valid_ops:
        raise HTTPException(status_code=422, detail=f"invalid op: {req.op}. expected one of {sorted(valid_ops)}")
    log("INFO", "F1-REQ", f"op={req.op}", component="F1", extra={
        "name": req.name or "F1",
        "html_len": len(req.html or ""),
        "has_prev_html": bool(req.prev_html),
        "has_current_html": bool(req.current_html),
        "llm_attempt_index": req.llm_attempt_index,
        "llm_feedback_len": len(req.llm_feedback or ""),
    })
    res = FindHomePage(
        req.html,
        name=req.name or "F1",
    debug=bool(req.debug) if req.debug is not None else False,
        op=req.op,
    clean_tmp=bool(req.clean_tmp) if req.clean_tmp is not None else False,
    save_on_nochange=bool(req.save_on_nochange) if req.save_on_nochange is not None else False,
    save_label=req.save_label,
    # Raw HTMLs (preferred)
    prev_html=req.prev_html,
    current_html=req.current_html,
    # Filtered HTMLs (legacy)
        prev_filtered_html=req.prev_filtered_html,
        current_filtered_html=req.current_filtered_html,
        wait_ms=req.wait_ms,
        # LLM planning
        llm_feedback=req.llm_feedback,
        llm_attempt_index=req.llm_attempt_index,
    )
    keys = list(res.keys())
    log("INFO", "F1-RES", f"keys={keys}", component="F1", extra={"op": req.op})
    return res


@app.post("/api/f2")
def f2(req: GoUserTaskRequest) -> Dict[str, Any]:
    """F2: goUserTaskPage feature entry (repurposed).

    Operations (req.op):
      - openSideMenu: plan click for side menu toggle
      - goUserPage: plan navigation to taskLabel (static first, LLM fallback placeholder)
      - checkPageChanged: diff prev/current raw html
      - fullFlow: optional open side menu then goUserPage

    Backward compatibility: if no op provided but prev/current html given -> perform diff only.
    """
    op = (req.op or "").strip()
    # Raw diff only fallback
    if not op:
        if not (req.current_html or req.html):
            raise HTTPException(status_code=422, detail="missing html or op")
        res = detect_web_page_change(current_raw_html=req.current_html or req.html, prev_raw_html=req.prev_html)
        return {
            "ok": True,
            "changed": res.changed,
            "reason": res.reason,
            "before_hash": res.before_hash,
            "after_hash": res.after_hash,
            "details": res.details or {},
            "mode": "diff-only",
        }

    # Require html for planning ops (except pure checkPageChanged which uses current_html)
    if op in {"openSideMenu", "goUserPage", "fullFlow"} and not (req.html):
        raise HTTPException(status_code=422, detail="missing html for planning")

    if op == "openSideMenu":
        return plan_open_side_menu(req.html)
    if op == "goUserPage":
        if not req.taskLabel:
            raise HTTPException(status_code=422, detail="missing taskLabel")
        return plan_go_user_page(
            filtered_html=req.html,
            task_label=req.taskLabel,
            use_llm_fallback=True,
            force_llm=bool(req.force_llm),
            llm_feedback=req.llm_feedback,
            llm_attempt_index=req.llm_attempt_index,
        )
    if op == "checkPageChanged":
        return plan_check_page_changed(
            current_raw_html=req.current_html,
            prev_raw_html=req.prev_html,
        )
    if op == "fullFlow":
        if not req.taskLabel:
            raise HTTPException(status_code=422, detail="missing taskLabel for fullFlow")
        return plan_full_user_task_flow(
            filtered_html=req.html,
            task_label=req.taskLabel,
            open_menu_first=True if req.open_menu_first is None else bool(req.open_menu_first),
            llm_feedback=req.llm_feedback,
            llm_attempt_index=req.llm_attempt_index,
        )
    raise HTTPException(status_code=422, detail=f"invalid op: {op}")


@app.post("/api/calib")
def calib(req: F3Request) -> Dict[str, Any]:
    """Calibration API (backend-heavy).

    ops:
      - startSession { html, current_url, task }
      - scanDom { html }
      - saveDraft { mapping: { host, task, draft } }
      - list { mapping?: { host } }
      - load { mapping: { host, task } }
      - finalizeToConfig { mapping: { host, task } }
    """
    op = (req.op or "").strip()
    if not op:
        raise HTTPException(status_code=422, detail="missing op")

    from Features.calibFillUserTaskPageStatic import (
        plan_calib_start_session,
        plan_calib_scan_dom,
        plan_calib_save_draft,
        plan_calib_list,
        plan_calib_load,
        plan_calib_finalize_to_config,
        plan_calib_test_fill_plan,
    )

    if op == "startSession":
        return plan_calib_start_session(req.html, req.current_url, req.task)
    if op == "scanDom":
        return plan_calib_scan_dom(req.html)
    if op == "saveDraft":
        body = req.mapping or {}
        host = body.get("host") or ""
        task = body.get("task") or (req.task or "Yeni Trafik")
        draft = body.get("draft") or {}
        if not host:
            raise HTTPException(status_code=422, detail="missing host")
        return plan_calib_save_draft(host, task, draft)
    if op == "list":
        host = (req.mapping or {}).get("host")
        return plan_calib_list(host)
    if op == "load":
        body = req.mapping or {}
        host = body.get("host") or ""
        task = body.get("task") or (req.task or "Yeni Trafik")
        if not host:
            raise HTTPException(status_code=422, detail="missing host")
        return plan_calib_load(host, task)
    if op == "finalizeToConfig":
        body = req.mapping or {}
        host = body.get("host") or ""
        task = body.get("task") or (req.task or "Yeni Trafik")
        if not host:
            raise HTTPException(status_code=422, detail="missing host")
        return plan_calib_finalize_to_config(host, task)
    if op == "testFillPlan":
        body = req.mapping or {}
        host = body.get("host") or ""
        task = body.get("task") or (req.task or "Yeni Trafik")
        if not host:
            raise HTTPException(status_code=422, detail="missing host")
        return plan_calib_test_fill_plan(host, task)
    raise HTTPException(status_code=422, detail=f"invalid op: {op}")


@app.post("/api/f3")
def f3(req: F3Request) -> Dict[str, Any]:
    """F3: fillFormsUserTaskPage feature entry.

    Operations (req.op):
      - loadRuhsatFromTmp: auto-ingest ruhsat JSON from tmp (or via Vision LLM)
      - analyzePage: LLM-based page analysis to produce { page_kind, field_mapping, actions }
      - buildFillPlan: turn field_mapping + ruhsat_json into FillPlan actions
      - detectFinalPage: static final-page detection via CTA synonyms
    """
    op = (req.op or "").strip()
    if not op:
        raise HTTPException(status_code=422, detail="missing op")

    if op == "loadRuhsatFromTmp":
        return plan_load_ruhsat_json()

    if op == "analyzePage":
        if not req.html:
            raise HTTPException(status_code=422, detail="missing html")
        return plan_analyze_page(req.html, req.ruhsat_json or {})

    if op == "buildFillPlan":
        # Build plan of set_value/select_option actions from mapping + ruhsat_json
        return plan_build_fill_plan(req.mapping or {}, req.ruhsat_json or {})

    if op == "detectFinalPage":
        if not req.html:
            raise HTTPException(status_code=422, detail="missing html")
        return plan_detect_final_page(req.html)

    if op == "checkPageChanged":
        return plan_check_page_changed_f3(req.current_html, req.prev_html)

    if op == "detectFormsFilled":
        # req.mapping may carry filler result { details: [...] }, or pass req.html for fallback
        min_filled = 2
        try:
            if isinstance(req.mapping, dict) and isinstance(req.mapping.get('min_filled'), int):
                min_filled = int(req.mapping.get('min_filled'))
        except Exception:
            pass
        from Features.fillFormsUserTaskPage import plan_detect_forms_filled  # type: ignore
        return plan_detect_forms_filled(details=req.mapping, html=req.html, min_filled=min_filled)

    raise HTTPException(status_code=422, detail=f"invalid op: {op}")


@app.post("/api/f3-static")
def f3_static(req: F3Request) -> Dict[str, Any]:
    """F3-Static: fillFormsUserTaskPageStatic feature entry (STATIC ONLY).

    Operations (req.op):
      - loadRuhsatFromTmp: auto-ingest ruhsat JSON from tmp (or via Vision LLM)
      - analyzePageStaticFillForms: STATIC-only page analysis using heuristics
      - validateCriticalFields: validate critical field mapping success
      - detectFinalPage: static final-page detection via CTA synonyms
      - detectFormsFilled: check if forms are filled
      - checkShouldFallbackToLLM: determine if LLM fallback is needed
    """
    op = (req.op or "").strip()
    if not op:
        raise HTTPException(status_code=422, detail="missing op")

    log("INFO", "F3-STATIC", f"F3-Static operation: {op}", component="F3-Static", extra={
        "html_len": len(req.html or ""),
        "current_url": req.current_url,
        "task": req.task,
        "has_mapping": bool(req.mapping),
        "has_ruhsat": bool(req.ruhsat_json),
        "has_validation": bool(req.validation_result)
    })

    from Features.fillFormsUserTaskPageStatic import (
        plan_load_ruhsat_json as static_plan_load_ruhsat_json,
        plan_analyze_page_static_fill_forms,
        plan_validate_critical_fields,
        plan_detect_final_page as static_plan_detect_final_page,
        plan_detect_forms_filled as static_plan_detect_forms_filled,
        plan_check_should_fallback_to_llm,
    )

    if op == "loadRuhsatFromTmp":
        return static_plan_load_ruhsat_json()

    if op == "analyzePageStaticFillForms":
        if not req.html:
            raise HTTPException(status_code=422, detail="missing html")
        return plan_analyze_page_static_fill_forms(req.html, req.current_url, req.task)

    if op == "validateCriticalFields":
        if not req.mapping or not req.ruhsat_json:
            raise HTTPException(status_code=422, detail="missing field_mapping or ruhsat_json")
        return plan_validate_critical_fields(req.mapping, req.ruhsat_json, req.task)

    if op == "detectFinalPage":
        if not req.html:
            raise HTTPException(status_code=422, detail="missing html")
        return static_plan_detect_final_page(req.html)

    if op == "detectFormsFilled":
        min_filled = 2
        if hasattr(req, 'min_filled') and isinstance(req.min_filled, int):
            min_filled = req.min_filled
        return static_plan_detect_forms_filled(details=req.mapping, html=req.html, min_filled=min_filled)

    if op == "checkShouldFallbackToLLM":
        if not req.validation_result:
            raise HTTPException(status_code=422, detail="missing validation_result")
        return plan_check_should_fallback_to_llm(req.validation_result, req.task)

    raise HTTPException(status_code=422, detail=f"invalid op: {op}")


@app.post("/api/html/capture")
def capture_html(req: HtmlSaveRequest) -> Dict[str, Any]:
    """POST: GUI'den gelen iframe HTML'ini isteğe bağlı (on-demand) yakala.

    - F1 tuşuna basınca (veya manuel) UI bu endpoint'e { html, name } gönderir.
    - Backend tmp/html klasörünü temizler, dosyayı yazar, memory.html'e kaydeder.
    - Çıktı: path, fingerprint, timestamp, name.
    """
    res = get_save_Html(req.html, name=req.name)
    return {
        "ok": True,
        "path": str(res.html_path),
        "fingerprint": res.fingerprint,
        "timestamp": res.timestamp,
        "name": res.name,
    }


@app.get("/api/logs")
def get_logs() -> Dict[str, Any]:
    """Return accumulated backend logs for the UI log panel."""
    try:
        logs = get_log_records()
        return {"logs": logs}
    except Exception:
        return {"logs": []}


@app.post("/api/logs/clear")
def clear_logs() -> Dict[str, Any]:
    """Clear accumulated backend logs."""
    try:
        clear_log_records()
        return {"ok": True}
    except Exception:
        return {"ok": False}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Accept JPEG/PNG and stage into configured data dir (goFillForms.input.imageDir)."""
    try:
        orig_name = file.filename or "upload"
        ext = (orig_name.split(".")[-1] or "").lower()
        if ext not in {"jpg", "jpeg", "png"}:
            raise HTTPException(status_code=415, detail=f"unsupported file type: .{ext}")
        data = await file.read()
        res = stage_uploaded_file(data, orig_name)
        log("INFO", "UPLOAD", f"staged {res.get('path')}", component="F3", extra={"size": len(data), "orig": orig_name})
        return {"ok": True, "result": "JPEG yüklendi ve kaydedildi.", "file_path": res.get("path")}
    except HTTPException:
        raise
    except Exception as e:
        log("ERROR", "UPLOAD", f"upload failed: {e}", component="F3")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5100"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
