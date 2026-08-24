import contextlib
import io
import json
from pathlib import Path

from hsr_axis_sim.regression.manifest import (
    load_regression_manifest,
    regression_manifest_from_dict,
)
from hsr_axis_sim.regression.runner import (
    format_regression_markdown,
    format_regression_text,
    format_regression_json,
    main,
    run_regression,
)


MANIFEST_PATH = "hsr_axis_sim/data/regression_manifest.json"


def test_loading_default_manifest_succeeds():
    manifest = load_regression_manifest(MANIFEST_PATH)

    assert manifest.manifest_id == "HSR_AXIS_REGRESSION_BASELINE_001Z"
    assert manifest.counts_by_group() == {
        "replays": 12,
        "manual": 1,
        "scenarios": 2,
        "action_sequence_traces": 1,
        "trace_evidence": 2,
    }
    action_sequence_entries = manifest.groups["action_sequence_traces"]
    assert action_sequence_entries[0].id == (
        "real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only"
    )
    assert action_sequence_entries[0].checks == ["lint", "action_sequence"]
    assert {entry.check for entry in manifest.groups["trace_evidence"]} == {
        "semantic_map", "frame_anchors"
    }


def test_manifest_mode_regression_passes_with_default_manifest():
    manifest = load_regression_manifest(MANIFEST_PATH)

    report = run_regression(manifest=manifest)

    assert report.passed is True
    assert report.total == 20
    assert report.manifest_id == "HSR_AXIS_REGRESSION_BASELINE_001Z"


def test_manifest_cli_json_includes_metadata():
    stdout = io.StringIO()

    with contextlib.redirect_stdout(stdout):
        result = main(["--manifest", MANIFEST_PATH, "--format", "json"])

    payload = json.loads(stdout.getvalue())
    assert result == 0
    assert payload["manifest_id"] == "HSR_AXIS_REGRESSION_BASELINE_001Z"
    assert payload["manifest_counts"]["replays"] == 12
    assert payload["manifest_counts"]["action_sequence_traces"] == 1
    assert payload["manifest_counts"]["trace_evidence"] == 2


def test_manifest_only_replays_runs_replay_checks_only():
    manifest = load_regression_manifest(MANIFEST_PATH)

    report = run_regression(manifest=manifest, only="replays")

    assert report.passed is True
    assert report.total == 12
    assert {result.group for result in report.results} == {"replays"}


def test_manifest_only_action_sequence_traces_runs_lint_and_sequence_checks():
    manifest = load_regression_manifest(MANIFEST_PATH)

    report = run_regression(manifest=manifest, only="action_sequence_traces")

    assert report.passed is True
    assert report.total == 2
    assert {result.group for result in report.results} == {"action_sequence_traces"}
    assert {result.details["check"] for result in report.results} == {
        "lint",
        "action_sequence",
    }
    action_sequence_result = next(
        result for result in report.results if result.details["check"] == "action_sequence"
    )
    assert action_sequence_result.details["checked_steps"] == 9


def test_manifest_only_trace_evidence_runs_evidence_checks():
    manifest = load_regression_manifest(MANIFEST_PATH)

    report = run_regression(manifest=manifest, only="trace_evidence")

    assert report.passed is True
    assert report.total == 2
    assert {result.group for result in report.results} == {"trace_evidence"}
    assert {result.details["check"] for result in report.results} == {
        "semantic_map", "frame_anchors"
    }


def test_duplicate_entry_ids_are_rejected():
    data = {
        "manifest_id": "bad",
        "project": "hsr-axis-simulator",
        "description": "bad",
        "groups": {
            "replays": [
                {
                    "id": "dup",
                    "path": "hsr_axis_sim/data/golden_replays/bronya_seele_timeline_mvp.json",
                },
                {
                    "id": "dup",
                    "path": "hsr_axis_sim/data/golden_replays/bronya_seele_timeline_mvp.json",
                },
            ]
        },
    }

    try:
        regression_manifest_from_dict(data, manifest_path=Path("bad.json"))
    except ValueError as exc:
        assert "Duplicate manifest id" in str(exc)
    else:
        raise AssertionError("Expected duplicate manifest id failure.")


def test_missing_fixture_path_is_rejected():
    data = {
        "manifest_id": "bad",
        "project": "hsr-axis-simulator",
        "description": "bad",
        "groups": {
            "replays": [
                {"id": "missing", "path": "hsr_axis_sim/data/golden_replays/not_here.json"}
            ]
        },
    }

    try:
        regression_manifest_from_dict(data, manifest_path=Path("bad.json"))
    except ValueError as exc:
        assert "does not exist" in str(exc)
    else:
        raise AssertionError("Expected missing fixture path failure.")


def test_invalid_group_name_is_rejected():
    data = {
        "manifest_id": "bad",
        "project": "hsr-axis-simulator",
        "description": "bad",
        "groups": {"unknown": []},
    }

    try:
        regression_manifest_from_dict(data, manifest_path=Path("bad.json"))
    except ValueError as exc:
        assert "Unsupported manifest group" in str(exc)
    else:
        raise AssertionError("Expected unsupported group failure.")


def test_manifest_without_action_sequence_group_is_backward_compatible():
    data = {
        "manifest_id": "old",
        "project": "hsr-axis-simulator",
        "description": "old manifest",
        "groups": {
            "replays": [],
            "manual": [],
            "scenarios": [],
        },
    }

    manifest = regression_manifest_from_dict(data, manifest_path=Path("old.json"))

    assert manifest.counts_by_group() == {
        "replays": 0,
        "manual": 0,
        "scenarios": 0,
        "action_sequence_traces": 0,
        "trace_evidence": 0,
    }


def test_action_sequence_group_requires_supported_checks():
    data = {
        "manifest_id": "bad",
        "project": "hsr-axis-simulator",
        "description": "bad",
        "groups": {
            "action_sequence_traces": [
                {
                    "id": "bad_checks",
                    "path": "hsr_axis_sim/data/manual_video_traces/intake/real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only.json",
                    "checks": ["lint"],
                }
            ]
        },
    }

    try:
        regression_manifest_from_dict(data, manifest_path=Path("bad.json"))
    except ValueError as exc:
        assert "must include both" in str(exc)
    else:
        raise AssertionError("Expected action_sequence check validation failure.")


def test_manifest_json_renderer_includes_metadata():
    report = run_regression(manifest=load_regression_manifest(MANIFEST_PATH))

    payload = json.loads(format_regression_json(report))

    assert payload["manifest_id"] == "HSR_AXIS_REGRESSION_BASELINE_001Z"
    assert payload["manifest_counts"]["scenarios"] == 2
    assert payload["manifest_counts"]["action_sequence_traces"] == 1
    assert payload["manifest_counts"]["trace_evidence"] == 2


def test_manifest_text_and_markdown_reports_include_trace_evidence():
    report = run_regression(manifest=load_regression_manifest(MANIFEST_PATH))

    assert "PASS 2/2 trace evidence checks" in format_regression_text(report)
    markdown = format_regression_markdown(report)
    assert "| trace_evidence | 2 | 0 | 2 |" in markdown
    assert "trace_evidence=2" in markdown


def test_trace_evidence_requires_supported_check():
    data = _trace_evidence_manifest_entry(check="unknown")

    try:
        regression_manifest_from_dict(data, manifest_path=Path("bad.json"))
    except ValueError as exc:
        assert ".check" in str(exc)
    else:
        raise AssertionError("Expected unsupported trace evidence check failure.")


def test_trace_evidence_requires_source_trace_path():
    data = _trace_evidence_manifest_entry()
    del data["groups"]["trace_evidence"][0]["source_trace_path"]

    try:
        regression_manifest_from_dict(data, manifest_path=Path("bad.json"))
    except ValueError as exc:
        assert "source_trace_path" in str(exc)
    else:
        raise AssertionError("Expected missing source trace path failure.")


def _trace_evidence_manifest_entry(check="semantic_map"):
    return {
        "manifest_id": "bad",
        "project": "hsr-axis-simulator",
        "description": "bad",
        "groups": {
            "trace_evidence": [{
                "id": "evidence",
                "path": "hsr_axis_sim/data/manual_video_traces/semantic_maps/real_video_trace_001_botu_dilemma_semantics_v0_1.json",
                "source_trace_path": "hsr_axis_sim/data/manual_video_traces/intake/real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only.json",
                "check": check,
            }]
        },
    }
