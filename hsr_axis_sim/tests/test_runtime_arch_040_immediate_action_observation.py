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
from hsr_axis_sim.runtime_contracts import (
    RuntimeEventType,
    RuntimeImmediateActionObservation,
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
    ("arch_038_reviewed_change_speed_expected.json", 2604, "c23b34e0afffdfe4bee53d028e5ff21d946623300b169ba57e5ddfb69478df2a"),
)


def _adapter_config() -> LegacyEventAdapterConfig:
    return LegacyEventAdapterConfig(
        "immediate-observation-stream",
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
                "immediate-observation-trace",
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"source": "arch-040"},
            ),
            False,
        ),
    )


def _immediate_event_data(**overrides):
    data = {
        "actor_id": "actor",
        "action_id": "make-immediate",
        "target_id": "target",
        "before_av": 80,
        "after_av": 0,
    }
    data.update(overrides)
    return data


def test_immediate_action_observation_is_frozen_strict_and_exact():
    observation = RuntimeImmediateActionObservation(
        target_id="target",
        before_av=80,
        after_av=0,
    )
    assert observation.to_payload() == {
        "target_id": "target",
        "before_av": 80,
        "after_av": 0,
    }
    with pytest.raises(FrozenInstanceError):
        observation.after_av = 1

    assert RuntimeImmediateActionObservation(
        target_id="target", before_av=-20, after_av=0
    ).before_av == -20
    assert RuntimeImmediateActionObservation(
        target_id="target", before_av=0, after_av=0
    ).after_av == 0


@pytest.mark.parametrize(
    "kwargs, error_type",
    [
        ({"target_id": ""}, ValueError),
        ({"before_av": True}, TypeError),
        ({"after_av": False}, TypeError),
        ({"before_av": inf}, ValueError),
        ({"before_av": nan}, ValueError),
        ({"after_av": inf}, ValueError),
        ({"after_av": 1}, ValueError),
        ({"after_av": -1}, ValueError),
    ],
)
def test_immediate_action_observation_rejects_malformed_contract(kwargs, error_type):
    values = {"target_id": "target", "before_av": 80, "after_av": 0}
    values.update(kwargs)
    with pytest.raises(error_type):
        RuntimeImmediateActionObservation(**values)


def test_legacy_action_immediate_maps_to_dedicated_runtime_event_and_payload():
    data = _immediate_event_data()
    result = adapt_legacy_event(
        Event("action_immediate", data), sequence=5, config=_adapter_config()
    )

    assert result.event_type is RuntimeEventType.ACTION_VALUE_IMMEDIATE
    assert result.action_id == "make-immediate"
    assert result.actor_id == "actor"
    assert result.target_id == "target"
    assert dict(result.payload["legacy_data"]) == data
    assert dict(result.payload["immediate_action"]) == {
        "target_id": "target",
        "before_av": 80,
        "after_av": 0,
    }
    assert "action_advance" not in result.payload
    assert result.payload["adapter"]["mapping_status"] == "BOUND"
    assert result.payload["adapter"]["mechanic_id"] == "LEGACY_EVENT.ACTION_IMMEDIATE"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: data.pop("after_av"),
        lambda data: data.__setitem__("after_av", 1),
        lambda data: data.__setitem__("before_av", nan),
        lambda data: data.__setitem__("target_id", ""),
    ],
)
def test_malformed_action_immediate_is_rejected_not_degraded(mutation):
    data = _immediate_event_data()
    mutation(data)
    with pytest.raises(LegacyEventSchemaError):
        adapt_legacy_event(
            Event("action_immediate", data), sequence=0, config=_adapter_config()
        )


def test_production_immediate_action_preserves_av_to_zero_and_exact_event_order():
    actor = Unit("actor", "Actor", "ally", 100, current_av=20)
    target = Unit("target", "Target", "ally", 100, current_av=80)
    state = BattleState([actor, target])

    Action(
        "make-immediate",
        "Make Immediate",
        "actor",
        effects=[ImmediateAction(target_ids=["target"])],
        ends_turn=False,
    ).execute(state)

    assert target.current_av == 0
    assert state.extra_turn_stack == []
    assert [event.type for event in state.pending_events] == [
        "action_started",
        "action_immediate",
        "action_finished",
    ]
    assert state.pending_events[1].data == {
        "actor_id": "actor",
        "action_id": "make-immediate",
        "target_id": "target",
        "before_av": 80,
        "after_av": 0,
    }


@pytest.mark.parametrize("before_av", [0, -20])
def test_zero_or_negative_before_av_still_sets_zero_and_emits_observation(before_av):
    actor = Unit("actor", "Actor", "ally", 100, current_av=20)
    target = Unit("target", "Target", "ally", 100, current_av=before_av)
    state = BattleState([actor, target])

    Action(
        "make-immediate",
        "Make Immediate",
        "actor",
        effects=[ImmediateAction(target_ids=["target"])],
        ends_turn=False,
    ).execute(state)

    assert target.current_av == 0
    assert state.pending_events[1].type == "action_immediate"
    assert state.pending_events[1].data["before_av"] == before_av
    assert state.pending_events[1].data["after_av"] == 0


class ObserveImmediateTargetAv(Effect):
    def apply(self, state, action, turn_context):
        target = state.get_unit(action.event_data["target_id"])
        state.logs.append(f"observed-immediate-av:{target.current_av}")


def test_action_immediate_trigger_observes_post_mutation_zero_av():
    actor = Unit("actor", "Actor", "ally", 100, current_av=20)
    target = Unit("target", "Target", "ally", 100, current_av=80)
    state = BattleState(
        [actor, target],
        triggers=[
            Trigger(
                id="observe-immediate",
                owner_id="actor",
                event_type="action_immediate",
                condition={"type": "always"},
                effects=[ObserveImmediateTargetAv()],
            )
        ],
    )

    Action(
        "make-immediate",
        "Make Immediate",
        "actor",
        effects=[ImmediateAction(target_ids=["target"])],
        ends_turn=False,
    ).execute(state)

    assert target.current_av == 0
    assert state.logs == ["trigger:observe-immediate", "observed-immediate-av:0"]


def test_arch_012_capture_contains_exact_typed_three_record_immediate_trace():
    actor = Unit("actor", "Actor", "ally", 100, current_av=20)
    target = Unit("target", "Target", "ally", 100, current_av=80)
    state = BattleState([actor, target])
    action = Action(
        "make-immediate",
        "Make Immediate",
        "actor",
        effects=[ImmediateAction(target_ids=["target"])],
        ends_turn=False,
    )

    result = execute_action_and_capture_pending_events(
        state, action, request=_capture_request()
    )

    records = result.capture_result.capture_result.bridge_result.artifact.document.records
    assert [record.sequence for record in records] == [0, 1, 2]
    assert [record.event.event_type for record in records] == [
        RuntimeEventType.ACTION_START,
        RuntimeEventType.ACTION_VALUE_IMMEDIATE,
        RuntimeEventType.ACTION_END,
    ]
    immediate = records[1].event
    assert immediate.action_id == "make-immediate"
    assert immediate.actor_id == "actor"
    assert immediate.target_id == "target"
    assert dict(immediate.payload["immediate_action"]) == {
        "target_id": "target",
        "before_av": 80,
        "after_av": 0,
    }
    assert records[1].numeric_values == {}
    assert result.next_cursor == PendingEventCaptureCursor(3, 3)


def test_self_target_immediate_action_preserves_actor_target_identity():
    actor = Unit("actor", "Actor", "ally", 100, current_av=80)
    state = BattleState([actor])

    Action(
        "self-immediate",
        "Self Immediate",
        "actor",
        effects=[ImmediateAction(target_ids=["actor"])],
        ends_turn=False,
    ).execute(state)

    assert actor.current_av == 0
    event = state.pending_events[1]
    assert event.type == "action_immediate"
    assert event.data["actor_id"] == "actor"
    assert event.data["target_id"] == "actor"
    assert event.data["before_av"] == 80
    assert event.data["after_av"] == 0


def test_multi_target_immediate_observations_preserve_declared_target_order():
    actor = Unit("actor", "Actor", "ally", 100, current_av=20)
    first = Unit("first", "First", "ally", 100, current_av=70)
    second = Unit("second", "Second", "ally", 100, current_av=40)
    state = BattleState([actor, first, second])

    Action(
        "multi-immediate",
        "Multi Immediate",
        "actor",
        effects=[ImmediateAction(target_ids=["second", "first"])],
        ends_turn=False,
    ).execute(state)

    immediate_events = [
        event for event in state.pending_events if event.type == "action_immediate"
    ]
    assert [event.data["target_id"] for event in immediate_events] == ["second", "first"]
    assert [event.data["before_av"] for event in immediate_events] == [40, 70]
    assert first.current_av == second.current_av == 0


def test_advance_delay_and_change_speed_observations_remain_distinct():
    assert RuntimeEventType.ACTION_VALUE_IMMEDIATE is not RuntimeEventType.ACTION_VALUE_ADVANCED
    assert "action_advanced" in inspect.getsource(AdvanceAction)
    assert "action_delayed" in inspect.getsource(DelayAction)
    assert "speed_changed" in inspect.getsource(ChangeSpeed)
    immediate_source = inspect.getsource(ImmediateAction)
    assert "action_immediate" in immediate_source
    assert "action_advanced" not in immediate_source
    assert "action_delayed" not in immediate_source
    assert "speed_changed" not in immediate_source


def test_grant_extra_turn_remains_separate_unobserved_and_lifo_unchanged():
    source = inspect.getsource(GrantExtraTurn)
    assert "action_immediate" not in source
    assert "emit_event" not in source

    state = BattleState([])
    state.extra_turn_stack.extend(["first", "second", "third"])
    assert state.extra_turn_stack.pop() == "third"
    assert state.extra_turn_stack.pop() == "second"
    assert state.extra_turn_stack.pop() == "first"


def test_all_eight_reviewed_fixture_byte_identities_remain_exact():
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
    assert runtime.total == 8
    assert runtime.passed_count == 8


def test_production_extra_turn_lifo_compatibility_is_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])

    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == [
        "third",
        "second",
        "first",
    ]
