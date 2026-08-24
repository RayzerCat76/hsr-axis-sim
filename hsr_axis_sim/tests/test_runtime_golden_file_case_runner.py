from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from hsr_axis_sim.runtime_contracts import RuntimeEvent, RuntimeEventType
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
    build_runtime_trace_artifact,
    build_runtime_trace_document,
)
from hsr_axis_sim.runtime_golden_cases import (
    GoldenReplayFileCase,
    GoldenReplayFileCaseInputError,
    GoldenReplayFileReadError,
    render_golden_replay_file_case_text,
    run_golden_replay_file_case,
)
from hsr_axis_sim.runtime_golden_replays import GoldenReplayValidationConfig
from hsr_axis_sim.runtime_loaders import RuntimeTraceSizeLimitError, TraceCanonicalFormPolicy


def event(sequence, *, event_id, event_type):
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
        {"fixture": "manual"},
    )


def artifact(*, trace_id, second_type=RuntimeEventType.ACTION_END):
    document = build_runtime_trace_document(
        [
            event(0, event_id="manual-event-001", event_type=RuntimeEventType.ACTION_START),
            event(1, event_id="manual-event-002", event_type=second_type),
        ],
        config=TraceExportConfig(
            trace_id,
            TraceSequencePolicy.CONTIGUOUS,
            EmptyTracePolicy.REJECT,
            {"construction": "manual"},
        ),
    )
    return build_runtime_trace_artifact(document, pretty=False)


def make_case(base: Path, *, mismatch=False, max_bytes=100_000):
    case_dir = base / "case"
    case_dir.mkdir()
    expected = artifact(trace_id="manual-golden-001-expected")
    actual = artifact(
        trace_id="manual-golden-001-actual",
        second_type=RuntimeEventType.ACTION_START if mismatch else RuntimeEventType.ACTION_END,
    )
    (case_dir / "expected.json").write_bytes(expected.payload_bytes)
    (case_dir / "actual.json").write_bytes(actual.payload_bytes)
    config = GoldenReplayValidationConfig(
        replay_id="manual-golden-001",
        expected_sha256=expected.sha256,
        canonical_form_policy=TraceCanonicalFormPolicy.EITHER_CANONICAL,
        max_bytes=max_bytes,
    )
    return GoldenReplayFileCase(config, "case/expected.json", "case/actual.json"), expected, actual


def test_matching_file_case_runs_with_resolved_path_provenance(tmp_path):
    case, expected, actual = make_case(tmp_path)
    result = run_golden_replay_file_case(case, base_directory=tmp_path)

    assert result.matches is True
    assert result.replay_id == "manual-golden-001"
    assert result.validation.expected_sha256 == expected.sha256
    assert result.validation.actual_sha256 == actual.sha256
    assert Path(result.base_directory) == tmp_path.resolve()
    assert Path(result.expected_path) == (tmp_path / "case" / "expected.json").resolve()
    assert Path(result.actual_path) == (tmp_path / "case" / "actual.json").resolve()


def test_diverged_file_case_preserves_existing_first_divergence(tmp_path):
    case, _, _ = make_case(tmp_path, mismatch=True)
    result = run_golden_replay_file_case(case, base_directory=tmp_path)

    assert result.matches is False
    divergence = result.validation.first_divergence.divergence
    assert divergence is not None
    assert divergence.record_index == 1
    assert divergence.first_field_difference is not None
    assert divergence.first_field_difference.path == "/event/event_type"


def test_file_case_text_is_repeatable_and_wraps_001b_report(tmp_path):
    case, _, _ = make_case(tmp_path)
    result = run_golden_replay_file_case(case, base_directory=tmp_path)
    first = render_golden_replay_file_case_text(result)
    second = render_golden_replay_file_case_text(result)

    assert first == second
    assert first.startswith("GOLDEN_REPLAY_FILE_CASE_PASS\n")
    assert "GOLDEN_REPLAY_VALIDATION\nGOLDEN_REPLAY_PASS\n" in first
    assert "FIRST_DIVERGENCE_REPORT\nTRACE_MATCH\n" in first


def test_case_paths_must_be_canonical_relative_posix_paths(tmp_path):
    expected = artifact(trace_id="expected")
    config = GoldenReplayValidationConfig(
        "case",
        expected.sha256,
        TraceCanonicalFormPolicy.EITHER_CANONICAL,
        100_000,
    )
    for bad in ("", "../expected.json", "/expected.json", "./expected.json", "a//expected.json", "a\\expected.json"):
        with pytest.raises(GoldenReplayFileCaseInputError):
            GoldenReplayFileCase(config, bad, "actual.json")


def test_missing_base_directory_or_case_file_is_controlled(tmp_path):
    case, _, _ = make_case(tmp_path)
    with pytest.raises(GoldenReplayFileReadError):
        run_golden_replay_file_case(case, base_directory=tmp_path / "missing")

    (tmp_path / "case" / "actual.json").unlink()
    with pytest.raises(GoldenReplayFileReadError):
        run_golden_replay_file_case(case, base_directory=tmp_path)


def test_symlink_escape_from_base_directory_is_rejected(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    expected = artifact(trace_id="expected")
    outside = artifact(trace_id="actual")
    (base / "expected.json").write_bytes(expected.payload_bytes)
    outside_path = tmp_path / "outside.json"
    outside_path.write_bytes(outside.payload_bytes)
    try:
        (base / "actual.json").symlink_to(outside_path)
    except OSError:
        pytest.skip("symlink creation is unavailable on this platform")

    config = GoldenReplayValidationConfig(
        "manual-golden-001",
        expected.sha256,
        TraceCanonicalFormPolicy.EITHER_CANONICAL,
        100_000,
    )
    case = GoldenReplayFileCase(config, "expected.json", "actual.json")
    with pytest.raises(GoldenReplayFileReadError):
        run_golden_replay_file_case(case, base_directory=base)


def test_bounded_read_defers_size_semantics_to_strict_validator(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    expected = artifact(trace_id="expected")
    max_bytes = len(expected.payload_bytes) + 10
    (base / "expected.json").write_bytes(expected.payload_bytes)
    (base / "actual.json").write_bytes(b"x" * (max_bytes + 1))
    config = GoldenReplayValidationConfig(
        "manual-golden-001",
        expected.sha256,
        TraceCanonicalFormPolicy.EITHER_CANONICAL,
        max_bytes,
    )
    case = GoldenReplayFileCase(config, "expected.json", "actual.json")
    with pytest.raises(RuntimeTraceSizeLimitError):
        run_golden_replay_file_case(case, base_directory=base)


def test_file_case_and_run_result_are_frozen(tmp_path):
    case, _, _ = make_case(tmp_path)
    result = run_golden_replay_file_case(case, base_directory=tmp_path)
    with pytest.raises(FrozenInstanceError):
        case.actual_relative_path = "other.json"
    with pytest.raises(FrozenInstanceError):
        result.actual_path = "other"


def test_wrong_runner_and_renderer_input_types_are_rejected(tmp_path):
    with pytest.raises(GoldenReplayFileCaseInputError):
        run_golden_replay_file_case(object(), base_directory=tmp_path)
    with pytest.raises(GoldenReplayFileCaseInputError):
        render_golden_replay_file_case_text(object())
