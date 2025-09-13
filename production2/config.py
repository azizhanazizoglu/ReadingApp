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
    "staticMaxCandidates": 40,
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


def get_static_max_candidates_find_home_page() -> int:
    val = get("findHomePage.staticMaxCandidates")
    try:
        ival = int(val) if val is not None else int(DEFAULT_CONFIG["findHomePage"]["staticMaxCandidates"])  # type: ignore[index]
        return ival if ival > 0 else 40
    except Exception:
        return 40

# --- New: goUserTaskPage ---

DEFAULT_CONFIG.setdefault("goUserTaskPage", {
    "staticMaxCandidates": 50,
    "mapping": {
        "max_alternatives": 12
    },
    "stateflow": {
        "maxLoops": 6,
        "maxStaticTries": 8,
        "maxLLMTries": 3,
        "waitAfterClickMs": 800
    },
    "letLLMMap_goUserTask": {
        "defaultPrompt": (
            "You are an expert web UI analyzer. From the given filtered HTML and the user task label, "
            "identify the single control that opens the requested task/page. The label is flexible and may be in Turkish or English; "
            "use fuzzy matching on visible text, aria-label/title, and data-* (e.g., data-component-content with URL-encoded text).\n\n"
            "Selector rules:\n- Allowed selectorType: text | css | xpath.\n- Prefer the clickable ancestor (<a> or <button>) that contains the label or icon.\n"
            "Output STRICT JSON only: {\n  \"selectorType\": \"css|xpath|text\",\n  \"selector\": \"<string>\",\n  \"alternatives\": [\"<string>\"],\n  \"rationale\": \"<short reason>\"\n}"
        ),
        "maxAttempts": 4
    }
})

# --- New: goFillForms (F3) ---

DEFAULT_CONFIG.setdefault("goFillForms", {
    "input": {
        "jsonPath": "",              # optional prepared ruhsat json
    "imageDir": "tmp/data",      # where staged images are stored (relative to production2 root)
    "sourceDir": ""              # optional: auto-copy latest from this dir into imageDir on F3
    },
    "llm": {
        "model": "gpt-4o",           # model for both vision and mapping
        "temperature": 0.0,
        # Centralized prompt for F3 mapping (can be overridden in config.json)
        "mappingPrompt": (
            "You are an expert web UI analyzer. Task: Given filtered HTML of an insurance form page "
            "and extracted ruhsat JSON (vehicle registration), decide if this is a fillable form page or the final activation page.\n\n"
            "If fillable, return a JSON with keys: page_kind='fill_form', field_mapping (map logical keys to selectors), and optional actions (button texts like 'Devam', 'İleri').\n"
            "If final activation page, return page_kind='final_activation' and actions containing visible final CTA texts, e.g., 'Poliçeyi Aktifleştir'.\n\n"
            "VERY IMPORTANT mapping rules:\n"
            "- Only include fields that are PRESENT on THIS page. Do NOT include fields from other steps/pages.\n"
            "- Each field_mapping selector MUST point to exactly one input/select/textarea element (unique). Avoid container/form selectors.\n"
			"- Prefer stable CSS like #id, input[name=...], select[name=...], textarea[name=...]. If id/name are missing but the element has a unique data-lov-id attribute, use [data-lov-id='...']. Use XPath only when CSS is not possible.\n"
            "- For clicks in actions, you may return visible texts (e.g., 'Devam'), but DO NOT put text:... into field_mapping.\n"
            "Output STRICT JSON only with keys: {page_kind, field_mapping?, actions?, evidence?}.\n"
        )
    },
    "persist": {
        "dir": "tmp/ruhsat_json"     # where to store normalized extractions (optional)
    },
    "stateflow": {
        "maxLoops": 10,
    "waitAfterActionMs": 600,
    "maxLLMTries": 3,
    # New: timing knobs for field filling/verification (used by UI SF)
    # Per-field attempts wait list (ms) e.g. 3 attempts
    "perFieldAttemptWaits": [250, 400, 600],
    # Extra delay after each single-field fill before verifying (ms)
    "postFillVerifyDelayMs": 200,
    # Delay before running html-only filled check (ms)
    "htmlCheckDelayMs": 200,
    # Commit behavior flags
    "commitEnter": True,
    "clickOutside": True
    },
    "finalCtas": [
        "Poliçeyi Aktifleştir", "Policeyi Aktiflestir", "Poliçeyi Üret", "Poliçeyi Yazdır"
    ]
})

def get_go_fill_forms(key: str, default: Any = None) -> Any:
    return get(f"goFillForms.{key}", default)


def get_static_max_candidates_go_user_task() -> int:
    val = get("goUserTaskPage.staticMaxCandidates")
    try:
        return int(val) if val is not None else int(DEFAULT_CONFIG["goUserTaskPage"]["staticMaxCandidates"])  # type: ignore[index]
    except Exception:
        return 50


def get_map_user_task(key: str, default: Any = None) -> Any:
    return get(f"goUserTaskPage.mapping.{key}", default)


def get_llm_prompt_go_user_task_default() -> str:
    val = get("goUserTaskPage.letLLMMap_goUserTask.defaultPrompt")
    if isinstance(val, str) and val.strip():
        return val
    return DEFAULT_CONFIG["goUserTaskPage"]["letLLMMap_goUserTask"]["defaultPrompt"]  # type: ignore[index]


def get_llm_max_attempts_go_user_task() -> int:
    val = get("goUserTaskPage.letLLMMap_goUserTask.maxAttempts")
    try:
        ival = int(val) if val is not None else int(DEFAULT_CONFIG["goUserTaskPage"]["letLLMMap_goUserTask"]["maxAttempts"])  # type: ignore[index]
        return ival if ival > 0 else 4
    except Exception:
        return 4


def get_go_user_task_stateflow(key: str, default: Any = None) -> Any:
    return get(f"goUserTaskPage.stateflow.{key}", default)
