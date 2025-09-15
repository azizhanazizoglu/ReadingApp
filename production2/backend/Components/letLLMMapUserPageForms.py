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
		# NEW: include input placeholders / aria-labels / names as label-like hints
		for el in soup.select('input, select, textarea'):
			try:
				attrs = getattr(el, 'attrs', {}) or {}
				for a in ('placeholder', 'aria-label', 'name', 'title'):
					v = attrs.get(a)
					if v and str(v).strip():
						texts.append(str(v).strip())
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
	if has_any(['şasi', 'sasi', 'şase', 'sase', 'chassis', 'vin']):
		cand.append('sasi_no')
	if has_any(['motor no', 'motor', 'engine', 'engine no', 'engine number', 'motor numarası', 'motor numarasi']):
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
	# Strengthened default prompt: explicit schema, strict-output rules, selector constraints, and omission when unsure.
	default = (
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
	# Allow override via config.json
	try:
		cfg_prompt = get("goFillForms.llm.mappingPrompt")
		if isinstance(cfg_prompt, str) and cfg_prompt.strip():
			default = cfg_prompt
	except Exception:
		pass
	labels = _extract_labels_and_text(html)
	cand_keys = _infer_keys_from_labels(labels)

	# Summarize available controls to help the LLM pick real selectors
	controls_summary: List[str] = []
	ids_present: List[str] = []
	names_present: List[str] = []
	data_attr_names_present: List[str] = []
	data_attr_examples: List[str] = []
	try:
		from bs4 import BeautifulSoup  # type: ignore
		soup = BeautifulSoup(html or '', 'html.parser')
		attr_name_counts: Dict[str, int] = {}
		for el in soup.select('input, select, textarea')[:120]:
			try:
				attrs = getattr(el, 'attrs', {}) or {}
				tag = (getattr(el, 'name', '') or '').lower()
				idv = attrs.get('id') or ''
				namev = attrs.get('name') or ''
				ph = attrs.get('placeholder') or ''
				al = attrs.get('aria-label') or ''
				aria_lb = attrs.get('aria-labelledby') or ''
				aria_db = attrs.get('aria-describedby') or ''
				title = attrs.get('title') or ''
				bits = [tag]
				if idv:
					bits.append(f"#{idv}")
					ids_present.append(str(idv))
				if namev:
					bits.append(f"name={namev}")
					names_present.append(str(namev))
				if ph:
					bits.append(f"ph={ph}")
				if al:
					bits.append(f"aria={al}")
				if aria_lb:
					bits.append(f"aria-labelledby={aria_lb}")
				if aria_db:
					bits.append(f"aria-describedby={aria_db}")
				if title:
					bits.append(f"title={title}")
				# linked label text
				try:
					if idv:
						lab_el = soup.find('label', {'for': idv})
						if lab_el and hasattr(lab_el, 'get_text'):
							bits.append("label=" + lab_el.get_text(" ").strip())
					parent_label = el.find_parent('label') if hasattr(el, 'find_parent') else None
					if parent_label and hasattr(parent_label, 'get_text'):
						bits.append("label-wrap=" + parent_label.get_text(" ").strip())
					if aria_lb:
						for rid in str(aria_lb).split():
							ref_el = soup.find(id=rid)
							if ref_el and hasattr(ref_el, 'get_text'):
								bits.append("lb=" + ref_el.get_text(" ").strip())
					if aria_db:
						for rid in str(aria_db).split():
							ref_el = soup.find(id=rid)
							if ref_el and hasattr(ref_el, 'get_text'):
								bits.append("db=" + ref_el.get_text(" ").strip())
				except Exception:
					pass
				# include up to two data-* attributes to help LLM pick stable selectors
				data_bits = []
				for k, v in list(attrs.items()):
					try:
						if not isinstance(k, str) or not k.startswith('data-'):
							continue
						vs = v if isinstance(v, str) else None
						if not vs or len(vs) > 160:
							continue
						data_bits.append(f"{k}={vs}")
						if k not in data_attr_names_present:
							data_attr_names_present.append(k)
						if len(data_attr_examples) < 60:
							data_attr_examples.append(f"[{k}='{vs}']")
						attr_name_counts[k] = attr_name_counts.get(k, 0) + 1
					except Exception:
						pass
				for db in data_bits[:2]:
					bits.append(db)
				controls_summary.append(" ".join(bits)[:200])
			except Exception:
				pass
	except Exception:
		pass

	# Compute rare attribute names as likely stable candidates
	rare_attr_names: List[str] = []
	try:
		for an, cnt in (attr_name_counts or {}).items():
			if cnt <= 3:
				rare_attr_names.append(an)
	except Exception:
		pass
	parts = [default]
	# Always append strict selector rules and examples to reduce hallucinations
	parts.append(
		"\nStrict selector rules (MANDATORY):\n"
		"- Return ONLY selectors that exist in the provided HTML.\n"
		"- Each selector must match exactly one input/select/textarea (or contenteditable).\n"
		"- Prefer in this order: #id (if present), then tag[name=...], then unique data-* (e.g., [data-testid=...], [data-qa=...]), then [aria-label=...] or placeholder/title.\n"
		"- If an element has an id, DO NOT return input[name=...] for it; use #id.\n"
		"- Do NOT assume site-specific attribute names. Only use attribute names you actually see listed in the inventory below.\n"
		"- If you are not sure a unique selector exists, omit that logical key. Do not guess.\n"
		"Examples: If the plate field is <input id=\"plateNo\" name=\"plateNo\">, return \"#plateNo\". If chassis is <input name=\"chassis\"> and unique, return \"input[name='chassis']\".\n"
	)
	if ruhsat_json:
		try:
			js = json.dumps(ruhsat_json, ensure_ascii=False)
			parts.append("Ruhsat JSON (authoritative values to use when fields exist on this page):\n" + js)
		except Exception:
			pass
	if cand_keys:
		parts.append(
			"Likely present logical keys on this step (restrict mapping ONLY to these if you map anything): "
			+ ", ".join(cand_keys)
		)
	if ids_present:
		parts.append("IDs present on this page (prefer these first):\n- #" + "\n- #".join(list(dict.fromkeys(ids_present))[:60]))
	if names_present:
		parts.append("Names present (use only if no id; ensure unique):\n- " + "\n- ".join(list(dict.fromkeys(names_present))[:60]))
	if data_attr_names_present:
		parts.append("data-* attributes seen on this page (unique attributes are valid stable selectors when id/name are missing):\n- " + "\n- ".join(list(dict.fromkeys(data_attr_names_present))[:40]))
	if data_attr_examples:
		parts.append("Examples of data-* selectors present (first 40):\n- " + "\n- ".join(list(dict.fromkeys(data_attr_examples))[:40]))
	if rare_attr_names:
		parts.append("Rare attribute names observed (likely stable):\n- " + "\n- ".join(sorted(list(dict.fromkeys(rare_attr_names)))[:30]))
	if controls_summary:
		parts.append("Available controls (first 60; showing tag, id/name, data-*, aria/placeholder):\n- " + "\n- ".join(controls_summary[:60]))
	parts.append("Detected labels/placeholders (truncated):\n" + "; ".join(labels[:30]))
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
	'plaka_no': ['plaka', 'plaka no', 'plate', 'vehicle plate', 'plaka numarası', 'plaka numarasi', 'license plate', 'plate number'],
	'ad_soyad': ['ad soyad', 'ad/soyad', 'isim', 'name', 'full name', 'ad soyadı', 'ad soyadi'],
	'tckimlik': ['tc', 'tc kimlik', 'kimlik', 'kimlik no', 'identity', 'national id', 'tckn', 't.c. kimlik'],
	'dogum_tarihi': ['doğum tarihi', 'dogum tarihi', 'birth date', 'birthdate', 'dob'],
	'model_yili': ['model yılı', 'model yili', 'model year', 'yil', 'yılı', 'yili'],
	'sasi_no': ['şasi', 'sasi', 'şasi no', 'sasi no', 'şasi numarası', 'sasi numarasi', 'şasi num', 'sasi num', 'şase', 'sase', 'chassis', 'vin'],
	'motor_no': ['motor', 'motor no', 'motor no.', 'motor numarası', 'motor numarasi', 'engine', 'engine no', 'engine number'],
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


def _score_element_text(soup, n, key: str, synonyms: Dict[str, List[str]]) -> int:
	try:
		attrs = getattr(n, 'attrs', {}) or {}
		texts: List[str] = []
		# label[for=id]
		try:
			idv = attrs.get('id')
			if idv and soup is not None:
				try:
					lab_el = soup.find('label', {'for': idv})
					if lab_el and hasattr(lab_el, 'get_text'):
						texts.append(lab_el.get_text(" "))
				except Exception:
					pass
		except Exception:
			pass
		# wrapping label text
		try:
			parent_label = n.find_parent('label') if hasattr(n, 'find_parent') else None
			if parent_label and hasattr(parent_label, 'get_text'):
				texts.append(parent_label.get_text(" "))
		except Exception:
			pass
		# aria-labelledby / aria-describedby references
		try:
			for aria_attr in ('aria-labelledby', 'aria-describedby'):
				ref = attrs.get(aria_attr)
				if ref and soup is not None:
					# can be space-separated ids
					for rid in str(ref).split():
						try:
							ref_el = soup.find(id=rid)
							if ref_el and hasattr(ref_el, 'get_text'):
								texts.append(ref_el.get_text(" "))
						except Exception:
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
		# Prefer unique data-* attributes (generic across sites), including common testing hooks
		def _quote_attr(val: str) -> str:
			s = str(val)
			# choose quotes that don't conflict with the value
			if "'" in s and '"' not in s:
				return f'"{s}"'
			return f"'{s.replace("'", "\\'")}'"
		# Try any unique data-* generically (no site-specific assumptions)
		for a, v in list((attrs or {}).items()):
			try:
				if isinstance(a, str) and a.startswith('data-') and isinstance(v, str):
					qp = _quote_attr(v)
					sel1 = f"{tag}[{a}={qp}]"
					sel2 = f"[{a}={qp}]"
					if len(soup.select(sel1)) == 1:
						return sel1
					if len(soup.select(sel2)) == 1:
						return sel2
			except Exception:
				pass
		# Angular/Reactive forms: formcontrolname as stable attribute
		try:
			v = attrs.get('formcontrolname')
			if v:
				qp = _quote_attr(v)
				sel1 = f"{tag}[formcontrolname={qp}]"
				sel2 = f"[formcontrolname={qp}]"
				if len(soup.select(sel1)) == 1:
					return sel1
				if len(soup.select(sel2)) == 1:
					return sel2
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
				score = _score_element_text(soup, n, key, syns)
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
					# classify selector kind for diagnostics
					kind = "unknown"; attr_used = None
					try:
						ss = sel_s
						if ss.startswith('#'):
							kind = 'id'
						elif "[name=" in ss:
							kind = 'name'
						else:
							m = re.search(r"\[(data-[^=\]]+)=", ss)
							if m:
								kind = 'data-attr'
								attr_used = m.group(1)
							elif "[aria-label=" in ss:
								kind = 'aria-label'
							elif "[aria-labelledby=" in ss:
								kind = 'aria-labelledby'
							elif "[aria-describedby=" in ss:
								kind = 'aria-describedby'
							elif "[placeholder=" in ss:
								kind = 'placeholder'
							elif "[title=" in ss:
								kind = 'title'
							elif "." in ss and ":nth-of-type(" not in ss:
								kind = 'class'
							elif ":nth-of-type(" in ss:
								kind = 'nth-of-type'
					except Exception:
						pass
					ctx["selector_kind"] = kind
					if attr_used:
						ctx["selector_attr"] = attr_used
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
	# Prefer mappingModel; fallback to generic model or env
	model = get("goFillForms.llm.mappingModel", get("goFillForms.llm.model", os.getenv("LLM_MODEL", "gpt-4o")))
	temp = float(get("goFillForms.llm.temperature", 0.0) or 0.0)

	prompt = _build_prompt(html, ruhsat_json)
	try:
		# Log a short snippet of the prompt for diagnostics
		_log("INFO", "F3-PROMPT", (prompt or "")[:1500], component="F3")
		# Also log provided ruhsat JSON (truncated) to prove dynamic input
		try:
			_ru = json.dumps(ruhsat_json or {}, ensure_ascii=False)
			_log("INFO", "F3-PROMPT-RUHSAT", (_ru or "")[:1500], component="F3")
		except Exception:
			pass
	except Exception:
		pass
	raw: str = ""
	_log("INFO", "F3-ANALYZE", f"key_present={bool(key)} model={model} temp={temp}", component="F3")
	if key:
		try:
			from openai import OpenAI  # type: ignore
			client = OpenAI(api_key=key)
			# First attempt with max_tokens (legacy param)
			try:
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
			except Exception as e1:
				# Retry using max_completion_tokens when model rejects max_tokens
				msg = str(e1)
				if ("max_tokens" in msg and "max_completion_tokens" in msg) or ("unsupported_parameter" in msg and "max_tokens" in msg):
					try:
						_log("WARN", "F3-LLM-RETRY", "retrying with max_completion_tokens=400", component="F3")
						resp = client.chat.completions.create(
							model=model,
							messages=[
								{"role": "system", "content": "Return ONLY strict JSON."},
								{"role": "user", "content": prompt},
							],
							temperature=temp,
							max_completion_tokens=400,  # type: ignore[arg-type]
						)
						raw = (resp.choices[0].message.content or "").strip()
					except Exception:
						raw = ""
				else:
					# Different error
					raw = ""
		except Exception:
			try:
				import openai  # type: ignore
				openai.api_key = key
				# First attempt with max_tokens
				try:
					raw = openai.chat.completions.create(  # type: ignore[attr-defined]
						model=model,
						messages=[
							{"role": "system", "content": "Return ONLY strict JSON."},
							{"role": "user", "content": prompt},
						],
						temperature=temp,
						max_tokens=400,
					).choices[0].message.content.strip()
				except Exception as e2:
					msg2 = str(e2)
					if ("max_tokens" in msg2 and "max_completion_tokens" in msg2) or ("unsupported_parameter" in msg2 and "max_tokens" in msg2):
						try:
							_log("WARN", "F3-LLM-RETRY", "retrying (legacy) with max_completion_tokens=400", component="F3")
							raw = openai.chat.completions.create(  # type: ignore[attr-defined]
								model=model,
								messages=[
									{"role": "system", "content": "Return ONLY strict JSON."},
									{"role": "user", "content": prompt},
								],
								temperature=temp,
								max_completion_tokens=400,  # type: ignore[arg-type]
							).choices[0].message.content.strip()
						except Exception:
							raw = ""
					else:
						raw = ""
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
	# Keep a copy of the original LLM validation before any heuristics, so we can assess LLM quality.
	llm_validation_snapshot = dict(validated) if isinstance(validated, dict) else {"cleaned": {}, "dropped": {}, "stats": {}}

	# Config flag to control heuristic salvage behavior (default True to preserve current behavior)
	try:
		heuristics_enabled = bool(get("goFillForms.llm.useHeuristics", True))
	except Exception:
		heuristics_enabled = True

	# Heuristic salvage: if enabled and some keys dropped, try to map by label/attributes and merge
	mapping_source: Dict[str, str] = {}
	heuristics_used = False
	heuristics_added_keys: List[str] = []
	if heuristics_enabled and page_kind == 'fill_form' and isinstance(validated, dict):
		cleaned_now = dict(validated.get('cleaned') or {})
		dropped_now = dict(validated.get('dropped') or {})
		# If nothing kept, try broader fallback on common keys or original keys
		if len(cleaned_now) == 0:
			keys = list(original_mapping.keys()) if isinstance(original_mapping, dict) and original_mapping else []
			if not keys:
				keys = ['plaka_no', 'tckimlik', 'dogum_tarihi', 'ad_soyad', 'model_yili', 'sasi_no', 'motor_no']
			auto_map = _heuristic_map_fields(html, keys)
			if auto_map:
				auto_valid = _validate_and_clean_mapping(html, auto_map)
				if len(auto_valid.get('cleaned') or {}) > 0:
					validated = auto_valid
					heuristics_used = True
					heuristics_added_keys = list((auto_valid.get('cleaned') or {}).keys())
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
						heuristics_used = True
						heuristics_added_keys = list(c2.keys())
						mapping_source.update({k: 'auto' for k in c2.keys()})
	# Debug helpers about prompt usage
	try:
		_cfg_prompt = get("goFillForms.llm.mappingPrompt")
		_prompt_source = "config" if (isinstance(_cfg_prompt, str) and _cfg_prompt.strip()) else "builtin"
	except Exception:
		_prompt_source = "builtin"
	_ru_keys = list((ruhsat_json or {}).keys())

	out: Dict[str, Any] = {
		"ok": True,
		"page_kind": page_kind,
	"field_mapping": validated.get("cleaned") if page_kind == 'fill_form' else {},
		"actions": data.get("actions") or [],
		"evidence": data.get("evidence") or None,
		"raw": raw,
		# Diagnostics (safe to ignore by UI)
		"prompt_source": _prompt_source,
		"prompt_snippet": (prompt or "")[:1500],
		"ruhsat_keys": _ru_keys,
	# New diagnostics to assess LLM mapping quality vs heuristics
	"llm_field_mapping": original_mapping if isinstance(original_mapping, dict) else {},
	"llm_validation": llm_validation_snapshot,
	"heuristics_enabled": heuristics_enabled,
	"heuristics_used": heuristics_used,
	"heuristics_added_keys": heuristics_added_keys,
	}
	if page_kind == 'fill_form':
		out["validation"] = validated
		if mapping_source:
			out["mapping_source"] = mapping_source
	return out


if __name__ == "__main__":
	# minimal smoke test (no API call will return ok=False)
	print(json.dumps(map_json_to_html_fields("<form></form>", {"plaka_no": "06 ABC 123"}), indent=2, ensure_ascii=False))

