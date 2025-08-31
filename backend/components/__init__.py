"""
Core production components (≤120 LOC each), testable in isolation.
Interfaces derive from logic gates; orchestration follows TSX state flow.
"""

from .types import (
    PageKind,
    Mapping,
    MappingField,
    Action,
    DiffResult,
)
