from __future__ import annotations

import hashlib
from .types import DiffResult
from backend.logging_utils import log_backend


class DiffService:
    """Cheap HTML change detector using SHA256 + length markers."""

    def fingerprint(self, html: str) -> str:
        return hashlib.sha256(html.encode("utf-8")).hexdigest() + f":{len(html)}"

    def diff(self, prev_html: str, new_html: str) -> DiffResult:
        prev_fp = self.fingerprint(prev_html)
        new_fp = self.fingerprint(new_html)
        changed = prev_fp != new_fp
        reason = "fingerprint_changed" if changed else "no_change"
        log_backend(
            "[INFO] [BE-2301] Diff",
            code="BE-2301",
            component="DiffService",
            extra={"changed": changed, "reason": reason}
        )
        return DiffResult(changed=changed, reason=reason, prev_fingerprint=prev_fp, new_fingerprint=new_fp)
