import importlib
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
from hsr_axis_sim.runtime_action_session_validation import run_action_session_validation
from hsr_axis_sim.runtime_action_sessions import (
    ExplicitActionCaptureStep,
    MultiActionCaptureSessionConfig,
    MultiActionCaptureSessionFailure,
    run_multi_action_capture_session,
)
from hsr_axis_sim.runtime_adapters import (
    AmbiguousLegacyEventPolicy,
    LegacyEventAdapterConfig,
    UnknownLegacyEventPolicy,
)
from hsr_axis_sim.runtime_capture_cursors import PendingEventCaptureCursor
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
)
from hsr_axis_sim.runtime_golden_replays import GoldenReplayValidationConfig
from hsr_axis_sim.runtime_loaders import TraceCanonicalFormPolicy
from hsr_axis_sim.runtime_trace_bridges import LegacyEventTraceBridgeConfig
from hsr_axis_sim.runtime_trace_stitching import CapturedTraceStitchConfig
from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.effects import ConsumeEnergy
from hsr_axis_sim.sim.state import BattleState
from hsr_axis_sim.sim.timeline import Timeline
from hsr_axis_sim.sim.turn_context import TurnContext
from hsr_axis_sim.sim.unit import Unit


ROOT = Path(__file__).parents[2]
LEGACY_MANIFEST_PATH = ROOT / "hsr_axis_sim" / "data" / "regression_manifest.json"
RUNTIME_MANIFEST_PATH = (
    ROOT / "hsr_axis_sim" / "data" / "runtime_action_session_regression_manifest.json"
)
ACTOR_ID = "energy-failure-actor"
ACTION_ID = "insufficient-energy-action"
TARGET_ID = "energy-failure-target"
ERROR_MESSAGE = (
    "Unit 'energy-failure-target' has insufficient energy: "
    "10 available, 20 required."
)


def _state():
    return BattleState(
        [
            Unit(
                id=TARGET_ID,
                name=TARGET_ID,
                team="ally",
                base_speed=100,
                energy=10,
                max_energy=100,
            )
        ]
    )


def _failing_action(*, ends_turn=True):
    return Action(
        ACTION_ID,
        ACTION_ID,
        ACTOR_ID,
        effects=[ConsumeEnergy(target_ids=[TARGET_ID], amount=20)],
        ends_turn=ends_turn,
    )


def _adapter_config():
    return LegacyEventAdapterConfig(
        "arch-030-failure-stream",
        UnknownLegacyEventPolicy.REJECT,
        AmbiguousLegacyEventPolicy.REJECT,
    )


def _export_config(index):
    return TraceExportConfig(
        f"arch-030-segment-{index}",
        TraceSequencePolicy.CONTIGUOUS,
        EmptyTracePolicy.REJECT,
        {"task": "HSR-RUNTIME-ARCH-030", "segment": index},
    )


def _session_config(count):
    return MultiActionCaptureSessionConfig(
        PendingEventCaptureCursor(0, 0),
        _adapter_config(),
        tuple(_export_config(index) for index in range(count)),
        False,
    )


def _single_action_request():
    cursor = PendingEventCaptureCursor(0, 0)
    return SingleActionEventCaptureRequest(
        cursor,
        LegacyEventTraceBridgeConfig(
            _adapter_config(),
            0,
            _export_config(0),
            False,
        ),
    )


def _stitch_config():
    return CapturedTraceStitchConfig(
        TraceExportConfig(
            "arch-030-failure-stitch",
            TraceSequencePolicy.CONTIGUOUS,
            EmptyTracePolicy.REJECT,
            {"task": "HSR-RUNTIME-ARCH-030"},
        ),
        False,
    )


def _golden_config():
    return GoldenReplayValidationConfig(
        "arch-030-failure-should-not-reach-golden",
        "0" * 64,
        TraceCanonicalFormPolicy.COMPACT_ONLY,
        100_000,
    )


def test_direct_production_insufficient_energy_failure_preserves_target_and_partial_state():
    state = _state()
    context = TurnContext(actor_id=ACTOR_ID)

    with pytest.raises(ValueError) as caught:
        _failing_action(ends_turn=True).execute(state, context)

    assert type(caught.value) is ValueError
    assert str(caught.value) == ERROR_MESSAGE
    target = state.get_unit(TARGET_ID)
    assert target.id == TARGET_ID
    assert target.energy == 10
    assert target.max_energy == 100
    assert context.actions_taken == []
    assert context.should_end_turn is True
    assert [event.type for event in state.pending_events] == ["action_started"]
    assert state.pending_events[0].data == {
        "actor_id": ACTOR_ID,
        "action_id": ACTION_ID,
    }
    assert all(event.type != "energy_changed" for event in state.pending_events)
    assert all(event.type != "action_finished" for event in state.pending_events)
    assert all(event.type != "turn_ended" for event in state.pending_events)


def test_arch_012_propagates_energy_error_and_skips_capture(monkeypatch):
    state = _state()
    context = TurnContext(actor_id=ACTOR_ID)
    request = _single_action_request()
    module = importlib.import_module("hsr_axis_sim.runtime_action_captures.capture")
    capture_calls = []

    def forbidden_capture(*args, **kwargs):
        capture_calls.append((args, kwargs))
        raise AssertionError("capture must not run after insufficient-Energy failure")

    monkeypatch.setattr(
        module,
        "capture_battle_state_pending_events_from_cursor",
        forbidden_capture,
    )

    with pytest.raises(ValueError) as caught:
        execute_action_and_capture_pending_events(
            state,
            _failing_action(ends_turn=False),
            request=request,
            turn_context=context,
        )

    assert type(caught.value) is ValueError
    assert str(caught.value) == ERROR_MESSAGE
    assert capture_calls == []
    assert state.get_unit(TARGET_ID).energy == 10
    assert [event.type for event in state.pending_events] == ["action_started"]
    assert context.actions_taken == []
    assert context.should_end_turn is False
    assert request.cursor == PendingEventCaptureCursor(0, 0)


def test_arch_013_first_step_energy_failure_wraps_exact_cause_and_initial_cursor():
    state = _state()
    later = Action("later-action", "later-action", ACTOR_ID, ends_turn=False)
    steps = (
        ExplicitActionCaptureStep(_failing_action(ends_turn=False)),
        ExplicitActionCaptureStep(later),
    )
    config = _session_config(2)

    with pytest.raises(MultiActionCaptureSessionFailure) as caught:
        run_multi_action_capture_session(state, steps, config=config)

    failure = caught.value
    assert failure.failed_action_index == 0
    assert failure.failed_action_id == ACTION_ID
    assert failure.completed_results == ()
    assert failure.last_successful_cursor == config.initial_cursor
    assert type(failure.__cause__) is ValueError
    assert str(failure.__cause__) == ERROR_MESSAGE
    assert state.get_unit(TARGET_ID).energy == 10
    assert [event.type for event in state.pending_events] == ["action_started"]
    assert failure.last_successful_cursor.pending_event_index == 0
    assert len(state.pending_events) == 1
    assert all(event.data.get("action_id") != "later-action" for event in state.pending_events)


def test_arch_013_energy_failure_after_completed_step_preserves_confirmed_boundary_only():
    state = _state()
    first = Action("completed-action", "completed-action", ACTOR_ID, ends_turn=False)
    third = Action("never-runs", "never-runs", ACTOR_ID, ends_turn=False)
    steps = (
        ExplicitActionCaptureStep(first),
        ExplicitActionCaptureStep(_failing_action(ends_turn=False)),
        ExplicitActionCaptureStep(third),
    )

    with pytest.raises(MultiActionCaptureSessionFailure) as caught:
        run_multi_action_capture_session(state, steps, config=_session_config(3))

    failure = caught.value
    assert failure.failed_action_index == 1
    assert failure.failed_action_id == ACTION_ID
    assert len(failure.completed_results) == 1
    first_result = failure.completed_results[0]
    assert first_result.action_id == "completed-action"
    assert first_result.next_cursor == PendingEventCaptureCursor(2, 2)
    assert failure.last_successful_cursor == first_result.next_cursor
    assert type(failure.__cause__) is ValueError
    assert str(failure.__cause__) == ERROR_MESSAGE
    assert state.get_unit(TARGET_ID).energy == 10
    assert [event.type for event in state.pending_events] == [
        "action_started",
        "action_finished",
        "action_started",
    ]
    assert [event.data.get("action_id") for event in state.pending_events] == [
        "completed-action",
        "completed-action",
        ACTION_ID,
    ]
    assert len(state.pending_events) == (
        failure.last_successful_cursor.pending_event_index + 1
    )
    assert all(event.type != "energy_changed" for event in state.pending_events)
    assert all(event.data.get("action_id") != "never-runs" for event in state.pending_events)


def test_arch_016_energy_failure_stops_before_stitch_and_golden(monkeypatch):
    state = _state()
    steps = (ExplicitActionCaptureStep(_failing_action(ends_turn=False)),)
    module = importlib.import_module("hsr_axis_sim.runtime_action_session_validation.run")
    downstream_calls = []

    def forbidden_stitch(*args, **kwargs):
        downstream_calls.append(("stitch", args, kwargs))
        raise AssertionError("stitch must not run for failed Energy session")

    def forbidden_golden(*args, **kwargs):
        downstream_calls.append(("golden", args, kwargs))
        raise AssertionError("Golden validation must not run for failed Energy session")

    monkeypatch.setattr(module, "stitch_successful_action_session", forbidden_stitch)
    monkeypatch.setattr(
        module,
        "validate_successful_session_against_golden",
        forbidden_golden,
    )

    with pytest.raises(MultiActionCaptureSessionFailure) as caught:
        run_action_session_validation(
            state,
            steps,
            session_config=_session_config(1),
            stitch_config=_stitch_config(),
            expected_payload_bytes=b"{}",
            golden_config=_golden_config(),
        )

    assert downstream_calls == []
    assert caught.value.failed_action_index == 0
    assert type(caught.value.__cause__) is ValueError
    assert str(caught.value.__cause__) == ERROR_MESSAGE
    assert state.get_unit(TARGET_ID).energy == 10
    assert [event.type for event in state.pending_events] == ["action_started"]


def test_successful_regressions_and_lifo_remain_unchanged():
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
    assert runtime.total == 5
    assert runtime.passed_count == 5

    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    lifo_state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(lifo_state).actor_id for _ in range(3)] == [
        "third",
        "second",
        "first",
    ]
