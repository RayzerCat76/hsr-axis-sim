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
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_6,
    RuntimeActionSessionRegressionActionDelaySetup,
    RuntimeActionSessionRegressionChangeSpeedSetup,
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
]


def _base_case():
    return {
        "id": "arch-038-reviewed-static-change-speed",
        "expected_path": (
            "hsr_axis_sim/data/runtime_golden_fixtures/"
            "arch_038_reviewed_change_speed_expected.json"
        ),
        "expected_sha256": FIXTURES[-1][2],
        "stream_id": "arch-038-reviewed-axis",
        "actor_id": "speed-actor",
        "actions": [
            {
                "action_id": "reviewed-change-speed",
                "name": "reviewed-change-speed",
                "ends_turn": False,
            }
        ],
    }


def _change_speed_setup(*, new_speed=200, initial_av=80):
    return {
        "kind": "CHANGE_SPEED",
        "target_id": "speed-actor",
        "target_name": "Speed Actor",
        "team": "ally",
        "base_speed": 100,
        "initial_av": initial_av,
        "action_index": 0,
        "new_speed": new_speed,
    }


def _delay_setup():
    return {
        "kind": "ACTION_DELAY",
        "target_id": "delay-actor",
        "target_name": "Delay Actor",
        "team": "ally",
        "base_speed": 100,
        "initial_av": 30,
        "action_index": 0,
        "percent": 0.25,
    }


def _manifest(version: str, setup):
    case = _base_case()
    case["setup"] = setup
    return {
        "schema": "hsr_runtime_action_session_regression",
        "version": version,
        "manifest_id": "arch-039-version-probe",
        "cases": [case],
    }


def _parse(data):
    return runtime_action_session_regression_manifest_from_dict(
        data,
        ROOT / "arch_039_synthetic_manifest.json",
    )


def test_supported_versions_are_exactly_v1_0_through_v1_7():
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_6 == "1.6"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION == "1.7"
    assert RUNTIME_ACTION_SESSION_REGRESSION_SUPPORTED_VERSIONS == (
        "1.0",
        "1.1",
        "1.2",
        "1.3",
        "1.4",
        "1.5",
        "1.6",
        "1.7",
    )


def test_v1_6_explicitly_rejects_change_speed_as_v1_7_syntax():
    with pytest.raises(ValueError, match="CHANGE_SPEED.*requires manifest version '1.7'"):
        _parse(
            _manifest(
                RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_6,
                _change_speed_setup(),
            )
        )


def test_v1_7_accepts_exact_frozen_change_speed_setup():
    parsed = _parse(
        _manifest(RUNTIME_ACTION_SESSION_REGRESSION_VERSION, _change_speed_setup())
    )
    assert parsed.cases[0].setup == RuntimeActionSessionRegressionChangeSpeedSetup(
        target_id="speed-actor",
        target_name="Speed Actor",
        team="ally",
        base_speed=100,
        initial_av=80,
        action_index=0,
        new_speed=200,
    )
    with pytest.raises(FrozenInstanceError):
        parsed.cases[0].setup.new_speed = 160


def test_action_delay_remains_v1_6_and_v1_7_syntax_but_not_v1_5():
    with pytest.raises(ValueError, match="ACTION_DELAY.*requires manifest version '1.6'"):
        _parse(
            _manifest(
                RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5,
                _delay_setup(),
            )
        )

    for version in (RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_6, "1.7"):
        parsed = _parse(_manifest(version, _delay_setup()))
        assert isinstance(
            parsed.cases[0].setup,
            RuntimeActionSessionRegressionActionDelaySetup,
        )


def test_change_speed_fields_are_exact():
    extra = _change_speed_setup()
    extra["mode"] = "speed"
    with pytest.raises(ValueError, match="unsupported field"):
        _parse(_manifest("1.7", extra))

    missing = _change_speed_setup()
    missing.pop("new_speed")
    with pytest.raises(ValueError, match="missing required field"):
        _parse(_manifest("1.7", missing))


@pytest.mark.parametrize("field", ["target_id", "target_name", "team"])
@pytest.mark.parametrize("invalid", ["", None, 1, False])
def test_change_speed_identity_fields_require_non_empty_strings(field, invalid):
    setup = _change_speed_setup()
    setup[field] = invalid
    with pytest.raises(ValueError, match=field):
        _parse(_manifest("1.7", setup))


@pytest.mark.parametrize("field", ["base_speed", "initial_av", "new_speed"])
@pytest.mark.parametrize(
    "invalid",
    [True, False, "1", None, math.inf, -math.inf, math.nan],
)
def test_change_speed_numeric_fields_require_finite_non_boolean_numbers(field, invalid):
    setup = _change_speed_setup()
    setup[field] = invalid
    with pytest.raises(ValueError, match=field):
        _parse(_manifest("1.7", setup))


@pytest.mark.parametrize("field", ["base_speed", "new_speed"])
@pytest.mark.parametrize("invalid", [0, 0.0, -1, -100.0])
def test_change_speed_speed_fields_must_be_positive(field, invalid):
    setup = _change_speed_setup()
    setup[field] = invalid
    with pytest.raises(ValueError, match="greater than zero"):
        _parse(_manifest("1.7", setup))


@pytest.mark.parametrize("invalid", [True, False, -1, 0.0, "0", None])
def test_change_speed_action_index_requires_exact_nonnegative_integer(invalid):
    setup = _change_speed_setup()
    setup["action_index"] = invalid
    with pytest.raises(ValueError, match="action_index"):
        _parse(_manifest("1.7", setup))


def test_change_speed_action_index_must_address_declared_action():
    setup = _change_speed_setup()
    setup["action_index"] = 1
    with pytest.raises(ValueError, match="declared action"):
        _parse(_manifest("1.7", setup))


@pytest.mark.parametrize("initial_av", [0, -10.0])
def test_change_speed_initial_av_is_finite_but_not_newly_range_restricted(initial_av):
    parsed = _parse(
        _manifest("1.7", _change_speed_setup(initial_av=initial_av))
    )
    assert parsed.cases[0].setup.initial_av == initial_av


def test_locked_v1_7_manifest_contains_exact_eight_reviewed_cases_in_order():
    manifest = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)

    assert len(manifest.cases) == 8
    assert [case.case_id for case in manifest.cases] == CASE_IDS
    eighth = manifest.cases[7]
    assert eighth.expected_path == FIXTURES[-1][0].resolve()
    assert eighth.expected_sha256 == FIXTURES[-1][2]
    assert eighth.stream_id == "arch-038-reviewed-axis"
    assert eighth.actor_id == "speed-actor"
    assert [action.action_id for action in eighth.actions] == ["reviewed-change-speed"]
    assert [action.name for action in eighth.actions] == ["reviewed-change-speed"]
    assert [action.ends_turn for action in eighth.actions] == [False]
    assert eighth.setup == RuntimeActionSessionRegressionChangeSpeedSetup(
        target_id="speed-actor",
        target_name="Speed Actor",
        team="ally",
        base_speed=100,
        initial_av=80,
        action_index=0,
        new_speed=200,
    )


def test_locked_runtime_lane_passes_eight_of_eight_with_expected_counts_and_digests():
    report = run_runtime_action_session_regression(
        load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    )

    assert report.passed is True
    assert report.total == 8
    assert report.passed_count == 8
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
    ]
    assert [result.details["expected_sha256"] for result in report.results] == [
        item[2] for item in FIXTURES
    ]
    actual_sha256 = report.results[7].details["actual_sha256"]
    assert len(actual_sha256) == 64
    assert all(character in "0123456789abcdef" for character in actual_sha256)


def test_change_speed_harness_change_surfaces_existing_structured_after_av_divergence():
    locked = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    case = locked.cases[7]
    assert isinstance(case.setup, RuntimeActionSessionRegressionChangeSpeedSetup)
    changed = replace(case, setup=replace(case.setup, new_speed=160))

    report = run_runtime_action_session_regression(
        RuntimeActionSessionRegressionManifest(
            manifest_id="arch-039-controlled-change-speed-mismatch",
            path=ROOT / "arch_039_controlled_change_speed_mismatch.json",
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
        "/event/payload/legacy_data/after_av"
    )


def test_all_eight_reviewed_fixture_byte_identities_remain_exact():
    for path, size, digest in FIXTURES:
        payload = path.read_bytes()
        assert len(payload) == size
        assert hashlib.sha256(payload).hexdigest() == digest


def test_change_speed_regression_harness_is_closed_and_explicitly_targeted():
    manifest_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "manifest.py"
    ).read_text(encoding="utf-8")
    runner_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "runner.py"
    ).read_text(encoding="utf-8")
    combined = manifest_source + runner_source

    assert 'kind == "CHANGE_SPEED"' in manifest_source
    assert "RuntimeActionSessionRegressionChangeSpeedSetup" in manifest_source
    assert "ChangeSpeed" in runner_source
    assert (
        "ChangeSpeed(target_ids=[setup.target_id], new_speed=setup.new_speed)"
        in runner_source
    )

    for forbidden in (
        "ImmediateAction",
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


def test_arch_038_fixture_is_not_added_to_legacy_manifest():
    legacy_text = LEGACY_MANIFEST_PATH.read_text(encoding="utf-8")
    assert "arch_038_reviewed_change_speed_expected.json" not in legacy_text


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
