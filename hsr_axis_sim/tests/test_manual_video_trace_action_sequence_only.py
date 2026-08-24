import json
import subprocess
import sys
from pathlib import Path

from hsr_axis_sim.regression.manifest import load_regression_manifest
from hsr_axis_sim.regression.runner import run_regression
from hsr_axis_sim.sim.replay import ReplayValidator
from hsr_axis_sim.sim.replay_lint import (
    lint_manual_video_trace,
    load_and_lint_manual_video_trace,
)


ROOT = Path(__file__).resolve().parents[1]
ACTION_SEQUENCE_TRACE = (
    ROOT
    / "data"
    / "manual_video_traces"
    / "intake"
    / "real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only.json"
)
MANIFEST_PATH = "hsr_axis_sim/data/regression_manifest.json"


def load_action_sequence_trace():
    return ReplayValidator().load_replay(ACTION_SEQUENCE_TRACE)


def test_action_sequence_only_fixture_passes_lint_and_sequence_check():
    trace = load_action_sequence_trace()

    assert load_and_lint_manual_video_trace(ACTION_SEQUENCE_TRACE) == []
    result = ReplayValidator().validate(trace)

    assert result.passed is True
    assert result.checked_steps == 9
    assert [
        (step["step"], step["actor"], step["action"])
        for step in trace["steps"]
    ] == [
        (1, "tingyun", "ultimate"),
        (2, "pela", "skill"),
        (3, "remembrance_trailblazer", "skill"),
        (4, "tingyun", "skill"),
        (5, "pela", "ultimate"),
        (6, "naxia", "ultimate"),
        (7, "naxia", "basic_plus_extra_skill"),
        (8, "mem", "advance_naxia"),
        (9, "naxia", "skill_plus_extra_skill"),
    ]


def test_action_sequence_only_unknown_numeric_fields_require_unknown_allowed():
    trace = load_action_sequence_trace()

    assert lint_manual_video_trace(trace) == []

    trace["unknown_allowed"] = False
    issues = lint_manual_video_trace(trace)

    assert any("unknown_allowed" in issue for issue in issues)
    assert any("uses 'unknown'" in issue for issue in issues)


def test_action_sequence_only_replay_skips_numeric_expectations():
    trace = load_action_sequence_trace()
    trace["steps"][0]["expect"] = {
        "skill_points": 99,
        "units": {
            "naxia": {
                "energy": 999,
                "hp": 1,
                "current_toughness": 0
            }
        }
    }

    result = ReplayValidator().validate(trace)

    assert result.passed is True
    assert result.checked_steps == 9


def test_action_sequence_only_lint_rejects_numeric_observations_when_skipping():
    trace = load_action_sequence_trace()
    trace["steps"][0]["observable"]["energy"] = 130

    issues = lint_manual_video_trace(trace)

    assert any("observable.energy" in issue for issue in issues)
    assert any("numeric_expectations is 'skip'" in issue for issue in issues)


def test_action_sequence_only_missing_required_metadata_fails_lint():
    for field_name in ["source", "team", "scenario", "check_mode", "steps"]:
        trace = load_action_sequence_trace()
        del trace[field_name]

        issues = lint_manual_video_trace(trace)

        assert any(field_name in issue for issue in issues)


def test_action_sequence_only_missing_actor_or_action_fails_lint():
    for field_name in ["actor", "action"]:
        trace = load_action_sequence_trace()
        del trace["steps"][0][field_name]

        issues = lint_manual_video_trace(trace)

        assert any(field_name in issue for issue in issues)


def test_action_sequence_only_lint_cli_passes_for_fixture():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "hsr_axis_sim.sim.replay_lint",
            str(ACTION_SEQUENCE_TRACE),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "PASS real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only" in (
        result.stdout
    )


def test_existing_regression_manifest_includes_real_trace_as_action_sequence_only():
    manifest = load_regression_manifest(MANIFEST_PATH)
    manifest_data = json.loads(Path(MANIFEST_PATH).read_text(encoding="utf-8"))

    assert manifest.counts_by_group()["action_sequence_traces"] == 1
    action_sequence_entry = next(
        entry
        for entry in manifest_data["groups"]["action_sequence_traces"]
        if entry["id"] == "real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only"
    )
    assert action_sequence_entry["checks"] == ["lint", "action_sequence"]

    report = run_regression(manifest=manifest)

    assert report.passed is True
