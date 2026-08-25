from dataclasses import dataclass

import pytest

from hsr_axis_sim.runtime_action_captures import (
    SingleActionEventCaptureRequest,
    execute_action_and_capture_pending_events,
)
from hsr_axis_sim.runtime_adapters import (
    AmbiguousLegacyEventPolicy,
    LegacyEventAdapterConfig,
    LegacyEventSchemaError,
    UnknownLegacyEventPolicy,
    adapt_legacy_event,
)
from hsr_axis_sim.runtime_capture_cursors import PendingEventCaptureCursor
from hsr_axis_sim.runtime_contracts import RuntimeEventType
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
)
from hsr_axis_sim.runtime_trace_bridges import LegacyEventTraceBridgeConfig
from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.effects import (
    ConsumeEnergy,
    ConsumeSkillPoint,
    Effect,
    GainEnergy,
    GainSkillPoint,
)
from hsr_axis_sim.sim.events import Event, Trigger
from hsr_axis_sim.sim.state import BattleState
from hsr_axis_sim.sim.turn_context import TurnContext
from hsr_axis_sim.sim.unit import Unit


def _unit(unit_id: str, *, energy: float = 0, max_energy: float = 100) -> Unit:
    return Unit(
        id=unit_id,
        name=unit_id,
        team="ally",
        base_speed=100,
        energy=energy,
        max_energy=max_energy,
    )


def _action(effect: Effect, *, action_id: str = "resource-action") -> Action:
    return Action(
        action_id,
        action_id,
        "actor",
        effects=[effect],
        ends_turn=False,
    )


def _resource_events(state: BattleState, event_type: str):
    return [event for event in state.pending_events if event.type == event_type]


def _adapter_config() -> LegacyEventAdapterConfig:
    return LegacyEventAdapterConfig(
        "resource-stream",
        UnknownLegacyEventPolicy.REJECT,
        AmbiguousLegacyEventPolicy.REJECT,
    )


def _bridge_config() -> LegacyEventTraceBridgeConfig:
    return LegacyEventTraceBridgeConfig(
        _adapter_config(),
        0,
        TraceExportConfig(
            "resource-capture-trace",
            TraceSequencePolicy.CONTIGUOUS,
            EmptyTracePolicy.REJECT,
            {"source": "arch-020-resource-capture"},
        ),
        False,
    )


def test_gain_energy_emits_exact_unclamped_and_clamped_observations():
    unit = _unit("target", energy=10, max_energy=100)
    state = BattleState([unit])
    _action(GainEnergy(target_ids=["target"], amount=25)).execute(state)

    assert unit.energy == 35
    event = _resource_events(state, "energy_changed")[0]
    assert event.data == {
        "actor_id": "actor",
        "action_id": "resource-action",
        "resource_kind": "ENERGY",
        "scope": "UNIT",
        "before": 10,
        "after": 35,
        "requested_delta": 25,
        "applied_delta": 25,
        "cap": 100,
        "unit_id": "target",
    }

    unit = _unit("target", energy=90, max_energy=100)
    state = BattleState([unit])
    _action(GainEnergy(target_ids=["target"], amount=25)).execute(state)
    event = _resource_events(state, "energy_changed")[0]
    assert unit.energy == 100
    assert event.data["requested_delta"] == 25
    assert event.data["applied_delta"] == 10
    assert event.data["before"] == 90
    assert event.data["after"] == 100


def test_consume_energy_success_and_failure_preserve_existing_mutation_rules():
    unit = _unit("target", energy=50, max_energy=100)
    state = BattleState([unit])
    _action(ConsumeEnergy(target_ids=["target"], amount=20)).execute(state)

    assert unit.energy == 30
    event = _resource_events(state, "energy_changed")[0]
    assert event.data["requested_delta"] == -20
    assert event.data["applied_delta"] == -20
    assert event.data["before"] == 50
    assert event.data["after"] == 30

    unit = _unit("target", energy=10, max_energy=100)
    state = BattleState([unit])
    with pytest.raises(ValueError, match="insufficient energy"):
        _action(ConsumeEnergy(target_ids=["target"], amount=20)).execute(state)

    assert unit.energy == 10
    assert _resource_events(state, "energy_changed") == []
    assert [event.type for event in state.pending_events] == ["action_started"]


def test_gain_skill_point_emits_exact_unclamped_and_clamped_observations():
    state = BattleState([], skill_points=2, max_skill_points=5)
    _action(GainSkillPoint(amount=2)).execute(state)

    assert state.skill_points == 4
    event = _resource_events(state, "skill_points_changed")[0]
    assert event.data == {
        "actor_id": "actor",
        "action_id": "resource-action",
        "resource_kind": "SKILL_POINTS",
        "scope": "TEAM",
        "before": 2,
        "after": 4,
        "requested_delta": 2,
        "applied_delta": 2,
        "cap": 5,
        "unit_id": None,
    }

    state = BattleState([], skill_points=4, max_skill_points=5)
    _action(GainSkillPoint(amount=3)).execute(state)
    event = _resource_events(state, "skill_points_changed")[0]
    assert state.skill_points == 5
    assert event.data["requested_delta"] == 3
    assert event.data["applied_delta"] == 1


def test_consume_skill_point_success_and_failure_preserve_existing_mutation_rules():
    state = BattleState([], skill_points=3, max_skill_points=5)
    _action(ConsumeSkillPoint(amount=2)).execute(state)

    assert state.skill_points == 1
    event = _resource_events(state, "skill_points_changed")[0]
    assert event.data["requested_delta"] == -2
    assert event.data["applied_delta"] == -2
    assert event.data["before"] == 3
    assert event.data["after"] == 1

    state = BattleState([], skill_points=1, max_skill_points=5)
    with pytest.raises(ValueError, match="Insufficient skill points"):
        _action(ConsumeSkillPoint(amount=2)).execute(state)

    assert state.skill_points == 1
    assert _resource_events(state, "skill_points_changed") == []
    assert [event.type for event in state.pending_events] == ["action_started"]


def test_multi_target_energy_emits_one_event_per_target_in_declared_target_order():
    first = _unit("first", energy=1)
    second = _unit("second", energy=2)
    state = BattleState([first, second])

    _action(GainEnergy(target_ids=["second", "first"], amount=5)).execute(state)

    events = _resource_events(state, "energy_changed")
    assert [event.data["unit_id"] for event in events] == ["second", "first"]
    assert [event.data["before"] for event in events] == [2, 1]
    assert [event.data["after"] for event in events] == [7, 6]


@dataclass
class RecordResourceTrigger(Effect):
    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        state.logs.append(
            f"resource_trigger:{action.event_data['unit_id']}:{action.event_data['after']}"
        )


def test_resource_event_uses_normal_trigger_visible_dispatch_path():
    unit = _unit("target", energy=10)
    state = BattleState(
        [unit],
        triggers=[
            Trigger(
                id="resource-trigger",
                owner_id="actor",
                event_type="energy_changed",
                condition={"type": "always"},
                effects=[RecordResourceTrigger()],
            )
        ],
    )

    _action(GainEnergy(target_ids=["target"], amount=5)).execute(state)

    assert "trigger:resource-trigger" in state.logs
    assert "resource_trigger:target:15" in state.logs


def test_adapter_binds_energy_resource_event_with_exact_structured_projection():
    data = {
        "actor_id": "actor",
        "action_id": "energy-action",
        "resource_kind": "ENERGY",
        "scope": "UNIT",
        "before": 90,
        "after": 100,
        "requested_delta": 25,
        "applied_delta": 10,
        "cap": 100,
        "unit_id": "target",
    }
    event = Event("energy_changed", data)
    result = adapt_legacy_event(event, sequence=3, config=_adapter_config())

    assert result.event_type is RuntimeEventType.ENERGY_CHANGED
    assert result.action_id == "energy-action"
    assert result.actor_id == "actor"
    assert result.target_id == "target"
    assert result.payload["adapter"]["mapping_status"] == "BOUND"
    assert result.payload["adapter"]["semantic_gap_ids"] == ()
    assert dict(result.payload["resource_change"]) == {
        "resource_kind": "ENERGY",
        "scope": "UNIT",
        "before": 90,
        "after": 100,
        "requested_delta": 25,
        "applied_delta": 10,
        "cap": 100,
        "unit_id": "target",
    }
    assert dict(result.payload["legacy_data"]) == data

    data["after"] = 999
    assert result.payload["resource_change"]["after"] == 100
    assert result.payload["legacy_data"]["after"] == 100


def test_adapter_binds_skill_point_resource_event_without_target_id():
    data = {
        "actor_id": "actor",
        "action_id": "sp-action",
        "resource_kind": "SKILL_POINTS",
        "scope": "TEAM",
        "before": 3,
        "after": 1,
        "requested_delta": -2,
        "applied_delta": -2,
        "cap": 5,
        "unit_id": None,
    }
    result = adapt_legacy_event(
        Event("skill_points_changed", data),
        sequence=4,
        config=_adapter_config(),
    )

    assert result.event_type is RuntimeEventType.SKILL_POINTS_CHANGED
    assert result.action_id == "sp-action"
    assert result.actor_id == "actor"
    assert result.target_id is None
    assert dict(result.payload["resource_change"]) == {
        "resource_kind": "SKILL_POINTS",
        "scope": "TEAM",
        "before": 3,
        "after": 1,
        "requested_delta": -2,
        "applied_delta": -2,
        "cap": 5,
        "unit_id": None,
    }


@pytest.mark.parametrize(
    "event",
    [
        Event(
            "energy_changed",
            {
                "actor_id": "actor",
                "action_id": "a",
                "resource_kind": "ENERGY",
                "scope": "UNIT",
                "before": 1,
                "after": 2,
                "requested_delta": 1,
                "applied_delta": 1,
                "unit_id": "u",
            },
        ),
        Event(
            "energy_changed",
            {
                "actor_id": "actor",
                "action_id": "a",
                "resource_kind": "SKILL_POINTS",
                "scope": "TEAM",
                "before": 1,
                "after": 2,
                "requested_delta": 1,
                "applied_delta": 1,
                "cap": 5,
                "unit_id": None,
            },
        ),
        Event(
            "skill_points_changed",
            {
                "actor_id": "actor",
                "action_id": "a",
                "resource_kind": "SKILL_POINTS",
                "scope": "UNIT",
                "before": 1,
                "after": 2,
                "requested_delta": 1,
                "applied_delta": 1,
                "cap": 5,
                "unit_id": None,
            },
        ),
    ],
)
def test_malformed_resource_legacy_data_is_rejected_without_repair(event):
    with pytest.raises(LegacyEventSchemaError):
        adapt_legacy_event(event, sequence=0, config=_adapter_config())


def test_arch_012_capture_observes_resource_event_between_action_boundaries():
    unit = _unit("target", energy=10)
    state = BattleState([unit])
    action = _action(GainEnergy(target_ids=["target"], amount=5))
    request = SingleActionEventCaptureRequest(
        PendingEventCaptureCursor(0, 0),
        _bridge_config(),
    )

    result = execute_action_and_capture_pending_events(
        state,
        action,
        request=request,
    )

    records = result.capture_result.capture_result.bridge_result.artifact.document.records
    assert [record.event.event_type for record in records] == [
        RuntimeEventType.ACTION_START,
        RuntimeEventType.ENERGY_CHANGED,
        RuntimeEventType.ACTION_END,
    ]
    assert all(dict(record.numeric_values) == {} for record in records)
    assert dict(records[1].event.payload["resource_change"]) == {
        "resource_kind": "ENERGY",
        "scope": "UNIT",
        "before": 10,
        "after": 15,
        "requested_delta": 5,
        "applied_delta": 5,
        "cap": 100,
        "unit_id": "target",
    }
