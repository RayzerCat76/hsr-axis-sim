import contextlib
import io
import json
from pathlib import Path

from hsr_axis_sim.regression.runner import (
    discover_action_sequence_trace_paths,
    discover_manual_paths,
    discover_replay_paths,
    discover_runtime_action_session_entries,
    discover_scenario_paths,
    format_regression_json,
    format_regression_markdown,
    format_regression_text,
    main,
    run_regression,
)
from hsr_axis_sim.regression.manifest import RegressionManifestEntry


RUNTIME_FIXTURE_PATH = Path(
    "hsr_axis_sim/data/runtime_golden_fixtures/arch_017_reviewed_action_session_expected.json"
)
RUNTIME_FIXTURE_SHA256 = "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66"


def test_default_runner_discovers_fixture_groups():
    assert discover_replay_paths()
    assert discover_manual_paths()
    assert discover_scenario_paths()
    assert discover_action_sequence_trace_paths()
    runtime_entries = discover_runtime_action_session_entries()
    assert len(runtime_entries) == 1
    assert runtime_entries[0].id == "arch-017-reviewed-static-action-session"


def test_default_in_process_runner_returns_passing_report():
    report = run_regression()

    assert report.passed is True
    assert report.total > 0
    assert report.failed_count == 0
    runtime_results = [
        result for result in report.results if result.group == "runtime_action_sessions"
    ]
    assert len(runtime_results) == 1
    assert runtime_results[0].passed is True


def test_only_replays_limits_to_replay_checks():
    report = run_regression(only="replays")

    assert report.results
    assert {result.group for result in report.results} == {"replays"}


def test_only_manual_limits_to_manual_checks():
    report = run_regression(only="manual")

    assert report.results
    assert {result.group for result in report.results} == {"manual"}


def test_only_scenarios_limits_to_scenario_checks():
    report = run_regression(only="scenarios")

    assert report.results
    assert {result.group for result in report.results} == {"scenarios"}


def test_only_action_sequence_traces_limits_to_action_sequence_checks():
    report = run_regression(only="action_sequence_traces")

    assert report.results
    assert {result.group for result in report.results} == {"action_sequence_traces"}
    assert {result.details["check"] for result in report.results} == {
        "lint",
        "action_sequence",
    }


def test_only_trace_evidence_limits_to_evidence_checks():
    report = run_regression(
        only="trace_evidence",
        trace_evidence_entries=[
            RegressionManifestEntry(
                id="semantic",
                path=Path("hsr_axis_sim/data/manual_video_traces/semantic_maps/real_video_trace_001_botu_dilemma_semantics_v0_1.json"),
                check="semantic_map",
                source_trace_path=Path("hsr_axis_sim/data/manual_video_traces/intake/real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only.json"),
            )
        ],
    )

    assert report.passed is True
    assert report.total == 1
    assert {result.group for result in report.results} == {"trace_evidence"}


def test_only_runtime_action_sessions_uses_discovered_locked_entry():
    report = run_regression(only="runtime_action_sessions")

    assert report.passed is True
    assert report.total == 1
    assert {result.group for result in report.results} == {"runtime_action_sessions"}
    result = report.results[0]
    assert result.details["check"] == "no_effect_action_session_golden"
    assert result.details["action_count"] == 2
    assert result.details["expected_sha256"] == RUNTIME_FIXTURE_SHA256


def test_text_renderer_contains_title_and_pass_counts():
    text = format_regression_text(run_regression())

    assert "HSR Axis Regression Report" in text
    assert "PASS" in text
    assert "action-sequence trace checks" in text
    assert "runtime action-session Golden checks" in text
    assert "trace evidence checks" not in text


def test_markdown_renderer_contains_title_and_summary_table():
    markdown = format_regression_markdown(run_regression())

    assert "# HSR Axis Regression Report" in markdown
    assert "| Group | Passed | Failed | Total |" in markdown
    assert "| runtime_action_sessions | 1 | 0 | 1 |" in markdown


def test_json_renderer_is_valid_and_includes_results():
    rendered = format_regression_json(run_regression())
    payload = json.loads(rendered)

    assert payload["passed"] is True
    assert payload["results"]
    assert any(
        result["group"] == "runtime_action_sessions"
        for result in payload["results"]
    )


def test_trace_evidence_invalid_semantic_map_becomes_failed_result(tmp_path):
    invalid = tmp_path / "invalid_semantic_map.json"
    invalid.write_text("{}", encoding="utf-8")
    report = run_regression(
        only="trace_evidence",
        trace_evidence_entries=[_trace_evidence_entry("semantic", invalid, "semantic_map")],
    )
    assert report.passed is False
    assert report.total == 1
    assert report.results[0].group == "trace_evidence"


def test_trace_evidence_invalid_frame_anchors_becomes_failed_result(tmp_path):
    invalid = tmp_path / "invalid_frame_anchors.json"
    invalid.write_text("{}", encoding="utf-8")
    report = run_regression(
        only="trace_evidence",
        trace_evidence_entries=[_trace_evidence_entry("anchors", invalid, "frame_anchors")],
    )
    assert report.passed is False
    assert report.total == 1
    assert report.results[0].group == "trace_evidence"


def test_runtime_action_session_mismatch_uses_accepted_first_divergence():
    entry = RegressionManifestEntry(
        id="runtime-mismatch",
        path=RUNTIME_FIXTURE_PATH,
        check="no_effect_action_session_golden",
        expected_sha256=RUNTIME_FIXTURE_SHA256,
        adapter_stream_id="arch-017-reviewed-static",
        actor_id="reviewed-actor",
        action_ids=["reviewed-action-a", "reviewed-action-c"],
    )

    report = run_regression(
        only="runtime_action_sessions",
        runtime_action_session_entries=[entry],
    )

    assert report.passed is False
    assert report.total == 1
    result = report.results[0]
    assert result.group == "runtime_action_sessions"
    assert result.details["mismatch_count"] >= 1
    assert result.details["first_divergence_record_index"] == 2
    assert result.details["first_divergence_path"] == "/event/action_id"


def test_cli_output_writes_file(tmp_path):
    output_path = tmp_path / "regression_report.md"

    result = main(["--format", "markdown", "--output", str(output_path)])

    assert result == 0
    assert "# HSR Axis Regression Report" in output_path.read_text(encoding="utf-8")


def test_invalid_only_fails_clearly():
    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        result = main(["--only", "bad_group"])

    assert result != 0
    assert "Invalid --only group" in stderr.getvalue()


def test_fail_fast_stops_after_first_failure(tmp_path):
    bad_replay = tmp_path / "bad_replay.json"
    bad_replay.write_text("{not-json", encoding="utf-8")
    good_replay = Path("hsr_axis_sim/data/golden_replays/bronya_seele_timeline_mvp.json")

    report = run_regression(
        only="replays",
        fail_fast=True,
        replay_paths=[bad_replay, good_replay],
    )

    assert report.passed is False
    assert report.total == 1
    assert report.results[0].passed is False


def test_missing_action_sequence_trace_path_causes_regression_failure(tmp_path):
    missing_trace = tmp_path / "missing_action_sequence_trace.json"

    report = run_regression(
        only="action_sequence_traces",
        action_sequence_paths=[missing_trace],
    )

    assert report.passed is False
    assert report.total == 2
    assert report.failed_count == 2
    assert all(result.group == "action_sequence_traces" for result in report.results)


def test_invalid_action_sequence_trace_causes_regression_failure(tmp_path):
    bad_trace = tmp_path / "bad_action_sequence_trace.json"
    bad_trace.write_text(
        json.dumps(
            {
                "name": "bad_action_sequence_trace",
                "source": {
                    "type": "manual_video_trace",
                    "platform": "bilibili",
                    "url": "unknown",
                    "title": "unknown",
                },
                "scenario": {
                    "game_context": "Honkai: Star Rail 3.4",
                    "mode": "博徒困境",
                    "floor": "第12层",
                    "side": "第一面",
                },
                "team": [{"unit_id": "naxia", "character": "那刻夏"}],
                "check_mode": "action_sequence_only",
                "unknown_allowed": True,
                "numeric_expectations": "skip",
                "steps": [
                    {
                        "step": 1,
                        "video_timestamp": "unknown",
                        "action": "ultimate",
                        "target": "unknown",
                        "target_confidence": "unknown",
                        "observable": {
                            "actor_action_sequence": True,
                            "energy": 130,
                        },
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = run_regression(
        only="action_sequence_traces",
        action_sequence_paths=[bad_trace],
    )

    assert report.passed is False
    assert report.total == 2
    assert {result.details["check"] for result in report.results} == {
        "lint",
        "action_sequence",
    }
    assert any(not result.passed for result in report.results)


def _trace_evidence_entry(entry_id, path, check):
    return RegressionManifestEntry(
        id=entry_id,
        path=path,
        check=check,
        source_trace_path=Path(
            "hsr_axis_sim/data/manual_video_traces/intake/real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only.json"
        ),
    )
