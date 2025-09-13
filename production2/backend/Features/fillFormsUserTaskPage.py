from __future__ import annotations

"""fillFormsUserTaskPage feature orchestrator (F3).

Provides planning (no direct execution) for actions:
  - loadRuhsatFromTmp: ingest ruhsat JSON (prepared or via Vision LLM on latest image)
  - analyzePage: LLM-based field mapping and action suggestion per page
  - buildFillPlan: convert field_mapping + ruhsat_json to a FillPlan (set_value/select_option + optional click)
  - detectFinalPage: static detection of final activation CTAs (e.g., "Poliçeyi Aktifleştir")
  - checkPageChanged: detect raw HTML change (hash/normalized)

Also exposes plan_full_fill_flow to chain analyzePage + buildFillPlan when needed.
"""

from typing import Any, Dict, Optional
from dataclasses import asdict
from pathlib import Path as _Path
import sys
import hashlib
import json as _json

_this = _Path(__file__).resolve()
_root = _this.parents[2]
if str(_root) not in sys.path:
	sys.path.insert(0, str(_root))

from Components.readInputConvertJson import read_input_and_convert_to_json  # type: ignore
from Components.letLLMMapUserPageForms import map_json_to_html_fields  # type: ignore
from Components.detectFinalPageArrivedinUserTask import detect_final_page_arrived  # type: ignore
from Components.fillPageFromMapping import fill_and_go  # type: ignore
from Components.detectWepPageChange import detect_web_page_change  # type: ignore
from Components.detectFormsAreFilled import detect_forms_filled  # type: ignore
from memory import FillPlan  # type: ignore
from Components.uploadToSystemData import ensure_f3_data_ready  # type: ignore


def _fingerprint(html: Optional[str]) -> Optional[str]:
	if not html:
		return None
	try:
		return hashlib.sha256(html.encode("utf-8")).hexdigest()
	except Exception:
		return None


# ------------------------- loadRuhsatFromTmp -------------------------

def plan_load_ruhsat_json() -> Dict[str, Any]:
	"""Return ruhsat JSON via ingest pipeline.

	Delegates to read_input_and_convert_to_json. Pass-through the structure.
	"""
	try:
		# First, try staging inputs from configured sourceDir into imageDir
		prep = ensure_f3_data_ready()
		res = read_input_and_convert_to_json()
		if isinstance(res, dict):
			res.setdefault("prep", prep)
		return res
	except Exception as e:
		return {"ok": False, "error": f"ingest_failed: {e}"}


# ------------------------- analyzePage -------------------------

def plan_analyze_page(filtered_html: Optional[str], ruhsat_json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
	if not filtered_html:
		return {"ok": False, "error": "no_filtered_html"}
	try:
		out = map_json_to_html_fields(filtered_html, ruhsat_json or {})
		# Attach a simple fingerprint for observability
		fp = _fingerprint(filtered_html)
		out["fingerprint"] = fp

		# Dump artifacts for debugging (HTML + mapping JSON)
		try:
			dump_dir = _root / "tmp" / "JpegJsonWebpageHtml"
			dump_dir.mkdir(parents=True, exist_ok=True)
			base = (fp or "page")[:16]
			html_path = dump_dir / f"{base}.html"
			map_path = dump_dir / f"{base}_mapping.json"
			with open(html_path, "w", encoding="utf-8") as f:
				f.write(filtered_html)
			with open(map_path, "w", encoding="utf-8") as f:
				_json.dump(out, f, ensure_ascii=False, indent=2)
			out.setdefault("debug_dumps", {})
			out["debug_dumps"].update({"html": str(html_path), "mapping": str(map_path)})
		except Exception:
			pass
		return out
	except Exception as e:
		return {"ok": False, "error": f"analyze_failed: {e}"}


# ------------------------- buildFillPlan -------------------------

def plan_build_fill_plan(mapping: Optional[Dict[str, Any]], ruhsat_json: Optional[Dict[str, Any]]) -> Dict[str, Any]:
	"""Build FillPlan actions from LLM-provided mapping and ruhsat data.

	mapping is expected to be { field_mapping: {logical -> selector}, llm_actions?: [str] }
	"""
	try:
		mapping = mapping or {}
		fm = mapping.get("field_mapping") if isinstance(mapping, dict) else None
		if not isinstance(fm, dict):
			fm = {}
		data = ruhsat_json or {}
		# Compose selector->value map
		sel_map: Dict[str, Any] = {}
		for k, sel in fm.items():
			try:
				if isinstance(sel, str) and k in data:
					sel_map[sel] = data.get(k)
			except Exception:
				pass
		# Optional action button (css:...)
		action_button = None
		try:
			acts = mapping.get("llm_actions") if isinstance(mapping, dict) else None
			if isinstance(acts, list) and acts:
				first = acts[0]
				if isinstance(first, str) and first.lower().startswith("css:"):
					action_button = first[4:].strip()
		except Exception:
			action_button = None
		plan: FillPlan = fill_and_go(sel_map, action_button_selector=action_button)  # type: ignore
		return {"ok": True, "planType": "fillPlan", "plan": asdict(plan)}
	except Exception as e:
		return {"ok": False, "error": f"plan_failed: {e}"}


# ------------------------- detectFinalPage -------------------------

def plan_detect_final_page(filtered_html: Optional[str]) -> Dict[str, Any]:
	if not filtered_html:
		return {"ok": True, "is_final": False, "reason": "no_html"}
	try:
		out = detect_final_page_arrived(filtered_html)
		return {"ok": True, **out, "fingerprint": _fingerprint(filtered_html)}
	except Exception as e:
		return {"ok": False, "error": f"detect_failed: {e}"}


# ------------------------- checkPageChanged -------------------------

def plan_check_page_changed(current_raw_html: Optional[str], prev_raw_html: Optional[str], use_normalized_compare: bool = True) -> Dict[str, Any]:
	result = detect_web_page_change(
		current_raw_html=current_raw_html,
		prev_raw_html=prev_raw_html,
		use_normalized_compare=use_normalized_compare,
	)
	return {"ok": True, "action": "checkPageChanged", "result": asdict(result)}


# ------------------------- detectFormsFilled -------------------------

def plan_detect_forms_filled(details: Optional[Dict[str, Any]] = None, html: Optional[str] = None, min_filled: int = 2) -> Dict[str, Any]:
	"""Check if at least min_filled inputs are filled.

	details: response from frontend filler: { details: [ { before, after, field, ... } ] }
	html: optional current HTML to fallback-check
	"""
	try:
		det_list = None
		if isinstance(details, dict) and isinstance(details.get('details'), list):
			det_list = details.get('details')
		out = detect_forms_filled(det_list, html, min_filled=min_filled)
		return {"ok": True, **out}
	except Exception as e:
		return {"ok": False, "error": f"detect_forms_failed: {e}"}


if __name__ == "__main__":  # smoke test
	demo_filtered = """
	<form>
	  <label for="plk">Plaka</label>
	  <input id="plk" />
	  <button>Devam</button>
	</form>
	"""
	import json as _json
	print("-- analyzePage --")
	print(_json.dumps(plan_analyze_page(demo_filtered, {"plaka_no": "06 ABC 123"}), indent=2, ensure_ascii=False)[:500])
	print("-- detectFinalPage --")
	print(_json.dumps(plan_detect_final_page('<button>Poliçeyi Aktifleştir</button>'), indent=2, ensure_ascii=False))
