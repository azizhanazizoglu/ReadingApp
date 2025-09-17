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


def save_config(new_cfg: Dict[str, Any]) -> None:
    """Persist merged config back to production2/config.json and refresh cache."""
    global _CACHED
    try:
        _CFG_PATH.write_text(json.dumps(new_cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        _CACHED = None
        load_config()  # reload into cache
    except Exception:
        # Do not crash callers; they can handle missing write permissions
        pass


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
    "model": "gpt-4o",           # fallback model (used if specific model not set)
    "mappingModel": "gpt-4o",    # model for HTML→selector mapping (F3 analyzePage)
    "visionModel": "gpt-4o-mini",# model for Vision JPEG→JSON extract (F3 ingest)
        "temperature": 0.0,
        "useHeuristics": False,         # allow heuristic salvage when LLM mapping is incomplete
        # Centralized prompt for F3 mapping (can be overridden in config.json)
        "mappingPrompt": (
            "You are an expert web UI analyzer.\n"
            "Given: (1) filtered HTML of an insurance form step, (2) extracted ruhsat JSON (vehicle registration).\n"
            "Goal: Decide page_kind and, when it's a fillable form, map logical ruhsat keys to UNIQUE, existing form control selectors on THIS page.\n\n"
            "Output: STRICT JSON ONLY, matching this schema exactly (no extra keys, no prose):\n"
            "{\n  \"page_kind\": \"fill_form\" | \"final_activation\",\n  \"field_mapping\"?: { [logical_key: string]: string /* CSS or XPath */ },\n  \"actions\"?: string[],\n  \"evidence\"?: string\n}\n\n"
            "Rules for mapping when page_kind='fill_form':\n"
            "- Include ONLY fields that are present on THIS page and visibly correspond to the ruhsat info.\n"
            "- Each selector MUST resolve to exactly one input/select/textarea (or contenteditable) element in the provided HTML.\n"
            "- Prefer stable CSS selectors in this order: #id, tag[name=...], unique data-* (e.g., [data-testid=...], [data-qa=...]), [aria-label=...], placeholder/title if UNIQUE. Use XPath only if no unique CSS is possible.\n"
            "- Do NOT fabricate selectors. If a reliable unique selector cannot be formed, OMIT that key.\n"
            "- Do NOT return labels/headings or button texts as field_mapping values.\n"
            "- If a logical field is not present on this step, simply omit it from field_mapping.\n\n"
            "If this is the final activation/confirmation page (no editable fields), return page_kind='final_activation' and provide actions as the visible CTA texts (e.g., 'Poliçeyi Aktifleştir', 'Devam').\n"
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
    ],
    # New: static-first settings for form fill
    "static": {
        "actions": ["Devam", "İleri", "Ileri", "Kaydet", "Poliçeyi Aktifleştir", "Aktifleştir"],
        "fallbackThreshold": 0.75,
        # Global synonyms (can be overridden per-scenario)
        "synonyms": {
            "plaka_no": ["plaka", "plaka no", "plaka numarası", "araç plakası", "plate", "license plate"],
            "sasi_no": ["şasi", "şasi no", "şasi numarası", "vin", "chassis"],
            "model_yili": ["model yılı", "yıl", "model year", "production year"],
            "motor_no": ["motor no", "motor numarası", "engine number"],
            "marka": ["marka", "brand", "make"],
            "model": ["model", "araç modeli", "vehicle model"],
            "yakit": ["yakit", "yakıt", "fuel"],
            "renk": ["renk", "color", "colour"]
        },
        "criticalFields": {
            "Yeni Trafik": ["plaka_no", "model_yili", "sasi_no", "motor_no"]
        },
        "scenarios": {
            "Yeni Trafik": {
                # Add any id/name selector hints if the site is known
                "criticalSelectors": {
                    # Example hints (safe, only applied if present)
                    "plaka_no": ["#plate", "[name='plaka']", "input[aria-label='Plaka']"],
                    "model_yili": ["[name='modelYili']", "input[placeholder*='Model']"],
                    "sasi_no": ["[name='sasi']", "[name='vin']", "input[placeholder*='Şasi']"],
                    "motor_no": ["[name='motorNo']", "input[placeholder*='Motor']"]
                }
            }
        }
    }
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
