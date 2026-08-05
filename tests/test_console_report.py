from datetime import datetime, timezone

from drift_detector.models.drift import DriftFinding
from drift_detector.models.report import DriftReport, ReportSummary
from drift_detector.reports.console import render_console


def test_console_report_uses_compact_summary_and_table():
    report = DriftReport(
        scan_id="scan-123",
        provider="aws",
        state_source="terraform.tfstate",
        started_at=datetime(2026, 6, 9, 19, 11, 15, tzinfo=timezone.utc),
        completed_at=datetime(2026, 6, 9, 19, 11, 16, tzinfo=timezone.utc),
        summary=ReportSummary(expected_resources=1, actual_resources=1, findings=2, modified_resources=1, tag_drifts=1),
        findings=[
            DriftFinding(resource_id="bucket-123", resource_type="aws_s3_bucket", drift_type="attribute_changed", severity="medium", attribute_path="versioning", expected="enabled", actual="disabled", message="changed"),
            DriftFinding(resource_id="bucket-123", resource_type="aws_s3_bucket", drift_type="tag_changed", severity="low", attribute_path="tags.Environment", expected="prod", actual="stage", message="changed"),
        ],
    )

    output = render_console(report)

    assert "SUMMARY" in output
    assert "FINDINGS" in output
    assert "KIND" in output
    assert "SEVERITY" in output
    assert "RESOURCE" in output
    assert "Attribute Changes:  1" in output
    assert "Tag Changes:        1" in output
    assert "attribute_changed" in output
    assert "warning" in output
    assert "bucket-123 (aws_s3_bucket)" in output
    assert "Message:" not in output
