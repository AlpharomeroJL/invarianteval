from __future__ import annotations

import pytest

from invarianteval.core.provenance import ProvenanceDeriver
from invarianteval.providers.base import FieldPolicy, Provenance


@pytest.fixture
def deriver() -> ProvenanceDeriver:
    return ProvenanceDeriver()


def test_locked_field_auto_filled_fails(deriver: ProvenanceDeriver) -> None:
    model_parsed = {"pass_fail_result": "pass", "panel_model": "ABC-100"}
    final_output = {"pass_fail_result": "pass", "panel_model": "ABC-100"}
    policies = {"pass_fail_result": FieldPolicy.locked, "panel_model": FieldPolicy.model_allowed}

    trace = deriver.derive("t1", model_parsed, final_output, policies)

    pf = trace.field("pass_fail_result")
    assert pf is not None
    assert pf.model_originated is True
    assert pf.provenance == Provenance.ai_suggested
    assert pf.policy == FieldPolicy.locked


def test_human_confirmed_model_field(deriver: ProvenanceDeriver) -> None:
    model_parsed = {"pass_fail_result": "pass"}
    final_output = {"pass_fail_result": "pass"}
    policies = {"pass_fail_result": FieldPolicy.locked}

    trace = deriver.derive(
        "t2",
        model_parsed,
        final_output,
        policies,
        human_confirmed={"pass_fail_result": True},
    )

    pf = trace.field("pass_fail_result")
    assert pf is not None
    assert pf.provenance == Provenance.ai_confirmed_by_human


def test_human_only_field(deriver: ProvenanceDeriver) -> None:
    model_parsed = {"panel_model": "ABC-100"}
    final_output = {"panel_model": "ABC-100", "device_status": "operational"}
    policies = {
        "panel_model": FieldPolicy.model_allowed,
        "device_status": FieldPolicy.locked,
    }

    trace = deriver.derive("t3", model_parsed, final_output, policies)

    status = trace.field("device_status")
    assert status is not None
    assert status.model_originated is False
    assert status.provenance == Provenance.human_entered


def test_model_allowed_field(deriver: ProvenanceDeriver) -> None:
    model_parsed = {"panel_model": "ABC-100"}
    final_output = {"panel_model": "ABC-100"}
    policies = {"panel_model": FieldPolicy.model_allowed}

    trace = deriver.derive("t4", model_parsed, final_output, policies)

    pm = trace.field("panel_model")
    assert pm is not None
    assert pm.model_originated is True
    assert pm.provenance == Provenance.ai_suggested
