from __future__ import annotations

from typing import Any, Dict, Optional

from Components.detectWepPageChange import detect_web_page_change


def DetectWebPageChange(current_raw_html: Optional[str] = None, prev_raw_html: Optional[str] = None) -> Dict[str, Any]:
    """Feature-level wrapper for web page change detection.

    - If inputs are None, falls back to memory.raw_html history.
    - Returns a JSON-serializable dict suitable for API responses.
    """
    res = detect_web_page_change(current_raw_html=current_raw_html, prev_raw_html=prev_raw_html)
    return {
        "ok": True,
        "changed": res.changed,
        "reason": res.reason,
        "before_hash": res.before_hash,
        "after_hash": res.after_hash,
        "details": res.details or {},
    }
