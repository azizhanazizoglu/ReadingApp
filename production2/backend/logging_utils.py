from __future__ import annotations

from collections import deque
from datetime import datetime
from threading import Lock
from typing import Any, Deque, Dict, List, Optional

_LOCK = Lock()
_MAX = 500
_LOGS: Deque[Dict[str, Any]] = deque(maxlen=_MAX)


def log(level: str, code: str, message: str, *, component: str = "backend", extra: Optional[Dict[str, Any]] = None) -> None:
    rec = {
        "time": datetime.utcnow().isoformat() + "Z",
        "level": level.upper(),
        "code": code,
        "component": component,
        "message": message,
        "extra": extra or {},
    }
    with _LOCK:
        _LOGS.append(rec)


def get_log_records() -> List[Dict[str, Any]]:
    with _LOCK:
        return list(_LOGS)


def clear_log_records() -> None:
    with _LOCK:
        _LOGS.clear()
