from __future__ import annotations

"""Calibration storage helpers.

Persist and retrieve calibration drafts per host/task inside a single
JSON file at production2/calib.json, and merge finalized mapping into
config.json structure.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import re
import time
from urllib.parse import urlparse

_THIS = Path(__file__).resolve()
_ROOT = _THIS.parents[2]
_CALIB_FILE = _ROOT / "calib.json"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def host_from_url(u: Optional[str]) -> str:
    try:
        return urlparse(u or "").hostname or "unknown"
    except Exception:
        return "unknown"


def _safe_task(task: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-\. ]+", "_", task or "task")


def _read_all() -> Dict[str, Any]:
    if not _CALIB_FILE.exists():
        return {}
    try:
        data = json.loads(_CALIB_FILE.read_text(encoding="utf-8") or "{}")
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _write_all(data: Dict[str, Any]) -> None:
    _CALIB_FILE.write_text(json.dumps(data or {}, ensure_ascii=False, indent=2), encoding="utf-8")


def load(host: str, task: str) -> Dict[str, Any]:
    from backend.logging_utils import log  # type: ignore
    
    data = _read_all()
    site = data.get(host) if isinstance(data, dict) else None
    if not isinstance(site, dict):
        log("INFO", "CALIB-LOAD", f"No calibration data found for host={host}", component="CalibStorage", extra={
            "host": host,
            "task": task,
            "calib_file_exists": _CALIB_FILE.exists(),
            "available_hosts": list(data.keys()) if isinstance(data, dict) else []
        })
        return {}
    
    t = site.get(task)
    result = t if isinstance(t, dict) else {}
    
    log("INFO", "CALIB-LOAD", f"Calibration data loaded for {host}/{task}", component="CalibStorage", extra={
        "host": host,
        "task": task,
        "calib_file": str(_CALIB_FILE),
        "has_field_selectors": bool(result.get("fieldSelectors")),
        "field_count": len(result.get("fieldSelectors", {})),
        "field_keys": list(result.get("fieldSelectors", {}).keys()),
        "has_actions": bool(result.get("actions")),
        "action_count": len(result.get("actions", [])),
        "updated_at": result.get("updatedAt", "never")
    })
    
    return result


def save(host: str, task: str, data: Dict[str, Any]) -> Dict[str, Any]:
    all_data = _read_all()
    if not isinstance(all_data, dict):
        all_data = {}
    site = all_data.setdefault(host, {})
    if not isinstance(site, dict):
        all_data[host] = site = {}
    payload = dict(data or {})
    payload.setdefault("host", host)
    payload.setdefault("task", task)
    payload["updatedAt"] = _now()
    payload.setdefault("createdAt", payload["updatedAt"])
    site[task] = payload
    _write_all(all_data)
    return {"ok": True, "path": str(_CALIB_FILE)}


def list_sites() -> List[str]:
    data = _read_all()
    if isinstance(data, dict):
        return list(data.keys())
    return []


def list_tasks(host: str) -> List[str]:
    data = _read_all()
    site = data.get(host) if isinstance(data, dict) else None
    if isinstance(site, dict):
        return list(site.keys())
    return []


def clear(host: Optional[str] = None, task: Optional[str] = None) -> Dict[str, Any]:
    """Clear calibration data.

    - No host/task: clear entire calib.json
    - host only: remove that host subtree
    - host + task: remove that specific draft; drop host key if empty afterwards
    """
    data = _read_all()
    if not host:
        _write_all({})
        return {"ok": True, "cleared": "all"}
    if not isinstance(data, dict):
        return {"ok": True, "cleared": "none"}
    site = data.get(host)
    if not isinstance(site, dict):
        return {"ok": True, "cleared": "none"}
    if not task:
        # remove entire host subtree
        try:
            del data[host]
        except Exception:
            pass
        _write_all(data)
        return {"ok": True, "cleared": {"host": host}}
    # remove specific task under host
    if task in site:
        try:
            del site[task]
        except Exception:
            pass
        # drop host if empty
        if not site:
            try:
                del data[host]
            except Exception:
                pass
        else:
            data[host] = site
        _write_all(data)
        return {"ok": True, "cleared": {"host": host, "task": task}}
    return {"ok": True, "cleared": "none"}


def finalize_to_config(host: str, task: str) -> Dict[str, Any]:
    # Merge calib/<host>/<task>.json into config.json runtime section
    from config import load_config, save_config  # type: ignore
    calib = load(host, task)
    if not calib:
        return {"ok": False, "error": "no_calibration"}
    cfg = load_config()
    sites = cfg.setdefault("staticFormMapping", {}).setdefault("sites", {})
    site = sites.setdefault(host, {})
    # Multi-page aware: keep backward-compat top-level based on first page if pages present
    pages = calib.get("pages") or []
    first = pages[0] if isinstance(pages, list) and pages else None
    fieldSelectors = calib.get("fieldSelectors", first.get("fieldSelectors", {}) if isinstance(first, dict) else {})
    actions = calib.get("actions", [a.get("label") for a in (first.get("actionsDetail", []) if isinstance(first, dict) else []) if a and isinstance(a, dict) and a.get("label")])
    executionOrder = calib.get("executionOrder", first.get("executionOrder", []) if isinstance(first, dict) else [])
    criticalFields = calib.get("criticalFields", first.get("criticalFields", []) if isinstance(first, dict) else [])
    actionsDetail = calib.get("actionsDetail", first.get("actionsDetail", []) if isinstance(first, dict) else [])
    actionsExecutionOrder = calib.get("actionsExecutionOrder", actions)

    site[task] = {
        "fieldSelectors": fieldSelectors,
        "actions": actions,
        "executionOrder": executionOrder,
        "criticalFields": criticalFields,
        "synonyms": calib.get("synonyms", {}),
        # New fields
        "actionsDetail": actionsDetail,
        "actionsExecutionOrder": actionsExecutionOrder,
        "pages": pages,
        "multiPage": bool(pages),
    }
    save_config(cfg)
    return {"ok": True, "merged": True, "site": host, "task": task}
