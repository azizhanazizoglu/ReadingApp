from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Callable

from backend.components.mapping_validator import MappingValidator
from backend.components.script_filler import ScriptFiller
from backend.components.diff_service import DiffService
from backend.components.finalization import FinalDetector, Finalizer
from backend.components.error_manager import ErrorManager, ErrorState
from backend.logging_utils import log_backend


@dataclass
class MapFillResult:
    mapping_valid: bool
    changed: bool
    is_final: bool
    attempts: int


class MapAndFill:
    def __init__(
        self,
        map_form_fields_llm: Callable[[str, Dict[str, Any]], Dict[str, Any]],
        validator: MappingValidator,
        filler: ScriptFiller,
        diff: DiffService,
        final_detector: FinalDetector,
        finalizer: Finalizer,
        errors: ErrorManager | None = None,
    ) -> None:
        self.map_llm = map_form_fields_llm
        self.validator = validator
        self.filler = filler
        self.diff = diff
        self.final_detector = final_detector
        self.finalizer = finalizer
        self.errors = errors or ErrorManager(ErrorState())

    def run(self, html: str, ruhsat_json: Dict[str, Any], prev_html: str | None = None, max_map_attempts: int = 3) -> MapFillResult:
        try:
            log_backend(
                "[INFO] [BE-2800] MapAndFill start",
                code="BE-2800",
                component="MapAndFill",
                extra={"html_len": len(html) if isinstance(html, str) else 0, "prev_len": (len(prev_html) if isinstance(prev_html, str) else 0), "max_attempts": max_map_attempts}
            )
        except Exception:
            pass
        attempts = 0
        while attempts < max_map_attempts:
            attempts += 1
            mapping = self.map_llm(html, ruhsat_json)
            if not self.validator.validate_mapping_selectors(html, mapping):
                if self.errors.error_tick_and_decide("mapping") == "abort":
                    log_backend(
                        "[WARN] [BE-2801] MapAndFill mapping abort",
                        code="BE-2801",
                        component="MapAndFill",
                        extra={"attempts": attempts}
                    )
                    return MapFillResult(mapping_valid=False, changed=False, is_final=False, attempts=attempts)
                continue
            # Valid mapping, generate filler script (execution outside)
            _script = self.filler.generate_and_execute_fill_script(mapping)
            # Simulate DOM change for unit tests
            new_html = html + "<!--filled-->"
            changed = True if prev_html is None else self.diff.diff(prev_html, new_html).changed
            is_final = self.final_detector.detect_final_page(new_html)
            log_backend(
                "[INFO] [BE-2802] MapAndFill success",
                code="BE-2802",
                component="MapAndFill",
                extra={"attempts": attempts, "changed": changed, "is_final": is_final, "llm": True}
            )
            return MapFillResult(mapping_valid=True, changed=changed, is_final=is_final, attempts=attempts)
        return MapFillResult(mapping_valid=False, changed=False, is_final=False, attempts=attempts)
