from dataclasses import FrozenInstanceError
import importlib

import pytest

from hsr_axis_sim.runtime_action_sessions import (
    ExplicitActionCaptureStep,
    MultiActionCaptureSessionConfig,
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
from hsr_axis_sim.runtime_session_golden_validation import (
    RuntimeSessionGoldenValidationInputError,
    SuccessfulSessionGoldenValidationResult,
    validate_successful_session_against_golden,
)
from hsr_axis_sim.runtime_session_stitching import stitch_successful_action_session
from hsr_axis_sim.runtime_stitched_golden_validation import (
    validate_stitched_actual_against_golden,
)
from hsr_axis_sim.runtime_trace_stitching import CapturedTraceStitchConfig
from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.state import BattleState


def _adapter_config():
    return LegacyEventAdapterConfig(
        "session-golden-stream",
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


def _session_stitch(action_ids=("action-a", "action-b"), trace_id="actual-session"):
    state = BattleState([])
    steps = tuple(
        ExplicitActionCaptureStep(
            Action(action_id, action_id, "actor", ends_turn=False)
        )
        for action_id in action_ids
    )
    session = run_multi_action_capture_session(
        state,
        steps,
        config=MultiActionCaptureSessionConfig(
            PendingEventCaptureCursor(0, 0),
            _adapter_config(),
            tuple(_segment_export(index) for index in range(len(steps))),
            False,
        ),
    )
    return stitch_successful_action_session(
        session,
        config=CapturedTraceStitchConfig(
            TraceExportConfig(
                trace_id,
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"source": "arch-015-test"},
            ),
            False,
        ),
    )


def _golden_config(expected_sha256):
    return GoldenReplayValidationConfig(
        "session-golden-replay",
        expected_sha256,
        TraceCanonicalFormPolicy.EITHER_CANONICAL,
        100_000,
    )


def test_matching_successful_session_handoff_returns_golden_pass_with_full_provenance():
    session_stitch = _session_stitch()
    artifact = session_stitch.stitch_result.artifact

    result = validate_successful_session_against_golden(
        session_stitch,
        artifact.payload_bytes,
        config=_golden_config(artifact.sha256),
    )

    assert result.matches is True
    assert result.session_stitch_result is session_stitch
    assert result.validation_result.stitch_result is session_stitch.stitch_result
    assert result.actual_sha256 == artifact.sha256
    assert result.validation_result.validation_result.actual_sha256 == artifact.sha256


def test_mismatching_expected_session_remains_completed_golden_failure():
    actual = _session_stitch(("action-a", "action-b"), "actual")
    expected = _session_stitch(("action-a", "action-c"), "expected")
    expected_artifact = expected.stitch_result.artifact

    result = validate_successful_session_against_golden(
        actual,
        expected_artifact.payload_bytes,
        config=_golden_config(expected_artifact.sha256),
    )

    assert result.matches is False
    golden = result.validation_result.validation_result
    assert golden.comparison.mismatch_count >= 1
    assert golden.first_divergence.matches is False
    assert result.validation_result.stitch_result is actual.stitch_result


def test_handoff_calls_arch_011_once_with_exact_arch_014_stitch_object(monkeypatch):
    session_stitch = _session_stitch()
    artifact = session_stitch.stitch_result.artifact
    config = _golden_config(artifact.sha256)
    expected_result = validate_stitched_actual_against_golden(
        session_stitch.stitch_result,
        artifact.payload_bytes,
        config=config,
    )

    module = importlib.import_module(
        "hsr_axis_sim.runtime_session_golden_validation.validate"
    )
    calls = []

    def recording_validator(stitch_result, expected_payload_bytes, *, config):
        calls.append((stitch_result, expected_payload_bytes, config))
        return expected_result

    monkeypatch.setattr(
        module, "validate_stitched_actual_against_golden", recording_validator
    )
    result = module.validate_successful_session_against_golden(
        session_stitch,
        artifact.payload_bytes,
        config=config,
    )

    assert len(calls) == 1
    passed_stitch, passed_expected, passed_config = calls[0]
    assert passed_stitch is session_stitch.stitch_result
    assert passed_expected is artifact.payload_bytes
    assert passed_config is config
    assert result.validation_result is expected_result


def test_invalid_input_types_are_rejected_before_arch_011_invocation(monkeypatch):
    session_stitch = _session_stitch()
    artifact = session_stitch.stitch_result.artifact
    config = _golden_config(artifact.sha256)
    module = importlib.import_module(
        "hsr_axis_sim.runtime_session_golden_validation.validate"
    )
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("ARCH-011 must not run for invalid ARCH-015 input")

    monkeypatch.setattr(
        module, "validate_stitched_actual_against_golden", forbidden
    )

    with pytest.raises(RuntimeSessionGoldenValidationInputError):
        module.validate_successful_session_against_golden(
            object(), artifact.payload_bytes, config=config
        )
    with pytest.raises(RuntimeSessionGoldenValidationInputError):
        module.validate_successful_session_against_golden(
            session_stitch, bytearray(artifact.payload_bytes), config=config
        )
    with pytest.raises(RuntimeSessionGoldenValidationInputError):
        module.validate_successful_session_against_golden(
            session_stitch, artifact.payload_bytes, config=object()
        )
    assert calls == []


def test_underlying_arch_011_failure_propagates_unchanged(monkeypatch):
    session_stitch = _session_stitch()
    artifact = session_stitch.stitch_result.artifact
    config = _golden_config(artifact.sha256)
    module = importlib.import_module(
        "hsr_axis_sim.runtime_session_golden_validation.validate"
    )

    class SentinelArch011Error(RuntimeError):
        pass

    sentinel = SentinelArch011Error("intentional ARCH-011 failure")

    def failing_validator(*args, **kwargs):
        raise sentinel

    monkeypatch.setattr(
        module, "validate_stitched_actual_against_golden", failing_validator
    )
    with pytest.raises(SentinelArch011Error) as caught:
        module.validate_successful_session_against_golden(
            session_stitch,
            artifact.payload_bytes,
            config=config,
        )
    assert caught.value is sentinel


def test_wrapper_is_frozen_and_rejects_different_stitch_object_provenance():
    session_stitch_a = _session_stitch(("action-a",), "same")
    session_stitch_b = _session_stitch(("action-a",), "same")
    artifact = session_stitch_a.stitch_result.artifact
    validation = validate_stitched_actual_against_golden(
        session_stitch_a.stitch_result,
        artifact.payload_bytes,
        config=_golden_config(artifact.sha256),
    )
    result = SuccessfulSessionGoldenValidationResult(
        session_stitch_a,
        validation,
    )

    with pytest.raises(FrozenInstanceError):
        result.validation_result = object()
    with pytest.raises(
        RuntimeSessionGoldenValidationInputError,
        match="exact ARCH-014 stitch object",
    ):
        SuccessfulSessionGoldenValidationResult(session_stitch_b, validation)
    with pytest.raises(RuntimeSessionGoldenValidationInputError):
        SuccessfulSessionGoldenValidationResult(object(), validation)
    with pytest.raises(RuntimeSessionGoldenValidationInputError):
        SuccessfulSessionGoldenValidationResult(session_stitch_a, object())
