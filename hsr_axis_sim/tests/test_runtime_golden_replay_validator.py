from dataclasses import FrozenInstanceError
import hashlib

import pytest

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
    GoldenReplayValidationInputError,
    render_golden_replay_validation_text,
    validate_golden_replay_bytes,
)
from hsr_axis_sim.runtime_loaders import (
    RuntimeTraceCanonicalityError,
    RuntimeTraceDigestMismatchError,
    TraceCanonicalFormPolicy,
    TraceDigestStatus,
)


def event(sequence, *, event_id, event_type, payload=None):
    return RuntimeEvent(
        event_id,
        event_type,
        sequence,
        "manual-action-001",
        None,
        None,
        "manual-actor",
        "manual-actor",
        None,
        payload or {"fixture": "manual"},
    )


def artifact(events, *, trace_id, metadata=None, pretty=False):
    document = build_runtime_trace_document(
        events,
        config=TraceExportConfig(
            trace_id,
            TraceSequencePolicy.CONTIGUOUS,
            EmptyTracePolicy.REJECT,
            metadata or {},
        ),
    )
    return build_runtime_trace_artifact(document, pretty=pretty)


def manual_golden_artifact(*, pretty=False):
    return artifact(
        [
            event(0, event_id="manual-event-001", event_type=RuntimeEventType.ACTION_START),
            event(1, event_id="manual-event-002", event_type=RuntimeEventType.ACTION_END),
        ],
        trace_id="manual-golden-001-expected",
        metadata={"construction": "manual", "purpose": "contract-fixture"},
        pretty=pretty,
    )


def config_for(expected):
    return GoldenReplayValidationConfig(
        replay_id="manual-golden-001",
        expected_sha256=expected.sha256,
        canonical_form_policy=TraceCanonicalFormPolicy.EITHER_CANONICAL,
        max_bytes=100_000,
    )


def test_manually_constructed_golden_replay_matches_deterministically():
    expected = manual_golden_artifact()
    actual = artifact(
        list(expected.document.records[index].event for index in range(expected.document.record_count)),
        trace_id="manual-golden-001-actual",
        metadata={"source": "deterministic-test-output"},
    )

    result = validate_golden_replay_bytes(
        expected.payload_bytes,
        actual.payload_bytes,
        config=config_for(expected),
    )

    assert result.matches is True
    assert result.comparison.matches is True
    assert result.first_divergence.matches is True
    assert result.expected_sha256 == expected.sha256
    assert result.actual_sha256 == actual.sha256
    assert result.expected_load.digest_status is TraceDigestStatus.MATCHED
    assert result.actual_load.digest_status is TraceDigestStatus.NOT_PROVIDED


def test_record_field_mismatch_propagates_existing_first_divergence():
    expected = manual_golden_artifact()
    actual = artifact(
        [
            event(0, event_id="manual-event-001", event_type=RuntimeEventType.ACTION_START),
            event(1, event_id="manual-event-002", event_type=RuntimeEventType.ACTION_START),
        ],
        trace_id="manual-golden-001-actual",
    )

    result = validate_golden_replay_bytes(
        expected.payload_bytes,
        actual.payload_bytes,
        config=config_for(expected),
    )

    assert result.matches is False
    divergence = result.first_divergence.divergence
    assert divergence is not None
    assert divergence.record_index == 1
    assert divergence.first_field_difference is not None
    assert divergence.first_field_difference.path == "/event/event_type"
    assert divergence.first_field_difference.expected_value == RuntimeEventType.ACTION_END.value
    assert divergence.first_field_difference.actual_value == RuntimeEventType.ACTION_START.value


def test_expected_golden_sha_mismatch_is_rejected_by_strict_loader():
    expected = manual_golden_artifact()
    actual = manual_golden_artifact()
    bad = GoldenReplayValidationConfig(
        replay_id="manual-golden-001",
        expected_sha256="0" * 64,
        canonical_form_policy=TraceCanonicalFormPolicy.EITHER_CANONICAL,
        max_bytes=100_000,
    )
    with pytest.raises(RuntimeTraceDigestMismatchError):
        validate_golden_replay_bytes(expected.payload_bytes, actual.payload_bytes, config=bad)


def test_noncanonical_expected_input_is_rejected_after_digest_validation():
    expected = manual_golden_artifact()
    noncanonical = expected.payload_bytes + b"\n"
    config = GoldenReplayValidationConfig(
        replay_id="manual-golden-001",
        expected_sha256=hashlib.sha256(noncanonical).hexdigest(),
        canonical_form_policy=TraceCanonicalFormPolicy.EITHER_CANONICAL,
        max_bytes=100_000,
    )
    with pytest.raises(RuntimeTraceCanonicalityError):
        validate_golden_replay_bytes(noncanonical, expected.payload_bytes, config=config)


def test_noncanonical_actual_input_is_rejected():
    expected = manual_golden_artifact()
    with pytest.raises(RuntimeTraceCanonicalityError):
        validate_golden_replay_bytes(
            expected.payload_bytes,
            expected.payload_bytes + b"\n",
            config=config_for(expected),
        )


def test_config_validation_is_strict_and_model_is_frozen():
    expected = manual_golden_artifact()
    valid = config_for(expected)
    with pytest.raises(FrozenInstanceError):
        valid.max_bytes = 1
    with pytest.raises(GoldenReplayValidationInputError):
        GoldenReplayValidationConfig("", expected.sha256, TraceCanonicalFormPolicy.EITHER_CANONICAL, 100)
    with pytest.raises(GoldenReplayValidationInputError):
        GoldenReplayValidationConfig("x", "BAD", TraceCanonicalFormPolicy.EITHER_CANONICAL, 100)
    with pytest.raises(GoldenReplayValidationInputError):
        GoldenReplayValidationConfig("x", expected.sha256, "EITHER_CANONICAL", 100)
    with pytest.raises(GoldenReplayValidationInputError):
        GoldenReplayValidationConfig("x", expected.sha256, TraceCanonicalFormPolicy.EITHER_CANONICAL, 0)
    with pytest.raises(GoldenReplayValidationInputError):
        GoldenReplayValidationConfig("x", expected.sha256, TraceCanonicalFormPolicy.EITHER_CANONICAL, True)


def test_result_is_frozen_and_text_is_repeatable():
    expected = manual_golden_artifact(pretty=True)
    actual = artifact(
        [record.event for record in expected.document.records],
        trace_id="manual-golden-001-actual",
        pretty=True,
    )
    result = validate_golden_replay_bytes(
        expected.payload_bytes,
        actual.payload_bytes,
        config=config_for(expected),
    )
    first = render_golden_replay_validation_text(result)
    second = render_golden_replay_validation_text(result)
    assert first == second
    assert first.startswith("GOLDEN_REPLAY_PASS\n")
    assert "expected_digest_status=MATCHED\n" in first
    assert "actual_digest_status=NOT_PROVIDED\n" in first
    assert "FIRST_DIVERGENCE_REPORT\nTRACE_MATCH\n" in first
    with pytest.raises(FrozenInstanceError):
        result.comparison = object()


def test_wrong_validator_and_renderer_input_types_are_rejected():
    expected = manual_golden_artifact()
    with pytest.raises(GoldenReplayValidationInputError):
        validate_golden_replay_bytes(expected.payload_bytes, expected.payload_bytes, config=object())
    with pytest.raises(GoldenReplayValidationInputError):
        render_golden_replay_validation_text(object())
