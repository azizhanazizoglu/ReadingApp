from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any


class PageKind(str, Enum):
    dashboard = "dashboard"
    home = "home"
    menu = "menu"
    user_task = "user_task"
    final = "final"
    unknown = "unknown"


@dataclass
class Action:
    description: str
    selector: Optional[str] = None
    event: str = "click"


@dataclass
class MappingField:
    json_key: str
    selector: str
    value: Optional[Any] = None


@dataclass
class Mapping:
    fields: List[MappingField]
    actions: List[Action]
    page_kind: PageKind = PageKind.unknown
    is_final: bool = False


@dataclass
class DiffResult:
    changed: bool
    reason: str
    prev_fingerprint: str
    new_fingerprint: str
