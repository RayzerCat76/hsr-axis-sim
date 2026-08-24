import copy
import subprocess
import sys
from pathlib import Path

from hsr_axis_sim.sim.replay import ReplayValidator
from hsr_axis_sim.sim.replay_lint import (
    lint_manual_video_trace,
    lint_manual_video_trace_intake,
    load_and_lint_manual_video_trace,
)


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_TRACE = (
    ROOT
    / "data"
    / "manual_video_traces"
    / "samples"
    / "manual_video_trace_sample_mvp.json"
)
NON_MANUAL_REPLAY = ROOT / "data" / "golden_replays" / "character_kit_001_mvp.json"
INTAKE_TRACE = (
    ROOT
    / "data"
    / "manual_video_traces"
    / "intake"
    / "real_video_trace_001_botu_dilemma_3_4_floor12_side1_opening_v0_3.json"
)


def load_sample():
    return ReplayValidator().load_replay(SAMPLE_TRACE)


def test_valid_sample_passes_lint():
    assert load_and_lint_manual_video_trace(SAMPLE_TRACE) == []


def test_valid_sample_passes_replay_validator():
    validator = ReplayValidator()
    result = validator.validate(validator.load_replay(SAMPLE_TRACE))

    assert result.passed is True
    assert result.checked_steps == 3


def test_missing_required_source_metadata_fails_lint():
    replay = load_sample()
    del replay["source"]["video_title"]

    issues = lint_manual_video_trace(replay)

    assert any("video_title" in issue for issue in issues)


def test_missing_expected_actor_on_normal_step_fails_unless_allowed():
    replay = load_sample()
    del replay["steps"][0]["expected_actor"]

    issues = lint_manual_video_trace(replay)
    assert any("expected_actor" in issue for issue in issues)

    replay["steps"][0]["allow_missing_expected_actor"] = True
    assert not any("expected_actor" in issue for issue in lint_manual_video_trace(replay))


def test_invalid_forced_rng_type_fails_lint():
    replay = load_sample()
    replay["steps"][0]["forced_rng"] = []

    issues = lint_manual_video_trace(replay)

    assert any("forced_rng" in issue for issue in issues)


def test_invalid_expect_type_fails_lint():
    replay = load_sample()
    replay["steps"][0]["expect"] = []

    issues = lint_manual_video_trace(replay)

    assert any("expect" in issue for issue in issues)


def test_step_requires_action_skill_or_enemy_ai_marker():
    replay = load_sample()
    del replay["steps"][0]["skill_id"]

    issues = lint_manual_video_trace(replay)

    assert any("skill_id, action_id, or use_enemy_ai" in issue for issue in issues)


def test_non_manual_existing_replay_does_not_fail_lint():
    replay = ReplayValidator().load_replay(NON_MANUAL_REPLAY)

    assert lint_manual_video_trace(replay) == []


def test_lint_cli_returns_zero_for_valid_sample():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "hsr_axis_sim.sim.replay_lint",
            str(SAMPLE_TRACE),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "PASS manual_video_trace_sample_mvp" in result.stdout


def test_real_video_trace_intake_draft_passes_intake_lint():
    trace = ReplayValidator().load_replay(INTAKE_TRACE)

    assert lint_manual_video_trace_intake(trace) == []
    assert lint_manual_video_trace(trace) == []
    assert trace["validation_policy"]["include_in_locked_manifest"] is False
    assert trace["validation_policy"]["allow_missing_expect_fields"] is True


def test_real_video_trace_intake_sequence_matches_confirmed_opening():
    trace = ReplayValidator().load_replay(INTAKE_TRACE)

    sequence = [
        (step["step"], step["expected_actor"], step["action_kind"], step["action_label_cn"])
        for step in trace["steps"]
    ]

    assert sequence == [
        (1, "tingyun", "ultimate", "停云终结技"),
        (2, "pela", "skill", "佩拉战技"),
        (3, "remembrance_trailblazer", "skill", "记忆主战技"),
        (4, "tingyun", "skill", "停云战技"),
        (5, "pela", "ultimate", "佩拉终结技"),
        (6, "nakxia", "ultimate", "那刻夏终结技"),
        (7, "nakxia", "basic_plus_bonus_skill", "那刻夏普攻 + 额外战技"),
        (8, "mimi", "action_advance", "迷迷拉条那刻夏"),
        (9, "nakxia", "skill_plus_bonus_skill", "那刻夏战技 + 额外战技"),
    ]


def test_real_video_trace_intake_lint_allows_empty_expectations():
    trace = ReplayValidator().load_replay(INTAKE_TRACE)

    assert all(step.get("expect") == {} for step in trace["steps"])
    assert lint_manual_video_trace_intake(trace) == []
