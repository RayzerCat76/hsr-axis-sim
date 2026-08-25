import hashlib
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from hsr_axis_sim.regression.manifest import load_regression_manifest
from hsr_axis_sim.regression.runner import run_regression
from hsr_axis_sim.runtime_action_session_regression.manifest import (
    RUNTIME_ACTION_SESSION_REGRESSION_SUPPORTED_VERSIONS,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_0,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_1,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_2,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_3,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_4,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5,
    RuntimeActionSessionRegressionEnergyConsumeSetup,
    RuntimeActionSessionRegressionEnergyGainSetup,
    RuntimeActionSessionRegressionManifest,
    RuntimeActionSessionRegressionSkillPointConsumeSetup,
    RuntimeActionSessionRegressionSkillPointGainSetup,
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
ARCH_017_PATH = FIXTURE_DIR / "arch_017_reviewed_action_session_expected.json"
ARCH_021_PATH = FIXTURE_DIR / "arch_021_reviewed_clamped_energy_expected.json"
ARCH_023_PATH = FIXTURE_DIR / "arch_023_reviewed_clamped_skill_point_expected.json"
ARCH_025_PATH = FIXTURE_DIR / "arch_025_reviewed_energy_consume_expected.json"
ARCH_027_PATH = FIXTURE_DIR / "arch_027_reviewed_skill_point_consume_expected.json"
ARCH_017_SHA256 = "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66"
ARCH_021_SHA256 = "4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605"
ARCH_023_SHA256 = "fc359b367c2922ed39e059f89ad16845ba215508292cfa43ca2ab6031c4c9ba9"
ARCH_025_SHA256 = "7d61528687a5a2f499249e0f914f6f2f50975c7c153165eddd5e116f3ed19a75"
ARCH_027_SHA256 = "d0dcf128f3a28f691324f4e9295b7bcd66460598186f6059d4619f55e8ae39ec"
ARCH_017_RELATIVE = (
    "hsr_axis_sim/data/runtime_golden_fixtures/"
    "arch_017_reviewed_action_session_expected.json"
)


def _base_case():
    return {
        "id": "arch-017-reviewed-static-action-session",
        "expected_path": ARCH_017_RELATIVE,
        "expected_sha256": ARCH_017_SHA256,
        "stream_id": "arch-017-reviewed-static",
        "actor_id": "reviewed-actor",
        "actions": [
            {
                "action_id": "reviewed-action-a",
                "name": "reviewed-action-a",
                "ends_turn": False,
            }
        ],
    }


def _energy_gain_setup():
    return {
        "kind": "ENERGY_GAIN",
        "target_id": "resource-target",
        "target_name": "resource-target",
        "team": "ally",
        "base_speed": 100,
        "initial_energy": 90,
        "max_energy": 100,
        "action_index": 0,
        "amount": 25,
    }


def _skill_point_gain_setup():
    return {
        "kind": "SKILL_POINT_GAIN",
        "initial_skill_points": 4,
        "max_skill_points": 5,
        "action_index": 0,
        "amount": 3,
    }


def _energy_consume_setup():
    return {
        "kind": "ENERGY_CONSUME",
        "target_id": "consume-target",
        "target_name": "consume-target",
        "team": "ally",
        "base_speed": 100,
        "initial_energy": 80,
        "max_energy": 100,
        "action_index": 0,
        "amount": 30,
    }


def _skill_point_consume_setup():
    return {
        "kind": "SKILL_POINT_CONSUME",
        "initial_skill_points": 4,
        "max_skill_points": 5,
        "action_index": 0,
        "amount": 2,
    }


def _manifest(version: str, setup_marker=...):
    case = _base_case()
    if setup_marker is not ...:
        case["setup"] = setup_marker
    return {
        "schema": "hsr_runtime_action_session_regression",
        "version": version,
        "manifest_id": "arch-028-version-probe",
        "cases": [case],
    }


def _parse(data):
    return runtime_action_session_regression_manifest_from_dict(
        data,
        ROOT / "arch_028_synthetic_manifest.json",
    )


def test_supported_versions_preserve_v1_0_through_v1_5():
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_0 == "1.0"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_1 == "1.1"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_2 == "1.2"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_3 == "1.3"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_4 == "1.4"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5 == "1.5"
    assert RUNTIME_ACTION_SESSION_REGRESSION_SUPPORTED_VERSIONS[:6] == (
        "1.0",
        "1.1",
        "1.2",
        "1.3",
        "1.4",
        "1.5",
    )


def test_v1_3_explicitly_rejects_skill_point_consume_as_v1_4_syntax():
    with pytest.raises(ValueError, match="requires manifest version '1.4'"):
        _parse(
            _manifest(
                RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_3,
                _skill_point_consume_setup(),
            )
        )


def test_historical_v1_4_requires_setup_and_accepts_exact_five_closed_kinds():
    with pytest.raises(ValueError, match="missing required field"):
        _parse(_manifest(RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_4))

    empty = _parse(
        _manifest(
            RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_4,
            {"kind": "EMPTY"},
        )
    )
    energy_gain = _parse(
        _manifest(
            RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_4,
            _energy_gain_setup(),
        )
    )
    skill_point_gain = _parse(
        _manifest(
            RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_4,
            _skill_point_gain_setup(),
        )
    )
    energy_consume = _parse(
        _manifest(
            RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_4,
            _energy_consume_setup(),
        )
    )
    skill_point_consume = _parse(
        _manifest(
            RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_4,
            _skill_point_consume_setup(),
        )
    )

    assert empty.cases[0].setup is None
    assert isinstance(
        energy_gain.cases[0].setup,
        RuntimeActionSessionRegressionEnergyGainSetup,
    )
    assert isinstance(
        skill_point_gain.cases[0].setup,
        RuntimeActionSessionRegressionSkillPointGainSetup,
    )
    assert isinstance(
        energy_consume.cases[0].setup,
        RuntimeActionSessionRegressionEnergyConsumeSetup,
    )
    assert skill_point_consume.cases[0].setup == (
        RuntimeActionSessionRegressionSkillPointConsumeSetup(
            initial_skill_points=4,
            max_skill_points=5,
            action_index=0,
            amount=2,
        )
    )


def test_skill_point_consume_setup_is_frozen():
    setup = RuntimeActionSessionRegressionSkillPointConsumeSetup(
        initial_skill_points=4,
        max_skill_points=5,
        action_index=0,
        amount=2,
    )
    with pytest.raises(FrozenInstanceError):
        setup.amount = 1


def test_v1_4_skill_point_consume_fields_are_exact_and_unknown_kind_is_rejected():
    extra = _skill_point_consume_setup()
    extra["mode"] = "consume"
    with pytest.raises(ValueError, match="unsupported field"):
        _parse(_manifest("1.4", extra))

    missing = _skill_point_consume_setup()
    missing.pop("amount")
    with pytest.raises(ValueError, match="missing required field"):
        _parse(_manifest("1.4", missing))

    unknown = _skill_point_consume_setup()
    unknown["kind"] = "GENERIC_RESOURCE_EFFECT"
    with pytest.raises(ValueError, match="kind"):
        _parse(_manifest("1.4", unknown))


@pytest.mark.parametrize("field", ["initial_skill_points", "max_skill_points", "amount"])
@pytest.mark.parametrize("invalid", [True, False, 1.5, "2", None])
def test_skill_point_consume_resource_values_require_exact_integers(field, invalid):
    setup = _skill_point_consume_setup()
    setup[field] = invalid

    with pytest.raises(ValueError, match=field):
        _parse(_manifest("1.4", setup))


@pytest.mark.parametrize("invalid", [True, False, -1, 0.0, "0", None])
def test_skill_point_consume_action_index_requires_exact_nonnegative_integer(invalid):
    setup = _skill_point_consume_setup()
    setup["action_index"] = invalid

    with pytest.raises(ValueError, match="action_index"):
        _parse(_manifest("1.4", setup))


def test_skill_point_consume_action_index_must_address_declared_action():
    setup = _skill_point_consume_setup()
    setup["action_index"] = 1

    with pytest.raises(ValueError, match="declared action"):
        _parse(_manifest("1.4", setup))


def test_arch_028_fifth_reviewed_case_remains_exact_after_later_promotions():
    manifest = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)

    assert [case.case_id for case in manifest.cases[:5]] == [
        "arch-017-reviewed-static-action-session",
        "arch-021-reviewed-static-clamped-energy",
        "arch-023-reviewed-static-clamped-skill-point",
        "arch-025-reviewed-static-energy-consume",
        "arch-027-reviewed-static-skill-point-consume",
    ]
    fifth = manifest.cases[4]
    assert fifth.expected_path == ARCH_027_PATH.resolve()
    assert fifth.expected_sha256 == ARCH_027_SHA256
    assert fifth.stream_id == "arch-027-reviewed-resource"
    assert fifth.actor_id == "sp-consume-actor"
    assert [action.action_id for action in fifth.actions] == [
        "reviewed-skill-point-consume"
    ]
    assert [action.ends_turn for action in fifth.actions] == [False]
    assert fifth.setup == RuntimeActionSessionRegressionSkillPointConsumeSetup(
        initial_skill_points=4,
        max_skill_points=5,
        action_index=0,
        amount=2,
    )


def test_arch_028_first_five_runtime_cases_still_pass_after_later_promotions():
    report = run_runtime_action_session_regression(
        load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    )

    assert report.passed is True
    assert report.total >= 5
    assert report.passed_count == report.total
    assert [result.case_id for result in report.results[:5]] == [
        "arch-017-reviewed-static-action-session",
        "arch-021-reviewed-static-clamped-energy",
        "arch-023-reviewed-static-clamped-skill-point",
        "arch-025-reviewed-static-energy-consume",
        "arch-027-reviewed-static-skill-point-consume",
    ]
    assert [result.details["record_count"] for result in report.results[:5]] == [
        4,
        3,
        3,
        3,
        3,
    ]
    assert [result.details["expected_sha256"] for result in report.results[:5]] == [
        ARCH_017_SHA256,
        ARCH_021_SHA256,
        ARCH_023_SHA256,
        ARCH_025_SHA256,
        ARCH_027_SHA256,
    ]


def test_skill_point_consume_harness_change_surfaces_reviewed_after_divergence():
    locked = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    case = locked.cases[4]
    assert isinstance(case.setup, RuntimeActionSessionRegressionSkillPointConsumeSetup)
    changed = replace(case, setup=replace(case.setup, amount=1))

    report = run_runtime_action_session_regression(
        RuntimeActionSessionRegressionManifest(
            manifest_id="arch-028-controlled-sp-consume-mismatch",
            path=ROOT / "arch_028_controlled_sp_consume_mismatch.json",
            cases=(changed,),
        )
    )

    assert report.passed is False
    result = report.results[0]
    assert result.error == "Runtime action-session Golden mismatch."
    assert result.details["record_count"] == 3
    assert result.details["first_divergence_record_index"] == 1
    assert result.details["first_divergence_path"] == "/event/payload/legacy_data/after"


def test_all_first_five_reviewed_fixture_byte_identities_remain_exact():
    expected = (
        (ARCH_017_PATH, 3013, ARCH_017_SHA256),
        (ARCH_021_PATH, 2759, ARCH_021_SHA256),
        (ARCH_023_PATH, 2744, ARCH_023_SHA256),
        (ARCH_025_PATH, 2750, ARCH_025_SHA256),
        (ARCH_027_PATH, 2796, ARCH_027_SHA256),
    )
    for path, size, digest in expected:
        payload = path.read_bytes()
        assert len(payload) == size
        assert hashlib.sha256(payload).hexdigest() == digest


def test_runtime_regression_harness_stays_closed_not_generic_effect_dsl():
    manifest_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "manifest.py"
    ).read_text(encoding="utf-8")
    runner_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "runner.py"
    ).read_text(encoding="utf-8")
    combined = manifest_source + runner_source

    for token in (
        "ENERGY_GAIN",
        "SKILL_POINT_GAIN",
        "ENERGY_CONSUME",
        "SKILL_POINT_CONSUME",
    ):
        assert token in manifest_source
    for token in ("GainEnergy", "GainSkillPoint", "ConsumeEnergy", "ConsumeSkillPoint"):
        assert token in runner_source
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
