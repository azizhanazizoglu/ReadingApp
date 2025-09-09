


from __future__ import annotations

from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path as _Path
import json
import sys
import hashlib
from dataclasses import asdict

# Make production2 importable to reach memory and config
_this = _Path(__file__).resolve()
_root = _this.parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from config import get_find_homepage_variants, get_map_home_page_stetic  # type: ignore
from memory import MappingJson, MappingMeta, MappingAction, MappingCandidate  # type: ignore

def map_home_page_static(html: Optional[str] = None, name: Optional[str] = None) -> MappingJson:
    """Scan filtered HTML for 'Home' button variants and save a mapping JSON.

    - Inputs:
      - html: filtered HTML; if None, uses memory.html.get_last_html()
      - name: optional base name for the mapping file
    - Output file: production2/tmp/jsonMappings/<name>.json
    - Returns: MappingJson (meta, mapping, candidates)
    """
    variants: List[str] = get_find_homepage_variants()

    def canon(s: str) -> str:
        return (s or "").casefold().replace(" ", "").replace("-", "").replace("_", "")

    wanted = {canon(v) for v in variants}

    # Source HTML (filtered) - require explicit input (no global memory fallback)
    filtered_html = html
    if not filtered_html:
        return {"ok": False, "error": "no_filtered_html"}

    # Try BeautifulSoup; fallback to regex if unavailable
    soup = None
    try:
        from bs4 import BeautifulSoup  # type: ignore
        soup = BeautifulSoup(filtered_html, "html.parser")
    except Exception:
        soup = None

    candidates: List[Dict[str, Any]] = []

    def pick_text(tag) -> str:
        if tag is None:
            return ""
        if getattr(tag, "name", "") == "input":
            return (tag.get("value") or tag.get("aria-label") or tag.get("title") or tag.get("data-label") or "").strip()
        # buttons/links: use visible text first
        txt = (tag.get_text(separator=" ", strip=True) or "").strip()
        if not txt:
            txt = (tag.get("aria-label") or tag.get("title") or tag.get("data-label") or "").strip()
        return txt

    def score_for(text: str, tag_name: str) -> int:
        c = canon(text)
        if not c:
            return 0
        base = 0
        # prioritize tag types
        if tag_name == "button":
            base += 3
        elif tag_name == "a":
            base += 2
        elif tag_name == "input":
            base += 1
        # exact match highest
        if c in wanted:
            return base + 5
        # contains match
        if any(w in c for w in wanted):
            return base + 3
        return 0

    def selectors_for(tag) -> Dict[str, List[str]]:
        sels: Dict[str, List[str]] = {"css": [], "heuristic": []}
        if tag is None:
            return sels
        t = getattr(tag, "name", "") or "*"
        tid = (tag.get("id") or "").strip()
        tname = (tag.get("name") or "").strip()
        aria = (tag.get("aria-label") or "").strip()
        href = (tag.get("href") or "").strip()
        val = (tag.get("value") or "").strip()
        role = (tag.get("role") or "").strip()
        text = pick_text(tag)
        if tid:
            sels["css"].append(f"#{tid}")
        if tname:
            sels["css"].append(f"{t}[name='{tname}']")
        if aria:
            sels["css"].append(f"{t}[aria-label='{aria}']")
        if role == "button":
            sels["css"].append(f"{t}[role='button']")
        if href and t == "a":
            sels["css"].append(f"a[href='{href}']")
        if val and t == "input":
            sels["css"].append(f"input[value='{val}']")
        if text:
            # pseudo locator; UI executor can interpret text:= contains
            sels["heuristic"].append(f"text:{text}")
        return sels

    if soup is not None:
        # consider buttons, anchors, inputs of type=button/submit
        elems = []
        elems += list(soup.find_all("button"))
        elems += list(soup.find_all("a"))
        elems += list(soup.find_all("input"))
        for el in elems:
            tname = getattr(el, "name", "")
            if tname == "input":
                itype = (el.get("type") or "").lower()
                if itype not in ("button", "submit", "image"):
                    continue
            text = pick_text(el)
            s = score_for(text, tname)
            if s <= 0:
                continue
            attrs = {k: v for k, v in (el.attrs or {}).items() if k in {"id", "name", "type", "href", "aria-label", "title", "value", "role"}}
            candidates.append({
                "type": tname or "*",
                "text": text,
                "attributes": attrs,
                "selectors": selectors_for(el),
                "score": s,
                "action": "click",
            })
    else:
        # regex fallback: search for tags containing home-like words
        import re as _re
        html_src = filtered_html
        pat = _re.compile(r"<(button|a)[^>]*>(.*?)</\1>|<input[^>]*>", _re.IGNORECASE | _re.DOTALL)
        for m in pat.finditer(html_src):
            tag = (m.group(1) or "input").lower()
            inner = m.group(2) or ""
            # extract attrs simple
            tag_src = m.group(0)
            text = _re.sub(r"<[^>]+>", " ", inner)
            text = _re.sub(r"\s+", " ", text).strip()
            # attrs
            attrs = {}
            for key in ["id", "name", "type", "href", "aria-label", "title", "value", "role"]:
                mm = _re.search(fr"{key}=['\"]([^'\"]+)['\"]", tag_src, _re.IGNORECASE)
                if mm:
                    attrs[key] = mm.group(1)
            # attempt text from attrs if empty
            if not text:
                text = attrs.get("value") or attrs.get("aria-label") or attrs.get("title") or ""
            s = score_for(text, tag)
            if s <= 0:
                continue
            # minimal selectors
            css = []
            if attrs.get("id"):
                css.append(f"#{attrs['id']}")
            if attrs.get("name"):
                css.append(f"{tag}[name='{attrs['name']}']")
            if attrs.get("aria-label"):
                css.append(f"{tag}[aria-label='{attrs['aria-label']}']")
            selectors = {"css": css, "heuristic": [f"text:{text}"] if text else []}
            candidates.append({
                "type": tag,
                "text": text,
                "attributes": attrs,
                "selectors": selectors,
                "score": s,
                "action": "click",
            })

    # prioritize candidates by score desc, then by specificity (id present)
    def has_id(c):
        return 1 if c.get("attributes", {}).get("id") else 0
    candidates.sort(key=lambda c: (c.get("score", 0), has_id(c)), reverse=True)

    # Prepare output dir and filename
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%fZ")
    base = name or "home_buttons"
    out_dir = _root / "tmp" / "jsonMappings"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Clean directory (like get_save_Html does for tmp/html)
    try:
        for p in out_dir.iterdir():
            try:
                if p.is_file() or p.is_symlink():
                    p.unlink()
                elif p.is_dir():
                    import shutil as _sh
                    _sh.rmtree(p)
            except Exception:
                pass
    except Exception:
        pass

    # compute a local fingerprint (stateless)
    try:
        html_fp = hashlib.sha256(filtered_html.encode("utf-8")).hexdigest()
    except Exception:
        html_fp = None

    max_alt = int(get_map_home_page_stetic("max_alternatives", 10) or 10)

    # Build dataclass objects from results
    primary_selector = (
        candidates[0]["selectors"]["css"][0]
        if candidates and candidates[0]["selectors"]["css"]
        else (
            candidates[0]["selectors"]["heuristic"][0]
            if candidates and candidates[0]["selectors"]["heuristic"]
            else None
        )
    )
    alternatives: List[str] = [
        *(candidates[0]["selectors"].get("css", []) if candidates else []),
        *(candidates[0]["selectors"].get("heuristic", []) if candidates else []),
    ][:max_alt]

    meta_dc = MappingMeta(
        timestamp=ts,
        source="map_home_page_static",
        variants=variants,
        html_fingerprint=html_fp,
    )
    action_dc = MappingAction(
        primary_selector=primary_selector,
        action="click",
        alternatives=alternatives,
    )
    candidates_dc: List[MappingCandidate] = [
        MappingCandidate(
            type=c.get("type", "*"),
            text=c.get("text", ""),
            attributes=c.get("attributes", {}),
            selectors=c.get("selectors", {}),
            score=int(c.get("score", 0)),
            action=c.get("action", "click"),
        )
        for c in candidates
    ]

    mapping_json = MappingJson(meta=meta_dc, mapping=action_dc, candidates=candidates_dc)

    out_path = out_dir / f"{base}_{ts}.json"
    out_path.write_text(json.dumps(asdict(mapping_json), indent=2, ensure_ascii=False), encoding="utf-8")

    return mapping_json
