from dataclasses import FrozenInstanceError
import importlib

import pytest

from hsr_axis_sim.runtime_contracts import RuntimeEvent, RuntimeEventType
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
    build_runtime_trace_artifact,
    build_runtime_trace_document,
)
from hsr_axis_sim.runtime_golden_batches import (
    GoldenReplayBatchInputError,
    GoldenReplayBatchPlan,
    GoldenReplayBatchResult,
    render_golden_replay_batch_text,
    run_golden_replay_batch,
)
from hsr_axis_sim.runtime_golden_cases import GoldenReplayFileCase, GoldenReplayFileReadError
from hsr_axis_sim.runtime_golden_replays import GoldenReplayValidationConfig
from hsr_axis_sim.runtime_loaders import TraceCanonicalFormPolicy


def event(sequence, *, event_id, event_type):
    return RuntimeEvent(
        event_id,
        event_type,
        sequence,
        f"action-{sequence}",
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
            event(0, event_id=f"{trace_id}-event-0", event_type=RuntimeEventType.ACTION_START),
            event(1, event_id=f"{trace_id}-event-1", event_type=second_type),
        ],
        config=TraceExportConfig(
            trace_id,
            TraceSequencePolicy.CONTIGUOUS,
            EmptyTracePolicy.REJECT,
            {"construction": "manual"},
        ),
    )
    return build_runtime_trace_artifact(document, pretty=False)


def write_case(base, replay_id, *, mismatch=False):
    directory = base / "cases" / replay_id
    directory.mkdir(parents=True)
    expected = artifact(trace_id=f"{replay_id}-expected")
    actual_events = [record.event for record in expected.document.records]
    if mismatch:
        actual_events[1] = RuntimeEvent(
            actual_events[1].event_id,
            RuntimeEventType.ACTION_START,
            actual_events[1].sequence,
            actual_events[1].action_id,
            actual_events[1].attack_id,
            actual_events[1].hit_id,
            actual_events[1].actor_id,
            actual_events[1].source_id,
            actual_events[1].target_id,
            actual_events[1].payload,
        )
    actual_document = build_runtime_trace_document(
        actual_events,
        config=TraceExportConfig(
            f"{replay_id}-actual",
            TraceSequencePolicy.CONTIGUOUS,
            EmptyTracePolicy.REJECT,
            {"construction": "manual-actual"},
        ),
    )
    actual = build_runtime_trace_artifact(actual_document, pretty=False)
    expected_path = directory / "expected.json"
    actual_path = directory / "actual.json"
    expected_path.write_bytes(expected.payload_bytes)
    actual_path.write_bytes(actual.payload_bytes)
    config = GoldenReplayValidationConfig(
        replay_id,
        expected.sha256,
        TraceCanonicalFormPolicy.EITHER_CANONICAL,
        100_000,
    )
    return GoldenReplayFileCase(
        config,
        f"cases/{replay_id}/expected.json",
        f"cases/{replay_id}/actual.json",
    )


def test_batch_runs_in_declared_order_and_mismatch_does_not_stop_later_cases(tmp_path):
    cases = (
        write_case(tmp_path, "case-a"),
        write_case(tmp_path, "case-b", mismatch=True),
        write_case(tmp_path, "case-c"),
    )
    plan = GoldenReplayBatchPlan("batch-001", cases)

    result = run_golden_replay_batch(plan, base_directory=tmp_path)

    assert [item.replay_id for item in result.results] == ["case-a", "case-b", "case-c"]
    assert [item.matches for item in result.results] == [True, False, True]
    assert result.matches is False
    assert result.matched_case_count == 2
    assert result.mismatched_case_count == 1
    assert result.first_mismatch_index == 1


def test_all_matching_batch_has_no_first_mismatch(tmp_path):
    plan = GoldenReplayBatchPlan(
        "batch-match",
        (write_case(tmp_path, "case-a"), write_case(tmp_path, "case-b")),
    )
    result = run_golden_replay_batch(plan, base_directory=tmp_path)
    assert result.matches is True
    assert result.matched_case_count == 2
    assert result.mismatched_case_count == 0
    assert result.first_mismatch_index is None


def test_batch_plan_rejects_empty_non_tuple_wrong_type_and_duplicate_replay_ids(tmp_path):
    case = write_case(tmp_path, "case-a")
    with pytest.raises(GoldenReplayBatchInputError):
        GoldenReplayBatchPlan("", (case,))
    with pytest.raises(GoldenReplayBatchInputError):
        GoldenReplayBatchPlan("batch", ())
    with pytest.raises(GoldenReplayBatchInputError):
        GoldenReplayBatchPlan("batch", [case])
    with pytest.raises(GoldenReplayBatchInputError):
        GoldenReplayBatchPlan("batch", (case, object()))
    with pytest.raises(GoldenReplayBatchInputError):
        GoldenReplayBatchPlan("batch", (case, case))


def test_operational_exception_is_fail_fast_at_exact_case(tmp_path, monkeypatch):
    first = write_case(tmp_path, "case-a")
    second = write_case(tmp_path, "case-b")
    third = write_case(tmp_path, "case-c")
    (tmp_path / second.actual_relative_path).unlink()
    plan = GoldenReplayBatchPlan("batch-fail-fast", (first, second, third))

    module = importlib.import_module("hsr_axis_sim.runtime_golden_batches.run")
    original = module.run_golden_replay_file_case
    calls = []

    def recording_runner(case, *, base_directory):
        calls.append(case.replay_id)
        return original(case, base_directory=base_directory)

    monkeypatch.setattr(module, "run_golden_replay_file_case", recording_runner)
    with pytest.raises(GoldenReplayFileReadError):
        module.run_golden_replay_batch(plan, base_directory=tmp_path)
    assert calls == ["case-a", "case-b"]


def test_batch_text_is_repeatable_and_case_reports_follow_declared_order(tmp_path):
    plan = GoldenReplayBatchPlan(
        "batch-text",
        (
            write_case(tmp_path, "case-a"),
            write_case(tmp_path, "case-b", mismatch=True),
            write_case(tmp_path, "case-c"),
        ),
    )
    result = run_golden_replay_batch(plan, base_directory=tmp_path)
    first = render_golden_replay_batch_text(result)
    second = render_golden_replay_batch_text(result)

    assert first == second
    assert first.startswith("GOLDEN_REPLAY_BATCH_FAIL\n")
    assert "case_count=3\nmatched_case_count=2\nmismatched_case_count=1\nfirst_mismatch_index=1\n" in first
    positions = [first.index(f'CASE index={index} replay_id="{name}"') for index, name in enumerate(("case-a", "case-b", "case-c"))]
    assert positions == sorted(positions)


def test_batch_plan_and_result_are_frozen_and_result_alignment_is_strict(tmp_path):
    cases = (write_case(tmp_path, "case-a"), write_case(tmp_path, "case-b"))
    plan = GoldenReplayBatchPlan("batch-frozen", cases)
    result = run_golden_replay_batch(plan, base_directory=tmp_path)
    with pytest.raises(FrozenInstanceError):
        plan.batch_id = "other"
    with pytest.raises(FrozenInstanceError):
        result.results = ()
    with pytest.raises(GoldenReplayBatchInputError):
        GoldenReplayBatchResult(plan, result.base_directory, tuple(reversed(result.results)))
    with pytest.raises(GoldenReplayBatchInputError):
        GoldenReplayBatchResult(plan, result.base_directory, result.results[:1])


def test_wrong_runner_and_renderer_input_types_are_rejected(tmp_path):
    with pytest.raises(GoldenReplayBatchInputError):
        run_golden_replay_batch(object(), base_directory=tmp_path)
    with pytest.raises(GoldenReplayBatchInputError):
        render_golden_replay_batch_text(object())
