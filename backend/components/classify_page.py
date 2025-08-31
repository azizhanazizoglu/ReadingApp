from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .types import PageKind
from backend.logging_utils import log_backend


@dataclass
class Classification:
    kind: PageKind
    is_final: bool


class ClassifyPage:
    """Fast, deterministic page classifier using regex markers.
    Extend patterns per site plugin if needed.
    """

    def __init__(self) -> None:
        self._dash = re.compile(r"Dashboard|Gösterge|Anasayfa", re.I)
        self._menu = re.compile(r"Menü|Side\s*Menu|Kullanıcı|Home", re.I)
        self._final = re.compile(r"Poliçeyi\s*Aktifleştir|PDF\s*Hazır|İndir", re.I)
        self._task = re.compile(r"Trafik|Sağlık|Sigorta|Teklif", re.I)

    def classify(self, html: str) -> Classification:
        is_final = bool(self._final.search(html))
        if self._dash.search(html):
            res = Classification(kind=PageKind.dashboard, is_final=is_final)
            log_backend("[INFO] [BE-2201] Classify: dashboard", code="BE-2201", component="ClassifyPage")
            return res
        if self._menu.search(html):
            res = Classification(kind=PageKind.home, is_final=is_final)
            log_backend("[INFO] [BE-2202] Classify: home", code="BE-2202", component="ClassifyPage")
            return res
        if self._task.search(html):
            res = Classification(kind=PageKind.user_task, is_final=is_final)
            log_backend("[INFO] [BE-2203] Classify: user_task", code="BE-2203", component="ClassifyPage")
            return res
        res = Classification(kind=PageKind.unknown, is_final=is_final)
        log_backend("[INFO] [BE-2204] Classify: unknown", code="BE-2204", component="ClassifyPage")
        return res
