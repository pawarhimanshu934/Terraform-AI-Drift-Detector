from __future__ import annotations

from drift_detector.models.report import DriftReport


def render_console(report: DriftReport) -> str:
    lines = [
        "Terraform Drift Report",
        "======================",
        f"Scan ID: {report.scan_id}",
        f"Provider: {report.provider}",
        f"Resources expected: {report.summary.expected_resources}",
        f"Resources checked: {report.summary.actual_resources}",
        f"Findings: {report.summary.findings}",
        "",
    ]
    for finding in report.findings:
        lines.extend([
            f"[{finding.severity.upper()}] {finding.drift_type}",
            f"Resource: {finding.resource_type}.{finding.resource_id}",
            f"Path: {finding.attribute_path or '-'}",
            f"Expected: {finding.expected}",
            f"Actual: {finding.actual}",
            f"Message: {finding.message}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"
