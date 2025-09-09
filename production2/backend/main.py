from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path

# Import capture helper (Components is a sibling folder of this file)
from Components.getHtml import get_save_Html
from Features.findHomePage import FindHomePage
from Components.getHtml import remember_raw_html
from Components.detectWepPageChange import detect_web_page_change
from logging_utils import log, get_log_records, clear_log_records


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


@app.post("/api/tsx/dev-run")
def tsx_dev_run(req: TsxRequest) -> Dict[str, Any]:
    """POST: TsX akışı (gelecekte). Girdi alır, aksiyon üretir (yan etki vardır)."""
    # Placeholder: implement Tsx orchestration here later
    return {
        "state": "noop",
        "details": {
            "message": "TsX not implemented yet in production2 backend",
            "phase": "init",
        },
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
def f2(req: Dict[str, Any] | None = None) -> Dict[str, Any]:
    # Optional: if raw html is provided, remember it for future diffs
    if isinstance(req, dict):
        cur = req.get("current_html") or req.get("html")
        prev = req.get("prev_html")
    else:
        cur = None
        prev = None
    if cur:
        remember_raw_html(cur, {"source": "f2"})
    res = detect_web_page_change(current_raw_html=cur, prev_raw_html=prev)
    return {
        "ok": True,
        "changed": res.changed,
        "reason": res.reason,
        "before_hash": res.before_hash,
        "after_hash": res.after_hash,
        "details": res.details or {},
    }


@app.post("/api/f3")
def f3() -> Dict[str, Any]:
    return {"ok": True, "feature": "F3", "message": "Not implemented"}


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


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5100"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
