from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from drift_detector.models.drift import DriftFinding


@dataclass
class ReportSummary:
    expected_resources: int = 0
    actual_resources: int = 0
    findings: int = 0
    missing_resources: int = 0
    unexpected_resources: int = 0
    modified_resources: int = 0
    tag_drifts: int = 0
    unsupported_resources: int = 0


@dataclass
class DriftReport:
    scan_id: str
    provider: str
    state_source: str
    summary: ReportSummary
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    findings: list[DriftFinding] = field(default_factory=list)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    def model_dump_json(self, indent: int | None = None) -> str:
        return json.dumps(self.model_dump(), indent=indent, default=str)
