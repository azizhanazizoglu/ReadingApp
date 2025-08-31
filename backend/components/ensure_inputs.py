from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Tuple, Dict, Any
from backend.logging_utils import log_backend


@dataclass
class EnsureInputsResult:
    ruhsat_json: Dict[str, Any]
    source: str  # 'json' or 'jpg'
    path: Optional[Path] = None


class EnsureInputs:
    """Precondition handler: obtain ruhsat_json from disk or via extractor.
    Designed for unit tests with temp dirs and stub extractors.
    """

    def select_latest_or_merge_ruhsat_json(self, json_dir: Path) -> Optional[EnsureInputsResult]:
        json_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(json_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            return None
        # Pick latest for simplicity; merging could be added later
        data = json.loads(files[0].read_text(encoding="utf-8"))
        log_backend(
            "[INFO] [BE-2001] EnsureInputs: selected JSON",
            code="BE-2001",
            component="EnsureInputs",
            extra={"path": str(files[0])}
        )
        return EnsureInputsResult(ruhsat_json=data, source="json", path=files[0])

    def extract_ruhsat_from_jpg(self, jpg_dir: Path, extractor: Callable[[Path], Dict[str, Any]]) -> EnsureInputsResult:
        jpg_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(jpg_dir.glob("*.jpg"))
        if not files:
            raise FileNotFoundError("No JPG files found for extraction")
        # Use first image deterministically; callers can choose otherwise
        data = extractor(files[0])
        log_backend(
            "[INFO] [BE-2002] EnsureInputs: extracted from JPG",
            code="BE-2002",
            component="EnsureInputs",
            extra={"path": str(files[0])}
        )
        return EnsureInputsResult(ruhsat_json=data, source="jpg", path=files[0])
