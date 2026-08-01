from __future__ import annotations

from drift_detector.models.resource import ResourceModel
from drift_detector.providers.base import CloudProvider


class AWSProvider(CloudProvider):
    """AWS provider adapter skeleton.

    The core engine is usable with injected actual resources today. Installing the optional
    `aws` dependency enables future boto3 fetcher implementations without changing callers.
    """

    name = "aws"

    def __init__(self, profile: str | None = None, regions: list[str] | None = None) -> None:
        self.profile = profile
        self.regions = regions or []

    def fetch_resources(self, expected_resources: list[ResourceModel]) -> list[ResourceModel]:
        raise NotImplementedError(
            "Live AWS fetching is not implemented yet. Use JSON actual-resource input or extend AWSProvider."
        )
