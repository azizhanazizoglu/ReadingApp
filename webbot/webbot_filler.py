from __future__ import annotations

"""
webbot_filler: TS3 helper functions to build a fill plan and analyze selectors.

Unit-testable pure functions that the frontend (TS3) can call via backend endpoints
for diagnostics. These do not perform DOM operations; they prepare data and analysis
to help validate mappings and values before injection.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import re
import json as _json


def _normalize_key(s: str) -> str:
    t = str(s).lower()
    t = (
        t.replace('ç', 'c').replace('ğ', 'g').replace('ı', 'i').replace('ö', 'o').replace('ş', 's').replace('ü', 'u')
         .replace('Ç', 'c').replace('Ğ', 'g').replace('İ', 'i').replace('Ö', 'o').replace('Ş', 's').replace('Ü', 'u')
    )
    t = re.sub(r"[^\w]+", "", t, flags=re.UNICODE)
    return t


def flatten_data(obj: Any, base: Tuple[str, ...] = ()) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if obj is None:
        return out
    if not isinstance(obj, dict):
        return out
    for k, v in obj.items():
        path = base + (k,)
        if isinstance(v, dict):
            out.update(flatten_data(v, path))
        else:
            norm = _normalize_key(k)
            out[norm] = {"value": v, "path": ".".join(path)}
    return out


def extract_from_raw(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not text or not isinstance(text, str):
        return out
    s = text.replace("\r", "")
    # Plaka: 2-digit province + letters + digits
    m = re.search(r"\b([0-8][0-9])\s*[- ]?\s*([A-ZÇĞİÖŞÜ]{1,3})\s*[- ]?\s*([0-9]{2,4})\b", s, flags=re.I)
    if m:
        out["plaka_no"] = f"{m.group(1)} {m.group(2).upper()} {m.group(3)}"
    # T.C. Kimlik: 11 digits
    m = re.search(r"\b\d{11}\b", s)
    if m:
        out["tckimlik"] = m.group(0)
    # Doğum tarihi: dd[./-]mm[./-]yyyy
    m = re.search(r"\b([0-3]?\d)[./-]([0-1]?\d)[./-](\d{4})\b", s)
    if m:
        dd = m.group(1).zfill(2)
        mm = m.group(2).zfill(2)
        yyyy = m.group(3)
        out["dogum_tarihi"] = f"{yyyy}-{mm}-{dd}"
    # Ad Soyad: heuristic (optional)
    m = re.search(r"ad\s*soyad[ıi]?\s*[:：]?\s*([^\n]+)", s, flags=re.I)
    if m:
        out["ad_soyad"] = m.group(1).strip()
    return out


def _unwrap_code_fence(text: str) -> str:
    if not isinstance(text, str):
        return ""
    s = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s, flags=re.IGNORECASE)
    return (m.group(1).strip() if m else s)


def extract_from_raw_response_json(raw_response: str) -> Dict[str, Any]:
    """If raw_response looks like a code-fenced JSON, parse and return dict; else {}."""
    try:
        inner = _unwrap_code_fence(raw_response)
        return _json.loads(inner)
    except Exception:
        return {}


DEFAULT_SYNONYMS: Dict[str, List[str]] = {
    'plaka_no': ['plaka', 'plakano', 'plate', 'plateno', 'aracplaka', 'vehicleplate'],
    'ad_soyad': ['adsoyad', 'isim', 'ad', 'soyad', 'name', 'fullname', 'full_name'],
    'tckimlik': ['tc', 'tckimlik', 'kimlik', 'kimlikno', 'tcno', 'identity', 'nationalid'],
    'dogum_tarihi': ['dogumtarihi', 'd_tarihi', 'dtarihi', 'birthdate', 'birth_date', 'dob'],
}


def resolve_values(mapping_keys: List[str], ruhsat_json: Dict[str, Any] | None, raw_text: str | None,
                   synonyms: Dict[str, List[str]] | None = None,
                   sample_values: Dict[str, Any] | None = None,
                   use_dummy_when_empty: bool = True) -> Tuple[Dict[str, Any], List[str]]:
    logs: List[str] = []
    flat = flatten_data(ruhsat_json or {})
    logs.append("flat-keys " + ",".join(list(flat.keys())[:80]))
    raw = raw_text or ""
    raw_extract = extract_from_raw(raw)
    # Additionally, check ruhsat_json['raw_response'] for code-fenced JSON and merge
    if isinstance(ruhsat_json, dict) and isinstance(ruhsat_json.get('raw_response'), str):
        j = extract_from_raw_response_json(ruhsat_json['raw_response'])
        if j:
            # Merge keys directly (they often match desired field names)
            for k in ["tckimlik", "dogum_tarihi", "ad_soyad", "plaka_no"]:
                if k in j and j[k] not in (None, ""):
                    raw_extract[k] = j[k]
            logs.append("raw-json " + str({k: j.get(k) for k in ["tckimlik","dogum_tarihi","ad_soyad","plaka_no"]}))
    if raw_extract:
        logs.append("raw-extract " + str(raw_extract))
    syns = synonyms or DEFAULT_SYNONYMS
    resolved: Dict[str, Any] = {}
    for key in mapping_keys:
        nkey = _normalize_key(key)
        cands = {nkey}
        for s in syns.get(key, []):
            cands.add(_normalize_key(s))
        found_val = None
        found_from = ''
        for c in cands:
            if c in flat and flat[c]["value"] not in (None, ""):
                found_val = flat[c]["value"]
                found_from = flat[c]["path"]
                break
        if found_val is None:
            # substring fallback
            for fk, info in flat.items():
                if any(c in fk for c in cands):
                    if info["value"] not in (None, ""):
                        found_val = info["value"]
                        found_from = info["path"]
                        break
        if found_val is None and key in raw_extract:
            found_val = raw_extract[key]
            found_from = 'rawresponse'
        # sample values from mapping if provided
        if (found_val is None or str(found_val).strip() == '') and sample_values and key in sample_values:
            found_val = sample_values[key]
            found_from = 'mapping.sample'
        resolved[key] = found_val or ''
        logs.append(f"resolve {key} <- {found_from or 'N/A'} = {str(found_val)[:60]}{'…' if (found_val and len(str(found_val))>60) else ''}")

    # Normalize common fields
    if isinstance(resolved.get('plaka_no'), str):
        resolved['plaka_no'] = resolved['plaka_no'].replace('\n', ' ').upper().strip()
    if isinstance(resolved.get('tckimlik'), str):
        resolved['tckimlik'] = re.sub(r"\D+", "", resolved['tckimlik'])

    # Dummy fallback for selector debugging
    if use_dummy_when_empty and all((not str(resolved.get(k, '')).strip()) for k in mapping_keys):
        dummy = {
            'plaka_no': '34 ABC 123',
            'tckimlik': '10000000000',
            'dogum_tarihi': '1990-01-01',
            'ad_soyad': 'Ali Veli',
        }
        for k in mapping_keys:
            if not str(resolved.get(k, '')).strip():
                resolved[k] = dummy.get(k, 'TEST')
                logs.append(f"dummy {k} <- {resolved[k]}")
        logs.append("note TS1 empty; dummy mode enabled")
    return resolved, logs


@dataclass
class FillItem:
    field: str
    selector: str
    value: Any


def build_fill_plan(mapping: Dict[str, Any], ruhsat_json: Dict[str, Any] | None,
                    raw_text: str | None = None,
                    options: Dict[str, Any] | None = None) -> Tuple[List[FillItem], Dict[str, Any], List[str]]:
    options = options or {}
    fm: Dict[str, str] = mapping.get('field_mapping', {}) or {}
    sample_values = mapping.get('sample_values') or mapping.get('value_defaults') or {}
    keys = list(fm.keys())
    resolved, logs = resolve_values(keys, ruhsat_json, raw_text, sample_values=sample_values,
                                    use_dummy_when_empty=options.get('use_dummy_when_empty', True))
    plan = [FillItem(field=k, selector=fm[k], value=resolved.get(k, '')) for k in keys]
    return plan, resolved, logs


def analyze_selectors(html: str, mapping: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Return count of nodes matching each selector using BeautifulSoup CSS select."""
    from bs4 import BeautifulSoup
    res: Dict[str, Dict[str, Any]] = {}
    soup = BeautifulSoup(html or '', 'html.parser')
    fm: Dict[str, str] = mapping.get('field_mapping', {}) or {}
    for k, sel in fm.items():
        info = {"selector": sel, "count": 0}
        try:
            nodes = soup.select(sel)
            info["count"] = len(nodes)
        except Exception as e:
            info["error"] = str(e)
        res[k] = info
    return res


def generate_injection_script(plan: List[FillItem], highlight: bool = True, simulate_typing: bool = True,
                              step_delay_ms: int = 0) -> str:
    """Create a minimal JS script that logs the plan and attempts fills by selector.
    This is primarily for debugging and parity tests.
    """
    entries = [
        {
            "field": it.field,
            "selector": it.selector,
            "value": it.value,
        }
        for it in plan
    ]
    # keep script simple; real typing logic exists in frontend ts3Service
    return (
        "(() => {\n"+
        f"  const items = {entries!r};\n"+
        f"  const highlight = {str(bool(highlight)).lower()};\n"+
        f"  const simulateTyping = {str(bool(simulate_typing)).lower()};\n"+
        f"  const step = {int(step_delay_ms)};\n"+
        "  const delay = ms => new Promise(r => setTimeout(r, ms));\n"+
        "  const logs = [];\n"+
        "  const setVal = async (el, val) => {\n"+
        "    try { el.focus(); } catch(e) {}\n"+
        "    try { el.value = String(val==null?'':val); el.dispatchEvent(new Event('input', {bubbles:true})); el.dispatchEvent(new Event('change', {bubbles:true})); } catch(e) {}\n"+
        "    try { el.blur(); } catch(e) {}\n"+
        "  };\n"+
        "  return (async () => {\n"+
        "    let filled = 0;\n"+
        "    for (const it of items) {\n"+
        "      let el = null;\n"+
        "      try { const els = document.querySelectorAll(String(it.selector)); logs.push('selector-check '+it.field+' -> '+it.selector+' (count='+els.length+')'); if (els.length>0) el = els[0]; } catch(e) { logs.push('selector-error '+it.field+' -> '+String(e)); }\n"+
        "      if (!el) { logs.push('not-found '+it.field); continue; }\n"+
        "      await setVal(el, it.value); filled++;\n"+
        "      if (highlight) { try { el.scrollIntoView({behavior:'smooth', block:'center'}); el.style.outline='2px solid #22c55e'; setTimeout(()=>{ try{ el.style.outline=''; }catch(e){} }, Math.max(1200, step)); } catch(e) {} }\n"+
        "      if (step>0) await delay(step);\n"+
        "    }\n"+
        "    return { ok: true, filled, logs };\n"+
        "  })();\n"+
        "})()"
    )
