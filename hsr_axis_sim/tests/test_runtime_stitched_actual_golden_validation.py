from dataclasses import FrozenInstanceError
import importlib

import pytest

from hsr_axis_sim.runtime_adapters import (
    AmbiguousLegacyEventPolicy,
    LegacyEventAdapterConfig,
    UnknownLegacyEventPolicy,
)
from hsr_axis_sim.runtime_capture_cursors import (
    PendingEventCaptureCursor,
    PendingEventCursorCaptureRequest,
    capture_battle_state_pending_events_from_cursor,
)
from hsr_axis_sim.runtime_contracts import RuntimeEvent, RuntimeEventType
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
    build_runtime_trace_artifact,
    build_runtime_trace_document,
)
from hsr_axis_sim.runtime_golden_replays import (
    GoldenReplayValidationConfig,
    validate_golden_replay_bytes,
)
from hsr_axis_sim.runtime_loaders import (
    RuntimeTraceDigestMismatchError,
    TraceCanonicalFormPolicy,
)
from hsr_axis_sim.runtime_trace_bridges import LegacyEventTraceBridgeConfig
from hsr_axis_sim.runtime_trace_stitching import (
    CapturedTraceStitchConfig,
    stitch_captured_trace_segments,
)
from hsr_axis_sim.runtime_stitched_golden_validation import (
    StitchedActualGoldenValidationResult,
    StitchedGoldenValidationInputError,
    render_stitched_actual_golden_validation_text,
    validate_stitched_actual_against_golden,
)
from hsr_axis_sim.sim import BattleState, Unit
from hsr_axis_sim.sim.events import Event


def _bridge_config(start_sequence: int, trace_id: str):
    return LegacyEventTraceBridgeConfig(
        LegacyEventAdapterConfig(
            "golden-handoff-stream",
            UnknownLegacyEventPolicy.REJECT,
            AmbiguousLegacyEventPolicy.REJECT,
        ),
        start_sequence,
        TraceExportConfig(
            trace_id,
            TraceSequencePolicy.CONTIGUOUS,
            EmptyTracePolicy.REJECT,
            {"segment": trace_id},
        ),
        False,
    )


def _stitched_actual():
    state = BattleState(units=[Unit("ally", "Ally", "ally", 100)])
    state.emit_event(Event("action_started", {"actor_id": "ally", "action_id": "a"}))
    state.emit_event(Event("action_finished", {"actor_id": "ally", "action_id": "a"}))

    first = capture_battle_state_pending_events_from_cursor(
        state,
        request=PendingEventCursorCaptureRequest(
            PendingEventCaptureCursor(0, 40),
            1,
            _bridge_config(40, "segment-a"),
        ),
    )
    second = capture_battle_state_pending_events_from_cursor(
        state,
        request=PendingEventCursorCaptureRequest(
            first.next_cursor,
            2,
            _bridge_config(41, "segment-b"),
        ),
    )
    return stitch_captured_trace_segments(
        (first, second),
        config=CapturedTraceStitchConfig(
            TraceExportConfig(
                "stitched-actual",
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"source": "arch-010"},
            ),
            False,
        ),
    )


def _golden_config(expected_sha256: str):
    return GoldenReplayValidationConfig(
        "stitched-replay",
        expected_sha256,
        TraceCanonicalFormPolicy.EITHER_CANONICAL,
        100_000,
    )


def _mismatching_expected_artifact(stitch):
    events = [record.event for record in stitch.artifact.document.records]
    original = events[1]
    events[1] = RuntimeEvent(
        original.event_id,
        RuntimeEventType.ACTION_START,
        original.sequence,
        original.action_id,
        original.attack_id,
        original.hit_id,
        original.actor_id,
        original.source_id,
        original.target_id,
        original.payload,
    )
    document = build_runtime_trace_document(
        events,
        config=TraceExportConfig(
            "expected-mismatch",
            TraceSequencePolicy.CONTIGUOUS,
            EmptyTracePolicy.REJECT,
            {"source": "manual-expected"},
        ),
    )
    return build_runtime_trace_artifact(document, pretty=False)


def test_matching_stitched_actual_handoff_preserves_exact_sha_and_returns_golden_pass():
    stitch = _stitched_actual()
    result = validate_stitched_actual_against_golden(
        stitch,
        stitch.artifact.payload_bytes,
        config=_golden_config(stitch.artifact.sha256),
    )

    assert result.matches is True
    assert result.actual_sha256 == stitch.artifact.sha256
    assert result.validation_result.actual_sha256 == stitch.artifact.sha256
    assert result.validation_result.actual_load.artifact.payload_bytes == stitch.artifact.payload_bytes
    assert result.validation_result.actual_load.artifact.document == stitch.artifact.document


def test_handoff_passes_the_exact_stitch_payload_bytes_object_to_golden_validator(monkeypatch):
    stitch = _stitched_actual()
    module = importlib.import_module(
        "hsr_axis_sim.runtime_stitched_golden_validation.validate"
    )
    original = module.validate_golden_replay_bytes
    seen = []

    def recording_validator(expected_payload_bytes, actual_payload_bytes, *, config):
        seen.append(actual_payload_bytes is stitch.artifact.payload_bytes)
        return original(expected_payload_bytes, actual_payload_bytes, config=config)

    monkeypatch.setattr(module, "validate_golden_replay_bytes", recording_validator)
    result = module.validate_stitched_actual_against_golden(
        stitch,
        stitch.artifact.payload_bytes,
        config=_golden_config(stitch.artifact.sha256),
    )
    assert result.matches is True
    assert seen == [True]


def test_mismatching_expected_trace_uses_accepted_first_divergence_reporting():
    stitch = _stitched_actual()
    expected = _mismatching_expected_artifact(stitch)
    result = validate_stitched_actual_against_golden(
        stitch,
        expected.payload_bytes,
        config=_golden_config(expected.sha256),
    )

    assert result.matches is False
    assert result.validation_result.first_divergence.matches is False
    assert result.validation_result.comparison.mismatch_count >= 1
    text = render_stitched_actual_golden_validation_text(result)
    assert text.startswith("STITCHED_ACTUAL_GOLDEN_FAIL\n")
    assert "GOLDEN_REPLAY_VALIDATION\nGOLDEN_REPLAY_FAIL\n" in text
    assert "FIRST_DIVERGENCE_REPORT\n" in text


def test_expected_digest_failure_propagates_from_accepted_golden_validator():
    stitch = _stitched_actual()
    with pytest.raises(RuntimeTraceDigestMismatchError):
        validate_stitched_actual_against_golden(
            stitch,
            stitch.artifact.payload_bytes,
            config=_golden_config("0" * 64),
        )


def test_constructed_result_rejects_validation_of_different_actual_bytes():
    stitch = _stitched_actual()
    other_actual = _mismatching_expected_artifact(stitch)
    validation = validate_golden_replay_bytes(
        stitch.artifact.payload_bytes,
        other_actual.payload_bytes,
        config=_golden_config(stitch.artifact.sha256),
    )

    with pytest.raises(StitchedGoldenValidationInputError, match="payload bytes"):
        StitchedActualGoldenValidationResult(stitch, validation)


def test_deterministic_text_wraps_stitch_provenance_then_accepted_golden_text():
    stitch = _stitched_actual()
    result = validate_stitched_actual_against_golden(
        stitch,
        stitch.artifact.payload_bytes,
        config=_golden_config(stitch.artifact.sha256),
    )
    first = render_stitched_actual_golden_validation_text(result)
    second = render_stitched_actual_golden_validation_text(result)
    assert first == second
    assert first.startswith("STITCHED_ACTUAL_GOLDEN_PASS\n")
    assert f"stitched_actual_sha256={stitch.artifact.sha256}\n" in first
    assert "segment_count=2\nGOLDEN_REPLAY_VALIDATION\nGOLDEN_REPLAY_PASS\n" in first


def test_input_types_result_and_renderer_are_strict_and_frozen():
    stitch = _stitched_actual()
    config = _golden_config(stitch.artifact.sha256)
    with pytest.raises(StitchedGoldenValidationInputError):
        validate_stitched_actual_against_golden(
            object(), stitch.artifact.payload_bytes, config=config
        )
    with pytest.raises(StitchedGoldenValidationInputError):
        validate_stitched_actual_against_golden(stitch, bytearray(), config=config)
    with pytest.raises(StitchedGoldenValidationInputError):
        validate_stitched_actual_against_golden(
            stitch, stitch.artifact.payload_bytes, config=object()
        )
    with pytest.raises(StitchedGoldenValidationInputError):
        render_stitched_actual_golden_validation_text(object())

    result = validate_stitched_actual_against_golden(
        stitch,
        stitch.artifact.payload_bytes,
        config=config,
    )
    with pytest.raises(FrozenInstanceError):
        result.stitch_result = object()
