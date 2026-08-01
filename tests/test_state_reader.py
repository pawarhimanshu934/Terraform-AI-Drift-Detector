from drift_detector.state.extractor import extract_expected_resources
from drift_detector.state.reader import TerraformStateReader


def test_extracts_managed_resources_only():
    state = TerraformStateReader().read("tests/fixtures/terraform.tfstate")
    resources = extract_expected_resources(state)

    assert len(resources) == 1
    assert resources[0].identity == "aws:aws_instance:i-1234567890"
    assert resources[0].tags["Environment"] == "prod"
