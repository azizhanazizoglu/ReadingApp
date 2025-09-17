from __future__ import annotations

"""Calibration validation helpers."""

from typing import Any, Dict, List


def get_critical_fields(task: str, config: Dict[str, Any], fallback: List[str]) -> List[str]:
    # Try config staticFormMapping first
    crit = (((config.get("staticFormMapping", {}) or {}).get("tasks", {}) or {}).get(task) or {}).get("criticalFields") or []
    if isinstance(crit, list) and crit:
        return list(crit)
    return list(fallback or [])


def validate_mapping(field_selectors: Dict[str, str], critical_fields: List[str], threshold: float = 0.75) -> Dict[str, Any]:
    crit_set = set(critical_fields or [])
    mapped = [k for k in crit_set if field_selectors.get(k)]
    missing = [k for k in crit_set if not field_selectors.get(k)]
    total = max(1, len(crit_set))
    success_rate = len(mapped) / total
    return {
        "ok": True,
        "success_rate": success_rate,
        "mapped_critical": mapped,
        "missing_critical": missing,
        "threshold": threshold,
        "meets_threshold": success_rate >= threshold,
    }
