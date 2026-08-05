from drift_detector.engine.comparator import DriftEngine
from drift_detector.models.resource import ResourceModel


def test_detects_attribute_and_tag_drift():
    expected = ResourceModel(provider="aws", type="aws_instance", id="i-1", attributes={"instance_type": "t3.micro"}, tags={"Environment": "prod"})
    actual = ResourceModel(provider="aws", type="aws_instance", id="i-1", attributes={"instance_type": "t3.small"}, tags={"Environment": "stage"})

    report = DriftEngine().compare([expected], [actual], provider="aws", state_source="fixture")

    assert report.summary.findings == 2
    assert {finding.drift_type for finding in report.findings} == {"attribute_changed", "tag_changed"}


def test_detects_missing_and_unexpected_resources():
    expected = ResourceModel(provider="aws", type="aws_s3_bucket", id="expected")
    actual = ResourceModel(provider="aws", type="aws_s3_bucket", id="actual")

    report = DriftEngine().compare([expected], [actual], provider="aws", state_source="fixture")

    assert report.summary.missing_resources == 1
    assert report.summary.unexpected_resources == 1


def test_marks_live_provider_unsupported_types_without_missing_resource_noise():
    expected = ResourceModel(provider="aws", type="aws_s3_bucket_versioning", id="bucket")

    report = DriftEngine().compare([expected], [], provider="aws", state_source="fixture", unsupported_resource_types={"aws_s3_bucket_versioning"})

    assert report.summary.missing_resources == 0
    assert report.summary.unsupported_resources == 1
    assert report.findings[0].drift_type == "unsupported_resource"
