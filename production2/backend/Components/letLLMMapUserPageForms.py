from __future__ import annotations

"""LLM mapping for user task forms (F3).

Given filtered HTML and an optional ruhsat JSON, produce:
- page_kind: 'fill_form' | 'final_activation'
- field_mapping: { logical_field -> selector }
- actions: ["Next", "Devam", ...] optional follow-up buttons (visible text)
- evidence / rationale (optional)

Returns a dict suitable to be embedded in a feature plan.
"""

from pathlib import Path as _Path
from typing import Any, Dict, Optional, List
import os
import json
import re

_THIS = _Path(__file__).resolve()
_ROOT = _THIS.parents[2]
import sys as _sys
if str(_ROOT) not in _sys.path:
	_sys.path.insert(0, str(_ROOT))

from config import get  # type: ignore
try:
	from logging_utils import log as _log  # type: ignore
except Exception:
	def _log(*args, **kwargs):
		try:
			print("[F3-ANALYZE]", *args)
		except Exception:
			pass


def _extract_labels_and_text(html: str) -> List[str]:
	texts: List[str] = []
	try:
		from bs4 import BeautifulSoup  # type: ignore
		soup = BeautifulSoup(html or '', 'html.parser')
		# Collect label texts
		for lab in soup.find_all('label'):
			try:
				t = lab.get_text(" ")
				if t and t.strip():
					texts.append(t.strip())
			except Exception:
				pass
		# Also headings and strong texts near inputs (lightweight)
		for tag in ['strong', 'b', 'h1', 'h2', 'h3']:
			for el in soup.find_all(tag):
				try:
					t = el.get_text(" ")
					if t and t.strip():
						texts.append(t.strip())
				except Exception:
					pass
	except Exception:
		pass
	return texts


def _infer_keys_from_labels(labels: List[str]) -> List[str]:
	cand: List[str] = []
	labn = [_norm_text(x) for x in (labels or [])]
	def has_any(words: List[str]) -> bool:
		wn = [_norm_text(w) for w in words]
		return any(any(w in t for w in wn) for t in labn)
	# Common insurance fields
	if has_any(['plaka no', 'plaka', 'plate']):
		cand.append('plaka_no')
	if has_any(['kimlik', 't.c.', 'tc kimlik', 'kimlik bilgisi']):
		cand.append('tckimlik')
	if has_any(['doğum tarihi', 'dogum tarihi', 'birth']):
		cand.append('dogum_tarihi')
	if has_any(['ad soyad', 'ad/soyad', 'isim', 'name']):
		cand.append('ad_soyad')
	if has_any(['marka']):
		cand.append('marka')
	if has_any(['model yılı', 'model yili', 'model']):
		cand.append('model_yili')
	if has_any(['şasi', 'sasi']):
		cand.append('sasi_no')
	if has_any(['motor no']):
		cand.append('motor_no')
	if has_any(['yakıt', 'yakit', 'fuel']):
		cand.append('yakit')
	if has_any(['renk', 'color']):
		cand.append('renk')
	# Keep unique order
	seen = set(); out: List[str] = []
	for k in cand:
		if k not in seen:
			out.append(k); seen.add(k)
	return out


def _build_prompt(html: str, ruhsat_json: Optional[Dict[str, Any]]) -> str:
	default = (
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
	labels = _extract_labels_and_text(html)
	cand_keys = _infer_keys_from_labels(labels)
	parts = [default]
	if ruhsat_json:
		try:
			js = json.dumps(ruhsat_json, ensure_ascii=False)
			parts.append("Ruhsat JSON:\n" + js)
		except Exception:
			pass
	if cand_keys:
		parts.append("On this page, these field keys are likely present; ONLY include these in field_mapping: " + ", ".join(cand_keys))
	parts.append("Detected labels (truncated): \n" + "; ".join(labels[:30]))
	parts.append("Filtered HTML (truncated if long):\n" + (html[:16000] if isinstance(html, str) else ""))
	return "\n\n".join(parts)


def _try_parse_json(txt: str) -> Optional[Dict[str, Any]]:
	try:
		val = json.loads(txt)
		return val if isinstance(val, dict) else None
	except Exception:
		return None


def _parse_llm_json(raw: str) -> Dict[str, Any]:
	s = (raw or "").strip()
	m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s, flags=re.IGNORECASE)
	if m:
		s = m.group(1).strip()
	j = _try_parse_json(s)
	if j is not None:
		return j
	# last resort: substring braces
	try:
		i = s.find('{'); j = s.rfind('}')
		if 0 <= i < j:
			sub = s[i:j+1]
			d = _try_parse_json(sub)
			if d is not None:
				return d
	except Exception:
		pass
	return {}


_DEFAULT_SYNONYMS: Dict[str, List[str]] = {
	'plaka_no': ['plaka', 'plaka no', 'plate', 'vehicle plate', 'plaka numarası', 'plaka numarasi'],
	'ad_soyad': ['ad soyad', 'ad/soyad', 'isim', 'name', 'full name', 'ad soyadı', 'ad soyadi'],
	'tckimlik': ['tc', 'tc kimlik', 'kimlik', 'kimlik no', 'identity', 'national id', 'tckn', 't.c. kimlik'],
	'dogum_tarihi': ['doğum tarihi', 'dogum tarihi', 'birth date', 'birthdate', 'dob'],
	'model_yili': ['model yılı', 'model yili', 'model year', 'yil', 'yılı', 'yili'],
	'sasi_no': ['şasi', 'sasi', 'şasi no', 'sasi no', 'şasi numarası', 'sasi numarasi', 'şasi num', 'sasi num'],
}


def _norm_text(s: Optional[str]) -> str:
	if not s:
		return ''
	try:
		t = str(s)
		t = t.replace('\r', ' ').replace('\n', ' ')
		t = t.lower()
		t = (t
			 .replace('ç', 'c').replace('ğ', 'g').replace('ı', 'i').replace('ö', 'o').replace('ş', 's').replace('ü', 'u')
			 .replace('Ç', 'c').replace('Ğ', 'g').replace('İ', 'i').replace('Ö', 'o').replace('Ş', 's').replace('Ü', 'u'))
		t = re.sub(r"\s+", " ", t)
		return t.strip()
	except Exception:
		return str(s)


def _score_element_text(n, key: str, synonyms: Dict[str, List[str]]) -> int:
	try:
		attrs = getattr(n, 'attrs', {}) or {}
		texts: List[str] = []
		# label[for=id]
		lab = None
		try:
			idv = attrs.get('id')
			if idv:
				# will be resolved in caller via soup; here just keep placeholder
				pass
		except Exception:
			pass
		# attributes
		for a in ('placeholder', 'aria-label', 'name', 'title'):
			v = attrs.get(a)
			if v:
				texts.append(str(v))
		# surrounding text (parent)
		try:
			p = n.parent
			if p and hasattr(p, 'get_text'):
				texts.append(p.get_text(" "))
		except Exception:
			pass
		sig = _norm_text(" ".join(texts))
		syns = [key] + synonyms.get(key, [])
		syns_n = [_norm_text(x) for x in syns]
		score = 0
		for s in syns_n:
			if s and s in sig:
				score += 1
		return score
	except Exception:
		return 0


def _unique_selector_for_node(soup, n) -> Optional[str]:
	try:
		attrs = getattr(n, 'attrs', {}) or {}
		tag = (getattr(n, 'name', '') or '').lower() or 'input'
		# Prefer id
		idv = attrs.get('id')
		if idv:
			sel = f"#{idv}"
			try:
				if len(soup.select(sel)) == 1:
					return sel
			except Exception:
				pass
		# Prefer name
		namev = attrs.get('name')
		if namev:
			sel = f"{tag}[name='{namev}']"
			try:
				if len(soup.select(sel)) == 1:
					return sel
			except Exception:
				pass
		# Lovable builder adds unique data-lov-* attributes; use them if unique
		for a in ('data-lov-id', 'data-lov-name'):
			try:
				v = attrs.get(a)
				if v:
					sel = f"[{a}='{v}']"
					if len(soup.select(sel)) == 1:
						return sel
			except Exception:
				pass
		# Unique attribute-based selectors
		for a in ('placeholder', 'aria-label', 'title'):
			try:
				v = attrs.get(a)
				if v:
					sel = f"{tag}[{a}='{v}']"
					if len(soup.select(sel)) == 1:
						return sel
			except Exception:
				pass
		# Try class if single
		classes = attrs.get('class') or []
		if isinstance(classes, list) and len(classes) == 1:
			cls = classes[0]
			if cls:
				sel = f"{tag}.{cls}"
				try:
					if len(soup.select(sel)) == 1:
						return sel
				except Exception:
					pass
		# Try combining first two classes if present
		if isinstance(classes, list) and len(classes) >= 2:
			try:
				cls1 = classes[0] or ''
				cls2 = classes[1] or ''
				if cls1 and cls2:
					sel = f"{tag}.{cls1}.{cls2}"
					if len(soup.select(sel)) == 1:
						return sel
			except Exception:
				pass
		# Try under nearest form with id
		form = n.find_parent('form') if hasattr(n, 'find_parent') else None
		if form is not None:
			fattrs = getattr(form, 'attrs', {}) or {}
			fid = fattrs.get('id')
			if fid:
				# nth-of-type within form
				same = [x for x in form.select(tag)]
				for idx, x in enumerate(same):
					if x is n:
						sel = f"form#{fid} {tag}:nth-of-type({idx+1})"
						try:
							if len(soup.select(sel)) == 1:
								return sel
						except Exception:
							pass
		# last resort: nth-of-type at document level (brittle)
		all_same = [x for x in soup.select(tag)]
		for idx, x in enumerate(all_same):
			if x is n:
				sel = f"{tag}:nth-of-type({idx+1})"
				try:
					if len(soup.select(sel)) == 1:
						return sel
				except Exception:
					pass
	except Exception:
		return None
	return None


def _heuristic_map_fields(html: str, keys: List[str], synonyms: Optional[Dict[str, List[str]]] = None) -> Dict[str, str]:
	"""When LLM mapping fails, try to map logical keys to inputs by label/placeholder/name proximity."""
	try:
		from bs4 import BeautifulSoup  # type: ignore
		soup = BeautifulSoup(html or "", "html.parser")
		syns = synonyms or _DEFAULT_SYNONYMS
		# Collect candidate nodes
		cands = soup.select('input, select, textarea, [contenteditable="true"]')
		# Build mapping
		out: Dict[str, str] = {}
		for key in keys:
			best = None
			best_score = -1
			for n in cands:
				# filter out non-input-like
				tag = (getattr(n, 'name', '') or '').lower()
				if tag not in ('input', 'select', 'textarea'):
					# allow contenteditable
					attrs = getattr(n, 'attrs', {}) or {}
					ce = str(attrs.get('contenteditable', '')).lower() == 'true'
					if not ce:
						continue
				score = _score_element_text(n, key, syns)
				if score > best_score:
					best_score = score
					best = n
			if best is not None and best_score > 0:
				sel = _unique_selector_for_node(soup, best)
				if sel:
					out[key] = sel
		return out
	except Exception:
		return {}


def _validate_and_clean_mapping(html: str, field_mapping: Dict[str, Any]) -> Dict[str, Any]:
	"""Validate selectors against HTML. Keep only unique selectors that resolve to a single input/select/textarea.
	Returns { cleaned: {..}, dropped: {key: reason}, stats: {kept, dropped} }
	"""
	cleaned: Dict[str, str] = {}
	dropped: Dict[str, str] = {}
	contexts: Dict[str, Dict[str, Any]] = {}
	if not isinstance(field_mapping, dict) or not html:
		return {"cleaned": {}, "dropped": {k: "invalid-mapping" for k in (field_mapping or {})}, "stats": {"kept": 0, "dropped": len(field_mapping or {})}}
	try:
		from bs4 import BeautifulSoup  # type: ignore
		soup = BeautifulSoup(html or "", "html.parser")
		for k, sel in (field_mapping or {}).items():
			reason = None
			try:
				sel_s = str(sel)
				nodes = soup.select(sel_s)
			except Exception as e:  # selector parse error
				reason = f"selector-error:{e}"
				nodes = []
			if reason is None:
				if len(nodes) != 1:
					reason = f"non-unique:{len(nodes)}"
				else:
					n = nodes[0]
					tag = (getattr(n, 'name', '') or '').lower()
					# BeautifulSoup node for inputs has name 'input' etc.
					if tag not in ("input", "select", "textarea"):
						# allow contenteditable elements
						attrs = getattr(n, 'attrs', {}) or {}
						ce = str(attrs.get('contenteditable', '')).lower() == 'true'
						if not ce:
							reason = f"not-input:{tag or 'unknown'}"
			if reason is None:
				cleaned[k] = str(sel)
				try:
					# capture basic context to understand grouping
					n = nodes[0]
					form = n.find_parent('form') if hasattr(n, 'find_parent') else None
					ctx = {
						"tag": (getattr(n, 'name', '') or '').lower(),
						"id": (getattr(n, 'attrs', {}) or {}).get('id'),
						"name": (getattr(n, 'attrs', {}) or {}).get('name'),
					}
					if form is not None:
						fattrs = getattr(form, 'attrs', {}) or {}
						ctx["form"] = {
							"id": fattrs.get('id'),
							"name": fattrs.get('name'),
							"action": fattrs.get('action'),
							"class": fattrs.get('class'),
						}
					contexts[k] = ctx
				except Exception:
					pass
			else:
				dropped[k] = reason
		return {"cleaned": cleaned, "dropped": dropped, "contexts": contexts, "stats": {"kept": len(cleaned), "dropped": len(dropped)}}
	except Exception:
		# If bs4 not available, return original mapping as-is
		return {"cleaned": {k: str(v) for k, v in (field_mapping or {}).items()}, "dropped": {}, "contexts": {}, "stats": {"kept": len(field_mapping or {}), "dropped": 0}}


def map_json_to_html_fields(html: str, ruhsat_json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
	"""Compose an LLM call to map ruhsat_json to form fields or detect final activation page.

	Returns a dict: { ok, page_kind, field_mapping?, actions?, evidence?, raw? }
	"""
	key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
	model = get("goFillForms.llm.model", os.getenv("LLM_MODEL", "gpt-4o"))
	temp = float(get("goFillForms.llm.temperature", 0.0) or 0.0)

	prompt = _build_prompt(html, ruhsat_json)
	raw: str = ""
	_log("INFO", "F3-ANALYZE", f"key_present={bool(key)} model={model} temp={temp}", component="F3")
	if key:
		try:
			from openai import OpenAI  # type: ignore
			client = OpenAI(api_key=key)
			resp = client.chat.completions.create(
				model=model,
				messages=[
					{"role": "system", "content": "Return ONLY strict JSON."},
					{"role": "user", "content": prompt},
				],
				temperature=temp,
				max_tokens=400,
			)
			raw = (resp.choices[0].message.content or "").strip()
		except Exception:
			try:
				import openai  # type: ignore
				openai.api_key = key
				raw = openai.chat.completions.create(  # type: ignore[attr-defined]
					model=model,
					messages=[
						{"role": "system", "content": "Return ONLY strict JSON."},
						{"role": "user", "content": prompt},
					],
					temperature=temp,
					max_tokens=400,
				).choices[0].message.content.strip()
			except Exception:
				raw = ""
	# If no key or failure, return empty mapping (caller can fallback)
	if not raw:
		return {"ok": False, "error": "no_llm_response"}

	data = _parse_llm_json(raw)
	if not isinstance(data, dict) or not data:
		return {"ok": False, "error": "parse_failed", "raw": raw}

	page_kind = (data.get("page_kind") or "fill_form").strip().lower()
	original_mapping = data.get("field_mapping") or {}
	validated = _validate_and_clean_mapping(html, original_mapping) if page_kind == 'fill_form' else {"cleaned": {}, "dropped": {}, "stats": {}}
	# Heuristic salvage: if some keys dropped, try to map dropped ones by label/attributes and merge
	mapping_source: Dict[str, str] = {}
	if page_kind == 'fill_form' and isinstance(validated, dict):
		cleaned_now = dict(validated.get('cleaned') or {})
		dropped_now = dict(validated.get('dropped') or {})
		# If nothing kept, try broader fallback on common keys or original keys
		if len(cleaned_now) == 0:
			keys = list(original_mapping.keys()) if isinstance(original_mapping, dict) and original_mapping else []
			if not keys:
				keys = ['plaka_no', 'tckimlik', 'dogum_tarihi', 'ad_soyad', 'model_yili', 'sasi_no']
			auto_map = _heuristic_map_fields(html, keys)
			if auto_map:
				auto_valid = _validate_and_clean_mapping(html, auto_map)
				if len(auto_valid.get('cleaned') or {}) > 0:
					validated = auto_valid
					mapping_source.update({k: 'auto' for k in (auto_valid.get('cleaned') or {}).keys()})
		else:
			# Some keys were dropped: try to salvage only those
			if dropped_now:
				salvage_keys = list(dropped_now.keys())
				auto_map2 = _heuristic_map_fields(html, salvage_keys)
				if auto_map2:
					auto_valid2 = _validate_and_clean_mapping(html, auto_map2)
					c2 = auto_valid2.get('cleaned') or {}
					if c2:
						# merge into existing validated
						merged_cleaned = dict(cleaned_now)
						merged_cleaned.update(c2)
						merged_dropped = {k: v for k, v in dropped_now.items() if k not in c2}
						merged_contexts = dict(validated.get('contexts') or {})
						merged_contexts.update(auto_valid2.get('contexts') or {})
						validated = {
							"cleaned": merged_cleaned,
							"dropped": merged_dropped,
							"contexts": merged_contexts,
							"stats": {"kept": len(merged_cleaned), "dropped": len(merged_dropped)}
						}
						mapping_source.update({k: 'auto' for k in c2.keys()})
	out: Dict[str, Any] = {
		"ok": True,
		"page_kind": page_kind,
		"field_mapping": validated.get("cleaned") if page_kind == 'fill_form' else {},
		"actions": data.get("actions") or [],
		"evidence": data.get("evidence") or None,
		"raw": raw,
	}
	if page_kind == 'fill_form':
		out["validation"] = validated
		if mapping_source:
			out["mapping_source"] = mapping_source
	return out


if __name__ == "__main__":
	# minimal smoke test (no API call will return ok=False)
	print(json.dumps(map_json_to_html_fields("<form></form>", {"plaka_no": "06 ABC 123"}), indent=2, ensure_ascii=False))

