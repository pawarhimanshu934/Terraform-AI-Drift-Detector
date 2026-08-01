from __future__ import annotations

from typing import Any

from drift_detector.models.resource import ResourceModel


def _provider_from_type(resource_type: str) -> str:
    return resource_type.split("_", 1)[0] if "_" in resource_type else "unknown"


def extract_expected_resources(state: dict[str, Any]) -> list[ResourceModel]:
    resources: list[ResourceModel] = []
    for resource in state.get("resources", []):
        if resource.get("mode") != "managed":
            continue
        resource_type = resource.get("type", "unknown")
        provider = _provider_from_type(resource_type)
        for index, instance in enumerate(resource.get("instances", [])):
            attrs = instance.get("attributes") or {}
            resource_id = str(attrs.get("id") or instance.get("index_key") or f"{resource.get('name')}[{index}]")
            address = f"{resource_type}.{resource.get('name')}"
            if "index_key" in instance:
                address = f"{address}[{instance['index_key']!r}]"
            tags = attrs.get("tags") or attrs.get("tags_all") or {}
            resources.append(
                ResourceModel(
                    provider=provider,
                    type=resource_type,
                    id=resource_id,
                    name=resource.get("name"),
                    address=address,
                    region=attrs.get("region") or attrs.get("availability_zone"),
                    attributes=attrs,
                    tags={str(k): str(v) for k, v in tags.items()},
                    raw=instance,
                )
            )
    return resources
