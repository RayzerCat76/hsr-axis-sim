from dataclasses import FrozenInstanceError
import hashlib
import inspect
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
    RuntimeExtraTurnQueuedObservation,
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
    ("arch_041_reviewed_immediate_action_expected.json", 2620, "7fd1594362b5bf9a95eec6f6472b2f17afa9dcfe10196d81ec6c970eab86eea1"),
)


def _adapter_config() -> LegacyEventAdapterConfig:
    return LegacyEventAdapterConfig(
        "extra-turn-observation-stream",
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
                "extra-turn-observation-trace",
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"source": "arch-043"},
            ),
            False,
        ),
    )


def _queued_event_data(**overrides):
    data = {
        "actor_id": "actor",
        "action_id": "grant-extra",
        "target_id": "target",
        "stack_depth_before": 0,
        "stack_depth_after": 1,
    }
    data.update(overrides)
    return data


def test_extra_turn_queue_observation_is_frozen_strict_and_exact():
    observation = RuntimeExtraTurnQueuedObservation(
        target_id="target",
        stack_depth_before=0,
        stack_depth_after=1,
    )
    assert observation.to_payload() == {
        "target_id": "target",
        "stack_depth_before": 0,
        "stack_depth_after": 1,
    }
    with pytest.raises(FrozenInstanceError):
        observation.stack_depth_after = 2


@pytest.mark.parametrize(
    "kwargs, error_type",
    [
        ({"target_id": ""}, ValueError),
        ({"target_id": 1}, ValueError),
        ({"stack_depth_before": True}, TypeError),
        ({"stack_depth_after": False}, TypeError),
        ({"stack_depth_before": 0.0}, TypeError),
        ({"stack_depth_after": 1.0}, TypeError),
        ({"stack_depth_before": "0"}, TypeError),
        ({"stack_depth_before": -1}, ValueError),
        ({"stack_depth_after": -1}, ValueError),
        ({"stack_depth_before": 1, "stack_depth_after": 1}, ValueError),
        ({"stack_depth_before": 1, "stack_depth_after": 3}, ValueError),
    ],
)
def test_extra_turn_queue_observation_rejects_malformed_contract(kwargs, error_type):
    values = {
        "target_id": "target",
        "stack_depth_before": 0,
        "stack_depth_after": 1,
    }
    values.update(kwargs)
    with pytest.raises(error_type):
        RuntimeExtraTurnQueuedObservation(**values)


def test_legacy_extra_turn_queued_maps_to_dedicated_runtime_event_and_payload():
    data = _queued_event_data()
    result = adapt_legacy_event(
        Event("extra_turn_queued", data), sequence=5, config=_adapter_config()
    )

    assert result.event_type is RuntimeEventType.EXTRA_TURN_QUEUED
    assert result.action_id == "grant-extra"
    assert result.actor_id == "actor"
    assert result.target_id == "target"
    assert dict(result.payload["legacy_data"]) == data
    assert dict(result.payload["extra_turn_queue"]) == {
        "target_id": "target",
        "stack_depth_before": 0,
        "stack_depth_after": 1,
    }
    assert result.payload["adapter"]["mapping_status"] == "BOUND"
    assert result.payload["adapter"]["mechanic_id"] == "LEGACY_EVENT.EXTRA_TURN_QUEUED"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: data.pop("stack_depth_after"),
        lambda data: data.__setitem__("stack_depth_before", True),
        lambda data: data.__setitem__("stack_depth_after", 2),
        lambda data: data.__setitem__("target_id", ""),
    ],
)
def test_malformed_extra_turn_queued_is_rejected_not_degraded(mutation):
    data = _queued_event_data()
    mutation(data)
    with pytest.raises(LegacyEventSchemaError):
        adapt_legacy_event(
            Event("extra_turn_queued", data), sequence=0, config=_adapter_config()
        )


def test_production_grant_extra_turn_preserves_append_and_exact_event_order():
    actor = Unit("actor", "Actor", "ally", 100, current_av=20)
    target = Unit("target", "Target", "ally", 100, current_av=80)
    state = BattleState([actor, target])

    Action(
        "grant-extra",
        "Grant Extra",
        "actor",
        effects=[GrantExtraTurn(target_ids=["target"])],
        ends_turn=False,
    ).execute(state)

    assert state.extra_turn_stack == ["target"]
    assert target.current_av == 80
    assert [event.type for event in state.pending_events] == [
        "action_started",
        "extra_turn_queued",
        "action_finished",
    ]
    assert state.pending_events[1].data == {
        "actor_id": "actor",
        "action_id": "grant-extra",
        "target_id": "target",
        "stack_depth_before": 0,
        "stack_depth_after": 1,
    }


class ObserveQueuedStack(Effect):
    def apply(self, state, action, turn_context):
        state.logs.append(
            "observed-extra-stack:"
            f"{list(state.extra_turn_stack)}:"
            f"{action.event_data['stack_depth_after']}"
        )


def test_extra_turn_queued_trigger_observes_post_append_stack():
    actor = Unit("actor", "Actor", "ally", 100, current_av=20)
    target = Unit("target", "Target", "ally", 100, current_av=80)
    state = BattleState(
        [actor, target],
        triggers=[
            Trigger(
                id="observe-extra-turn",
                owner_id="actor",
                event_type="extra_turn_queued",
                condition={"type": "always"},
                effects=[ObserveQueuedStack()],
            )
        ],
    )

    Action(
        "grant-extra",
        "Grant Extra",
        "actor",
        effects=[GrantExtraTurn(target_ids=["target"])],
        ends_turn=False,
    ).execute(state)

    assert state.extra_turn_stack == ["target"]
    assert state.logs == [
        "trigger:observe-extra-turn",
        "observed-extra-stack:['target']:1",
    ]


def test_arch_012_capture_contains_exact_typed_three_record_extra_turn_trace():
    actor = Unit("actor", "Actor", "ally", 100, current_av=20)
    target = Unit("target", "Target", "ally", 100, current_av=80)
    state = BattleState([actor, target])
    action = Action(
        "grant-extra",
        "Grant Extra",
        "actor",
        effects=[GrantExtraTurn(target_ids=["target"])],
        ends_turn=False,
    )

    result = execute_action_and_capture_pending_events(
        state, action, request=_capture_request()
    )

    records = result.capture_result.capture_result.bridge_result.artifact.document.records
    assert [record.sequence for record in records] == [0, 1, 2]
    assert [record.event.event_type for record in records] == [
        RuntimeEventType.ACTION_START,
        RuntimeEventType.EXTRA_TURN_QUEUED,
        RuntimeEventType.ACTION_END,
    ]
    queued = records[1].event
    assert queued.action_id == "grant-extra"
    assert queued.actor_id == "actor"
    assert queued.target_id == "target"
    assert dict(queued.payload["extra_turn_queue"]) == {
        "target_id": "target",
        "stack_depth_before": 0,
        "stack_depth_after": 1,
    }
    assert dict(queued.payload["legacy_data"]) == _queued_event_data()
    assert queued.payload["adapter"]["mechanic_id"] == "LEGACY_EVENT.EXTRA_TURN_QUEUED"
    assert records[1].numeric_values == {}
    assert result.next_cursor == PendingEventCaptureCursor(3, 3)


def test_self_target_extra_turn_preserves_actor_target_identity_and_depth():
    actor = Unit("actor", "Actor", "ally", 100, current_av=80)
    state = BattleState([actor])

    Action(
        "self-extra",
        "Self Extra",
        "actor",
        effects=[GrantExtraTurn(target_ids=["actor"])],
        ends_turn=False,
    ).execute(state)

    assert state.extra_turn_stack == ["actor"]
    event = state.pending_events[1]
    assert event.type == "extra_turn_queued"
    assert event.data == {
        "actor_id": "actor",
        "action_id": "self-extra",
        "target_id": "actor",
        "stack_depth_before": 0,
        "stack_depth_after": 1,
    }


def test_multi_target_queue_events_preserve_append_order_then_resolve_lifo():
    actor = Unit("actor", "Actor", "ally", 100, current_av=90)
    first = Unit("first", "First", "ally", 100, current_av=80)
    second = Unit("second", "Second", "ally", 100, current_av=70)
    state = BattleState([actor, first, second])

    Action(
        "multi-extra",
        "Multi Extra",
        "actor",
        effects=[GrantExtraTurn(target_ids=["first", "second"])],
        ends_turn=False,
    ).execute(state)

    queued = [event for event in state.pending_events if event.type == "extra_turn_queued"]
    assert [event.data["target_id"] for event in queued] == ["first", "second"]
    assert [
        (event.data["stack_depth_before"], event.data["stack_depth_after"])
        for event in queued
    ] == [(0, 1), (1, 2)]
    assert state.extra_turn_stack == ["first", "second"]

    before_av = {unit.id: unit.current_av for unit in state.units}
    first_turn = Timeline.next_turn(state)
    second_turn = Timeline.next_turn(state)
    assert [first_turn.actor_id, second_turn.actor_id] == ["second", "first"]
    assert first_turn.is_extra_turn is True
    assert second_turn.is_extra_turn is True
    assert state.global_av == 0
    assert {unit.id: unit.current_av for unit in state.units} == before_av


def test_grant_extra_turn_observation_remains_distinct_from_axis_mutations():
    source = inspect.getsource(GrantExtraTurn)
    assert "extra_turn_queued" in source
    assert "extra_turn_stack.append" in source
    assert "action_advanced" not in source
    assert "action_delayed" not in source
    assert "speed_changed" not in source
    assert "action_immediate" not in source
    assert "current_av" not in source
    assert "priority" not in source.lower()

    assert "extra_turn_queued" not in inspect.getsource(AdvanceAction)
    assert "extra_turn_queued" not in inspect.getsource(DelayAction)
    assert "extra_turn_queued" not in inspect.getsource(ChangeSpeed)
    assert "extra_turn_queued" not in inspect.getsource(ImmediateAction)


def test_all_nine_reviewed_fixture_byte_identities_remain_exact():
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
    assert runtime.total == 9
    assert runtime.passed_count == 9


def test_production_extra_turn_lifo_compatibility_is_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])

    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == [
        "third",
        "second",
        "first",
    ]
