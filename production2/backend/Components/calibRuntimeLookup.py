from __future__ import annotations

"""Resolve site-specific static mapping for runtime.

Combines finalized config entries and the latest calibration draft, with the
draft taking precedence to enable quick iteration before finalizing.
"""

from typing import Any, Dict
from .calibStorage import load as _load_calib


def resolve_site_mapping(host: str, task: str, config: Dict[str, Any]) -> Dict[str, Any]:
    cfg_sites = (config.get("staticFormMapping", {}) or {}).get("sites", {})
    site = (cfg_sites.get(host) or {}).get(task) or {}
    calib = _load_calib(host, task)

    out = {
        "fieldSelectors": {},
        "actions": [],
        "executionOrder": [],
        "criticalFields": [],
        "synonyms": {},
    }
    # merge config then calib (calib wins)
    for k in out.keys():
        v = site.get(k)
        if isinstance(v, dict) or isinstance(v, list):
            out[k] = v
    for k in out.keys():
        v = calib.get(k)
        if isinstance(v, dict) or isinstance(v, list):
            out[k] = v
    return out
