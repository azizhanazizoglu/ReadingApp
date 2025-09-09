from __future__ import annotations

"""Production2 configuration loader.

Loads a JSON config file from production2/config.json and merges it over
defaults. Provides small helpers to access settings safely.
"""

from pathlib import Path
import json
from typing import Any, Dict, List, Optional

_HERE = Path(__file__).resolve().parent  # production2
_CFG_PATH = _HERE / "config.json"


DEFAULT_CONFIG: Dict[str, Any] = {
    "findHomePage": {
        "map_home_page_stetic": {
            "variants": [
                # Turkish variants
                "ana sayfa", "anasayfa", "ana-sayfa", "ana_sayfa",
                # English variants
                "home", "homepage", "home-page", "home_page",
                # Generic fallbacks
                "main", "start", "dashboard", "portal",
            ],
            "max_alternatives": 10,
        },
        # LLM fallback defaults for findHomePage
        "letLLMMap_findHomePage": {
            "defaultPrompt": (
                "You are an expert web UI analyzer. Task: From the given filtered HTML, "
                "identify the most likely navigation control that returns the user to the Home page. "
                "Consider these labels and variants: 'Ana Sayfa', 'Anasayfa', 'Home', 'Homepage', 'Dashboard', 'Main'. "
                "Prefer visible navigation links, buttons, or icons with descriptive attributes (aria-label, title, data-*).\n\n"
                "Output strict JSON only with this schema: {\n"
                "  \"selectorType\": \"css|xpath|text\",\n"
                "  \"selector\": \"<string>\",\n"
                "  \"alternatives\": [\"<string>\", ...],\n"
                "  \"rationale\": \"<short reason>\"\n"
                "}. Do not include any prose outside of JSON."
            ),
            "maxAttempts": 3
        }
    }
}

_CACHED: Optional[Dict[str, Any]] = None


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config() -> Dict[str, Any]:
    global _CACHED
    if _CACHED is not None:
        return _CACHED
    data: Dict[str, Any] = {}
    if _CFG_PATH.exists():
        try:
            data = json.loads(_CFG_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    _CACHED = _deep_merge(DEFAULT_CONFIG, data)
    return _CACHED


def get(path: str, default: Any = None) -> Any:
    cfg = load_config()
    cur: Any = cfg
    for part in path.split("."):
        if not isinstance(cur, dict):
            return default
        cur = cur.get(part)
        if cur is None:
            return default
    return cur


def get_find_homepage_variants() -> List[str]:
    vals = get("findHomePage.map_home_page_stetic.variants")
    return list(vals) if isinstance(vals, list) else list(DEFAULT_CONFIG["findHomePage"]["map_home_page_stetic"]["variants"])  # type: ignore[index]


def get_map_home_page_stetic(key: str, default: Any = None) -> Any:
    return get(f"findHomePage.map_home_page_stetic.{key}", default)


def get_llm_prompt_find_home_page_default() -> str:
    val = get("findHomePage.letLLMMap_findHomePage.defaultPrompt")
    if isinstance(val, str) and val.strip():
        return val
    return DEFAULT_CONFIG["findHomePage"]["letLLMMap_findHomePage"]["defaultPrompt"]  # type: ignore[index]


def get_llm_max_attempts_find_home_page() -> int:
    val = get("findHomePage.letLLMMap_findHomePage.maxAttempts")
    try:
        ival = int(val) if val is not None else int(DEFAULT_CONFIG["findHomePage"]["letLLMMap_findHomePage"]["maxAttempts"])  # type: ignore[index]
        return ival if ival > 0 else 3
    except Exception:
        return 3
