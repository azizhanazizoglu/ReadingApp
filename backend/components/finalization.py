from __future__ import annotations

import re
from typing import Dict, Any, Optional
from backend.logging_utils import log_backend


class FinalDetector:
    def __init__(self) -> None:
        self._final = re.compile(r"Poliçeyi\s*Aktifleştir|PDF\s*Hazır|İndir", re.I)

    def detect_final_page(self, html: str) -> bool:
        ok = bool(self._final.search(html))
        log_backend(
            "[INFO] [BE-2901] Final detect",
            code="BE-2901",
            component="FinalDetector",
            extra={"is_final": ok}
        )
        return ok


class Finalizer:
    def click_final_action(self, mapping: Dict[str, Any]) -> Optional[str]:
        # Return selector to click; execution handled by webview
        for act in mapping.get("actions", []):
            if "final" in act.get("description", "").lower():
                sel = act.get("selector")
                log_backend("[INFO] [BE-2902] Finalizer select", code="BE-2902", component="Finalizer", extra={"selector": sel})
                return sel
        return None
