from __future__ import annotations

from typing import Dict, Any, List
from backend.logging_utils import log_backend


class ScriptFiller:
    """Generates a minimal JS plan to fill fields and click actions.
    Keeps logic tiny for testability; execution is done by the webview.
    """

    def generate_and_execute_fill_script(self, mapping: Dict[str, Any]) -> str:
        # Normalize mapping into fields/actions lists of dicts
        fields_iter: List[Dict[str, Any]] = []
        actions_iter: List[Dict[str, Any]] = []

        try:
            # Fields: prefer explicit list; else build from field_mapping dict
            raw_fields = mapping.get("fields") if isinstance(mapping, dict) else None
            if isinstance(raw_fields, list) and raw_fields:
                for item in raw_fields:
                    if isinstance(item, dict):
                        fields_iter.append(item)
                    elif isinstance(item, str) and item:
                        fields_iter.append({"selector": item, "value": ""})
            else:
                fm = mapping.get("field_mapping", {}) if isinstance(mapping, dict) else {}
                if isinstance(fm, dict) and fm:
                    for _key, sel in fm.items():
                        if isinstance(sel, str) and sel:
                            fields_iter.append({"selector": sel, "value": ""})

            # Actions: accept list of dicts or strings
            raw_actions = mapping.get("actions", []) if isinstance(mapping, dict) else []
            if isinstance(raw_actions, list) and raw_actions:
                for item in raw_actions:
                    if isinstance(item, dict):
                        if item.get("selector"):
                            actions_iter.append({"selector": item.get("selector")})
                    elif isinstance(item, str) and item:
                        # Support minimal prefixes like "css#..." or plain CSS
                        selector = item
                        if selector.startswith("css#"):
                            selector = selector.split("#", 1)[1]
                        actions_iter.append({"selector": selector})

            # Build small previews
            def _preview(lst, key="selector"):
                out = []
                for it in lst[:6]:
                    try:
                        sel = it.get(key) if isinstance(it, dict) else str(it)
                        if isinstance(sel, str):
                            out.append(sel[:120])
                    except Exception:
                        pass
                return out
            log_backend(
                "[INFO] [BE-2950] ScriptFiller: building fill script",
                code="BE-2950",
                component="ScriptFiller",
                extra={"fields": len(fields_iter), "actions": len(actions_iter), "fields_preview": _preview(fields_iter), "actions_preview": _preview(actions_iter)}
            )
        except Exception:
            pass

        lines = [
            "(function(){",
            "  const sel = (s)=>document.querySelector(s);",
        ]
        # Write field values when possible (value may be empty string if not provided)
        for fld in fields_iter:
            try:
                selector = fld.get("selector")
                value = fld.get("value", "")
                if selector:
                    lines.append(f"  if(sel('{selector}')) sel('{selector}').value = {repr(value)};")
            except Exception:
                continue
        # Click actions
        for act in actions_iter:
            try:
                selector = act.get("selector")
                if selector:
                    lines.append(f"  if(sel('{selector}')) sel('{selector}').click();")
            except Exception:
                continue
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
