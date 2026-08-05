from __future__ import annotations

from abc import ABC, abstractmethod

from drift_detector.models.resource import ResourceModel


class CloudProvider(ABC):
    name: str

    @abstractmethod
    def fetch_resources(self, expected_resources: list[ResourceModel]) -> list[ResourceModel]:
        """Fetch actual cloud resources matching the expected resources when possible."""
