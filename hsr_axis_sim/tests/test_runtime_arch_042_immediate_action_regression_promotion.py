import hashlib
import math
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from hsr_axis_sim.regression.manifest import load_regression_manifest
from hsr_axis_sim.regression.runner import run_regression
from hsr_axis_sim.runtime_action_session_regression.manifest import (
    RUNTIME_ACTION_SESSION_REGRESSION_SUPPORTED_VERSIONS,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_6,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_7,
    RuntimeActionSessionRegressionChangeSpeedSetup,
    RuntimeActionSessionRegressionImmediateActionSetup,
    RuntimeActionSessionRegressionManifest,
    load_runtime_action_session_regression_manifest,
    runtime_action_session_regression_manifest_from_dict,
)
from hsr_axis_sim.runtime_action_session_regression.runner import (
    run_runtime_action_session_regression,
)
from hsr_axis_sim.sim import BattleState, Timeline, Unit


ROOT = Path(__file__).parents[2]
RUNTIME_MANIFEST_PATH = (
    ROOT / "hsr_axis_sim" / "data" / "runtime_action_session_regression_manifest.json"
)
LEGACY_MANIFEST_PATH = ROOT / "hsr_axis_sim" / "data" / "regression_manifest.json"
FIXTURE_DIR = ROOT / "hsr_axis_sim" / "data" / "runtime_golden_fixtures"

FIXTURES = (
    (
        FIXTURE_DIR / "arch_017_reviewed_action_session_expected.json",
        3013,
        "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66",
    ),
    (
        FIXTURE_DIR / "arch_021_reviewed_clamped_energy_expected.json",
        2759,
        "4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605",
    ),
    (
        FIXTURE_DIR / "arch_023_reviewed_clamped_skill_point_expected.json",
        2744,
        "fc359b367c2922ed39e059f89ad16845ba215508292cfa43ca2ab6031c4c9ba9",
    ),
    (
        FIXTURE_DIR / "arch_025_reviewed_energy_consume_expected.json",
        2750,
        "7d61528687a5a2f499249e0f914f6f2f50975c7c153165eddd5e116f3ed19a75",
    ),
    (
        FIXTURE_DIR / "arch_027_reviewed_skill_point_consume_expected.json",
        2796,
        "d0dcf128f3a28f691324f4e9295b7bcd66460598186f6059d4619f55e8ae39ec",
    ),
    (
        FIXTURE_DIR / "arch_032_reviewed_action_advance_expected.json",
        2818,
        "ab73c224d06690b379d398a5bc2c4b38a1ed654dfd86866d564417432c29d3ce",
    ),
    (
        FIXTURE_DIR / "arch_035_reviewed_action_delay_expected.json",
        2728,
        "9efbb65defb5eacc12150d31d0530d9a94b43a42e2303ebca643911f98094c4d",
    ),
    (
        FIXTURE_DIR / "arch_038_reviewed_change_speed_expected.json",
        2604,
        "c23b34e0afffdfe4bee53d028e5ff21d946623300b169ba57e5ddfb69478df2a",
    ),
    (
        FIXTURE_DIR / "arch_041_reviewed_immediate_action_expected.json",
        2620,
        "7fd1594362b5bf9a95eec6f6472b2f17afa9dcfe10196d81ec6c970eab86eea1",
    ),
)

CASE_IDS = [
    "arch-017-reviewed-static-action-session",
    "arch-021-reviewed-static-clamped-energy",
    "arch-023-reviewed-static-clamped-skill-point",
    "arch-025-reviewed-static-energy-consume",
    "arch-027-reviewed-static-skill-point-consume",
    "arch-032-reviewed-static-action-advance",
    "arch-035-reviewed-static-action-delay",
    "arch-038-reviewed-static-change-speed",
    "arch-041-reviewed-static-immediate-action",
]


def _base_case():
    return {
        "id": "arch-041-reviewed-static-immediate-action",
        "expected_path": (
            "hsr_axis_sim/data/runtime_golden_fixtures/"
            "arch_041_reviewed_immediate_action_expected.json"
        ),
        "expected_sha256": FIXTURES[-1][2],
        "stream_id": "arch-041-reviewed-axis",
        "actor_id": "immediate-actor",
        "actions": [
            {
                "action_id": "reviewed-immediate-action",
                "name": "reviewed-immediate-action",
                "ends_turn": False,
            }
        ],
    }


def _immediate_setup(*, initial_av=80):
    return {
        "kind": "IMMEDIATE_ACTION",
        "target_id": "immediate-actor",
        "target_name": "Immediate Actor",
        "team": "ally",
        "base_speed": 100,
        "initial_av": initial_av,
        "action_index": 0,
    }


def _change_speed_setup():
    return {
        "kind": "CHANGE_SPEED",
        "target_id": "speed-actor",
        "target_name": "Speed Actor",
        "team": "ally",
        "base_speed": 100,
        "initial_av": 80,
        "action_index": 0,
        "new_speed": 200,
    }


def _manifest(version: str, setup):
    case = _base_case()
    case["setup"] = setup
    return {
        "schema": "hsr_runtime_action_session_regression",
        "version": version,
        "manifest_id": "arch-042-version-probe",
        "cases": [case],
    }


def _parse(data):
    return runtime_action_session_regression_manifest_from_dict(
        data,
        ROOT / "arch_042_synthetic_manifest.json",
    )


def test_supported_versions_are_exactly_v1_0_through_v1_8():
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_7 == "1.7"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION == "1.8"
    assert RUNTIME_ACTION_SESSION_REGRESSION_SUPPORTED_VERSIONS == (
        "1.0",
        "1.1",
        "1.2",
        "1.3",
        "1.4",
        "1.5",
        "1.6",
        "1.7",
        "1.8",
    )


def test_v1_7_explicitly_rejects_immediate_action_as_v1_8_syntax():
    with pytest.raises(ValueError, match="IMMEDIATE_ACTION.*requires manifest version '1.8'"):
        _parse(
            _manifest(
                RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_7,
                _immediate_setup(),
            )
        )


def test_v1_8_accepts_exact_frozen_immediate_action_setup():
    parsed = _parse(
        _manifest(RUNTIME_ACTION_SESSION_REGRESSION_VERSION, _immediate_setup())
    )
    assert parsed.cases[0].setup == RuntimeActionSessionRegressionImmediateActionSetup(
        target_id="immediate-actor",
        target_name="Immediate Actor",
        team="ally",
        base_speed=100,
        initial_av=80,
        action_index=0,
    )
    with pytest.raises(FrozenInstanceError):
        parsed.cases[0].setup.initial_av = 60


def test_change_speed_remains_v1_7_and_v1_8_syntax_but_not_v1_6():
    with pytest.raises(ValueError, match="CHANGE_SPEED.*requires manifest version '1.7'"):
        _parse(
            _manifest(
                RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_6,
                _change_speed_setup(),
            )
        )

    for version in (RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_7, "1.8"):
        parsed = _parse(_manifest(version, _change_speed_setup()))
        assert isinstance(
            parsed.cases[0].setup,
            RuntimeActionSessionRegressionChangeSpeedSetup,
        )


def test_immediate_action_fields_are_exact():
    extra = _immediate_setup()
    extra["mode"] = "immediate"
    with pytest.raises(ValueError, match="unsupported field"):
        _parse(_manifest("1.8", extra))

    missing = _immediate_setup()
    missing.pop("initial_av")
    with pytest.raises(ValueError, match="missing required field"):
        _parse(_manifest("1.8", missing))


@pytest.mark.parametrize("field", ["target_id", "target_name", "team"])
@pytest.mark.parametrize("invalid", ["", None, 1, False])
def test_immediate_action_identity_fields_require_non_empty_strings(field, invalid):
    setup = _immediate_setup()
    setup[field] = invalid
    with pytest.raises(ValueError, match=field):
        _parse(_manifest("1.8", setup))


@pytest.mark.parametrize("field", ["base_speed", "initial_av"])
@pytest.mark.parametrize(
    "invalid",
    [True, False, "1", None, math.inf, -math.inf, math.nan],
)
def test_immediate_action_numeric_fields_require_finite_non_boolean_numbers(field, invalid):
    setup = _immediate_setup()
    setup[field] = invalid
    with pytest.raises(ValueError, match=field):
        _parse(_manifest("1.8", setup))


@pytest.mark.parametrize("invalid", [0, 0.0, -1, -100.0])
def test_immediate_action_base_speed_must_be_positive(invalid):
    setup = _immediate_setup()
    setup["base_speed"] = invalid
    with pytest.raises(ValueError, match="greater than zero"):
        _parse(_manifest("1.8", setup))


@pytest.mark.parametrize("invalid", [True, False, -1, 0.0, "0", None])
def test_immediate_action_index_requires_exact_nonnegative_integer(invalid):
    setup = _immediate_setup()
    setup["action_index"] = invalid
    with pytest.raises(ValueError, match="action_index"):
        _parse(_manifest("1.8", setup))


def test_immediate_action_index_must_address_declared_action():
    setup = _immediate_setup()
    setup["action_index"] = 1
    with pytest.raises(ValueError, match="declared action"):
        _parse(_manifest("1.8", setup))


@pytest.mark.parametrize("initial_av", [0, -10.0])
def test_immediate_action_initial_av_is_finite_but_not_newly_range_restricted(initial_av):
    parsed = _parse(_manifest("1.8", _immediate_setup(initial_av=initial_av)))
    assert parsed.cases[0].setup.initial_av == initial_av


def test_locked_v1_8_manifest_contains_exact_nine_reviewed_cases_in_order():
    manifest = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)

    assert len(manifest.cases) == 9
    assert [case.case_id for case in manifest.cases] == CASE_IDS
    ninth = manifest.cases[8]
    assert ninth.expected_path == FIXTURES[-1][0].resolve()
    assert ninth.expected_sha256 == FIXTURES[-1][2]
    assert ninth.stream_id == "arch-041-reviewed-axis"
    assert ninth.actor_id == "immediate-actor"
    assert [action.action_id for action in ninth.actions] == ["reviewed-immediate-action"]
    assert [action.name for action in ninth.actions] == ["reviewed-immediate-action"]
    assert [action.ends_turn for action in ninth.actions] == [False]
    assert ninth.setup == RuntimeActionSessionRegressionImmediateActionSetup(
        target_id="immediate-actor",
        target_name="Immediate Actor",
        team="ally",
        base_speed=100,
        initial_av=80,
        action_index=0,
    )


def test_locked_runtime_lane_passes_nine_of_nine_with_expected_counts_and_digests():
    report = run_runtime_action_session_regression(
        load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    )

    assert report.passed is True
    assert report.total == 9
    assert report.passed_count == 9
    assert report.failed_count == 0
    assert [result.case_id for result in report.results] == CASE_IDS
    assert [result.details["record_count"] for result in report.results] == [
        4,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
    ]
    assert [result.details["expected_sha256"] for result in report.results] == [
        item[2] for item in FIXTURES
    ]
    actual_sha256 = report.results[8].details["actual_sha256"]
    assert len(actual_sha256) == 64
    assert all(character in "0123456789abcdef" for character in actual_sha256)


def test_immediate_action_initial_av_change_surfaces_existing_typed_divergence():
    locked = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    case = locked.cases[8]
    assert isinstance(case.setup, RuntimeActionSessionRegressionImmediateActionSetup)
    changed = replace(case, setup=replace(case.setup, initial_av=60))

    report = run_runtime_action_session_regression(
        RuntimeActionSessionRegressionManifest(
            manifest_id="arch-042-controlled-immediate-action-mismatch",
            path=ROOT / "arch_042_controlled_immediate_action_mismatch.json",
            cases=(changed,),
        )
    )

    assert report.passed is False
    assert report.total == 1
    result = report.results[0]
    assert result.error == "Runtime action-session Golden mismatch."
    assert result.details["record_count"] == 3
    assert result.details["first_divergence_record_index"] == 1
    assert result.details["first_divergence_path"] == (
        "/event/payload/immediate_action/before_av"
    )


def test_all_nine_reviewed_fixture_byte_identities_remain_exact():
    for path, size, digest in FIXTURES:
        payload = path.read_bytes()
        assert len(payload) == size
        assert hashlib.sha256(payload).hexdigest() == digest


def test_immediate_action_regression_harness_is_closed_and_explicitly_targeted():
    manifest_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "manifest.py"
    ).read_text(encoding="utf-8")
    runner_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "runner.py"
    ).read_text(encoding="utf-8")
    combined = manifest_source + runner_source

    assert 'kind == "IMMEDIATE_ACTION"' in manifest_source
    assert "RuntimeActionSessionRegressionImmediateActionSetup" in manifest_source
    assert "ImmediateAction" in runner_source
    assert "ImmediateAction(target_ids=[setup.target_id])" in runner_source

    for forbidden in (
        "GrantExtraTurn",
        "importlib",
        "eval(",
        "exec(",
        "effect_class",
        "effect_type",
        "effect_kwargs",
        "**setup",
        "__import__",
    ):
        assert forbidden not in combined


def test_arch_041_fixture_is_not_added_to_legacy_manifest():
    legacy_text = LEGACY_MANIFEST_PATH.read_text(encoding="utf-8")
    assert "arch_041_reviewed_immediate_action_expected.json" not in legacy_text


def test_legacy_regression_and_trace_evidence_remain_unchanged():
    legacy = load_regression_manifest(LEGACY_MANIFEST_PATH)
    complete = run_regression(manifest=legacy)
    trace = run_regression(manifest=legacy, only="trace_evidence")

    assert complete.passed is True
    assert complete.total == 20
    assert complete.passed_count == 20
    assert trace.passed is True
    assert trace.total == 2
    assert trace.passed_count == 2


def test_production_lifo_compatibility_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])

    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == [
        "third",
        "second",
        "first",
    ]
