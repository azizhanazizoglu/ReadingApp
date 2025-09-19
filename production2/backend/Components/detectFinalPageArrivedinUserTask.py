from __future__ import annotations

"""detectFinalPageArrivedinUserTask

Static detection of final page state for the FillForms static flow.

Updated logic:
	1. Distinguish between a CTA presence (activation button) and actual final completion.
	2. Treat a page as *fully final* ONLY when PDF evidence is found (download link / embed).
	3. Provide structured signals so the stateflow can decide:
			 - cta_present (button text matches known synonyms)
			 - pdf_found (strong final signal)
			 - pdf_links / pdf_embeds lists for diagnostics

We still return legacy keys (is_final, hits, weak) for backward compatibility.
"""

from typing import Any, Dict, List
import re

FINAL_CTA_SYNONYMS: List[str] = [
    "Poliçeyi Aktifleştir",
    "Policeyi Aktiflestir",
    "Poliçeyi Üret",
    "Poliçeyi Yazdır",
    "Teklifi Onayla",
    "Satın Al",
]


def _normalize(s: str) -> str:
	try:
		import unicodedata
		s = unicodedata.normalize("NFKD", s)
		s = "".join(ch for ch in s if not unicodedata.combining(ch))
	except Exception:
		pass
	return s.lower().strip()


def detect_final_page_arrived(html: str) -> Dict[str, Any]:
	"""Return structured detection result.

	is_final is True ONLY if a PDF artifact is detected (strong completion signal).
	CTA presence alone (hits>0) yields cta_present but not final.
	"""
	if not isinstance(html, str) or not html:
		return {"is_final": False, "reason": "no_html", "cta_present": False, "pdf_found": False}

	low = _normalize(html)
	hits: List[str] = []
	for term in FINAL_CTA_SYNONYMS:
		t = _normalize(term)
		if t and t in low:
			hits.append(term)
	cta_present = bool(hits)

	# PDF evidence heuristics
	pdf_links = re.findall(r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']', html, flags=re.IGNORECASE)
	data_pdf = re.findall(r'href=["\'](data:application/pdf[^"\']+)["\']', html, flags=re.IGNORECASE)
	pdf_iframes = re.findall(r'<(?:iframe|embed|object)[^>]+(?:type=["\']application/pdf["\']|src=["\'][^"\']+\.pdf)', html, flags=re.IGNORECASE)

	pdf_found = bool(pdf_links or data_pdf or pdf_iframes)

	# Additionally detect common CTA classes/colors as weak signal
	weak = False
	if re.search(r"bg-green-600|btn-primary|btn-success|class=\".*(success|primary).*\"", html, flags=re.IGNORECASE):
		weak = True

	return {
		"is_final": pdf_found,        # strict final condition now
		"hits": hits,                 # CTA text hits
		"cta_present": cta_present,
		"weak": weak,
		"pdf_found": pdf_found,
		"pdf_links": pdf_links,
		"pdf_embeds": pdf_iframes + data_pdf,
		"reason": "pdf_detected" if pdf_found else ("cta_only" if cta_present else "no_final_signals"),
	}


if __name__ == "__main__":
	demo = '<button class="px-8 py-3 bg-green-600 text-white">Poliçeyi Aktifleştir</button>'
	print(detect_final_page_arrived(demo))

