from __future__ import annotations

"""uploadToSystemData

Centralized helper to stage input files for F3 into a stable data directory.

- Target directory is configured via goFillForms.input.imageDir (default: tmp/data)
- Optional source directory goFillForms.input.sourceDir can be used to auto-copy
  latest JPG/PNG (and its companion .json if present) into the target.
- Used by both /api/upload and F3 ingest to keep a single path for inputs.
"""

from pathlib import Path as _Path
from typing import Optional, Tuple, List, Dict, Any
import shutil
import os

_THIS = _Path(__file__).resolve()
_ROOT = _THIS.parents[2]  # production2

import sys as _sys
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

from config import get  # type: ignore
try:
    from logging_utils import log as _log  # type: ignore
except Exception:
    def _log(*args, **kwargs):
        try:
            print("[UPLOAD2DATA]", *args)
        except Exception:
            pass


def _get_target_dir() -> _Path:
    d = get("goFillForms.input.imageDir", "tmp/data")
    p = _ROOT / d if not os.path.isabs(str(d)) else _Path(d)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _get_source_dir() -> Optional[_Path]:
    d = get("goFillForms.input.sourceDir")
    if not isinstance(d, str) or not d.strip():
        return None
    p = _ROOT / d if not os.path.isabs(str(d)) else _Path(d)
    return p if p.exists() else None


def _latest_file(dir_path: _Path, patterns: Tuple[str, ...] = ("*.jpg", "*.jpeg", "*.png")) -> Optional[_Path]:
    cands: List[Tuple[float, _Path]] = []
    for pat in patterns:
        for p in dir_path.glob(pat):
            try:
                cands.append((p.stat().st_mtime, p))
            except Exception:
                pass
    if not cands:
        return None
    cands.sort(key=lambda x: x[0], reverse=True)
    return cands[0][1]


def clear_target_images() -> None:
    tgt = _get_target_dir()
    for pat in ("*.jpg", "*.jpeg", "*.png"):
        for p in tgt.glob(pat):
            try:
                p.unlink()
            except Exception:
                pass


def copy_latest_from_source() -> Dict[str, Any]:
    """Copy the latest image from sourceDir into target data dir.

    Also copies companion JSON (same stem) if available.
    Returns metadata for observability.
    """
    tgt = _get_target_dir()
    src = _get_source_dir()
    meta: Dict[str, Any] = {"target": str(tgt), "source": str(src) if src else None}
    if not src or not src.exists():
        _log("INFO", "UPLOAD2DATA", "no sourceDir configured or not found", component="F3", extra=meta)
        return {"ok": True, "copied": False, "meta": meta}

    latest = _latest_file(src)
    if not latest:
        _log("INFO", "UPLOAD2DATA", "no images in sourceDir", component="F3", extra=meta)
        return {"ok": True, "copied": False, "meta": meta}

    # Clear previous to avoid ambiguity
    clear_target_images()

    dest = tgt / latest.name
    shutil.copy2(str(latest), str(dest))
    meta["image"] = str(dest)

    # companion json
    comp = latest.with_suffix(".json")
    if comp.exists():
        comp_dest = dest.with_suffix(".json")
        try:
            shutil.copy2(str(comp), str(comp_dest))
            meta["companion_json"] = str(comp_dest)
        except Exception:
            pass

    _log("INFO", "UPLOAD2DATA", f"copied latest to {dest}", component="F3", extra=meta)
    return {"ok": True, "copied": True, "meta": meta}


def stage_uploaded_file(data: bytes, original_name: str) -> Dict[str, Any]:
    """Save uploaded file bytes into target data directory.

    Clears older images first; preserves extension from original_name.
    """
    tgt = _get_target_dir()
    clear_target_images()
    ext = (original_name.split(".")[-1] or "").lower()
    if ext not in {"jpg", "jpeg", "png"}:
        ext = "jpg"
    out = tgt / f"ruhsat_upload.{ext}"
    out.write_bytes(data)
    _log("INFO", "UPLOAD2DATA", f"staged uploaded file {out}", component="F3", extra={"size": len(data)})
    return {"ok": True, "path": str(out)}


def ensure_f3_data_ready() -> Dict[str, Any]:
    """Best-effort preparation before F3 ingest.

    If a sourceDir is configured, copy the latest image into the data dir.
    Always returns ok=True to avoid blocking; ingest will report precise issues.
    """
    try:
        res = copy_latest_from_source()
        return {"ok": True, "prepared": res.get("copied", False), "meta": res.get("meta")}
    except Exception as e:
        _log("WARN", "UPLOAD2DATA", f"prepare failed: {e}", component="F3")
        return {"ok": True, "prepared": False, "error": str(e)}
