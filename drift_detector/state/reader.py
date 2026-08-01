from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TerraformStateReader:
    """Reads local Terraform state files without invoking Terraform."""

    def read(self, path: str | Path) -> dict[str, Any]:
        state_path = Path(path)
        with state_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
