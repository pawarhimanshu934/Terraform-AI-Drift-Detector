from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ResourceModel:
    """Cloud-agnostic representation of an infrastructure resource."""

    provider: str
    type: str
    id: str
    name: str | None = None
    address: str | None = None
    region: str | None = None
    account_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] | None = None

    @property
    def identity(self) -> str:
        return f"{self.provider}:{self.type}:{self.id}"

    def model_dump(self, mode: str | None = None) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def model_validate(cls, data: dict[str, Any]) -> "ResourceModel":
        return cls(**data)
