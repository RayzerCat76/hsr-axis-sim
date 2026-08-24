from dataclasses import FrozenInstanceError
import hashlib
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
from hsr_axis_sim.runtime_golden_batches import GoldenReplayBatchPlan, run_golden_replay_batch
from hsr_axis_sim.runtime_golden_cases import GoldenReplayFileCase, GoldenReplayFileReadError
from hsr_axis_sim.runtime_golden_manifest_files import GoldenReplayManifestFileSpec
from hsr_axis_sim.runtime_golden_manifest_runs import (
    GoldenReplayManifestBatchRunResult,
    GoldenReplayManifestRunInputError,
    render_golden_replay_manifest_batch_text,
    run_golden_replay_manifest_batch,
)
from hsr_axis_sim.runtime_golden_manifests import (
    GoldenReplayManifestDigestMismatchError,
    build_golden_replay_manifest_artifact,
)
from hsr_axis_sim.runtime_golden_replays import GoldenReplayValidationConfig
from hsr_axis_sim.runtime_loaders import TraceCanonicalFormPolicy


def _event(sequence, *, event_id, event_type):
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


def _trace_artifact(*, trace_id, second_type=RuntimeEventType.ACTION_END):
    document = build_runtime_trace_document(
        [
            _event(0, event_id=f"{trace_id}-event-0", event_type=RuntimeEventType.ACTION_START),
            _event(1, event_id=f"{trace_id}-event-1", event_type=second_type),
        ],
        config=TraceExportConfig(
            trace_id,
            TraceSequencePolicy.CONTIGUOUS,
            EmptyTracePolicy.REJECT,
            {"construction": "manual"},
        ),
    )
    return build_runtime_trace_artifact(document, pretty=False)


def _write_case(base, replay_id, *, mismatch=False):
    directory = base / "cases" / replay_id
    directory.mkdir(parents=True)
    expected = _trace_artifact(trace_id=f"{replay_id}-expected")
    actual_events = [record.event for record in expected.document.records]
    if mismatch:
        second = actual_events[1]
        actual_events[1] = RuntimeEvent(
            second.event_id,
            RuntimeEventType.ACTION_START,
            second.sequence,
            second.action_id,
            second.attack_id,
            second.hit_id,
            second.actor_id,
            second.source_id,
            second.target_id,
            second.payload,
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
    (directory / "expected.json").write_bytes(expected.payload_bytes)
    (directory / "actual.json").write_bytes(actual.payload_bytes)
    return GoldenReplayFileCase(
        GoldenReplayValidationConfig(
            replay_id,
            expected.sha256,
            TraceCanonicalFormPolicy.EITHER_CANONICAL,
            100_000,
        ),
        f"cases/{replay_id}/expected.json",
        f"cases/{replay_id}/actual.json",
    )


def _write_manifest(base, cases, *, batch_id="manifest-batch-001"):
    plan = GoldenReplayBatchPlan(batch_id, tuple(cases))
    artifact = build_golden_replay_manifest_artifact(plan)
    path = base / "manifests" / "batch.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(artifact.payload_bytes)
    spec = GoldenReplayManifestFileSpec(
        "manifests/batch.json",
        100_000,
        artifact.sha256,
    )
    return plan, artifact, spec, path


def test_manifest_backed_batch_runs_declared_plan_under_same_resolved_base(tmp_path):
    cases = (
        _write_case(tmp_path, "case-a"),
        _write_case(tmp_path, "case-b", mismatch=True),
        _write_case(tmp_path, "case-c"),
    )
    plan, artifact, spec, manifest_path = _write_manifest(tmp_path, cases)

    result = run_golden_replay_manifest_batch(spec, base_directory=tmp_path)

    assert result.manifest_load.artifact == artifact
    assert result.manifest_load.manifest_path == str(manifest_path.resolve())
    assert result.batch_result.plan == plan
    assert result.batch_result.base_directory == result.manifest_load.base_directory
    assert [item.replay_id for item in result.batch_result.results] == ["case-a", "case-b", "case-c"]
    assert [item.matches for item in result.batch_result.results] == [True, False, True]
    assert result.matches is False
    assert result.batch_id == "manifest-batch-001"
    assert result.case_count == 3
    assert result.batch_result.first_mismatch_index == 1


def test_all_matching_manifest_batch_is_match(tmp_path):
    cases = (_write_case(tmp_path, "case-a"), _write_case(tmp_path, "case-b"))
    _, _, spec, _ = _write_manifest(tmp_path, cases, batch_id="all-match")

    result = run_golden_replay_manifest_batch(spec, base_directory=tmp_path)

    assert result.matches is True
    assert result.batch_result.matched_case_count == 2
    assert result.batch_result.mismatched_case_count == 0
    assert result.batch_result.first_mismatch_index is None


def test_deterministic_text_wraps_accepted_manifest_file_and_batch_reports(tmp_path):
    cases = (_write_case(tmp_path, "case-a"), _write_case(tmp_path, "case-b", mismatch=True))
    _, artifact, spec, _ = _write_manifest(tmp_path, cases, batch_id="text-batch")
    result = run_golden_replay_manifest_batch(spec, base_directory=tmp_path)

    first = render_golden_replay_manifest_batch_text(result)
    second = render_golden_replay_manifest_batch_text(result)

    assert first == second
    assert first.startswith("GOLDEN_REPLAY_MANIFEST_BATCH_FAIL\nMANIFEST_FILE\n")
    assert "GOLDEN_REPLAY_MANIFEST_FILE_LOADED\n" in first
    assert f"manifest_sha256={artifact.sha256}\n" in first
    assert "\nBATCH\nGOLDEN_REPLAY_BATCH_FAIL\n" in first
    assert first.index("\nMANIFEST_FILE\n") < first.index("\nBATCH\n")
    assert first.index('CASE index=0 replay_id="case-a"') < first.index('CASE index=1 replay_id="case-b"')


def test_bad_manifest_digest_fails_before_batch_execution(tmp_path, monkeypatch):
    cases = (_write_case(tmp_path, "case-a"),)
    _, _, _, _ = _write_manifest(tmp_path, cases)
    bad_spec = GoldenReplayManifestFileSpec("manifests/batch.json", 100_000, "0" * 64)

    module = importlib.import_module("hsr_axis_sim.runtime_golden_manifest_runs.run")
    calls = []

    def forbidden_batch(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("batch must not run when manifest loading fails")

    monkeypatch.setattr(module, "run_golden_replay_batch", forbidden_batch)
    with pytest.raises(GoldenReplayManifestDigestMismatchError):
        module.run_golden_replay_manifest_batch(bad_spec, base_directory=tmp_path)
    assert calls == []


def test_case_operational_failure_propagates_without_partial_composition_result(tmp_path):
    first = _write_case(tmp_path, "case-a")
    second = _write_case(tmp_path, "case-b")
    third = _write_case(tmp_path, "case-c")
    _, _, spec, _ = _write_manifest(tmp_path, (first, second, third))
    (tmp_path / second.actual_relative_path).unlink()

    with pytest.raises(GoldenReplayFileReadError):
        run_golden_replay_manifest_batch(spec, base_directory=tmp_path)


def test_result_is_frozen_and_rejects_plan_or_base_misalignment(tmp_path):
    cases = (_write_case(tmp_path, "case-a"),)
    _, _, spec, _ = _write_manifest(tmp_path, cases)
    result = run_golden_replay_manifest_batch(spec, base_directory=tmp_path)

    with pytest.raises(FrozenInstanceError):
        result.batch_result = object()

    other_base = tmp_path / "other"
    other_base.mkdir()
    other_case = _write_case(other_base, "other-case")
    other_batch = run_golden_replay_batch(
        GoldenReplayBatchPlan("other-batch", (other_case,)),
        base_directory=other_base,
    )
    with pytest.raises(GoldenReplayManifestRunInputError, match="plan"):
        GoldenReplayManifestBatchRunResult(result.manifest_load, other_batch)

    same_plan_other_base = tmp_path / "same-plan-other-base"
    same_plan_other_base.mkdir()
    same_case = _write_case(same_plan_other_base, "case-a")
    same_batch = run_golden_replay_batch(
        GoldenReplayBatchPlan("manifest-batch-001", (same_case,)),
        base_directory=same_plan_other_base,
    )
    with pytest.raises(GoldenReplayManifestRunInputError, match="base_directory"):
        GoldenReplayManifestBatchRunResult(result.manifest_load, same_batch)


def test_runner_and_renderer_reject_wrong_input_types(tmp_path):
    with pytest.raises(GoldenReplayManifestRunInputError):
        run_golden_replay_manifest_batch(object(), base_directory=tmp_path)
    with pytest.raises(GoldenReplayManifestRunInputError):
        render_golden_replay_manifest_batch_text(object())
