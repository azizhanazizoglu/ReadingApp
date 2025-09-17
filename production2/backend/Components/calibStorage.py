from __future__ import annotations

"""Calibration storage helpers.

Persist and retrieve calibration drafts per host/task under production2/calib,
and provide a function to merge a draft into config.json for runtime usage.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import re
import time
from urllib.parse import urlparse

_THIS = Path(__file__).resolve()
_ROOT = _THIS.parents[2]
_CALIB = _ROOT / "calib"
_CALIB.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def host_from_url(u: Optional[str]) -> str:
    try:
        return urlparse(u or "").hostname or "unknown"
    except Exception:
        return "unknown"


def _site_dir(host: str) -> Path:
    p = _CALIB / host
    p.mkdir(parents=True, exist_ok=True)
    return p


def _safe_task(task: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-\. ]+", "_", task or "task")


def task_file(host: str, task: str) -> Path:
    return _site_dir(host) / f"{_safe_task(task)}.json"


def load(host: str, task: str) -> Dict[str, Any]:
    p = task_file(host, task)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save(host: str, task: str, data: Dict[str, Any]) -> Dict[str, Any]:
    p = task_file(host, task)
    data = dict(data or {})
    data.setdefault("host", host)
    data.setdefault("task", task)
    data["updatedAt"] = _now()
    data.setdefault("createdAt", data["updatedAt"])
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "path": str(p)}


def list_sites() -> List[str]:
    return [d.name for d in _CALIB.iterdir() if d.is_dir()]


def list_tasks(host: str) -> List[str]:
    p = _site_dir(host)
    return [f.stem for f in p.glob("*.json")]


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
