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
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5,
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
    RuntimeActionAdvanceObservation,
    RuntimeActionDelayObservation,
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
from hsr_axis_sim.sim.timeline import Timeline
from hsr_axis_sim.sim.unit import Unit


ROOT = Path(__file__).parents[2]
LEGACY_MANIFEST_PATH = ROOT / "hsr_axis_sim" / "data" / "regression_manifest.json"
RUNTIME_MANIFEST_PATH = (
    ROOT / "hsr_axis_sim" / "data" / "runtime_action_session_regression_manifest.json"
)
FIXTURE_DIR = ROOT / "hsr_axis_sim" / "data" / "runtime_golden_fixtures"
LOCKED_FIXTURES = (
    (
        FIXTURE_DIR / "arch_017_reviewed_action_session_expected.json",
        3013,
        "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66",
    ),
    (
        FIXTURE_DIR / "arch_021_reviewed_clamped_energy_expected.json",
        2759,
        "4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605",
    ),
    (
        FIXTURE_DIR / "arch_023_reviewed_clamped_skill_point_expected.json",
        2744,
        "fc359b367c2922ed39e059f89ad16845ba215508292cfa43ca2ab6031c4c9ba9",
    ),
    (
        FIXTURE_DIR / "arch_025_reviewed_energy_consume_expected.json",
        2750,
        "7d61528687a5a2f499249e0f914f6f2f50975c7c153165eddd5e116f3ed19a75",
    ),
    (
        FIXTURE_DIR / "arch_027_reviewed_skill_point_consume_expected.json",
        2796,
        "d0dcf128f3a28f691324f4e9295b7bcd66460598186f6059d4619f55e8ae39ec",
    ),
    (
        FIXTURE_DIR / "arch_032_reviewed_action_advance_expected.json",
        2818,
        "ab73c224d06690b379d398a5bc2c4b38a1ed654dfd86866d564417432c29d3ce",
    ),
)


def _adapter_config() -> LegacyEventAdapterConfig:
    return LegacyEventAdapterConfig(
        "delay-observation-stream",
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
                "delay-observation-trace",
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"source": "arch-034"},
            ),
            False,
        ),
    )


def _delay_event_data(**overrides):
    data = {
        "actor_id": "actor",
        "action_id": "delay",
        "target_id": "target",
        "before_av": 30.0,
        "after_av": 55.0,
        "base_av": 100.0,
        "requested_percent": 0.25,
        "requested_delta_av": 25.0,
        "applied_delta_av": 25.0,
    }
    data.update(overrides)
    return data


def test_action_delay_observation_is_frozen_strict_and_serializes_exact_payload():
    observation = RuntimeActionDelayObservation(
        target_id="target",
        before_av=30.0,
        after_av=55.0,
        base_av=100.0,
        requested_percent=0.25,
        requested_delta_av=25.0,
        applied_delta_av=25.0,
    )

    assert observation.to_payload() == {
        "target_id": "target",
        "before_av": 30.0,
        "after_av": 55.0,
        "base_av": 100.0,
        "requested_percent": 0.25,
        "requested_delta_av": 25.0,
        "applied_delta_av": 25.0,
    }
    assert "clamped_to_zero" not in observation.to_payload()
    with pytest.raises(FrozenInstanceError):
        observation.after_av = 99


def test_signed_negative_delay_percent_and_negative_resulting_av_remain_representable():
    observation = RuntimeActionDelayObservation(
        target_id="target",
        before_av=30.0,
        after_av=-20.0,
        base_av=100.0,
        requested_percent=-0.5,
        requested_delta_av=-50.0,
        applied_delta_av=-50.0,
    )

    assert observation.after_av == -20.0
    assert observation.requested_percent == -0.5
    assert observation.requested_delta_av == -50.0


@pytest.mark.parametrize(
    "kwargs, error_type",
    [
        ({"target_id": ""}, ValueError),
        ({"before_av": True}, TypeError),
        ({"after_av": nan}, ValueError),
        ({"base_av": 0}, ValueError),
        ({"base_av": inf}, ValueError),
        ({"requested_percent": True}, TypeError),
        ({"requested_delta_av": 24.0}, ValueError),
        ({"after_av": 54.0}, ValueError),
        ({"applied_delta_av": 24.0}, ValueError),
    ],
)
def test_action_delay_observation_rejects_malformed_contract(kwargs, error_type):
    values = {
        "target_id": "target",
        "before_av": 30.0,
        "after_av": 55.0,
        "base_av": 100.0,
        "requested_percent": 0.25,
        "requested_delta_av": 25.0,
        "applied_delta_av": 25.0,
    }
    values.update(kwargs)
    with pytest.raises(error_type):
        RuntimeActionDelayObservation(**values)


def test_legacy_action_delayed_maps_to_dedicated_typed_runtime_event_and_payload():
    data = _delay_event_data()
    result = adapt_legacy_event(
        Event("action_delayed", data),
        sequence=4,
        config=_adapter_config(),
    )

    assert result.event_type is RuntimeEventType.ACTION_VALUE_DELAYED
    assert result.action_id == "delay"
    assert result.actor_id == "actor"
    assert result.target_id == "target"
    assert dict(result.payload["legacy_data"]) == data
    assert dict(result.payload["action_delay"]) == {
        "target_id": "target",
        "before_av": 30.0,
        "after_av": 55.0,
        "base_av": 100.0,
        "requested_percent": 0.25,
        "requested_delta_av": 25.0,
        "applied_delta_av": 25.0,
    }
    assert "action_advance" not in result.payload
    assert result.payload["adapter"]["mapping_status"] == "BOUND"
    assert result.payload["adapter"]["mechanic_id"] == "LEGACY_EVENT.ACTION_DELAYED"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: data.pop("after_av"),
        lambda data: data.__setitem__("requested_delta_av", 24.0),
        lambda data: data.__setitem__("after_av", 54.0),
        lambda data: data.__setitem__("target_id", ""),
    ],
)
def test_malformed_action_delayed_is_rejected_not_degraded(mutation):
    data = _delay_event_data()
    mutation(data)
    with pytest.raises(LegacyEventSchemaError):
        adapt_legacy_event(
            Event("action_delayed", data),
            sequence=0,
            config=_adapter_config(),
        )


def test_production_positive_self_delay_preserves_formula_and_emits_exact_event():
    unit = Unit("actor", "Actor", "ally", 100, current_av=30)
    state = BattleState([unit])
    action = Action(
        "delay",
        "Delay",
        "actor",
        effects=[DelayAction(percent=0.25)],
        ends_turn=False,
    )

    action.execute(state)

    assert unit.current_av == pytest.approx(55, abs=1e-6)
    assert [event.type for event in state.pending_events] == [
        "action_started",
        "action_delayed",
        "action_finished",
    ]
    assert state.pending_events[1].data == {
        "actor_id": "actor",
        "action_id": "delay",
        "target_id": "actor",
        "before_av": 30,
        "after_av": 55.0,
        "base_av": 100.0,
        "requested_percent": 0.25,
        "requested_delta_av": 25.0,
        "applied_delta_av": 25.0,
    }


def test_production_negative_delay_percent_preserves_existing_unclamped_formula():
    unit = Unit("actor", "Actor", "ally", 100, current_av=30)
    state = BattleState([unit])

    Action(
        "delay",
        "Delay",
        "actor",
        effects=[DelayAction(percent=-0.5)],
        ends_turn=False,
    ).execute(state)

    assert unit.current_av == pytest.approx(-20, abs=1e-6)
    data = state.pending_events[1].data
    assert data["before_av"] == 30
    assert data["after_av"] == -20.0
    assert data["requested_percent"] == -0.5
    assert data["requested_delta_av"] == -50.0
    assert data["applied_delta_av"] == -50.0
    assert "clamped_to_zero" not in data


class ObserveDelayedTargetAv(Effect):
    def apply(self, state, action, turn_context):
        target = state.get_unit(action.event_data["target_id"])
        state.logs.append(f"observed-delay-av:{target.current_av}")


def test_action_delayed_trigger_dispatch_observes_post_mutation_av():
    unit = Unit("actor", "Actor", "ally", 100, current_av=30)
    state = BattleState(
        [unit],
        triggers=[
            Trigger(
                id="observe-delay",
                owner_id="actor",
                event_type="action_delayed",
                condition={"type": "always"},
                effects=[ObserveDelayedTargetAv()],
            )
        ],
    )

    Action(
        "delay",
        "Delay",
        "actor",
        effects=[DelayAction(percent=0.25)],
        ends_turn=False,
    ).execute(state)

    assert unit.current_av == 55.0
    assert state.logs == ["trigger:observe-delay", "observed-delay-av:55.0"]
    assert [event.type for event in state.pending_events] == [
        "action_started",
        "action_delayed",
        "action_finished",
    ]


def test_arch_012_capture_contains_exact_typed_three_record_delay_trace():
    unit = Unit("actor", "Actor", "ally", 100, current_av=30)
    state = BattleState([unit])
    action = Action(
        "delay",
        "Delay",
        "actor",
        effects=[DelayAction(percent=0.25)],
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
        RuntimeEventType.ACTION_VALUE_DELAYED,
        RuntimeEventType.ACTION_END,
    ]
    delayed = records[1].event
    assert delayed.action_id == "delay"
    assert delayed.actor_id == "actor"
    assert delayed.target_id == "actor"
    assert dict(delayed.payload["action_delay"]) == {
        "target_id": "actor",
        "before_av": 30,
        "after_av": 55.0,
        "base_av": 100.0,
        "requested_percent": 0.25,
        "requested_delta_av": 25.0,
        "applied_delta_av": 25.0,
    }
    assert records[1].numeric_values == {}
    assert result.next_cursor == PendingEventCaptureCursor(3, 3)


def test_arch_031_advance_contract_and_production_observation_remain_unchanged():
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
    assert observation.to_payload()["clamped_to_zero"] is False

    unit = Unit("actor", "Actor", "ally", 100, current_av=80)
    state = BattleState([unit])
    Action(
        "advance",
        "Advance",
        "actor",
        effects=[AdvanceAction(percent=0.5)],
        ends_turn=False,
    ).execute(state)

    assert unit.current_av == 30.0
    assert [event.type for event in state.pending_events] == [
        "action_started",
        "action_advanced",
        "action_finished",
    ]
    assert "clamped_to_zero" in state.pending_events[1].data
    assert "action_delayed" not in [event.type for event in state.pending_events]


def test_locked_static_fixtures_and_all_regression_lanes_remain_valid_after_promotion():
    for path, size, digest in LOCKED_FIXTURES:
        payload = path.read_bytes()
        assert len(payload) == size
        assert hashlib.sha256(payload).hexdigest() == digest

    legacy = load_regression_manifest(LEGACY_MANIFEST_PATH)
    complete = run_regression(manifest=legacy)
    trace = run_regression(manifest=legacy, only="trace_evidence")
    runtime_manifest = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    runtime = run_runtime_action_session_regression(runtime_manifest)

    assert complete.passed is True
    assert complete.total == 20
    assert complete.passed_count == 20
    assert trace.passed is True
    assert trace.total == 2
    assert trace.passed_count == 2
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5 == "1.5"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION == "1.6"
    assert runtime.passed is True
    assert runtime.total == 7
    assert runtime.passed_count == 7
    assert runtime.failed_count == 0


def test_arch_034_scope_preserves_later_authorized_change_speed_observation():
    delay_source = inspect.getsource(DelayAction)
    advance_source = inspect.getsource(AdvanceAction)
    assert "action_delayed" in delay_source
    assert "action_advanced" not in delay_source
    assert "action_advanced" in advance_source
    assert "action_delayed" not in advance_source

    speed_source = inspect.getsource(ChangeSpeed)
    assert "action_delayed" not in speed_source
    assert "speed_changed" in speed_source
    assert "emit_event" in speed_source

    for effect_type in (ImmediateAction, GrantExtraTurn):
        source = inspect.getsource(effect_type)
        assert "action_delayed" not in source
        assert "speed_changed" not in source
        assert "emit_event" not in source


def test_production_extra_turn_lifo_compatibility_is_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])

    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == [
        "third",
        "second",
        "first",
    ]
