from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path

# Import capture helper (Components is a sibling folder of this file)
from Components.getHtml import get_save_Html
from Features.findHomePage import FindHomePage
from Components.getHtml import remember_raw_html
from Components.detectWepPageChange import detect_web_page_change


class TsxRequest(BaseModel):
    user_command: Optional[str] = None
    html: Optional[str] = None
    prev_html: Optional[str] = None
    executed_action: Optional[str] = None
    current_url: Optional[str] = None
    force_llm: Optional[bool] = None
    hard_reset: Optional[bool] = None
    ruhsat_json: Optional[Dict[str, Any]] = None


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
    html: str
    name: Optional[str] = None


@app.post("/api/f1")
def f1(req: HtmlCaptureRequest) -> Dict[str, Any]:
    """F1: On-demand FindHomePage feature entry.

    UI sends { html, name? } here; calls FindHomePage.
    """
    return FindHomePage(req.html, name=req.name or "F1")


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
def capture_html(req: HtmlCaptureRequest) -> Dict[str, Any]:
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
    """Minimal logs endpoint for legacy UI panels.

    Returns { logs: [] } to match existing FE expectation.
    """
    return {"logs": []}


@app.post("/api/logs/clear")
def clear_logs() -> Dict[str, Any]:
    """No-op clear endpoint for legacy UI. Always OK for now."""
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5100"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
