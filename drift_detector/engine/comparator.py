from __future__ import annotations

from datetime import datetime, timezone
from fnmatch import fnmatch
from uuid import uuid4

from drift_detector.config import IgnoreConfig
from drift_detector.models.drift import DriftFinding
from drift_detector.models.report import DriftReport, ReportSummary
from drift_detector.models.resource import ResourceModel

_VOLATILE_ATTRIBUTES = {"id", "arn", "created_at", "last_modified", "updated_at"}


def _ignored(path: str, patterns: list[str]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


class DriftEngine:
    def __init__(self, ignore: IgnoreConfig | None = None) -> None:
        self.ignore = ignore or IgnoreConfig()

    def compare(
        self,
        expected: list[ResourceModel],
        actual: list[ResourceModel],
        provider: str,
        state_source: str,
    ) -> DriftReport:
        started = datetime.now(timezone.utc)
        findings: list[DriftFinding] = []
        actual_by_identity = {resource.identity: resource for resource in actual}
        expected_by_identity = {resource.identity: resource for resource in expected}

        for resource in expected:
            actual_resource = actual_by_identity.get(resource.identity)
            if actual_resource is None:
                findings.append(DriftFinding(resource_id=resource.id, resource_type=resource.type, drift_type="missing_resource", severity="high", expected=resource.model_dump(mode="json"), actual=None, message=f"Expected resource {resource.identity} was not found in cloud inventory."))
                continue
            findings.extend(self._compare_attributes(resource, actual_resource))
            findings.extend(self._compare_tags(resource, actual_resource))

        for resource in actual:
            if resource.identity not in expected_by_identity:
                findings.append(DriftFinding(resource_id=resource.id, resource_type=resource.type, drift_type="unexpected_resource", severity="medium", expected=None, actual=resource.model_dump(mode="json"), message=f"Cloud resource {resource.identity} is not tracked in Terraform state."))

        summary = ReportSummary(
            expected_resources=len(expected),
            actual_resources=len(actual),
            findings=len(findings),
            missing_resources=sum(1 for item in findings if item.drift_type == "missing_resource"),
            unexpected_resources=sum(1 for item in findings if item.drift_type == "unexpected_resource"),
            modified_resources=sum(1 for item in findings if item.drift_type == "attribute_changed"),
            tag_drifts=sum(1 for item in findings if item.drift_type == "tag_changed"),
        )
        return DriftReport(scan_id=f"scan-{uuid4().hex[:12]}", started_at=started, completed_at=datetime.now(timezone.utc), provider=provider, state_source=state_source, summary=summary, findings=findings)

    def _compare_attributes(self, expected: ResourceModel, actual: ResourceModel) -> list[DriftFinding]:
        findings: list[DriftFinding] = []
        keys = set(expected.attributes) | set(actual.attributes)
        for key in sorted(keys):
            if key in {"tags", "tags_all"} or key in _VOLATILE_ATTRIBUTES:
                continue
            path = f"{expected.type}.{key}"
            if _ignored(path, self.ignore.attributes) or _ignored(key, self.ignore.attributes):
                continue
            expected_value = expected.attributes.get(key)
            actual_value = actual.attributes.get(key)
            if expected_value != actual_value:
                findings.append(DriftFinding(resource_id=expected.id, resource_type=expected.type, drift_type="attribute_changed", severity="medium", attribute_path=path, expected=expected_value, actual=actual_value, message=f"Attribute {path} changed for {expected.identity}."))
        return findings

    def _compare_tags(self, expected: ResourceModel, actual: ResourceModel) -> list[DriftFinding]:
        findings: list[DriftFinding] = []
        keys = set(expected.tags) | set(actual.tags)
        for key in sorted(keys):
            if _ignored(key, self.ignore.tags):
                continue
            expected_value = expected.tags.get(key)
            actual_value = actual.tags.get(key)
            if expected_value != actual_value:
                findings.append(DriftFinding(resource_id=expected.id, resource_type=expected.type, drift_type="tag_changed", severity="low", attribute_path=f"tags.{key}", expected=expected_value, actual=actual_value, message=f"Tag {key} changed for {expected.identity}."))
        return findings
