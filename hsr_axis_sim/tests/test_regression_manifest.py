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
EXPECTED_SHA256 = "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66"


def test_loading_default_manifest_succeeds():
    manifest = load_regression_manifest(MANIFEST_PATH)

    assert manifest.manifest_id == "HSR_AXIS_REGRESSION_BASELINE_001Z"
    assert manifest.counts_by_group() == {
        "replays": 12,
        "manual": 1,
        "scenarios": 2,
        "action_sequence_traces": 1,
        "runtime_action_sessions": 1,
        "trace_evidence": 2,
    }
    action_sequence_entries = manifest.groups["action_sequence_traces"]
    assert action_sequence_entries[0].id == (
        "real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only"
    )
    assert action_sequence_entries[0].checks == ["lint", "action_sequence"]
    runtime_entries = manifest.groups["runtime_action_sessions"]
    assert len(runtime_entries) == 1
    assert runtime_entries[0].id == "arch-017-reviewed-static-action-session"
    assert runtime_entries[0].expected_sha256 == EXPECTED_SHA256
    assert runtime_entries[0].stream_id == "arch-017-reviewed-static"
    assert runtime_entries[0].actor_id == "reviewed-actor"
    assert [action.action_id for action in runtime_entries[0].actions] == [
        "reviewed-action-a",
        "reviewed-action-b",
    ]
    assert [action.ends_turn for action in runtime_entries[0].actions] == [False, False]
    assert {entry.check for entry in manifest.groups["trace_evidence"]} == {
        "semantic_map", "frame_anchors"
    }


def test_manifest_mode_regression_passes_with_default_manifest():
    manifest = load_regression_manifest(MANIFEST_PATH)

    report = run_regression(manifest=manifest)

    assert report.passed is True
    assert report.total == 21
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
    assert payload["manifest_counts"]["runtime_action_sessions"] == 1
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


def test_manifest_only_runtime_action_sessions_runs_arch_016_golden_check():
    manifest = load_regression_manifest(MANIFEST_PATH)

    report = run_regression(manifest=manifest, only="runtime_action_sessions")

    assert report.passed is True
    assert report.total == 1
    assert {result.group for result in report.results} == {"runtime_action_sessions"}
    result = report.results[0]
    assert result.name == "arch-017-reviewed-static-action-session"
    assert result.details["check"] == "runtime_action_session_golden"
    assert result.details["action_count"] == 2
    assert result.details["record_count"] == 4
    assert result.details["expected_sha256"] == EXPECTED_SHA256


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


def test_manifest_without_runtime_action_session_group_is_backward_compatible():
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
        "runtime_action_sessions": 0,
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


def test_runtime_action_session_requires_lowercase_sha256():
    data = _runtime_action_session_manifest_entry()
    data["groups"]["runtime_action_sessions"][0]["expected_sha256"] = "A" * 64

    try:
        regression_manifest_from_dict(data, manifest_path=Path("bad.json"))
    except ValueError as exc:
        assert "expected_sha256" in str(exc)
    else:
        raise AssertionError("Expected invalid digest failure.")


def test_runtime_action_session_requires_nonempty_actions():
    data = _runtime_action_session_manifest_entry()
    data["groups"]["runtime_action_sessions"][0]["actions"] = []

    try:
        regression_manifest_from_dict(data, manifest_path=Path("bad.json"))
    except ValueError as exc:
        assert ".actions" in str(exc)
    else:
        raise AssertionError("Expected empty actions failure.")


def test_runtime_action_session_action_object_is_strict():
    data = _runtime_action_session_manifest_entry()
    action = data["groups"]["runtime_action_sessions"][0]["actions"][0]
    action["effects"] = []

    try:
        regression_manifest_from_dict(data, manifest_path=Path("bad.json"))
    except ValueError as exc:
        assert "unsupported field" in str(exc)
    else:
        raise AssertionError("Expected unsupported action field failure.")


def test_runtime_action_session_ends_turn_requires_boolean():
    data = _runtime_action_session_manifest_entry()
    data["groups"]["runtime_action_sessions"][0]["actions"][0]["ends_turn"] = 0

    try:
        regression_manifest_from_dict(data, manifest_path=Path("bad.json"))
    except ValueError as exc:
        assert "ends_turn" in str(exc)
    else:
        raise AssertionError("Expected invalid ends_turn failure.")


def test_runtime_action_session_missing_expected_path_is_rejected():
    data = _runtime_action_session_manifest_entry()
    data["groups"]["runtime_action_sessions"][0]["path"] = (
        "hsr_axis_sim/data/runtime_golden_fixtures/not_here.json"
    )

    try:
        regression_manifest_from_dict(data, manifest_path=Path("bad.json"))
    except ValueError as exc:
        assert "does not exist" in str(exc)
    else:
        raise AssertionError("Expected missing runtime fixture path failure.")


def test_manifest_json_renderer_includes_metadata():
    report = run_regression(manifest=load_regression_manifest(MANIFEST_PATH))

    payload = json.loads(format_regression_json(report))

    assert payload["manifest_id"] == "HSR_AXIS_REGRESSION_BASELINE_001Z"
    assert payload["manifest_counts"]["scenarios"] == 2
    assert payload["manifest_counts"]["action_sequence_traces"] == 1
    assert payload["manifest_counts"]["runtime_action_sessions"] == 1
    assert payload["manifest_counts"]["trace_evidence"] == 2


def test_manifest_text_and_markdown_reports_include_runtime_and_trace_evidence():
    report = run_regression(manifest=load_regression_manifest(MANIFEST_PATH))

    text = format_regression_text(report)
    assert "PASS 1/1 runtime action-session Golden checks" in text
    assert "PASS 2/2 trace evidence checks" in text
    markdown = format_regression_markdown(report)
    assert "| runtime_action_sessions | 1 | 0 | 1 |" in markdown
    assert "| trace_evidence | 2 | 0 | 2 |" in markdown
    assert "runtime_action_sessions=1" in markdown
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


def _runtime_action_session_manifest_entry():
    return {
        "manifest_id": "runtime",
        "project": "hsr-axis-simulator",
        "description": "runtime",
        "groups": {
            "runtime_action_sessions": [
                {
                    "id": "arch-017-reviewed-static-action-session",
                    "path": "hsr_axis_sim/data/runtime_golden_fixtures/arch_017_reviewed_action_session_expected.json",
                    "expected_sha256": EXPECTED_SHA256,
                    "stream_id": "arch-017-reviewed-static",
                    "actor_id": "reviewed-actor",
                    "actions": [
                        {
                            "action_id": "reviewed-action-a",
                            "name": "reviewed-action-a",
                            "ends_turn": False,
                        },
                        {
                            "action_id": "reviewed-action-b",
                            "name": "reviewed-action-b",
                            "ends_turn": False,
                        },
                    ],
                }
            ]
        },
    }


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
