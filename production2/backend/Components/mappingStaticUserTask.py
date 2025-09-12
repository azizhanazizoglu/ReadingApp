from typing import List, Dict, Any, Optional
import json
import os
import unicodedata
from pathlib import Path

# mappingStaticUserTask.py
"""
Static candidate mappings for the 'Yeni Trafik' (New Traffic) user task button.
Pattern is intentionally similar to mappingStatic.py (not shown here).
External project-specific variants can be appended from config.json at runtime.
"""


# Base static candidates (can be extended via config)
# NOTE: Keep synonyms here MINIMAL; full project-specific list should live in config.json
# under root key "userTaskButtons" so that deployments / customers can adjust without
# changing source code. Only the base_label is required here for bootstrap.
BASE_USER_TASK_CANDIDATES: List[Dict[str, Any]] = [
    {
        "id": "userTask.newTraffic",
        "base_label": "Yeni Trafik",
    # Keep only the canonical label; everything else should come from config.json
    "synonyms": ["Yeni Trafik"],
        "selectors": [
            # Direct text-based (exact)
            {"type": "text", "value": "Yeni Trafik"},
            # XPATH robust to nested span
            {"type": "xpath", "value": "//button[.//span[normalize-space()='Yeni Trafik']]"},
            # Fallback: any button containing the words (Turkish)
            {"type": "xpath", "value": "//button[contains(translate(., 'YENITRAF K', 'yenitraf k'), 'yeni') and contains(translate(., 'YENITRAF K', 'yenitraf k'), 'trafik')]"},
            # CSS (note :contains not standard in pure CSS, but some libs support it)
            {"type": "css", "value": "button span:contains('Yeni Trafik')"},
        ],
        "priority": 100,
        "category": "userTaskButton"
    }
]

def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.strip().lower()

def _default_config_path() -> Optional[str]:
    """Locate the canonical production2/config.json relative to this file."""
    try:
        prod_root = Path(__file__).resolve().parents[2]  # .../production2
        cfg = prod_root / "config.json"
        return str(cfg) if cfg.is_file() else None
    except Exception:
        return None


def load_config_variants(config_path: Optional[str]) -> List[Dict[str, Any]]:
    """
    Load extra variants from a config.json if it has:
    {
      "userTaskButtons": [
         {
           "id": "...",
           "addSynonyms": ["..."],
           "overrideSynonyms": ["..."],
           "extraSelectors": [{ "type":"xpath", "value":"..." }]
         }
      ]
    }
    """
    if not config_path:
        config_path = _default_config_path()
    if not config_path or not os.path.isfile(config_path):
        return []
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Support both top-level userTaskButtons and nested goUserTaskPage.userTaskButtons
        top = data.get("userTaskButtons", []) or []
        nested = []
        try:
            nested_cfg = data.get("goUserTaskPage", {})
            if isinstance(nested_cfg, dict):
                nested_list = nested_cfg.get("userTaskButtons", [])
                if isinstance(nested_list, list):
                    nested = nested_list
        except Exception:
            pass
        return (top + nested) if (top or nested) else []
    except Exception:
        return []

def merge_config(base: List[Dict[str, Any]], config_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_id = {c["id"]: c for c in base}
    for item in config_items:
        cid = item.get("id")
        if not cid:
            continue
        if cid not in by_id:
            # Allow entirely new button definitions
            by_id[cid] = {
                "id": cid,
                "base_label": item.get("base_label", cid),
                "synonyms": item.get("overrideSynonyms") or item.get("addSynonyms", []),
                "selectors": item.get("extraSelectors", []),
                "priority": item.get("priority", 50),
                "category": "userTaskButton"
            }
            continue

        target = by_id[cid]
        if "overrideSynonyms" in item and item["overrideSynonyms"]:
            target["synonyms"] = item["overrideSynonyms"]
        if "addSynonyms" in item and item["addSynonyms"]:
            # keep uniqueness
            existing_norm = {_normalize(s): s for s in target["synonyms"]}
            for syn in item["addSynonyms"]:
                n = _normalize(syn)
                if n not in existing_norm:
                    target["synonyms"].append(syn)
        if "extraSelectors" in item and item["extraSelectors"]:
            # Append then deduplicate by (type,value)
            existing = {(s.get("type"), s.get("value")) for s in target["selectors"] if isinstance(s, dict)}
            for sel in item["extraSelectors"]:
                if not isinstance(sel, dict):
                    continue
                key = (sel.get("type"), sel.get("value"))
                if key not in existing:
                    target["selectors"].append(sel)
                    existing.add(key)
        if "priority" in item:
            target["priority"] = item["priority"]
    # Deduplicate synonyms
    for c in by_id.values():
        seen = set()
        uniq = []
        for s in c["synonyms"]:
            n = _normalize(s)
            if n not in seen:
                seen.add(n)
                uniq.append(s)
        c["synonyms"] = uniq
        # Deduplicate selectors list
        if isinstance(c.get("selectors"), list):
            sel_seen = set()
            sel_uniq = []
            for sel in c["selectors"]:
                if not isinstance(sel, dict):
                    continue
                key = (sel.get("type"), sel.get("value"))
                if key not in sel_seen:
                    sel_seen.add(key)
                    sel_uniq.append(sel)
            c["selectors"] = sel_uniq
    return list(by_id.values())

def get_user_task_candidates(config_path: Optional[str] = None) -> List[Dict[str, Any]]:
    cfg_items = load_config_variants(config_path)
    return merge_config(BASE_USER_TASK_CANDIDATES, cfg_items)

def score_text_against_candidate(text: str, candidate: Dict[str, Any]) -> float:
    """
    Simple heuristic scoring.
    1.0 exact synonym match
    0.85 partial (substring) match
    0.70 token overlap
    else 0
    """
    t_norm = _normalize(text)
    best = 0.0
    for syn in candidate["synonyms"]:
        s_norm = _normalize(syn)
        if t_norm == s_norm:
            return 1.0
        if t_norm in s_norm or s_norm in t_norm:
            best = max(best, 0.85)
        else:
            t_tokens = set(t_norm.split())
            s_tokens = set(s_norm.split())
            inter = t_tokens & s_tokens
            if inter:
                ratio = len(inter) / max(len(s_tokens), 1)
                if ratio >= 0.5:
                    best = max(best, 0.70 * ratio)
    return best

def find_best_user_task_button(user_input: str, config_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Given user free-form text, return best matching candidate enriched with score.
    """
    candidates = get_user_task_candidates(config_path)
    scored = []
    for c in candidates:
        score = score_text_against_candidate(user_input, c)
        if score > 0:
            scored.append((score, c["priority"], c))
    if not scored:
        return None
    scored.sort(key=lambda x: (-x[0], -x[1]))
    result = dict(scored[0][2])
    result["matchScore"] = scored[0][0]
    return result

# Example usage (remove or guard if importing elsewhere)
if __name__ == "__main__":
    test_inputs = [
        "Yeni Trafik",
        "Trafik Ekle",
        "Add Traffic",
        "Create New Traffic Record",
        "trafik kaydı"
    ]
    for ti in test_inputs:
        print(ti, "=>", find_best_user_task_button(ti))