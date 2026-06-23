from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class AssertionSpec(BaseModel):
    name: str
    params: dict[str, Any] = Field(default_factory=dict)


class EvalCase(BaseModel):
    id: str
    input_file: str
    expected_file: str | None = None
    assertions: list[AssertionSpec] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def input_path(self, suite_dir: Path) -> Path:
        return suite_dir / self.input_file

    def expected_path(self, suite_dir: Path) -> Path | None:
        if not self.expected_file:
            return None
        return suite_dir / self.expected_file
