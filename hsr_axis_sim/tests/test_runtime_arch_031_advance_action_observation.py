from dataclasses import FrozenInstanceError
import inspect
from math import inf, nan

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
from hsr_axis_sim.runtime_contracts import (
    RuntimeActionAdvanceObservation,
    RuntimeEventType,
)
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
)
from hsr_axis_sim.runtime_trace_bridges import LegacyEventTraceBridgeConfig
from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.effects import (
    AdvanceAction,
    ChangeSpeed,
    DelayAction,
    Effect,
    GrantExtraTurn,
    ImmediateAction,
)
from hsr_axis_sim.sim.events import Event, Trigger
from hsr_axis_sim.sim.state import BattleState
from hsr_axis_sim.sim.unit import Unit


def _adapter_config() -> LegacyEventAdapterConfig:
    return LegacyEventAdapterConfig(
        "advance-observation-stream",
        UnknownLegacyEventPolicy.REJECT,
        AmbiguousLegacyEventPolicy.REJECT,
    )


def _capture_request() -> SingleActionEventCaptureRequest:
    return SingleActionEventCaptureRequest(
        PendingEventCaptureCursor(0, 0),
        LegacyEventTraceBridgeConfig(
            _adapter_config(),
            0,
            TraceExportConfig(
                "advance-observation-trace",
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"source": "arch-031"},
            ),
            False,
        ),
    )


def _advance_event_data(**overrides):
    data = {
        "actor_id": "actor",
        "action_id": "advance",
        "target_id": "target",
        "before_av": 80.0,
        "after_av": 30.0,
        "base_av": 100.0,
        "requested_percent": 0.5,
        "requested_delta_av": -50.0,
        "applied_delta_av": -50.0,
        "clamped_to_zero": False,
    }
    data.update(overrides)
    return data


def test_action_advance_observation_is_frozen_strict_and_serializes_exact_payload():
    observation = RuntimeActionAdvanceObservation(
        target_id="target",
        before_av=80.0,
        after_av=30.0,
        base_av=100.0,
        requested_percent=0.5,
        requested_delta_av=-50.0,
        applied_delta_av=-50.0,
        clamped_to_zero=False,
    )

    assert observation.to_payload() == {
        "target_id": "target",
        "before_av": 80.0,
        "after_av": 30.0,
        "base_av": 100.0,
        "requested_percent": 0.5,
        "requested_delta_av": -50.0,
        "applied_delta_av": -50.0,
        "clamped_to_zero": False,
    }
    with pytest.raises(FrozenInstanceError):
        observation.after_av = 99

    reverse = RuntimeActionAdvanceObservation(
        target_id="target",
        before_av=80.0,
        after_av=90.0,
        base_av=100.0,
        requested_percent=-0.1,
        requested_delta_av=10.0,
        applied_delta_av=10.0,
        clamped_to_zero=False,
    )
    assert reverse.after_av == 90.0


@pytest.mark.parametrize(
    "kwargs, error_type",
    [
        ({"target_id": ""}, ValueError),
        ({"before_av": True}, TypeError),
        ({"after_av": nan}, ValueError),
        ({"base_av": 0}, ValueError),
        ({"base_av": inf}, ValueError),
        ({"requested_percent": True}, TypeError),
        ({"requested_delta_av": -49.0}, ValueError),
        ({"applied_delta_av": -49.0}, ValueError),
        ({"after_av": 31.0}, ValueError),
        ({"clamped_to_zero": 0}, TypeError),
        ({"clamped_to_zero": True}, ValueError),
    ],
)
def test_action_advance_observation_rejects_malformed_contract(kwargs, error_type):
    values = {
        "target_id": "target",
        "before_av": 80.0,
        "after_av": 30.0,
        "base_av": 100.0,
        "requested_percent": 0.5,
        "requested_delta_av": -50.0,
        "applied_delta_av": -50.0,
        "clamped_to_zero": False,
    }
    values.update(kwargs)
    with pytest.raises(error_type):
        RuntimeActionAdvanceObservation(**values)


def test_clamped_observation_requires_true_only_when_unclamped_result_is_below_zero():
    observation = RuntimeActionAdvanceObservation(
        target_id="target",
        before_av=40.0,
        after_av=0,
        base_av=100.0,
        requested_percent=1.0,
        requested_delta_av=-100.0,
        applied_delta_av=-40.0,
        clamped_to_zero=True,
    )
    assert observation.clamped_to_zero is True

    exact_zero = RuntimeActionAdvanceObservation(
        target_id="target",
        before_av=100.0,
        after_av=0,
        base_av=100.0,
        requested_percent=1.0,
        requested_delta_av=-100.0,
        applied_delta_av=-100.0,
        clamped_to_zero=False,
    )
    assert exact_zero.clamped_to_zero is False


def test_legacy_action_advanced_maps_to_typed_runtime_event_and_payload():
    data = _advance_event_data()
    result = adapt_legacy_event(
        Event("action_advanced", data),
        sequence=7,
        config=_adapter_config(),
    )

    assert result.event_type is RuntimeEventType.ACTION_VALUE_ADVANCED
    assert result.action_id == "advance"
    assert result.actor_id == "actor"
    assert result.target_id == "target"
    assert dict(result.payload["legacy_data"]) == data
    assert dict(result.payload["action_advance"]) == {
        "target_id": "target",
        "before_av": 80.0,
        "after_av": 30.0,
        "base_av": 100.0,
        "requested_percent": 0.5,
        "requested_delta_av": -50.0,
        "applied_delta_av": -50.0,
        "clamped_to_zero": False,
    }
    assert result.payload["adapter"]["mapping_status"] == "BOUND"
    assert result.payload["adapter"]["mechanic_id"] == "LEGACY_EVENT.ACTION_ADVANCED"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: data.pop("after_av"),
        lambda data: data.__setitem__("requested_delta_av", -49.0),
        lambda data: data.__setitem__("clamped_to_zero", True),
        lambda data: data.__setitem__("target_id", ""),
    ],
)
def test_malformed_action_advanced_is_rejected_not_degraded(mutation):
    data = _advance_event_data()
    mutation(data)
    with pytest.raises(LegacyEventSchemaError):
        adapt_legacy_event(
            Event("action_advanced", data),
            sequence=0,
            config=_adapter_config(),
        )


def test_production_nonclamped_self_advance_preserves_formula_and_emits_exact_event():
    unit = Unit("actor", "Actor", "ally", 100, current_av=80)
    state = BattleState([unit])
    action = Action(
        "advance",
        "Advance",
        "actor",
        effects=[AdvanceAction(percent=0.5)],
        ends_turn=False,
    )

    action.execute(state)

    assert unit.current_av == pytest.approx(30, abs=1e-6)
    assert [event.type for event in state.pending_events] == [
        "action_started",
        "action_advanced",
        "action_finished",
    ]
    assert state.pending_events[1].data == {
        "actor_id": "actor",
        "action_id": "advance",
        "target_id": "actor",
        "before_av": 80,
        "after_av": 30.0,
        "base_av": 100.0,
        "requested_percent": 0.5,
        "requested_delta_av": -50.0,
        "applied_delta_av": -50.0,
        "clamped_to_zero": False,
    }


def test_production_clamped_advance_reports_requested_vs_applied_delta():
    unit = Unit("actor", "Actor", "ally", 100, current_av=40)
    state = BattleState([unit])
    Action(
        "advance",
        "Advance",
        "actor",
        effects=[AdvanceAction(percent=1.0)],
        ends_turn=False,
    ).execute(state)

    assert unit.current_av == 0
    data = state.pending_events[1].data
    assert data["before_av"] == 40
    assert data["after_av"] == 0
    assert data["base_av"] == 100.0
    assert data["requested_delta_av"] == -100.0
    assert data["applied_delta_av"] == -40
    assert data["clamped_to_zero"] is True


class ObserveAdvancedTargetAv(Effect):
    def apply(self, state, action, turn_context):
        target = state.get_unit(action.event_data["target_id"])
        state.logs.append(f"observed-av:{target.current_av}")


def test_action_advanced_trigger_dispatch_observes_post_mutation_av():
    unit = Unit("actor", "Actor", "ally", 100, current_av=80)
    state = BattleState(
        [unit],
        triggers=[
            Trigger(
                id="observe-advance",
                owner_id="actor",
                event_type="action_advanced",
                condition={"type": "always"},
                effects=[ObserveAdvancedTargetAv()],
            )
        ],
    )

    Action(
        "advance",
        "Advance",
        "actor",
        effects=[AdvanceAction(percent=0.5)],
        ends_turn=False,
    ).execute(state)

    assert unit.current_av == 30.0
    assert state.logs == ["trigger:observe-advance", "observed-av:30.0"]
    assert [event.type for event in state.pending_events] == [
        "action_started",
        "action_advanced",
        "action_finished",
    ]


def test_arch_012_capture_contains_exact_typed_three_record_advance_trace():
    unit = Unit("actor", "Actor", "ally", 100, current_av=80)
    state = BattleState([unit])
    action = Action(
        "advance",
        "Advance",
        "actor",
        effects=[AdvanceAction(percent=0.5)],
        ends_turn=False,
    )

    result = execute_action_and_capture_pending_events(
        state,
        action,
        request=_capture_request(),
    )

    records = result.capture_result.capture_result.bridge_result.artifact.document.records
    assert [record.sequence for record in records] == [0, 1, 2]
    assert [record.event.event_type for record in records] == [
        RuntimeEventType.ACTION_START,
        RuntimeEventType.ACTION_VALUE_ADVANCED,
        RuntimeEventType.ACTION_END,
    ]
    advance = records[1].event
    assert advance.action_id == "advance"
    assert advance.actor_id == "actor"
    assert advance.target_id == "actor"
    assert dict(advance.payload["action_advance"]) == {
        "target_id": "actor",
        "before_av": 80,
        "after_av": 30.0,
        "base_av": 100.0,
        "requested_percent": 0.5,
        "requested_delta_av": -50.0,
        "applied_delta_av": -50.0,
        "clamped_to_zero": False,
    }
    assert records[1].numeric_values == {}
    assert result.next_cursor == PendingEventCaptureCursor(3, 3)


def test_arch_031_scope_preserves_later_authorized_axis_effects():
    delay_source = inspect.getsource(DelayAction)
    assert "action_advanced" not in delay_source
    assert "action_delayed" in delay_source

    speed_source = inspect.getsource(ChangeSpeed)
    assert "action_advanced" not in speed_source
    assert "action_delayed" not in speed_source
    assert "speed_changed" in speed_source
    assert "emit_event" in speed_source

    immediate_source = inspect.getsource(ImmediateAction)
    assert "action_advanced" not in immediate_source
    assert "action_delayed" not in immediate_source
    assert "speed_changed" not in immediate_source
    assert "action_immediate" in immediate_source
    assert "emit_event" in immediate_source

    extra_turn_source = inspect.getsource(GrantExtraTurn)
    assert "action_advanced" not in extra_turn_source
    assert "action_delayed" not in extra_turn_source
    assert "speed_changed" not in extra_turn_source
    assert "action_immediate" not in extra_turn_source
    assert "extra_turn_queued" in extra_turn_source
    assert "emit_event" in extra_turn_source


def test_production_extra_turn_lifo_compatibility_is_unchanged():
    state = BattleState([])
    state.extra_turn_stack.extend(["first", "second", "third"])
    assert state.extra_turn_stack.pop() == "third"
    assert state.extra_turn_stack.pop() == "second"
    assert state.extra_turn_stack.pop() == "first"