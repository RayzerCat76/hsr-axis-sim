from dataclasses import FrozenInstanceError
import importlib

import pytest

from hsr_axis_sim.runtime_action_session_validation import (
    EndToEndActionSessionValidationResult,
    RuntimeActionSessionValidationInputError,
    run_action_session_validation,
)
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
from hsr_axis_sim.runtime_session_stitching import stitch_successful_action_session
from hsr_axis_sim.runtime_trace_stitching import CapturedTraceStitchConfig
from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.effects import Effect
from hsr_axis_sim.sim.state import BattleState


def _adapter_config():
    return LegacyEventAdapterConfig(
        "e2e-session-stream",
        UnknownLegacyEventPolicy.REJECT,
        AmbiguousLegacyEventPolicy.REJECT,
    )


def _segment_export(index):
    return TraceExportConfig(
        f"segment-{index}",
        TraceSequencePolicy.CONTIGUOUS,
        EmptyTracePolicy.REJECT,
        {"segment": index},
    )


def _inputs(action_ids=("action-a", "action-b")):
    steps = tuple(
        ExplicitActionCaptureStep(
            Action(action_id, action_id, "actor", ends_turn=False)
        )
        for action_id in action_ids
    )
    session_config = MultiActionCaptureSessionConfig(
        PendingEventCaptureCursor(0, 0),
        _adapter_config(),
        tuple(_segment_export(index) for index in range(len(steps))),
        False,
    )
    stitch_config = CapturedTraceStitchConfig(
        TraceExportConfig(
            "e2e-final",
            TraceSequencePolicy.CONTIGUOUS,
            EmptyTracePolicy.REJECT,
            {"source": "arch-016-test"},
        ),
        False,
    )
    return steps, session_config, stitch_config


def _expected_artifact(action_ids=("action-a", "action-b")):
    steps, session_config, stitch_config = _inputs(action_ids)
    session = run_multi_action_capture_session(
        BattleState([]),
        steps,
        config=session_config,
    )
    return stitch_successful_action_session(
        session,
        config=stitch_config,
    ).stitch_result.artifact


def _golden_config(expected_sha256):
    return GoldenReplayValidationConfig(
        "e2e-session-replay",
        expected_sha256,
        TraceCanonicalFormPolicy.EITHER_CANONICAL,
        100_000,
    )


def test_successful_end_to_end_action_session_returns_golden_pass():
    expected = _expected_artifact()
    steps, session_config, stitch_config = _inputs()
    state = BattleState([])

    result = run_action_session_validation(
        state,
        steps,
        session_config=session_config,
        stitch_config=stitch_config,
        expected_payload_bytes=expected.payload_bytes,
        golden_config=_golden_config(expected.sha256),
    )

    assert result.matches is True
    assert result.session_result.steps is steps
    assert result.session_stitch_result.session_result is result.session_result
    assert result.validation_result.session_stitch_result is result.session_stitch_result
    assert result.actual_sha256 == expected.sha256
    assert len(state.pending_events) == 4


def test_expected_trace_mismatch_returns_completed_first_divergence_result():
    expected = _expected_artifact(("action-a", "action-c"))
    steps, session_config, stitch_config = _inputs(("action-a", "action-b"))

    result = run_action_session_validation(
        BattleState([]),
        steps,
        session_config=session_config,
        stitch_config=stitch_config,
        expected_payload_bytes=expected.payload_bytes,
        golden_config=_golden_config(expected.sha256),
    )

    assert result.matches is False
    golden = result.validation_result.validation_result.validation_result
    assert golden.comparison.mismatch_count >= 1
    assert golden.first_divergence.matches is False


def test_orchestrator_calls_only_accepted_stages_in_order_with_exact_objects(monkeypatch):
    expected = _expected_artifact()
    steps, session_config, stitch_config = _inputs()
    golden_config = _golden_config(expected.sha256)
    state = BattleState([])
    module = importlib.import_module("hsr_axis_sim.runtime_action_session_validation.run")
    original_session = module.run_multi_action_capture_session
    original_stitch = module.stitch_successful_action_session
    original_golden = module.validate_successful_session_against_golden
    calls = []

    def recording_session(passed_state, passed_steps, *, config):
        assert passed_state is state
        assert passed_steps is steps
        assert config is session_config
        result = original_session(passed_state, passed_steps, config=config)
        calls.append(("session", result))
        return result

    def recording_stitch(session_result, *, config):
        assert session_result is calls[-1][1]
        assert config is stitch_config
        result = original_stitch(session_result, config=config)
        calls.append(("stitch", result))
        return result

    def recording_golden(session_stitch_result, expected_payload_bytes, *, config):
        assert session_stitch_result is calls[-1][1]
        assert expected_payload_bytes is expected.payload_bytes
        assert config is golden_config
        result = original_golden(
            session_stitch_result,
            expected_payload_bytes,
            config=config,
        )
        calls.append(("golden", result))
        return result

    monkeypatch.setattr(module, "run_multi_action_capture_session", recording_session)
    monkeypatch.setattr(module, "stitch_successful_action_session", recording_stitch)
    monkeypatch.setattr(
        module, "validate_successful_session_against_golden", recording_golden
    )

    result = module.run_action_session_validation(
        state,
        steps,
        session_config=session_config,
        stitch_config=stitch_config,
        expected_payload_bytes=expected.payload_bytes,
        golden_config=golden_config,
    )

    assert [name for name, _ in calls] == ["session", "stitch", "golden"]
    assert result.session_result is calls[0][1]
    assert result.session_stitch_result is calls[1][1]
    assert result.validation_result is calls[2][1]


def test_directly_checkable_invalid_inputs_are_rejected_before_action_execution():
    steps, session_config, stitch_config = _inputs(("action-a",))
    expected = _expected_artifact(("action-a",))
    golden_config = _golden_config(expected.sha256)

    cases = [
        dict(state=object()),
        dict(steps=()),
        dict(steps=(object(),)),
        dict(session_config=object()),
        dict(
            session_config=MultiActionCaptureSessionConfig(
                PendingEventCaptureCursor(0, 0), _adapter_config(), (), False
            )
        ),
        dict(stitch_config=object()),
        dict(expected_payload_bytes=bytearray(expected.payload_bytes)),
        dict(golden_config=object()),
    ]

    for overrides in cases:
        state = BattleState([])
        kwargs = dict(
            state=state,
            steps=steps,
            session_config=session_config,
            stitch_config=stitch_config,
            expected_payload_bytes=expected.payload_bytes,
            golden_config=golden_config,
        )
        kwargs.update(overrides)
        with pytest.raises(RuntimeActionSessionValidationInputError):
            run_action_session_validation(**kwargs)
        if isinstance(kwargs["state"], BattleState):
            assert kwargs["state"].pending_events == []


class _FailingEffect(Effect):
    def apply(self, state, action, turn_context):
        raise RuntimeError("intentional action failure")


def test_arch_013_failure_propagates_unchanged_and_prevents_later_stages(monkeypatch):
    steps, session_config, stitch_config = _inputs(("ok", "fail"))
    steps = (
        steps[0],
        ExplicitActionCaptureStep(
            Action("fail", "fail", "actor", effects=[_FailingEffect()], ends_turn=False)
        ),
    )
    state = BattleState([])
    module = importlib.import_module("hsr_axis_sim.runtime_action_session_validation.run")
    later_calls = []

    def forbidden(*args, **kwargs):
        later_calls.append((args, kwargs))
        raise AssertionError("later stage must not run after ARCH-013 failure")

    monkeypatch.setattr(module, "stitch_successful_action_session", forbidden)
    monkeypatch.setattr(module, "validate_successful_session_against_golden", forbidden)

    with pytest.raises(MultiActionCaptureSessionFailure) as caught:
        module.run_action_session_validation(
            state,
            steps,
            session_config=session_config,
            stitch_config=stitch_config,
            expected_payload_bytes=b"{}",
            golden_config=_golden_config("0" * 64),
        )

    assert caught.value.failed_action_index == 1
    assert caught.value.failed_action_id == "fail"
    assert isinstance(caught.value.__cause__, RuntimeError)
    assert later_calls == []
    assert len(state.pending_events) == 3


def test_arch_014_failure_after_successful_actions_propagates_without_golden(monkeypatch):
    steps, session_config, stitch_config = _inputs(("action-a",))
    state = BattleState([])
    module = importlib.import_module("hsr_axis_sim.runtime_action_session_validation.run")

    class SentinelStitchFailure(RuntimeError):
        pass

    sentinel = SentinelStitchFailure("intentional ARCH-014 failure")
    golden_calls = []

    def failing_stitch(*args, **kwargs):
        raise sentinel

    def forbidden_golden(*args, **kwargs):
        golden_calls.append((args, kwargs))
        raise AssertionError("ARCH-015 must not run after ARCH-014 failure")

    monkeypatch.setattr(module, "stitch_successful_action_session", failing_stitch)
    monkeypatch.setattr(
        module, "validate_successful_session_against_golden", forbidden_golden
    )

    with pytest.raises(SentinelStitchFailure) as caught:
        module.run_action_session_validation(
            state,
            steps,
            session_config=session_config,
            stitch_config=stitch_config,
            expected_payload_bytes=b"{}",
            golden_config=_golden_config("0" * 64),
        )
    assert caught.value is sentinel
    assert len(state.pending_events) == 2
    assert golden_calls == []


def test_arch_015_failure_after_successful_actions_and_stitch_propagates(monkeypatch):
    steps, session_config, stitch_config = _inputs(("action-a",))
    state = BattleState([])
    module = importlib.import_module("hsr_axis_sim.runtime_action_session_validation.run")

    class SentinelGoldenFailure(RuntimeError):
        pass

    sentinel = SentinelGoldenFailure("intentional ARCH-015 failure")

    def failing_golden(*args, **kwargs):
        raise sentinel

    monkeypatch.setattr(
        module, "validate_successful_session_against_golden", failing_golden
    )
    with pytest.raises(SentinelGoldenFailure) as caught:
        module.run_action_session_validation(
            state,
            steps,
            session_config=session_config,
            stitch_config=stitch_config,
            expected_payload_bytes=b"{}",
            golden_config=_golden_config("0" * 64),
        )
    assert caught.value is sentinel
    assert len(state.pending_events) == 2


def test_result_is_frozen_and_rejects_broken_stage_identity_chain():
    expected = _expected_artifact(("action-a",))
    steps, session_config, stitch_config = _inputs(("action-a",))
    result_a = run_action_session_validation(
        BattleState([]),
        steps,
        session_config=session_config,
        stitch_config=stitch_config,
        expected_payload_bytes=expected.payload_bytes,
        golden_config=_golden_config(expected.sha256),
    )
    result_b = run_action_session_validation(
        BattleState([]),
        steps,
        session_config=session_config,
        stitch_config=stitch_config,
        expected_payload_bytes=expected.payload_bytes,
        golden_config=_golden_config(expected.sha256),
    )

    with pytest.raises(FrozenInstanceError):
        result_a.validation_result = object()
    with pytest.raises(RuntimeActionSessionValidationInputError, match="ARCH-014"):
        EndToEndActionSessionValidationResult(
            result_a.session_result,
            result_b.session_stitch_result,
            result_b.validation_result,
        )
    with pytest.raises(RuntimeActionSessionValidationInputError, match="ARCH-015"):
        EndToEndActionSessionValidationResult(
            result_a.session_result,
            result_a.session_stitch_result,
            result_b.validation_result,
        )
