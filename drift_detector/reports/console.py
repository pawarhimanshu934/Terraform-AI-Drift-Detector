from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from drift_detector.models.report import DriftReport

_COLUMN_WIDTHS = {
    "kind": 19,
    "severity": 10,
    "resource": 42,
    "field": 32,
    "expected": 32,
    "actual": 32,
}
_SEVERITY_LABELS = {"low": "info", "medium": "warning", "high": "critical"}


def render_console(report: DriftReport) -> str:
    """Render a compact terminal report optimized for quick drift review."""

    lines = [
        f"Scan ID:    {report.scan_id}",
        f"Provider:   {report.provider}",
        f"State:      {report.state_source}",
        "Status:     completed" if report.completed_at else "Status:     running",
        f"Started:    {_format_time(report.started_at)}",
        f"Completed:  {_format_time(report.completed_at)}" if report.completed_at else "Completed:  -",
        "",
        "SUMMARY",
        f"Total Resources:    {report.summary.expected_resources}",
        f"Missing in Cloud:   {report.summary.missing_resources}",
        f"Extra in Cloud:     {report.summary.unexpected_resources}",
        f"Attribute Changes:  {report.summary.modified_resources}",
        f"Tag Changes:        {report.summary.tag_drifts}",
        f"Unsupported Types:  {report.summary.unsupported_resources}",
        f"Total Findings:     {report.summary.findings}",
        "",
        "FINDINGS",
    ]

    if not report.findings:
        lines.append("No drift detected.")
        return "\n".join(lines) + "\n"

    lines.append(_row("KIND", "SEVERITY", "RESOURCE", "FIELD", "EXPECTED", "ACTUAL"))
    for finding in report.findings:
        lines.append(
            _row(
                finding.drift_type,
                _severity_label(finding.severity),
                _resource_label(finding.resource_id, finding.resource_type),
                finding.attribute_path or "-",
                _format_value(finding.expected),
                _format_value(finding.actual),
            )
        )
    return "\n".join(lines) + "\n"


def _row(kind: str, severity: str, resource: str, field: str, expected: str, actual: str) -> str:
    return (
        f"{_clip(kind, _COLUMN_WIDTHS['kind']):<{_COLUMN_WIDTHS['kind']}} "
        f"{_clip(severity, _COLUMN_WIDTHS['severity']):<{_COLUMN_WIDTHS['severity']}} "
        f"{_clip(resource, _COLUMN_WIDTHS['resource']):<{_COLUMN_WIDTHS['resource']}} "
        f"{_clip(field, _COLUMN_WIDTHS['field']):<{_COLUMN_WIDTHS['field']}} "
        f"{_clip(expected, _COLUMN_WIDTHS['expected']):<{_COLUMN_WIDTHS['expected']}} "
        f"{_clip(actual, _COLUMN_WIDTHS['actual'])}"
    )


def _format_time(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _severity_label(severity: str) -> str:
    return _SEVERITY_LABELS.get(severity, severity)


def _resource_label(resource_id: str, resource_type: str) -> str:
    return f"{resource_type}:{resource_id}"


def _format_value(value: Any) -> str:
    if value is None:
        return "<nil>"
    if isinstance(value, dict):
        if "type" in value and "id" in value:
            return _resource_label(str(value["id"]), str(value["type"]))
        return "{" + ", ".join(f"{key}: {value[key]}" for key in sorted(value)) + "}"
    return str(value)


def _clip(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "…"
