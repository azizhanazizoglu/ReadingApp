from __future__ import annotations

"""detectFinalPageArrivedinUserTask

Statically detect whether the current HTML corresponds to the final activation page
where a CTA like "Poliçeyi Aktifleştir" is present. Returns a small structured
result usable by the feature/stateflow to stop early and click the CTA.
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
	if not isinstance(html, str) or not html:
		return {"is_final": False, "reason": "no_html"}
	low = _normalize(html)
	hits: List[str] = []
	for term in FINAL_CTA_SYNONYMS:
		t = _normalize(term)
		if t and t in low:
			hits.append(term)
	# Additionally detect common CTA classes/colors as weak signal
	weak = False
	if re.search(r"bg-green-600|btn-primary|btn-success|class=\".*(success|primary).*\"", html, flags=re.IGNORECASE):
		weak = True
	return {"is_final": bool(hits), "hits": hits, "weak": weak}


if __name__ == "__main__":
	demo = '<button class="px-8 py-3 bg-green-600 text-white">Poliçeyi Aktifleştir</button>'
	print(detect_final_page_arrived(demo))

