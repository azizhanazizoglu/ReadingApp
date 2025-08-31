from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from backend.logging_utils import log_backend

@dataclass
class CaptureOutput:
    html_path: Path
    fingerprint: str


class HtmlCaptureService:
    """Small, file-system-based capture util (framework-agnostic).

    Responsibilities:
    - Persist raw HTML for downstream analysis/tests.
    - Return stable fingerprint for diff checks.
    """

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def persist_html(self, html: str, name: str = "page") -> CaptureOutput:
        safe = name.replace("/", "_")
        out = self.base_dir / f"{safe}.html"
        out.write_text(html, encoding="utf-8")
        fp = hashlib.sha256(html.encode("utf-8")).hexdigest()
        log_backend(
            "[INFO] [BE-2101] Persist HTML",
            level="INFO",
            code="BE-2101",
            component="HtmlCaptureService",
            extra={"path": str(out), "fingerprint": fp}
        )
        return CaptureOutput(html_path=out, fingerprint=fp)
