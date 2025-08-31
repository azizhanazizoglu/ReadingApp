from __future__ import annotations

from typing import Dict, Any
from backend.logging_utils import log_backend


class ScriptFiller:
    """Generates a minimal JS plan to fill fields and click actions.
    Keeps logic tiny for testability; execution is done by the webview.
    """

    def generate_and_execute_fill_script(self, mapping: Dict[str, Any]) -> str:
        # Log mapping/plan summary for diagnostics
        try:
            fields = mapping.get("fields", []) or mapping.get("field_mapping", {})
            field_count = (len(fields) if isinstance(fields, list) else len(fields)) if fields is not None else 0
            action_count = len(mapping.get("actions", []) or [])
            log_backend(
                "[INFO] [BE-2950] ScriptFiller: building fill script",
                code="BE-2950",
                component="ScriptFiller",
                extra={"fields": field_count, "actions": action_count}
            )
        except Exception:
            pass
        lines = [
            "(function(){",
            "  const sel = (s)=>document.querySelector(s);",
        ]
        for fld in mapping.get("fields", []):
            selector = fld.get("selector")
            value = fld.get("value")
            if selector is not None:
                lines.append(f"  if(sel('{selector}')) sel('{selector}').value = {repr(value)};")
        for act in mapping.get("actions", []):
            selector = act.get("selector")
            if selector is not None:
                lines.append(f"  if(sel('{selector}')) sel('{selector}').click();")
        lines.append("})();")
        script = "\n".join(lines)
        try:
            log_backend(
                "[INFO] [BE-2951] ScriptFiller: script generated",
                code="BE-2951",
                component="ScriptFiller",
                extra={"bytes": len(script)}
            )
        except Exception:
            pass
        return script
