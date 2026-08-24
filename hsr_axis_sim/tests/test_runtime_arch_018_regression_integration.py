import contextlib
import hashlib
import inspect
import io
import json
from pathlib import Path

from hsr_axis_sim.regression.manifest import (
    RegressionManifestEntry,
    RuntimeActionSessionRegressionAction,
    load_regression_manifest,
)
from hsr_axis_sim.regression.runner import (
    _check_replay,
    _check_runtime_action_session,
    format_regression_markdown,
    format_regression_text,
    main,
    run_regression,
)
from hsr_axis_sim.sim import BattleState, Timeline, Unit


ROOT = Path(__file__).parents[2]
MANIFEST_PATH = ROOT / "hsr_axis_sim" / "data" / "regression_manifest.json"
EXPECTED_PATH = (
    ROOT
    / "hsr_axis_sim"
    / "data"
    / "runtime_golden_fixtures"
    / "arch_017_reviewed_action_session_expected.json"
)
EXPECTED_SHA256 = "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66"
EXPECTED_SIZE_BYTES = 3013
FIXTURE_ID = "arch-017-reviewed-static-action-session"
LEGACY_REPLAY_IDS = [
    "break_damage_elemental_mvp",
    "bronya_seele_multistep_mvp",
    "bronya_seele_timeline_mvp",
    "buff_duration_mvp",
    "character_kit_001_mvp",
    "damage_formula_v1_mvp",
    "damage_rng_mvp",
    "data_loaded_bronya_seele_mvp",
    "enemy_ai_mvp",
    "toughness_break_mvp",
    "trigger_on_kill_extra_turn_mvp",
    "ultimate_interrupt_mvp",
]


def test_locked_runtime_action_session_regression_is_distinct_and_passes():
    manifest = load_regression_manifest(MANIFEST_PATH)

    report = run_regression(manifest=manifest, only="runtime_action_sessions")

    assert report.passed is True
    assert report.total == 1
    result = report.results[0]
    assert result.group == "runtime_action_sessions"
    assert result.name == FIXTURE_ID
    assert result.path == str(EXPECTED_PATH.resolve())
    assert result.details["expected_sha256"] == EXPECTED_SHA256
    assert result.details["action_count"] == 2
    assert result.details["record_count"] == 4
    assert len(result.details["actual_sha256"]) == 64


def test_full_locked_regression_is_legacy_twenty_plus_one_runtime_check():
    manifest = load_regression_manifest(MANIFEST_PATH)

    report = run_regression(manifest=manifest)

    assert report.passed is True
    assert report.total == 21
    assert report.passed_count == 21
    assert report.failed_count == 0
    group_counts = {
        group: sum(result.group == group for result in report.results)
        for group in (
            "replays",
            "manual",
            "scenarios",
            "action_sequence_traces",
            "runtime_action_sessions",
            "trace_evidence",
        )
    }
    assert group_counts == {
        "replays": 12,
        "manual": 2,
        "scenarios": 2,
        "action_sequence_traces": 2,
        "runtime_action_sessions": 1,
        "trace_evidence": 2,
    }


def test_controlled_runtime_action_session_mismatch_surfaces_arch_006_first_divergence():
    entry = RegressionManifestEntry(
        id=FIXTURE_ID,
        path=EXPECTED_PATH,
        expected_sha256=EXPECTED_SHA256,
        stream_id="arch-017-reviewed-static",
        actor_id="reviewed-actor",
        actions=[
            RuntimeActionSessionRegressionAction(
                "reviewed-action-a", "reviewed-action-a", False
            ),
            RuntimeActionSessionRegressionAction(
                "reviewed-action-c", "reviewed-action-c", False
            ),
        ],
    )

    report = run_regression(
        only="runtime_action_sessions",
        runtime_action_session_entries=[entry],
    )

    assert report.passed is False
    assert report.total == 1
    result = report.results[0]
    assert result.group == "runtime_action_sessions"
    assert result.error == "Runtime action-session Golden mismatch."
    assert result.details["first_divergence_record_index"] == 2
    assert result.details["first_divergence_path"] == "/event/action_id"


def test_cli_only_runtime_action_sessions_reports_one_of_one():
    stdout = io.StringIO()

    with contextlib.redirect_stdout(stdout):
        code = main(
            [
                "--manifest",
                str(MANIFEST_PATH),
                "--only",
                "runtime_action_sessions",
                "--format",
                "text",
            ]
        )

    assert code == 0
    assert "PASS 1/1 runtime action-session Golden checks" in stdout.getvalue()
    assert "PASS 12/12 golden replays" not in stdout.getvalue()


def test_runtime_group_is_stable_in_text_markdown_and_json_reports():
    report = run_regression(manifest=load_regression_manifest(MANIFEST_PATH))

    text = format_regression_text(report)
    markdown = format_regression_markdown(report)
    payload = json.loads(json.dumps(report, default=lambda value: value.__dict__))

    assert "PASS 12/12 golden replays" in text
    assert "PASS 1/1 runtime action-session Golden checks" in text
    assert "| runtime_action_sessions | 1 | 0 | 1 |" in markdown
    assert payload["manifest_counts"]["runtime_action_sessions"] == 1


def test_arch_017_expected_artifact_remains_byte_for_byte_locked():
    payload = EXPECTED_PATH.read_bytes()

    assert len(payload) == EXPECTED_SIZE_BYTES
    assert hashlib.sha256(payload).hexdigest() == EXPECTED_SHA256
    assert not payload.endswith(b"\n")


def test_legacy_replay_entries_are_unchanged_and_still_use_replay_validator():
    manifest = load_regression_manifest(MANIFEST_PATH)

    assert [entry.id for entry in manifest.groups["replays"]] == LEGACY_REPLAY_IDS
    assert all("data/golden_replays/" in entry.path.as_posix() for entry in manifest.groups["replays"])
    replay_source = inspect.getsource(_check_replay)
    runtime_source = inspect.getsource(_check_runtime_action_session)
    assert "ReplayValidator()" in replay_source
    assert "ReplayValidator" not in runtime_source
    assert runtime_source.count("run_action_session_validation(") == 1


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])

    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == [
        "third",
        "second",
        "first",
    ]
