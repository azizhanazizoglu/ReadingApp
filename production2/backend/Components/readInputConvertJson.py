from __future__ import annotations

"""readInputConvertJson

Standalone input ingestor for FillForms (F3):
- Reads configuration from production2/config.json (goFillForms.input.*)
- Loads ruhsat data from either a provided JSON file or extracts from the latest image
  in the configured directory via an LLM (optional, requires OPENAI_API_KEY).
- Returns a normalized Python dict with extracted fields.

This module is self-contained within production2 and does not import external
project packages (license_llm, etc.).
"""

from pathlib import Path as _Path
from typing import Any, Dict, Optional, Tuple, List
import os
import glob
import json
import base64
from datetime import datetime as _dt

# Ensure production2 config import
_THIS = _Path(__file__).resolve()
_ROOT = _THIS.parents[2]
_BACKEND = _THIS.parents[1]
import sys as _sys
if str(_ROOT) not in _sys.path:
	_sys.path.insert(0, str(_ROOT))
if str(_BACKEND) not in _sys.path:
	_sys.path.insert(0, str(_BACKEND))

from config import get  # type: ignore
try:
	from logging_utils import log as _log  # type: ignore
except Exception:
	def _log(*args, **kwargs):
		try:
			print("[F3-INGEST]", *args)
		except Exception:
			pass


# Directory to dump raw and parsed LLM outputs for inspection
_LLM_DUMP_DIR = _ROOT / "tmp" / "jsonDatafromLLM"
_LLM_DUMP_DIR.mkdir(parents=True, exist_ok=True)


def _get_cfg(path: str, default: Any = None) -> Any:
	try:
		return get(path, default)
	except Exception:
		return default


def _latest_file_in_dir(dir_path: str, patterns: Tuple[str, ...] = ("*.jpg", "*.jpeg", "*.png")) -> Optional[str]:
	if not dir_path:
		return None
	try:
		cands: List[Tuple[float, str]] = []
		for pat in patterns:
			for p in glob.glob(os.path.join(dir_path, pat)):
				try:
					cands.append((os.path.getmtime(p), p))
				except Exception:
					pass
		if not cands:
			return None
		cands.sort(key=lambda x: x[0], reverse=True)
		return cands[0][1]
	except Exception:
		return None


def _read_json_file(json_path: str) -> Optional[Dict[str, Any]]:
	try:
		with open(json_path, "r", encoding="utf-8") as f:
			data = json.load(f)
		return data if isinstance(data, dict) else None
	except Exception:
		return None


def _extract_with_llm(image_path: str, model: Optional[str] = None, temperature: float = 0.0) -> Optional[Dict[str, Any]]:
	"""Use OpenAI Vision to extract ruhsat fields. Requires OPENAI_API_KEY.

	Returns a dict of fields on success, or None on failure.
	"""
	key = os.getenv("OPENAI_API_KEY")
	if not key:
		return None

	model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
	# Read image as base64 to construct data URL
	try:
		raw = _Path(image_path).read_bytes()
		b64 = base64.b64encode(raw).decode("ascii")
		ext = (image_path.split('.')[-1] or '').lower()
		mime = 'jpeg' if ext == 'jpg' else ('jpeg' if ext == 'jpeg' else ('png' if ext == 'png' else 'jpeg'))
		data_url = f"data:image/{mime};base64,{b64}"
	except Exception as e:
		try:
			_log("WARN", "F3-INGEST", f"failed to read image bytes: {e}", component="F3", extra={"path": image_path})
		except Exception:
			pass
		return None

	prompt = (
		"Extract fields from the Turkish vehicle registration (ruhsat) image and return STRICT JSON only.\n"
		"Use keys where possible (examples; include what is present):\n"
		"plaka_no, tckimlik, vergi_no, ad_soyad, adres, marka, model, model_yili, sasi_no, motor_no, yakit, renk.\n"
		"No prose, no explanations. Only one JSON object."
	)

	content = [
		{"type": "text", "text": prompt},
		{"type": "image_url", "image_url": {"url": data_url}},
	]

	# Try new SDK first, fallback to legacy
	try:
		from openai import OpenAI  # type: ignore
		client = OpenAI(api_key=key)
		resp = client.chat.completions.create(
			model=model,
			messages=[{"role": "user", "content": content}],  # type: ignore[arg-type]
			temperature=temperature,
			max_tokens=400,
		)
		txt = (resp.choices[0].message.content or "").strip()
	except Exception as e:
		try:
			_log("WARN", "F3-INGEST", f"openai chat.completions failed: {e}", component="F3")
		except Exception:
			pass
		# Fallback 1: Responses API (multi-modal)
		try:
			from openai import OpenAI as _OpenAI  # type: ignore
			_client2 = _OpenAI(api_key=key)
			resp2 = _client2.responses.create(
				model=model,
				input=[{
					"role": "user",
					"content": [
						{"type": "input_text", "text": prompt},
						{"type": "input_image", "image_url": data_url},
					]
				}]
			)
			# unified accessor
			try:
				txt = resp2.output_text  # type: ignore[attr-defined]
			except Exception:
				# fallback to first text output
				parts = getattr(resp2, "output", None)
				txt = str(parts)
		except Exception as e_resp:
			try:
				_log("WARN", "F3-INGEST", f"responses API failed: {e_resp}", component="F3")
			except Exception:
				pass
			# Fallback 2: legacy openai
			try:
				import openai  # type: ignore
				openai.api_key = key
				txt = openai.chat.completions.create(  # type: ignore[attr-defined]
					model=model,
					messages=[{"role": "user", "content": content}],
					temperature=temperature,
					max_tokens=400,
				).choices[0].message.content.strip()
			except Exception as e2:
				try:
					_log("WARN", "F3-INGEST", f"legacy openai call failed: {e2}", component="F3")
				except Exception:
					pass
				return None

	# Dump raw model output for debugging
	try:
		stem = _Path(image_path).stem
		ts = _dt.utcnow().strftime("%Y%m%d_%H%M%S%fZ")
		raw_file = _LLM_DUMP_DIR / f"{stem}_{ts}_raw.txt"
		raw_file.write_text(txt, encoding="utf-8", errors="ignore")
		# Also write a JSON-wrapped copy for convenience
		raw_json_file = _LLM_DUMP_DIR / f"{stem}_{ts}_raw.json"
		raw_json_file.write_text(json.dumps({"raw_response": txt}, indent=2, ensure_ascii=False), encoding="utf-8")
		_log("INFO", "F3-INGEST", f"saved LLM raw -> {raw_file}", component="F3")
		_log("INFO", "F3-INGEST", f"saved LLM raw JSON -> {raw_json_file}", component="F3")
	except Exception:
		pass

	# Parse JSON (allow code fences)
	try:
		import re
		s = txt.strip()
		m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s, flags=re.IGNORECASE)
		if m:
			s = m.group(1).strip()
		data = json.loads(s)
		# Save parsed JSON
		try:
			stem = _Path(image_path).stem
			ts2 = _dt.utcnow().strftime("%Y%m%d_%H%M%S%fZ")
			parsed_file = _LLM_DUMP_DIR / f"{stem}_{ts2}_parsed.json"
			parsed_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
			_log("INFO", "F3-INGEST", f"saved LLM parsed JSON -> {parsed_file}", component="F3", extra={"keys": list(data.keys())})
		except Exception:
			pass
		# Log parsed JSON (may be large)
		try:
			_log("INFO", "F3-INGEST", "llm parsed json", component="F3", extra={"json": data})
		except Exception:
			pass
		return data if isinstance(data, dict) else None
	except Exception:
		return None


def read_input_and_convert_to_json() -> Dict[str, Any]:
	"""Main entry: decide source and return ruhsat JSON + metadata.

	Config keys (production2/config.json):
	- goFillForms.input.jsonPath: optional absolute/relative path to a prepared JSON file
	- goFillForms.input.imageDir: directory containing uploaded images (tmp)
	- goFillForms.llm.model, goFillForms.llm.temperature
	- goFillForms.persist.dir: optional directory to save the normalized json copy
	"""
	json_path = _get_cfg("goFillForms.input.jsonPath")
	image_dir = _get_cfg("goFillForms.input.imageDir", str(_ROOT / "tmp/data"))
	model = _get_cfg("goFillForms.llm.model", os.getenv("LLM_MODEL", "gpt-4o-mini"))
	temperature = float(_get_cfg("goFillForms.llm.temperature", 0.0) or 0.0)
	persist_dir = _get_cfg("goFillForms.persist.dir")

	meta: Dict[str, Any] = {"source": None, "path": None, "llm_dump_dir": str(_LLM_DUMP_DIR)}
	_log("INFO", "F3-INGEST", f"jsonPath={json_path or ''} imageDir={image_dir}", component="F3")

	# Prefer explicit JSON if provided
	if isinstance(json_path, str) and json_path.strip():
		p = (_ROOT / json_path).resolve() if not os.path.isabs(json_path) else _Path(json_path)
		data = _read_json_file(str(p))
		if data is not None:
			meta.update({"source": "json", "path": str(p)})
			_log("INFO", "F3-INGEST", f"loaded json {p}", component="F3")
			return {"ok": True, "data": data, "meta": meta}

	# Else try image directory
	image_dir_abs = str((_ROOT / image_dir) if not os.path.isabs(str(image_dir)) else image_dir)
	meta["image_dir"] = image_dir_abs
	if not os.path.isdir(image_dir_abs):
		_log("WARN", "F3-INGEST", f"image dir not found {image_dir_abs}", component="F3")
		return {"ok": False, "error": "no_image_dir", "meta": meta}
	latest = _latest_file_in_dir(image_dir_abs)
	if latest:
		_log("INFO", "F3-INGEST", f"latest image {latest}", component="F3")
		# Companion json? (same stem)
		stem_json = os.path.splitext(latest)[0] + ".json"
		if os.path.isfile(stem_json):
			data = _read_json_file(stem_json)
			if data is not None:
				meta.update({"source": "companion_json", "path": stem_json})
				_log("INFO", "F3-INGEST", f"loaded companion json {stem_json}", component="F3")
				return {"ok": True, "data": data, "meta": meta}

		# Try LLM extraction
		if not os.getenv("OPENAI_API_KEY"):
			_log("WARN", "F3-INGEST", "OPENAI_API_KEY missing for vision extraction", component="F3")
			return {"ok": False, "error": "no_key_for_vision", "meta": {**meta, "path": latest}}
		data = _extract_with_llm(latest, model=model, temperature=temperature)
		if data is not None:
			meta.update({"source": "vision_llm", "path": latest})
			_log("INFO", "F3-INGEST", f"vision extracted fields={list(data.keys())}", component="F3")
			# Optional persist
			try:
				if isinstance(persist_dir, str) and persist_dir.strip():
					out_dir = (_ROOT / persist_dir).resolve() if not os.path.isabs(persist_dir) else _Path(persist_dir)
					out_dir.mkdir(parents=True, exist_ok=True)
					out_file = out_dir / ("ruhsat_" + _Path(latest).stem + ".json")
					out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
					meta["saved"] = str(out_file)
					_log("INFO", "F3-INGEST", f"saved {out_file}", component="F3")
			except Exception:
				pass
			return {"ok": True, "data": data, "meta": meta}

		# Vision tried but failed to extract JSON
		_log("WARN", "F3-INGEST", "vision extract failed", component="F3", extra={"meta": {**meta, "path": latest}})
		return {"ok": False, "error": "vision_extract_failed", "meta": {**meta, "path": latest}}

	# No images in directory
	_log("WARN", "F3-INGEST", "no images found in image_dir", component="F3", extra={"meta": meta})
	return {"ok": False, "error": "no_images_found", "meta": meta}

	_log("WARN", "F3-INGEST", "no input found", component="F3", extra={"meta": meta})
	return {"ok": False, "error": "no_input_found", "meta": meta}


if __name__ == "__main__":
	out = read_input_and_convert_to_json()
	print(json.dumps(out, indent=2, ensure_ascii=False))

