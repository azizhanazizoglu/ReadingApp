from __future__ import annotations

"""Resolve site-specific static mapping for runtime.

Combines finalized config entries and the latest calibration draft, with the
draft taking precedence to enable quick iteration before finalizing.
"""

from typing import Any, Dict
from .calibStorage import load as _load_calib


def resolve_site_mapping(host: str, task: str, config: Dict[str, Any]) -> Dict[str, Any]:
    from backend.logging_utils import log  # type: ignore
    
    # Force reload test - calib lookup function
    cfg_sites = (config.get("staticFormMapping", {}) or {}).get("sites", {})
    site = (cfg_sites.get(host) or {}).get(task) or {}
    calib = _load_calib(host, task)

    log("INFO", "CALIB-LOOKUP", f"Loading mappings for host={host}, task={task}", component="CalibLookup", extra={
        "host": host,
        "task": task,
        "config_has_site": bool(site),
        "calib_loaded": bool(calib),
        "calib_fields": list(calib.get("fieldSelectors", {}).keys()) if calib else [],
        "calib_actions": calib.get("actions", []) if calib else []
    })

    # Include pages & actionsDetail so static analyzer can apply per-page overrides.
    out = {
        "fieldSelectors": {},
        "actions": [],
        "executionOrder": [],
        "criticalFields": [],
        "synonyms": {},
        "pages": [],          # added
        "actionsDetail": []    # added (future usage)
    }
    # merge config then calib (calib wins)
    for k in list(out.keys()):
        v = site.get(k)
        if isinstance(v, (dict, list)):
            out[k] = v
    for k in list(out.keys()):
        v = calib.get(k)
        if isinstance(v, (dict, list)):
            out[k] = v
    
    log("INFO", "CALIB-RESULT", f"Final mapping resolved for {host}/{task}", component="CalibLookup", extra={
        "final_fields": list(out.get("fieldSelectors", {}).keys()),
        "final_actions": out.get("actions", []),
        "pages": len(out.get("pages", []) or []),
        "has_page_overrides": bool(out.get("pages")),
        "source": "calib.json" if calib else "config.json"
    })
    
    return out
