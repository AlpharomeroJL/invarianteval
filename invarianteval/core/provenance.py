from __future__ import annotations

from typing import Any

from invarianteval.core.evidence import find_evidence
from invarianteval.core.trace import FieldTrace, Trace
from invarianteval.providers.base import FieldPolicy, Provenance


def _flatten_dict(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten_dict(value, path))
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                item_path = f"{path}[{idx}]"
                if isinstance(item, dict):
                    result.update(_flatten_dict(item, item_path))
                else:
                    result[item_path] = item
        else:
            result[path] = value
    return result


def _is_model_originated(field: str, model_parsed: dict[str, Any], final_value: Any) -> bool:
    flat = _flatten_dict(model_parsed)
    if field not in flat:
        return False
    return flat[field] == final_value


class ProvenanceDeriver:
    def derive(
        self,
        case_id: str,
        model_parsed: dict[str, Any],
        final_output: dict[str, Any],
        field_policies: dict[str, FieldPolicy],
        human_confirmed: dict[str, bool] | None = None,
        confidence: dict[str, float] | None = None,
        input_text: str = "",
        source_spans: dict[str, list[int]] | None = None,
    ) -> Trace:
        human_confirmed = human_confirmed or {}
        confidence = confidence or {}
        source_spans = source_spans or {}
        flat_final = _flatten_dict(final_output)
        trace = Trace(case_id=case_id, input_text=input_text)

        for field, value in flat_final.items():
            policy = field_policies.get(field, FieldPolicy.model_allowed)
            model_originated = _is_model_originated(field, model_parsed, value)

            if not model_originated:
                provenance = Provenance.human_entered
            elif human_confirmed.get(field, False):
                provenance = Provenance.ai_confirmed_by_human
            else:
                provenance = Provenance.ai_suggested

            has_ev, evidence_text, span = find_evidence(field, value, input_text, source_spans)

            trace.fields[field] = FieldTrace(
                field=field,
                value=value,
                provenance=provenance,
                model_originated=model_originated,
                policy=policy,
                confidence=confidence.get(field),
                source_span=span if has_ev else None,
                evidence_text=evidence_text,
            )

        return trace
