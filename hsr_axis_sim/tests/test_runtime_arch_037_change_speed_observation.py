from dataclasses import FrozenInstanceError
import hashlib
import inspect
from math import inf, nan
from pathlib import Path

import pytest

from hsr_axis_sim.regression.manifest import load_regression_manifest
from hsr_axis_sim.regression.runner import run_regression
from hsr_axis_sim.runtime_action_captures import (
    SingleActionEventCaptureRequest,
    execute_action_and_capture_pending_events,
)
from hsr_axis_sim.runtime_action_session_regression.manifest import (
    load_runtime_action_session_regression_manifest,
)
from hsr_axis_sim.runtime_action_session_regression.runner import (
    run_runtime_action_session_regression,
)
from hsr_axis_sim.runtime_adapters import (
    AmbiguousLegacyEventPolicy,
    LegacyEventAdapterConfig,
    LegacyEventSchemaError,
    UnknownLegacyEventPolicy,
    adapt_legacy_event,
)
from hsr_axis_sim.runtime_capture_cursors import PendingEventCaptureCursor
from hsr_axis_sim.runtime_contracts import RuntimeEventType, RuntimeSpeedChangeObservation
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
from hsr_axis_sim.sim.timeline import Timeline
from hsr_axis_sim.sim.unit import Unit


ROOT = Path(__file__).parents[2]
LEGACY_MANIFEST_PATH = ROOT / "hsr_axis_sim" / "data" / "regression_manifest.json"
RUNTIME_MANIFEST_PATH = (
    ROOT / "hsr_axis_sim" / "data" / "runtime_action_session_regression_manifest.json"
)
FIXTURE_DIR = ROOT / "hsr_axis_sim" / "data" / "runtime_golden_fixtures"
FIXTURES = (
    ("arch_017_reviewed_action_session_expected.json", 3013, "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66"),
    ("arch_021_reviewed_clamped_energy_expected.json", 2759, "4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605"),
    ("arch_023_reviewed_clamped_skill_point_expected.json", 2744, "fc359b367c2922ed39e059f89ad16845ba215508292cfa43ca2ab6031c4c9ba9"),
    ("arch_025_reviewed_energy_consume_expected.json", 2750, "7d61528687a5a2f499249e0f914f6f2f50975c7c153165eddd5e116f3ed19a75"),
    ("arch_027_reviewed_skill_point_consume_expected.json", 2796, "d0dcf128f3a28f691324f4e9295b7bcd66460598186f6059d4619f55e8ae39ec"),
    ("arch_032_reviewed_action_advance_expected.json", 2818, "ab73c224d06690b379d398a5bc2c4b38a1ed654dfd86866d564417432c29d3ce"),
    ("arch_035_reviewed_action_delay_expected.json", 2728, "9efbb65defb5eacc12150d31d0530d9a94b43a42e2303ebca643911f98094c4d"),
)


def _adapter_config() -> LegacyEventAdapterConfig:
    return LegacyEventAdapterConfig(
        "speed-observation-stream",
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
                "speed-observation-trace",
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"source": "arch-037"},
            ),
            False,
        ),
    )


def _speed_event_data(**overrides):
    data = {
        "actor_id": "actor",
        "action_id": "change-speed",
        "target_id": "target",
        "before_speed": 100,
        "after_speed": 200,
        "before_av": 80,
        "after_av": 40.0,
    }
    data.update(overrides)
    return data


def test_speed_change_observation_is_frozen_strict_and_serializes_exact_payload():
    observation = RuntimeSpeedChangeObservation(
        target_id="target",
        before_speed=100,
        after_speed=200,
        before_av=80,
        after_av=40.0,
    )
    assert observation.to_payload() == {
        "target_id": "target",
        "before_speed": 100,
        "after_speed": 200,
        "before_av": 80,
        "after_av": 40.0,
    }
    with pytest.raises(FrozenInstanceError):
        observation.after_speed = 150

    negative_av = RuntimeSpeedChangeObservation(
        target_id="target",
        before_speed=100,
        after_speed=200,
        before_av=-20,
        after_av=-10.0,
    )
    assert negative_av.after_av == -10.0


@pytest.mark.parametrize(
    "kwargs, error_type",
    [
        ({"target_id": ""}, ValueError),
        ({"before_speed": True}, TypeError),
        ({"after_speed": 0}, ValueError),
        ({"after_speed": -1}, ValueError),
        ({"before_speed": inf}, ValueError),
        ({"after_speed": nan}, ValueError),
        ({"before_av": nan}, ValueError),
        ({"after_av": 41.0}, ValueError),
    ],
)
def test_speed_change_observation_rejects_malformed_contract(kwargs, error_type):
    values = {
        "target_id": "target",
        "before_speed": 100,
        "after_speed": 200,
        "before_av": 80,
        "after_av": 40.0,
    }
    values.update(kwargs)
    with pytest.raises(error_type):
        RuntimeSpeedChangeObservation(**values)


def test_legacy_speed_changed_maps_to_typed_runtime_event_and_payload():
    data = _speed_event_data()
    result = adapt_legacy_event(
        Event("speed_changed", data), sequence=7, config=_adapter_config()
    )

    assert result.event_type is RuntimeEventType.SPEED_CHANGED
    assert result.action_id == "change-speed"
    assert result.actor_id == "actor"
    assert result.target_id == "target"
    assert dict(result.payload["legacy_data"]) == data
    assert dict(result.payload["speed_change"]) == {
        "target_id": "target",
        "before_speed": 100,
        "after_speed": 200,
        "before_av": 80,
        "after_av": 40.0,
    }
    assert result.payload["adapter"]["mapping_status"] == "BOUND"
    assert result.payload["adapter"]["mechanic_id"] == "LEGACY_EVENT.SPEED_CHANGED"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: data.pop("after_av"),
        lambda data: data.__setitem__("after_av", 41),
        lambda data: data.__setitem__("after_speed", 0),
        lambda data: data.__setitem__("target_id", ""),
        lambda data: data.__setitem__("before_speed", inf),
    ],
)
def test_malformed_speed_changed_is_rejected_not_degraded(mutation):
    data = _speed_event_data()
    mutation(data)
    with pytest.raises(LegacyEventSchemaError):
        adapt_legacy_event(
            Event("speed_changed", data), sequence=0, config=_adapter_config()
        )


def test_production_speed_up_preserves_formula_and_emits_exact_event():
    unit = Unit("actor", "Actor", "ally", 100, current_av=80)
    state = BattleState([unit])
    action = Action(
        "change-speed",
        "Change Speed",
        "actor",
        effects=[ChangeSpeed(new_speed=200)],
        ends_turn=False,
    )

    action.execute(state)

    assert unit.speed == 200
    assert unit.current_av == 40.0
    assert [event.type for event in state.pending_events] == [
        "action_started",
        "speed_changed",
        "action_finished",
    ]
    assert state.pending_events[1].data == {
        "actor_id": "actor",
        "action_id": "change-speed",
        "target_id": "actor",
        "before_speed": 100,
        "after_speed": 200,
        "before_av": 80,
        "after_av": 40.0,
    }


def test_production_slow_down_preserves_existing_formula():
    unit = Unit("actor", "Actor", "ally", 200, current_av=40)
    state = BattleState([unit])

    Action(
        "slow",
        "Slow",
        "actor",
        effects=[ChangeSpeed(new_speed=100)],
        ends_turn=False,
    ).execute(state)

    assert unit.speed == 100
    assert unit.current_av == 80.0
    assert state.pending_events[1].data["before_speed"] == 200
    assert state.pending_events[1].data["after_speed"] == 100
    assert state.pending_events[1].data["before_av"] == 40
    assert state.pending_events[1].data["after_av"] == 80.0


def test_production_negative_av_is_rescaled_without_new_floor():
    unit = Unit("actor", "Actor", "ally", 100, current_av=-20)
    state = BattleState([unit])

    Action(
        "change-speed",
        "Change Speed",
        "actor",
        effects=[ChangeSpeed(new_speed=200)],
        ends_turn=False,
    ).execute(state)

    assert unit.current_av == -10.0
    assert state.pending_events[1].data["after_av"] == -10.0


@pytest.mark.parametrize("invalid", [0, -1, -100.0])
def test_nonpositive_new_speed_keeps_existing_error_and_emits_no_speed_observation(invalid):
    unit = Unit("actor", "Actor", "ally", 100, current_av=80)
    state = BattleState([unit])
    action = Action(
        "change-speed",
        "Change Speed",
        "actor",
        effects=[ChangeSpeed(new_speed=invalid)],
        ends_turn=False,
    )

    with pytest.raises(ValueError, match="New speed must be greater than zero"):
        action.execute(state)

    assert unit.speed == 100
    assert unit.current_av == 80
    assert [event.type for event in state.pending_events] == ["action_started"]


class ObserveChangedSpeedAndAv(Effect):
    def apply(self, state, action, turn_context):
        target = state.get_unit(action.event_data["target_id"])
        state.logs.append(f"observed-speed-av:{target.speed}:{target.current_av}")


def test_speed_changed_trigger_dispatch_observes_both_post_mutation_values():
    unit = Unit("actor", "Actor", "ally", 100, current_av=80)
    state = BattleState(
        [unit],
        triggers=[
            Trigger(
                id="observe-speed-change",
                owner_id="actor",
                event_type="speed_changed",
                condition={"type": "always"},
                effects=[ObserveChangedSpeedAndAv()],
            )
        ],
    )

    Action(
        "change-speed",
        "Change Speed",
        "actor",
        effects=[ChangeSpeed(new_speed=200)],
        ends_turn=False,
    ).execute(state)

    assert state.logs == [
        "trigger:observe-speed-change",
        "observed-speed-av:200:40.0",
    ]


def test_arch_012_capture_contains_exact_typed_three_record_speed_trace():
    unit = Unit("actor", "Actor", "ally", 100, current_av=80)
    state = BattleState([unit])
    action = Action(
        "change-speed",
        "Change Speed",
        "actor",
        effects=[ChangeSpeed(new_speed=200)],
        ends_turn=False,
    )

    result = execute_action_and_capture_pending_events(
        state, action, request=_capture_request()
    )

    records = result.capture_result.capture_result.bridge_result.artifact.document.records
    assert [record.sequence for record in records] == [0, 1, 2]
    assert [record.event.event_type for record in records] == [
        RuntimeEventType.ACTION_START,
        RuntimeEventType.SPEED_CHANGED,
        RuntimeEventType.ACTION_END,
    ]
    speed = records[1].event
    assert speed.action_id == "change-speed"
    assert speed.actor_id == "actor"
    assert speed.target_id == "actor"
    assert dict(speed.payload["speed_change"]) == {
        "target_id": "actor",
        "before_speed": 100,
        "after_speed": 200,
        "before_av": 80,
        "after_av": 40.0,
    }
    assert records[1].numeric_values == {}
    assert result.next_cursor == PendingEventCaptureCursor(3, 3)


def test_arch_037_scope_preserves_other_axis_effect_observations_and_exclusions():
    assert "action_advanced" in inspect.getsource(AdvanceAction)
    assert "action_delayed" in inspect.getsource(DelayAction)

    immediate_source = inspect.getsource(ImmediateAction)
    assert "speed_changed" not in immediate_source
    assert "action_immediate" in immediate_source
    assert "emit_event" in immediate_source

    extra_turn_source = inspect.getsource(GrantExtraTurn)
    assert "speed_changed" not in extra_turn_source
    assert "action_immediate" not in extra_turn_source
    assert "emit_event" not in extra_turn_source


def test_all_seven_reviewed_fixture_byte_identities_remain_exact():
    for filename, size, digest in FIXTURES:
        payload = (FIXTURE_DIR / filename).read_bytes()
        assert len(payload) == size
        assert hashlib.sha256(payload).hexdigest() == digest


def test_existing_regression_lanes_remain_accepted():
    legacy = load_regression_manifest(LEGACY_MANIFEST_PATH)
    complete = run_regression(manifest=legacy)
    trace = run_regression(manifest=legacy, only="trace_evidence")
    runtime = run_runtime_action_session_regression(
        load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    )

    assert complete.passed is True
    assert complete.total == 20
    assert complete.passed_count == 20
    assert trace.passed is True
    assert trace.total == 2
    assert trace.passed_count == 2
    assert runtime.passed is True
    assert runtime.total >= 7
    assert runtime.passed_count == runtime.total


def test_production_extra_turn_lifo_compatibility_is_unchanged():
    state = BattleState([])
    state.extra_turn_stack.extend(["first", "second", "third"])
    assert state.extra_turn_stack.pop() == "third"
    assert state.extra_turn_stack.pop() == "second"
    assert state.extra_turn_stack.pop() == "first"