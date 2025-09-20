from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup  # type: ignore
    _HAS_BS = True
except Exception:
    _HAS_BS = False
from .calibRuntimeLookup import resolve_site_mapping  # type: ignore


def _sha(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8", errors="ignore")).hexdigest()


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).lower()


def _soup(html: str):
    return BeautifulSoup(html or "", "html.parser") if _HAS_BS else None


def _exists_selector_in_html(html: str, selector: str) -> bool:
    if not (_HAS_BS and selector):
        return False
    try:
        return bool(_soup(html).select(selector))
    except Exception:
        return False


def _closest_label_text(inp) -> str:
    """Best-effort extraction of human label text for an input/select/textarea.

    Strategy (fast, bounded):
    1) <label for="id"> lookup anywhere in document
    2) If wrapped by <label> ... <input/> ... </label>, use ancestor label text
    3) aria-labelledby="id1 id2" → concat those elements' texts
    4) Walk up to 4 ancestors; for each, collect text of previous siblings (elements and text nodes)
       giving priority to elements with class names containing 'label' or role='label'
    5) Fallback to placeholder/aria-label/title/name
    """
    try:
        # 1) Global <label for=id>
        idv = inp.get("id")
        if idv:
            try:
                root = inp
                while getattr(root, "parent", None) is not None:
                    root = root.parent
                lbl = root.find("label", attrs={"for": idv})
                if lbl and getattr(lbl, "get_text", None):
                    txt = _clean(lbl.get_text(" ", strip=True))
                    if txt:
                        return txt
            except Exception:
                pass

        # 2) Input wrapped by a <label>
        try:
            anc_label = inp.find_parent("label")
            if anc_label and getattr(anc_label, "get_text", None):
                txt = _clean(anc_label.get_text(" ", strip=True))
                if txt:
                    return txt
        except Exception:
            pass

        # 3) aria-labelledby references
        try:
            aria_ids = (inp.get("aria-labelledby") or "").strip()
            if aria_ids:
                ids = [x for x in aria_ids.split() if x]
                root = inp
                while getattr(root, "parent", None) is not None:
                    root = root.parent
                collected: List[str] = []
                for i in ids[:3]:
                    ref = root.find(id=i)
                    if ref and getattr(ref, "get_text", None):
                        t = _clean(ref.get_text(" ", strip=True))
                        if t:
                            collected.append(t)
                if collected:
                    return _clean(" ".join(collected))
        except Exception:
            pass

        # 4) Look at previous siblings within closest containers
        p = inp.parent
        for _ in range(4):
            if not p:
                break
            prev_text_candidates: List[str] = []
            for sib in getattr(p, "children", []):
                if sib == inp:
                    break
                nm = getattr(sib, "name", None)
                # Prefer elements that look like labels
                if nm:
                    try:
                        cls = " ".join((sib.get("class") or [])) if hasattr(sib, 'get') else ""
                    except Exception:
                        cls = ""
                    role = sib.get("role") if hasattr(sib, 'get') else None
                    if ("label" in cls.lower()) or (role == "label") or (nm == "label"):
                        txt = _clean(getattr(sib, "get_text", lambda *_: "")(" ", strip=True))
                        if txt:
                            prev_text_candidates.append(txt)
                            continue
                    # Generic element before input
                    if hasattr(sib, "get_text"):
                        txt = _clean(sib.get_text(" ", strip=True))
                        if txt:
                            prev_text_candidates.append(txt)
                else:
                    # Text node
                    t = _clean(str(sib) or "")
                    if t:
                        prev_text_candidates.append(t)
            if prev_text_candidates:
                # Take the last 2 snippets as the likely label area
                t = _clean(" ".join(prev_text_candidates[-2:]))
                if t:
                    return t
            p = p.parent

        # 5) Fallback attributes
        for a in ("placeholder", "aria-label", "title", "name"):
            v = inp.get(a)
            if v:
                return _clean(v)
    except Exception:
        pass
    return ""


def _score_label_to_key(label_text: str, synonyms: Dict[str, List[str]]) -> Optional[str]:
    lt = _clean(label_text)
    best, sc = None, 0
    for key, arr in (synonyms or {}).items():
        for syn in arr or []:
            st = _clean(syn)
            if not st:
                continue
            if st in lt or lt in st:
                if len(st) > sc:
                    best, sc = key, len(st)
    return best


def _attr_text(inp) -> str:
    """Combine useful attribute values for matching if visible label text is weak."""
    try:
        parts: List[str] = []
        for a in ("id", "name", "placeholder", "aria-label", "title", "data-testid", "data-qa", "data-lov-id", "data-lov-name"):
            v = inp.get(a)
            if v:
                parts.append(str(v))
        return _clean(" ".join(parts))
    except Exception:
        return ""


def _best_selector(inp) -> Optional[str]:
    try:
        if inp.get("id"):
            return f"#{inp.get('id')}"
        if inp.get("name"):
            return f"[name='{inp.get('name')}']"
        for a in ("data-lov-id", "data-lov-name"):
            if inp.get(a):
                return f"[{a}='{inp.get(a)}']"
        for a in ("placeholder", "aria-label", "title"):
            if inp.get(a):
                v = str(inp.get(a)).replace("'", "\\'")
                return f"[{a}='{v}']"
        cls = inp.get("class") or []
        if isinstance(cls, list) and cls:
            return f"input.{'.'.join(cls)},textarea.{'.'.join(cls)},select.{'.'.join(cls)}"
        return inp.name or "input"
    except Exception:
        return None


DEFAULT_SYNONYMS = {
    "plaka_no": [
        "plaka", "plaka no", "plaka numarası", "araç plakası", "plaka numarasi",
        "plate", "license plate", "plate number"
    ],
    "sasi_no": [
        "şasi", "şasi no", "şasi numarası", "sase", "sase no", "şase", "asbis", "asbis no",
        "vin", "vin no", "vehicle identification number", "chassis", "chassis no"
    ],
    "model_yili": [
        "model yılı", "model yili", "yıl", "yili", "yılı", "model year", "production year", "year"
    ],
    "motor_no": [
        "motor no", "motor numarası", "motor numarasi", "engine", "engine number", "engine no"
    ],
    "tescil_tarihi": ["tescil tarihi", "tescil", "kayıt tarihi", "kayit tarihi", "kayıt tar."],
    "marka": ["marka", "brand", "make"],
    "model": ["model", "araç modeli", "vehicle model"],
    "yakit": ["yakıt", "yakit", "fuel", "fuel type"],
    "renk": ["renk", "color", "colour"],
}


def static_analyze_page(html: str, url: str, task: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Static alternative to analyzePage. Returns the same shape, without LLM.

        Config layout (append-only):
            goFillForms.static.actions
            goFillForms.static.synonyms
            goFillForms.static.scenarios.<Task>.criticalSelectors
            goFillForms.static.scenarios.<Task>.synonyms
            goFillForms.static.scenarios.<Task>.sections: [ { titleVariants: [..], fields: [..] } ]
        """
    def _cfg_get(c: Dict[str, Any], path: str, default=None):
        cur = c
        for k in path.split('.'):
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur
    scen = _cfg_get(cfg, f"goFillForms.static.scenarios.{task}", {}) or {}
    selector_hints: Dict[str, List[str]] = scen.get("criticalSelectors", {}) or {}
    synonyms: Dict[str, List[str]] = scen.get("synonyms") or _cfg_get(cfg, "goFillForms.static.synonyms", DEFAULT_SYNONYMS)
    sections: List[Dict[str, Any]] = scen.get("sections") or []
    actions_pref = [a.lower() for a in _cfg_get(cfg, "goFillForms.static.actions", ["Devam", "İleri", "Kaydet", "Poliçeyi Aktifleştir"]) ]

    mapping: Dict[str, str] = {}
    mapping_src: Dict[str, str] = {}
    contexts: Dict[str, Any] = {}
    used_hints: Dict[str, str] = {}
    actions_found: List[str] = []

    # 0) Seed mapping from site-specific calibration/config if available
    try:
        host = urlparse(url or "").hostname or ""
    except Exception:
        host = ""
    calib_page_match = None
    calib_page_actions: List[str] = []              # text labels (for text-based clicking)
    calib_page_action_selectors: List[str] = []      # css selectors for deterministic clicking
    if host:
        site_map = resolve_site_mapping(host, task, cfg) or {}
        seeded = site_map.get("fieldSelectors") or {}
        if isinstance(seeded, dict) and seeded:
            from backend.logging_utils import log  # type: ignore
            log("INFO", "CALIB-MAPPING", f"Applying calib.json mappings for {host}/{task}", component="StaticAnalyze", extra={
                "host": host,
                "task": task,
                "calib_fields": list(seeded.keys()),
                "calib_selectors": {k: v for k, v in seeded.items() if v}
            })
            
            for k, sel in seeded.items():
                if sel:
                    mapping[k] = sel
                    mapping_src[k] = "calib_site"
            
            log("INFO", "CALIB-APPLIED", f"Applied {len(seeded)} calib mappings", component="StaticAnalyze", extra={
                "applied_mappings": {k: v for k, v in mapping.items() if mapping_src.get(k) == "calib_site"},
                "mapping_sources": {k: v for k, v in mapping_src.items()}
            })
            
            # Page-level resolution: find matching page by urlSample prefix or simple containment
            try:
                pages = site_map.get("pages") or []
                if isinstance(pages, list):
                    for pg in pages:
                        if not isinstance(pg, dict):
                            continue
                        u_sample = pg.get("urlSample") or ""
                        if u_sample and url and (url.startswith(u_sample) or u_sample.startswith(url)):
                            calib_page_match = pg
                            break
                    if calib_page_match is None and url:
                        # fallback: substring match
                        for pg in pages:
                            if not isinstance(pg, dict):
                                continue
                            u_sample = pg.get("urlSample") or ""
                            if u_sample and u_sample.split("//")[-1].split("/")[0] in url:
                                calib_page_match = pg
                                break
                if calib_page_match:
                    from backend.logging_utils import log  # type: ignore
                    log("INFO", "CALIB-PAGE-MATCH", f"Matched calib page {calib_page_match.get('id')} ({calib_page_match.get('name')})", component="StaticAnalyze", extra={
                        "page_id": calib_page_match.get("id"),
                        "page_name": calib_page_match.get("name"),
                        "page_fields": list((calib_page_match.get("fieldSelectors") or {}).keys()),
                        "critical_fields": calib_page_match.get("criticalFields"),
                        "actions_detail": calib_page_match.get("actionsDetail"),
                    })
                    # Override seeded mapping with page-specific fieldSelectors if present
                    psel = calib_page_match.get("fieldSelectors") or {}
                    if isinstance(psel, dict):
                        for k,v in psel.items():
                            if v:
                                mapping[k] = v
                                # keep original source if existed, otherwise tag as calib_page
                                mapping_src[k] = mapping_src.get(k) or "calib_page"
                    # Extract actions from page actionsDetail if any
                    acts_det = calib_page_match.get("actionsDetail") or []
                    if isinstance(acts_det, list):
                        for ad in acts_det:
                            if isinstance(ad, dict):
                                lbl = ad.get("label") or ad.get("id") or "Action"
                                sel = ad.get("selector") or ""
                                if lbl and lbl not in calib_page_actions:
                                    calib_page_actions.append(str(lbl))
                                if sel:
                                    calib_page_action_selectors.append(sel)
            except Exception as _e:
                pass

            # Prefer site-provided global actions if page did not define any labels
            if calib_page_actions:
                actions_found.extend(calib_page_actions)
            elif isinstance(site_map.get("actions"), list) and site_map.get("actions"):
                actions_found.extend([str(x) for x in site_map.get("actions") if isinstance(x, str)])
            # Allow per-site synonyms override
            site_syn = site_map.get("synonyms")
            if isinstance(site_syn, dict) and site_syn:
                # merge: site-specific first
                tmp = dict(site_syn)
                for k, v in (synonyms or {}).items():
                    if k not in tmp:
                        tmp[k] = v
                synonyms = tmp
    # 1) selector hints (do not override with heuristics)
    for key, hint_list in (selector_hints or {}).items():
        if not isinstance(hint_list, list):
            continue
        for sel in hint_list:
            if _exists_selector_in_html(html, sel):
                if key not in mapping:  # keep calib seed
                    mapping[key] = sel
                    mapping_src[key] = "static_hint"
                used_hints[key] = sel
                break

    # 2) section-based mapping using headings (higher priority than generic heuristics)
    if _HAS_BS:
        s = _soup(html)
        if s:
            # Debug: Log all input fields found on the page
            try:
                all_inputs = s.select("input, textarea, select, [contenteditable=''], [contenteditable='true']")
                print(f"[DEBUG] Found {len(all_inputs)} input fields on page:")
                for i, inp in enumerate(all_inputs[:10]):  # First 10 only
                    print(f"[DEBUG]   {i+1}: tag={getattr(inp, 'name', '?')} id={inp.get('id')} name={inp.get('name')} class={inp.get('class')} placeholder={inp.get('placeholder')}")
                    print(f"[DEBUG]      label_text='{_closest_label_text(inp)[:50]}'")
            except Exception as e:
                print(f"[DEBUG] Error logging inputs: {e}")
            
            # Helper to get inputs under/near a heading node
            def _inputs_under(node) -> List[Any]:
                cand: List[Any] = []
                try:
                    cand.extend(node.select("input, textarea, select, [contenteditable=''], [contenteditable='true']"))
                except Exception:
                    pass
                if not cand:
                    steps = 0
                    for nxt in node.next_elements:
                        steps += 1
                        if steps > 800:
                            break
                        try:
                            nm = getattr(nxt, "name", None)
                            if nm and nm.lower() in ("h1","h2","h3","h4","h5","h6"):
                                break
                            if nm in ("input","textarea","select") or (hasattr(nxt, 'get') and (nxt.get('contenteditable') in ("", "true"))):
                                cand.append(nxt)
                        except Exception:
                            continue
                        if len(cand) >= 5:
                            break
                return cand

            def _is_for_key(el, key: str) -> bool:
                lbl = _closest_label_text(el)
                guessed = _score_label_to_key(lbl, synonyms)
                return guessed == key

            used_elements = set()
            if sections:
                for sec in sections:
                    tv = [_clean(x) for x in (sec.get("titleVariants") or []) if _clean(x)]
                    flds = list(sec.get("fields") or [])
                    if not tv or not flds:
                        continue
                    found_heading = None
                    for node in s.find_all(True):
                        try:
                            txt = _clean(node.get_text(" ", strip=True))
                        except Exception:
                            continue
                        if not txt:
                            continue
                        if any(v in txt for v in tv):
                            found_heading = node
                            break
                    if not found_heading:
                        continue
                    candidates = _inputs_under(found_heading)
                    for key in flds:
                        if key in mapping:
                            continue
                        chosen = None
                        for el in candidates:
                            if el in used_elements:
                                continue
                            if _is_for_key(el, key):
                                chosen = el
                                break
                        if not chosen:
                            for el in candidates:
                                if el not in used_elements:
                                    chosen = el
                                    break
                        if not chosen:
                            continue
                        sel = _best_selector(chosen)
                        if not sel:
                            continue
                        mapping[key] = sel
                        mapping_src[key] = "static_section"
                        contexts[key] = {"section": tv[0] if tv else None, "tag": getattr(chosen, "name", None), "id": chosen.get("id"), "name": chosen.get("name")}
                        used_elements.add(chosen)

            # 3) generic heuristic mapping for any remaining fields
            for el in s.select("input, textarea, select, [contenteditable=''], [contenteditable='true']"):
                # 3a) Try label-based
                key = _score_label_to_key(_closest_label_text(el), synonyms)
                # 3b) If still unknown, try attribute-based
                if not key:
                    key = _score_label_to_key(_attr_text(el), synonyms)
                if not key or key in mapping:
                    continue
                sel = _best_selector(el)
                if not sel:
                    continue
                mapping[key] = sel
                mapping_src[key] = "static_synonym"
                contexts[key] = {"tag": getattr(el, "name", None), "id": el.get("id"), "name": el.get("name")}

            # Text-based action discovery removed - using only calibration selectors as single source of truth
            pass
            # Action filtering removed - actions come only from calibration now

    fp = _sha(html)
    out = {
        "ok": len(mapping) > 0,
        "page_kind": "fill_form",
        "field_mapping": mapping,
        "actions": actions_found,
        "validation": {"contexts": contexts, "counts": {"mapped": len(mapping)}},
        "mapping_source": mapping_src,
        "fingerprint": fp,
        "debug_dumps": {"used": "static", "used_hints": used_hints, "used_sections": bool(sections)},
        "used": "static",
    }

    # Optional dump for debugging
    dump_dir = os.path.join(_cfg_get(cfg, "paths.tmpDir", "production2/tmp"), "JpegJsonWebpageHtml")
    os.makedirs(dump_dir, exist_ok=True)
    try:
        with open(os.path.join(dump_dir, f"{fp}_static_mapping.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # Log final mapping summary
    from backend.logging_utils import log  # type: ignore
    calib_mappings = {k: v for k, v in mapping.items() if mapping_src.get(k) == "calib_site"}
    other_mappings = {k: v for k, v in mapping.items() if mapping_src.get(k) != "calib_site"}
    
    # If we had page-level action selectors, expose them as css# actions first & log presence
    if calib_page_action_selectors:
        from backend.logging_utils import log  # type: ignore
        missing = [s for s in calib_page_action_selectors if s not in html]
        present = [s for s in calib_page_action_selectors if s in html]
        css_actions = [f"css#{s}" for s in calib_page_action_selectors]
        new_actions: List[str] = []
        for a in css_actions + actions_found:
            if a not in new_actions:
                new_actions.append(a)
        actions_found = new_actions
        log("INFO", "CALIB-PAGE-ACTIONS", f"Page action selectors resolved ({len(calib_page_action_selectors)})", component="StaticAnalyze", extra={
            "present": present,
            "missing": missing,
            "labels": calib_page_actions,
            "css_actions_injected": css_actions
        })

    log("INFO", "STATIC-MAPPING-FINAL", f"Static analysis complete for {host}/{task}", component="StaticAnalyze", extra={
        "total_mappings": len(mapping),
        "calib_mappings": calib_mappings,
        "calib_count": len(calib_mappings),
        "other_mappings": other_mappings,
        "other_count": len(other_mappings),
        "mapping_sources": mapping_src,
        "actions_found": actions_found,
        "url": url or "",
        "fingerprint": fp[:8] if fp else None
    })

    return out

