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
from hsr_axis_sim.runtime_session_stitching import (
    RuntimeSessionStitchInputError,
    SuccessfulSessionTraceStitchResult,
    stitch_successful_action_session,
)
from hsr_axis_sim.runtime_trace_stitching import (
    CapturedTraceStitchConfig,
    stitch_captured_trace_segments,
)
from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.state import BattleState


def _adapter_config():
    return LegacyEventAdapterConfig(
        "session-stitch-stream",
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


def _successful_session(action_ids=("action-a", "action-b", "action-c")):
    state = BattleState([])
    steps = tuple(
        ExplicitActionCaptureStep(
            Action(action_id, action_id, "actor", ends_turn=False)
        )
        for action_id in action_ids
    )
    config = MultiActionCaptureSessionConfig(
        PendingEventCaptureCursor(0, 0),
        _adapter_config(),
        tuple(_segment_export(index) for index in range(len(steps))),
        False,
    )
    return run_multi_action_capture_session(state, steps, config=config)


def _stitch_config(trace_id="session-final"):
    return CapturedTraceStitchConfig(
        TraceExportConfig(
            trace_id,
            TraceSequencePolicy.CONTIGUOUS,
            EmptyTracePolicy.REJECT,
            {"source": "successful-session-stitch"},
        ),
        False,
    )


def test_successful_session_stitches_exact_capture_segments_in_order():
    session = _successful_session()
    result = stitch_successful_action_session(session, config=_stitch_config())

    assert result.session_result is session
    assert result.segment_count == 3
    assert result.record_count == 6
    assert len(result.stitch_result.segments) == len(session.results)
    for stitched_segment, action_result in zip(
        result.stitch_result.segments, session.results
    ):
        assert stitched_segment is action_result.capture_result

    document = result.stitch_result.artifact.document
    assert document.trace_id == "session-final"
    assert document.metadata == {"source": "successful-session-stitch"}
    assert [record.sequence for record in document.records] == list(range(6))
    assert [record.event.action_id for record in document.records] == [
        "action-a",
        "action-a",
        "action-b",
        "action-b",
        "action-c",
        "action-c",
    ]

    source_events = tuple(
        record.event
        for action_result in session.results
        for record in action_result.capture_result.capture_result.bridge_result.artifact.document.records
    )
    for final_record, source_event in zip(document.records, source_events):
        assert final_record.event is source_event


def test_handoff_calls_arch_010_once_with_exact_segments_and_config(monkeypatch):
    session = _successful_session(("action-a", "action-b"))
    config = _stitch_config("exact-handoff")
    expected_segments = tuple(item.capture_result for item in session.results)
    expected_result = stitch_captured_trace_segments(expected_segments, config=config)

    module = importlib.import_module("hsr_axis_sim.runtime_session_stitching.stitch")
    calls = []

    def recording_stitch(segments, *, config):
        calls.append((segments, config))
        return expected_result

    monkeypatch.setattr(module, "stitch_captured_trace_segments", recording_stitch)
    result = module.stitch_successful_action_session(session, config=config)

    assert len(calls) == 1
    passed_segments, passed_config = calls[0]
    assert passed_config is config
    assert len(passed_segments) == len(expected_segments)
    for actual, expected in zip(passed_segments, expected_segments):
        assert actual is expected
    assert result.stitch_result is expected_result


def test_wrong_input_types_are_rejected_before_stitch_invocation(monkeypatch):
    session = _successful_session(("action-a",))
    config = _stitch_config()
    module = importlib.import_module("hsr_axis_sim.runtime_session_stitching.stitch")
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("stitcher must not be called for invalid handoff input")

    monkeypatch.setattr(module, "stitch_captured_trace_segments", forbidden)

    with pytest.raises(RuntimeSessionStitchInputError):
        module.stitch_successful_action_session(object(), config=config)
    with pytest.raises(RuntimeSessionStitchInputError):
        module.stitch_successful_action_session(session, config=object())
    assert calls == []


def test_underlying_arch_010_failure_propagates_unchanged(monkeypatch):
    session = _successful_session(("action-a",))
    config = _stitch_config()
    module = importlib.import_module("hsr_axis_sim.runtime_session_stitching.stitch")

    class SentinelStitchError(RuntimeError):
        pass

    sentinel = SentinelStitchError("intentional stitch failure")

    def failing_stitch(*args, **kwargs):
        raise sentinel

    monkeypatch.setattr(module, "stitch_captured_trace_segments", failing_stitch)
    with pytest.raises(SentinelStitchError) as caught:
        module.stitch_successful_action_session(session, config=config)
    assert caught.value is sentinel


def test_wrapper_is_frozen_and_rejects_session_stitch_provenance_mismatch():
    session_a = _successful_session(("action-a",))
    session_b = _successful_session(("action-a",))
    result_a = stitch_successful_action_session(session_a, config=_stitch_config("a"))

    with pytest.raises(FrozenInstanceError):
        result_a.stitch_result = object()
    with pytest.raises(RuntimeSessionStitchInputError, match="exact session capture object"):
        SuccessfulSessionTraceStitchResult(session_b, result_a.stitch_result)
    with pytest.raises(RuntimeSessionStitchInputError):
        SuccessfulSessionTraceStitchResult(object(), result_a.stitch_result)
    with pytest.raises(RuntimeSessionStitchInputError):
        SuccessfulSessionTraceStitchResult(session_a, object())
