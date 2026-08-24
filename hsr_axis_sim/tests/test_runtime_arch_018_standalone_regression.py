import contextlib
import hashlib
import io
import json
from pathlib import Path

import pytest

from hsr_axis_sim.regression.manifest import load_regression_manifest
from hsr_axis_sim.regression.runner import run_regression
from hsr_axis_sim.runtime_action_session_regression.manifest import (
    RuntimeActionSessionRegressionAction,
    RuntimeActionSessionRegressionCase,
    RuntimeActionSessionRegressionManifest,
    load_runtime_action_session_regression_manifest,
    runtime_action_session_regression_manifest_from_dict,
)
from hsr_axis_sim.runtime_action_session_regression.runner import (
    format_runtime_action_session_regression_json,
    format_runtime_action_session_regression_text,
    main,
    run_runtime_action_session_regression,
)
from hsr_axis_sim.sim import BattleState, Timeline, Unit


ROOT = Path(__file__).parents[2]
LEGACY_MANIFEST_PATH = ROOT / "hsr_axis_sim" / "data" / "regression_manifest.json"
RUNTIME_MANIFEST_PATH = (
    ROOT / "hsr_axis_sim" / "data" / "runtime_action_session_regression_manifest.json"
)
EXPECTED_PATH = (
    ROOT
    / "hsr_axis_sim"
    / "data"
    / "runtime_golden_fixtures"
    / "arch_017_reviewed_action_session_expected.json"
)
EXPECTED_RELATIVE_PATH = (
    "hsr_axis_sim/data/runtime_golden_fixtures/"
    "arch_017_reviewed_action_session_expected.json"
)
EXPECTED_SHA256 = "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66"
EXPECTED_SIZE_BYTES = 3013
FIXTURE_ID = "arch-017-reviewed-static-action-session"


def _valid_manifest_data():
    return {
        "schema": "hsr_runtime_action_session_regression",
        "version": "1.0",
        "manifest_id": "test-runtime-regression",
        "cases": [
            {
                "id": FIXTURE_ID,
                "expected_path": EXPECTED_RELATIVE_PATH,
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
        ],
    }


def _manifest_from_data(data):
    return runtime_action_session_regression_manifest_from_dict(
        data,
        ROOT / "synthetic_runtime_regression_manifest.json",
    )


def _mismatch_case() -> RuntimeActionSessionRegressionCase:
    return RuntimeActionSessionRegressionCase(
        case_id=FIXTURE_ID,
        expected_relative_path=EXPECTED_RELATIVE_PATH,
        expected_path=EXPECTED_PATH,
        expected_sha256=EXPECTED_SHA256,
        stream_id="arch-017-reviewed-static",
        actor_id="reviewed-actor",
        actions=(
            RuntimeActionSessionRegressionAction(
                "reviewed-action-a", "reviewed-action-a", False
            ),
            RuntimeActionSessionRegressionAction(
                "reviewed-action-c", "reviewed-action-c", False
            ),
        ),
    )


def test_locked_standalone_manifest_loads_one_reviewed_case_in_declared_order():
    manifest = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)

    assert manifest.manifest_id == "HSR_RUNTIME_ACTION_SESSION_REGRESSION_001"
    assert len(manifest.cases) == 1
    case = manifest.cases[0]
    assert case.case_id == FIXTURE_ID
    assert case.expected_relative_path == EXPECTED_RELATIVE_PATH
    assert case.expected_path == EXPECTED_PATH.resolve()
    assert case.expected_sha256 == EXPECTED_SHA256
    assert case.stream_id == "arch-017-reviewed-static"
    assert case.actor_id == "reviewed-actor"
    assert [action.action_id for action in case.actions] == [
        "reviewed-action-a",
        "reviewed-action-b",
    ]
    assert [action.ends_turn for action in case.actions] == [False, False]


def test_locked_standalone_runtime_regression_passes_one_of_one():
    manifest = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)

    report = run_runtime_action_session_regression(manifest)

    assert report.passed is True
    assert report.total == 1
    assert report.passed_count == 1
    assert report.failed_count == 0
    result = report.results[0]
    assert result.case_id == FIXTURE_ID
    assert result.expected_path == EXPECTED_RELATIVE_PATH
    assert result.passed is True
    assert result.details["action_count"] == 2
    assert result.details["record_count"] == 4
    assert result.details["expected_sha256"] == EXPECTED_SHA256
    assert len(result.details["actual_sha256"]) == 64


def test_controlled_mismatch_surfaces_existing_first_divergence_provenance():
    manifest = RuntimeActionSessionRegressionManifest(
        manifest_id="controlled-mismatch",
        path=ROOT / "controlled-mismatch.json",
        cases=(_mismatch_case(),),
    )

    report = run_runtime_action_session_regression(manifest)

    assert report.passed is False
    assert report.total == 1
    result = report.results[0]
    assert result.error == "Runtime action-session Golden mismatch."
    assert result.details["first_divergence_record_index"] == 2
    assert result.details["first_divergence_path"] == "/event/action_id"


def test_fail_fast_stops_after_first_failed_runtime_case():
    valid_case = load_runtime_action_session_regression_manifest(
        RUNTIME_MANIFEST_PATH
    ).cases[0]
    manifest = RuntimeActionSessionRegressionManifest(
        manifest_id="fail-fast",
        path=ROOT / "fail-fast.json",
        cases=(_mismatch_case(), valid_case),
    )

    stopped = run_runtime_action_session_regression(manifest, fail_fast=True)
    complete = run_runtime_action_session_regression(manifest, fail_fast=False)

    assert stopped.total == 1
    assert stopped.failed_count == 1
    assert complete.total == 2
    assert complete.failed_count == 1
    assert complete.passed_count == 1


def test_text_and_json_reports_are_deterministic_and_runtime_specific():
    report = run_runtime_action_session_regression(
        load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    )

    text_first = format_runtime_action_session_regression_text(report)
    text_second = format_runtime_action_session_regression_text(report)
    json_first = format_runtime_action_session_regression_json(report)
    json_second = format_runtime_action_session_regression_json(report)

    assert text_first == text_second
    assert json_first == json_second
    assert "PASS 1/1 runtime action-session Golden checks" in text_first
    assert "HSR Axis Regression Report" not in text_first
    payload = json.loads(json_first)
    assert payload["total"] == 1
    assert payload["passed_count"] == 1
    assert payload["results"][0]["case_id"] == FIXTURE_ID


def test_cli_runs_standalone_runtime_lane_without_legacy_runner_output():
    stdout = io.StringIO()

    with contextlib.redirect_stdout(stdout):
        code = main(
            [
                "--manifest",
                str(RUNTIME_MANIFEST_PATH),
                "--format",
                "text",
            ]
        )

    assert code == 0
    rendered = stdout.getvalue()
    assert "PASS 1/1 runtime action-session Golden checks" in rendered
    assert "PASS 12/12 golden replays" not in rendered


def test_manifest_root_schema_version_and_fields_are_strict():
    bad_schema = _valid_manifest_data()
    bad_schema["schema"] = "wrong"
    with pytest.raises(ValueError, match="manifest.schema"):
        _manifest_from_data(bad_schema)

    bad_version = _valid_manifest_data()
    bad_version["version"] = "2.0"
    with pytest.raises(ValueError, match="manifest.version"):
        _manifest_from_data(bad_version)

    unknown = _valid_manifest_data()
    unknown["extra"] = True
    with pytest.raises(ValueError, match="unsupported field"):
        _manifest_from_data(unknown)

    empty = _valid_manifest_data()
    empty["cases"] = []
    with pytest.raises(ValueError, match="non-empty list"):
        _manifest_from_data(empty)


def test_duplicate_case_ids_are_rejected():
    data = _valid_manifest_data()
    data["cases"].append(dict(data["cases"][0]))

    with pytest.raises(ValueError, match="Duplicate"):
        _manifest_from_data(data)


def test_expected_path_must_be_canonical_repo_relative_and_existing():
    for invalid in (
        str(EXPECTED_PATH.resolve()),
        "hsr_axis_sim/data/runtime_golden_fixtures/../runtime_golden_fixtures/arch_017_reviewed_action_session_expected.json",
        "hsr_axis_sim//data/runtime_golden_fixtures/arch_017_reviewed_action_session_expected.json",
        "hsr_axis_sim\\data\\runtime_golden_fixtures\\arch_017_reviewed_action_session_expected.json",
        "../outside.json",
        "hsr_axis_sim/data/runtime_golden_fixtures/not_here.json",
    ):
        data = _valid_manifest_data()
        data["cases"][0]["expected_path"] = invalid
        with pytest.raises(ValueError):
            _manifest_from_data(data)


def test_case_digest_and_action_contract_are_strict():
    bad_digest = _valid_manifest_data()
    bad_digest["cases"][0]["expected_sha256"] = "A" * 64
    with pytest.raises(ValueError, match="expected_sha256"):
        _manifest_from_data(bad_digest)

    empty_actions = _valid_manifest_data()
    empty_actions["cases"][0]["actions"] = []
    with pytest.raises(ValueError, match="actions"):
        _manifest_from_data(empty_actions)

    extra_action_field = _valid_manifest_data()
    extra_action_field["cases"][0]["actions"][0]["effects"] = []
    with pytest.raises(ValueError, match="unsupported field"):
        _manifest_from_data(extra_action_field)

    invalid_boolean = _valid_manifest_data()
    invalid_boolean["cases"][0]["actions"][0]["ends_turn"] = 0
    with pytest.raises(ValueError, match="ends_turn"):
        _manifest_from_data(invalid_boolean)


def test_wrong_but_well_formed_digest_becomes_failed_operational_check():
    case = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH).cases[0]
    wrong_digest_case = RuntimeActionSessionRegressionCase(
        case_id=case.case_id,
        expected_relative_path=case.expected_relative_path,
        expected_path=case.expected_path,
        expected_sha256="0" * 64,
        stream_id=case.stream_id,
        actor_id=case.actor_id,
        actions=case.actions,
    )
    manifest = RuntimeActionSessionRegressionManifest(
        manifest_id="wrong-digest",
        path=ROOT / "wrong-digest.json",
        cases=(wrong_digest_case,),
    )

    report = run_runtime_action_session_regression(manifest)

    assert report.passed is False
    assert report.total == 1
    assert "digest" in report.results[0].error.lower()


def test_arch_017_expected_artifact_remains_exact_and_legacy_manifest_does_not_reference_it():
    payload = EXPECTED_PATH.read_bytes()
    legacy_text = LEGACY_MANIFEST_PATH.read_text(encoding="utf-8")

    assert len(payload) == EXPECTED_SIZE_BYTES
    assert hashlib.sha256(payload).hexdigest() == EXPECTED_SHA256
    assert FIXTURE_ID not in legacy_text
    assert EXPECTED_PATH.name not in legacy_text
    assert "runtime_golden_fixtures" not in legacy_text


def test_legacy_locked_regression_identity_remains_twenty_of_twenty():
    report = run_regression(manifest=load_regression_manifest(LEGACY_MANIFEST_PATH))

    assert report.passed is True
    assert report.total == 20
    assert report.passed_count == 20
    assert report.failed_count == 0
    assert sum(result.group == "replays" for result in report.results) == 12
    assert sum(result.group == "manual" for result in report.results) == 2
    assert sum(result.group == "scenarios" for result in report.results) == 2
    assert sum(result.group == "action_sequence_traces" for result in report.results) == 2
    assert sum(result.group == "trace_evidence" for result in report.results) == 2


def test_trace_evidence_lane_remains_two_of_two():
    report = run_regression(
        manifest=load_regression_manifest(LEGACY_MANIFEST_PATH),
        only="trace_evidence",
    )

    assert report.passed is True
    assert report.total == 2
    assert report.passed_count == 2


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])

    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == [
        "third",
        "second",
        "first",
    ]
