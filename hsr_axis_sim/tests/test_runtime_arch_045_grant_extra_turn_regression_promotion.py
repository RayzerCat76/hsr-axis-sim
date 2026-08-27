import hashlib
import math
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from hsr_axis_sim.regression.manifest import load_regression_manifest
from hsr_axis_sim.regression.runner import run_regression
from hsr_axis_sim.runtime_action_session_regression.manifest import (
    RUNTIME_ACTION_SESSION_REGRESSION_SUPPORTED_VERSIONS,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_8,
    RuntimeActionSessionRegressionGrantExtraTurnSetup,
    RuntimeActionSessionRegressionImmediateActionSetup,
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
    (
        FIXTURE_DIR / "arch_044_reviewed_grant_extra_turn_expected.json",
        2658,
        "57eefb521cb5cf1840e49c36e5c9c85a08281a7014c23ece0e3d5df1e6dfefdd",
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
    "arch-044-reviewed-static-grant-extra-turn",
]

ACCEPTED_FIRST_NINE_ACTUAL_SHA256 = [
    "452d52be7dec07ddebe0ca5ec0ca3cf58d695bd2312ada684d70aa22891435d0",
    "80dda34881d32267ff819e985d7ed95256185e0c539f6e1b313aa67afcab9d3a",
    "0004d8947f3b7ce8e692af527f40579db94609e4ed3ae0b63bf40397ec4af043",
    "230e21dc23da2c37d89f26903dbd636463f5b0ec9adc7298e99331f3e24efb5f",
    "7a945e7016ffa4a6c074f563d7f0edf288239e92f596810cd434922e8fd5c525",
    "13d26b8efcb0db450445c036f49b31eec4ca346ca9d714f7e221bc084941a6ca",
    "c47754957a756bd03624aafdcd78e14ecbaed059cce0c99fddb0d116c88bde77",
    "a75555d3544a27638781a274a01ff8ee031e6394369be5c3c93c32dfed4c6698",
    "b41181b9bb09ec516d27f78a99ef455a69c2b5e678d93f8eaa5f94effdde8cb7",
]


def _base_case():
    return {
        "id": "arch-044-reviewed-static-grant-extra-turn",
        "expected_path": (
            "hsr_axis_sim/data/runtime_golden_fixtures/"
            "arch_044_reviewed_grant_extra_turn_expected.json"
        ),
        "expected_sha256": FIXTURES[-1][2],
        "stream_id": "arch-044-reviewed-axis",
        "actor_id": "extra-turn-actor",
        "actions": [
            {
                "action_id": "reviewed-grant-extra-turn",
                "name": "reviewed-grant-extra-turn",
                "ends_turn": False,
            }
        ],
    }


def _grant_setup(**changes):
    setup = {
        "kind": "GRANT_EXTRA_TURN",
        "target_id": "extra-turn-target",
        "target_name": "Extra Turn Target",
        "team": "ally",
        "base_speed": 100,
        "action_index": 0,
    }
    setup.update(changes)
    return setup


def _immediate_setup():
    return {
        "kind": "IMMEDIATE_ACTION",
        "target_id": "immediate-actor",
        "target_name": "Immediate Actor",
        "team": "ally",
        "base_speed": 100,
        "initial_av": 80,
        "action_index": 0,
    }


def _manifest(version: str, setup):
    case = _base_case()
    case["setup"] = setup
    return {
        "schema": "hsr_runtime_action_session_regression",
        "version": version,
        "manifest_id": "arch-045-version-probe",
        "cases": [case],
    }


def _parse(data):
    return runtime_action_session_regression_manifest_from_dict(
        data,
        ROOT / "arch_045_synthetic_manifest.json",
    )


def test_supported_versions_are_exactly_v1_0_through_v1_9():
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_8 == "1.8"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION == "1.9"
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
        "1.9",
    )


def test_v1_8_explicitly_rejects_grant_extra_turn_as_v1_9_syntax():
    with pytest.raises(
        ValueError,
        match="GRANT_EXTRA_TURN.*requires manifest version '1.9'",
    ):
        _parse(_manifest(RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_8, _grant_setup()))


def test_v1_9_accepts_exact_frozen_grant_extra_turn_setup():
    parsed = _parse(_manifest(RUNTIME_ACTION_SESSION_REGRESSION_VERSION, _grant_setup()))
    assert parsed.cases[0].setup == RuntimeActionSessionRegressionGrantExtraTurnSetup(
        target_id="extra-turn-target",
        target_name="Extra Turn Target",
        team="ally",
        base_speed=100,
        action_index=0,
    )
    with pytest.raises(FrozenInstanceError):
        parsed.cases[0].setup.base_speed = 110


def test_grant_extra_turn_fields_are_exact():
    extra = _grant_setup(mode="priority")
    with pytest.raises(ValueError, match="unsupported field"):
        _parse(_manifest("1.9", extra))

    missing = _grant_setup()
    missing.pop("target_id")
    with pytest.raises(ValueError, match="missing required field"):
        _parse(_manifest("1.9", missing))


@pytest.mark.parametrize("field", ["target_id", "target_name", "team"])
@pytest.mark.parametrize("invalid", ["", None, 1, False])
def test_grant_extra_turn_identity_fields_require_non_empty_strings(field, invalid):
    setup = _grant_setup(**{field: invalid})
    with pytest.raises(ValueError, match=field):
        _parse(_manifest("1.9", setup))


@pytest.mark.parametrize(
    "invalid",
    [True, False, "100", None, 0, 0.0, -1, -100.0, math.inf, -math.inf, math.nan],
)
def test_grant_extra_turn_base_speed_requires_positive_finite_non_boolean_number(invalid):
    setup = _grant_setup(base_speed=invalid)
    with pytest.raises(ValueError, match="base_speed"):
        _parse(_manifest("1.9", setup))


@pytest.mark.parametrize("invalid", [True, False, -1, 0.0, "0", None])
def test_grant_extra_turn_action_index_requires_exact_nonnegative_integer(invalid):
    setup = _grant_setup(action_index=invalid)
    with pytest.raises(ValueError, match="action_index"):
        _parse(_manifest("1.9", setup))


def test_grant_extra_turn_action_index_must_address_declared_action():
    setup = _grant_setup(action_index=1)
    with pytest.raises(ValueError, match="declared action"):
        _parse(_manifest("1.9", setup))


def test_immediate_action_remains_valid_in_v1_8_and_v1_9():
    for version in (RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_8, "1.9"):
        parsed = _parse(_manifest(version, _immediate_setup()))
        assert parsed.cases[0].setup == RuntimeActionSessionRegressionImmediateActionSetup(
            target_id="immediate-actor",
            target_name="Immediate Actor",
            team="ally",
            base_speed=100,
            initial_av=80,
            action_index=0,
        )


def test_locked_v1_9_manifest_contains_exact_ten_reviewed_cases_in_order():
    manifest = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)

    assert len(manifest.cases) == 10
    assert [case.case_id for case in manifest.cases] == CASE_IDS
    tenth = manifest.cases[9]
    assert tenth.expected_path == FIXTURES[-1][0].resolve()
    assert tenth.expected_sha256 == FIXTURES[-1][2]
    assert tenth.stream_id == "arch-044-reviewed-axis"
    assert tenth.actor_id == "extra-turn-actor"
    assert [action.action_id for action in tenth.actions] == ["reviewed-grant-extra-turn"]
    assert [action.name for action in tenth.actions] == ["reviewed-grant-extra-turn"]
    assert [action.ends_turn for action in tenth.actions] == [False]
    assert tenth.setup == RuntimeActionSessionRegressionGrantExtraTurnSetup(
        target_id="extra-turn-target",
        target_name="Extra Turn Target",
        team="ally",
        base_speed=100,
        action_index=0,
    )


def test_locked_runtime_lane_passes_ten_of_ten_and_preserves_first_nine_actual_digests():
    report = run_runtime_action_session_regression(
        load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    )

    assert report.passed is True
    assert report.total == 10
    assert report.passed_count == 10
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
        3,
    ]
    assert [result.details["expected_sha256"] for result in report.results] == [
        item[2] for item in FIXTURES
    ]
    assert [
        result.details["actual_sha256"] for result in report.results[:9]
    ] == ACCEPTED_FIRST_NINE_ACTUAL_SHA256
    tenth_actual = report.results[9].details["actual_sha256"]
    assert len(tenth_actual) == 64
    assert all(character in "0123456789abcdef" for character in tenth_actual)


def test_all_ten_reviewed_fixture_byte_identities_remain_exact():
    for path, size, digest in FIXTURES:
        payload = path.read_bytes()
        assert len(payload) == size
        assert hashlib.sha256(payload).hexdigest() == digest


def test_grant_extra_turn_regression_harness_is_closed_and_explicitly_targeted():
    manifest_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "manifest.py"
    ).read_text(encoding="utf-8")
    runner_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "runner.py"
    ).read_text(encoding="utf-8")
    combined = manifest_source + runner_source

    assert 'kind == "GRANT_EXTRA_TURN"' in manifest_source
    assert "RuntimeActionSessionRegressionGrantExtraTurnSetup" in manifest_source
    assert "GrantExtraTurn" in runner_source
    assert "GrantExtraTurn(target_ids=[setup.target_id])" in runner_source

    for forbidden in (
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


def test_arch_044_fixture_is_not_added_to_legacy_manifest():
    legacy_text = LEGACY_MANIFEST_PATH.read_text(encoding="utf-8")
    assert "arch_044_reviewed_grant_extra_turn_expected.json" not in legacy_text


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
