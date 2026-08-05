from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal environments
    yaml = None


@dataclass
class StateConfig:
    path: str
    source: str = "local"


@dataclass
class ProviderConfig:
    name: str
    profile: str | None = None
    regions: list[str] = field(default_factory=list)


@dataclass
class IgnoreConfig:
    attributes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class AppConfig:
    state: StateConfig
    provider: ProviderConfig
    ignore: IgnoreConfig = field(default_factory=IgnoreConfig)


def load_config(path: str | Path) -> AppConfig:
    if yaml is None:
        raise RuntimeError("PyYAML is required to load YAML config files.")
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return AppConfig(
        state=StateConfig(**data["state"]),
        provider=ProviderConfig(**data["provider"]),
        ignore=IgnoreConfig(**data.get("ignore", {})),
    )
