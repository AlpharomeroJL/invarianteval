from __future__ import annotations

from pathlib import Path
from typing import Any

from invarianteval.core.suite import load_suite


def list_invariants(suite_path: str) -> dict[str, Any]:
    suite = load_suite(Path(suite_path))
    cases_out: list[dict[str, Any]] = []
    for case in suite.cases:
        cases_out.append(
            {
                "id": case.id,
                "assertions": [
                    {"name": spec.name, "params": spec.params} for spec in case.assertions
                ],
            }
        )
    return {
        "name": suite.name,
        "schema_file": suite.schema_file,
        "field_policies": {k: v.value for k, v in suite.field_policies.items()},
        "equivalence_classes": {
            name: cls.model_dump() for name, cls in suite.equivalence_classes.items()
        },
        "cases": cases_out,
    }
