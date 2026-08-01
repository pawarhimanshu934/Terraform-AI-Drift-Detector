from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

DriftType = Literal[
    "missing_resource",
    "unexpected_resource",
    "attribute_changed",
    "tag_changed",
    "type_mismatch",
    "unsupported_resource",
]
Severity = Literal["low", "medium", "high"]


@dataclass
class DriftFinding:
    resource_id: str
    resource_type: str
    drift_type: DriftType
    severity: Severity
    message: str
    attribute_path: str | None = None
    expected: Any = None
    actual: Any = None

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
