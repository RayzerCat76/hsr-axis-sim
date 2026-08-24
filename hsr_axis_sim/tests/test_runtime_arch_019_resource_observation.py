from dataclasses import FrozenInstanceError
from math import inf, nan

import pytest

from hsr_axis_sim.runtime_contracts import (
    RuntimeEvent,
    RuntimeEventType,
    RuntimeResourceChangeObservation,
    RuntimeResourceKind,
    RuntimeResourceScope,
)
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
    build_runtime_trace_artifact,
    build_runtime_trace_document,
)
from hsr_axis_sim.runtime_loaders import (
    RuntimeTraceLoadConfig,
    TraceCanonicalFormPolicy,
    TraceDigestPolicy,
    load_runtime_trace_bytes,
)


def _energy_observation():
    return RuntimeResourceChangeObservation(
        RuntimeResourceKind.ENERGY,
        RuntimeResourceScope.UNIT,
        70.0,
        100.0,
        50.0,
        30.0,
        100.0,
        "unit-a",
    )


def _skill_point_observation():
    return RuntimeResourceChangeObservation(
        RuntimeResourceKind.SKILL_POINTS,
        RuntimeResourceScope.TEAM,
        4,
        5,
        3,
        1,
        5,
        None,
    )


def test_valid_energy_observation_payload_is_exact_and_deterministic():
    observation = _energy_observation()
    assert observation.to_payload() == {
        "resource_kind": "ENERGY",
        "scope": "UNIT",
        "before": 70.0,
        "after": 100.0,
        "requested_delta": 50.0,
        "applied_delta": 30.0,
        "cap": 100.0,
        "unit_id": "unit-a",
    }
    assert observation.to_payload() == observation.to_payload()


def test_valid_skill_point_observation_preserves_requested_vs_applied_clamp_delta():
    observation = _skill_point_observation()
    assert observation.to_payload() == {
        "resource_kind": "SKILL_POINTS",
        "scope": "TEAM",
        "before": 4,
        "after": 5,
        "requested_delta": 3,
        "applied_delta": 1,
        "cap": 5,
        "unit_id": None,
    }


def test_observation_is_frozen_and_runtime_event_freezes_payload():
    observation = _energy_observation()
    with pytest.raises(FrozenInstanceError):
        observation.after = 90.0

    mutable_payload = observation.to_payload()
    event = RuntimeEvent(
        "resource-energy-0",
        RuntimeEventType.ENERGY_CHANGED,
        0,
        "action-a",
        None,
        None,
        None,
        None,
        "unit-a",
        mutable_payload,
    )
    mutable_payload["after"] = 1.0
    assert event.payload["after"] == 100.0
    with pytest.raises(TypeError):
        event.payload["after"] = 1.0


@pytest.mark.parametrize("bad", [True, False, nan, inf, -inf])
def test_invalid_numeric_values_are_rejected(bad):
    kwargs = dict(
        resource_kind=RuntimeResourceKind.ENERGY,
        scope=RuntimeResourceScope.UNIT,
        before=70.0,
        after=100.0,
        requested_delta=50.0,
        applied_delta=30.0,
        cap=100.0,
        unit_id="unit-a",
    )
    for field in ("before", "after", "requested_delta", "applied_delta", "cap"):
        candidate = dict(kwargs)
        candidate[field] = bad
        with pytest.raises((TypeError, ValueError)):
            RuntimeResourceChangeObservation(**candidate)


def test_inconsistent_applied_delta_is_rejected():
    with pytest.raises(ValueError, match="after - before"):
        RuntimeResourceChangeObservation(
            RuntimeResourceKind.ENERGY,
            RuntimeResourceScope.UNIT,
            10.0,
            20.0,
            15.0,
            15.0,
            100.0,
            "unit-a",
        )


@pytest.mark.parametrize(
    ("scope", "unit_id"),
    [
        (RuntimeResourceScope.TEAM, "unit-a"),
        (RuntimeResourceScope.UNIT, None),
        (RuntimeResourceScope.UNIT, ""),
        (RuntimeResourceScope.UNIT, "   "),
    ],
)
def test_energy_requires_unit_scope_and_non_empty_unit_id(scope, unit_id):
    with pytest.raises(ValueError):
        RuntimeResourceChangeObservation(
            RuntimeResourceKind.ENERGY,
            scope,
            10.0,
            20.0,
            10.0,
            10.0,
            100.0,
            unit_id,
        )


def test_skill_points_require_team_scope_no_unit_and_integer_values():
    with pytest.raises(ValueError):
        RuntimeResourceChangeObservation(
            RuntimeResourceKind.SKILL_POINTS,
            RuntimeResourceScope.UNIT,
            1,
            2,
            1,
            1,
            5,
            None,
        )
    with pytest.raises(ValueError):
        RuntimeResourceChangeObservation(
            RuntimeResourceKind.SKILL_POINTS,
            RuntimeResourceScope.TEAM,
            1,
            2,
            1,
            1,
            5,
            "unit-a",
        )
    for field in ("before", "after", "requested_delta", "applied_delta", "cap"):
        values = {
            "before": 1,
            "after": 2,
            "requested_delta": 1,
            "applied_delta": 1,
            "cap": 5,
        }
        values[field] = float(values[field])
        with pytest.raises(TypeError, match="must be an integer"):
            RuntimeResourceChangeObservation(
                RuntimeResourceKind.SKILL_POINTS,
                RuntimeResourceScope.TEAM,
                values["before"],
                values["after"],
                values["requested_delta"],
                values["applied_delta"],
                values["cap"],
                None,
            )


def _round_trip(event_type, observation, target_id):
    event = RuntimeEvent(
        f"resource-{event_type.value.lower()}-0",
        event_type,
        0,
        "action-a",
        None,
        None,
        None,
        None,
        target_id,
        observation.to_payload(),
    )
    document = build_runtime_trace_document(
        [event],
        config=TraceExportConfig(
            "resource-observation-trace",
            TraceSequencePolicy.CONTIGUOUS,
            EmptyTracePolicy.REJECT,
            {"milestone": "ARCH-019"},
        ),
    )
    artifact = build_runtime_trace_artifact(document, pretty=False)
    loaded = load_runtime_trace_bytes(
        artifact.payload_bytes,
        config=RuntimeTraceLoadConfig(
            TraceCanonicalFormPolicy.COMPACT_ONLY,
            TraceDigestPolicy.SKIP,
            None,
            len(artifact.payload_bytes),
        ),
    )
    return artifact, loaded


@pytest.mark.parametrize(
    ("event_type", "observation", "target_id"),
    [
        (RuntimeEventType.ENERGY_CHANGED, _energy_observation(), "unit-a"),
        (RuntimeEventType.SKILL_POINTS_CHANGED, _skill_point_observation(), None),
    ],
)
def test_resource_event_types_round_trip_through_schema_v1_without_numeric_values(
    event_type, observation, target_id
):
    artifact, loaded = _round_trip(event_type, observation, target_id)
    record = loaded.artifact.document.records[0]
    assert loaded.artifact.document.schema_name == "hsr_runtime_trace"
    assert loaded.artifact.document.schema_version == "1.0"
    assert record.event.event_type is event_type
    assert dict(record.event.payload) == observation.to_payload()
    assert dict(record.numeric_values) == {}
    assert record.notes == ()
    assert loaded.artifact.payload_bytes is artifact.payload_bytes
