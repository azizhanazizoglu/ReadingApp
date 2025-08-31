from __future__ import annotations

from typing import Dict, Any
from backend.logging_utils import log_backend


class MappingValidator:
    """Selector count validator wrapper.

    Adapter around /api/ts3/analyze-selectors. Here represented as a
    callable passed at init to keep this component unit-testable.
    """

    def __init__(self, analyze_selectors: callable, min_hits: int = 3) -> None:
        self._analyze = analyze_selectors
        self._min_hits = min_hits

    def validate_mapping_selectors(self, html: str, mapping: Dict[str, Any]) -> bool:
        # Start log
        log_backend(
            "[INFO] [BE-2500] MappingValidator: start validation",
            code="BE-2500",
            component="MappingValidator",
            extra={"html_len": len(html) if isinstance(html, str) else 0}
        )
        stats = self._analyze(html, mapping)
        # Expect stats: {field: { selector: str, count: int, ... }}
        # Some analyzers may return counts as numbers under key 'count'.
        if isinstance(stats, dict):
            total = 0
            for info in stats.values():
                try:
                    if isinstance(info, dict):
                        cnt = info.get('count', 0)
                        # Coerce safely to int if possible
                        if isinstance(cnt, (int, float)):
                            total += int(cnt)
                        else:
                            total += int(str(cnt)) if str(cnt).isdigit() else 0
                    else:
                        # Back-compat: if analyzer returned a bare number
                        total += int(info)
                except Exception:
                    # Ignore malformed entries
                    pass
        else:
            total = 0
        log_backend(
            "[INFO] [BE-2502] MappingValidator: analysis done",
            code="BE-2502",
            component="MappingValidator",
            extra={"keys": len(stats) if isinstance(stats, dict) else 0}
        )
        ok = total >= self._min_hits
        log_backend(
            "[INFO] [BE-2501] Validate mapping",
            code="BE-2501",
            component="MappingValidator",
            extra={"total_hits": total, "min_hits": self._min_hits, "ok": ok}
        )
        return ok
