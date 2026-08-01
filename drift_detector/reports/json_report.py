from __future__ import annotations

import json
from pathlib import Path

from drift_detector.models.report import DriftReport


def render_json(report: DriftReport) -> str:
    return report.model_dump_json(indent=2)


def write_json(report: DriftReport, path: str | Path) -> None:
    Path(path).write_text(render_json(report) + "\n", encoding="utf-8")


def load_actual_resources(path: str | Path):
    from drift_detector.models.resource import ResourceModel

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("resources", [])
    return [ResourceModel.model_validate(item) for item in data]
