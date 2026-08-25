import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from hsr_axis_sim.regression.manifest import load_regression_manifest
from hsr_axis_sim.regression.runner import run_regression
from hsr_axis_sim.runtime_action_session_regression.manifest import (
    RUNTIME_ACTION_SESSION_REGRESSION_SUPPORTED_VERSIONS,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_0,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_1,
    RuntimeActionSessionRegressionEnergyGainSetup,
    RuntimeActionSessionRegressionManifest,
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
ARCH_017_SHA256 = "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66"
ARCH_021_SHA256 = "4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605"
ARCH_023_SHA256 = "fc359b367c2922ed39e059f89ad16845ba215508292cfa43ca2ab6031c4c9ba9"
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


def _energy_setup():
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


def _skill_point_setup():
    return {
        "kind": "SKILL_POINT_GAIN",
        "initial_skill_points": 4,
        "max_skill_points": 5,
        "action_index": 0,
        "amount": 3,
    }


def _manifest(version: str, setup_marker=...):
    case = _base_case()
    if setup_marker is not ...:
        case["setup"] = setup_marker
    return {
        "schema": "hsr_runtime_action_session_regression",
        "version": version,
        "manifest_id": "arch-024-version-probe",
        "cases": [case],
    }


def _parse(data):
    return runtime_action_session_regression_manifest_from_dict(
        data,
        ROOT / "arch_024_synthetic_manifest.json",
    )


def test_manifest_versions_are_explicit_and_ordered():
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_0 == "1.0"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_1 == "1.1"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION == "1.2"
    assert RUNTIME_ACTION_SESSION_REGRESSION_SUPPORTED_VERSIONS == (
        "1.0",
        "1.1",
        "1.2",
    )


def test_v1_0_exact_grammar_still_rejects_setup():
    parsed = _parse(_manifest("1.0"))
    assert parsed.cases[0].setup is None

    with pytest.raises(ValueError, match="unsupported field"):
        _parse(_manifest("1.0", {"kind": "EMPTY"}))


def test_v1_1_still_accepts_only_arch022_setup_kinds():
    empty = _parse(_manifest("1.1", {"kind": "EMPTY"}))
    energy = _parse(_manifest("1.1", _energy_setup()))

    assert empty.cases[0].setup is None
    assert isinstance(energy.cases[0].setup, RuntimeActionSessionRegressionEnergyGainSetup)

    with pytest.raises(ValueError, match="requires manifest version '1.2'"):
        _parse(_manifest("1.1", _skill_point_setup()))


def test_v1_2_requires_setup_and_accepts_all_three_closed_kinds():
    with pytest.raises(ValueError, match="missing required field"):
        _parse(_manifest("1.2"))

    empty = _parse(_manifest("1.2", {"kind": "EMPTY"}))
    energy = _parse(_manifest("1.2", _energy_setup()))
    skill_points = _parse(_manifest("1.2", _skill_point_setup()))

    assert empty.cases[0].setup is None
    assert isinstance(energy.cases[0].setup, RuntimeActionSessionRegressionEnergyGainSetup)
    assert skill_points.cases[0].setup == RuntimeActionSessionRegressionSkillPointGainSetup(
        initial_skill_points=4,
        max_skill_points=5,
        action_index=0,
        amount=3,
    )


def test_v1_2_skill_point_gain_fields_are_exact():
    extra = _skill_point_setup()
    extra["target_id"] = "forbidden"
    with pytest.raises(ValueError, match="unsupported field"):
        _parse(_manifest("1.2", extra))

    missing = _skill_point_setup()
    missing.pop("amount")
    with pytest.raises(ValueError, match="missing required field"):
        _parse(_manifest("1.2", missing))

    unknown = _skill_point_setup()
    unknown["kind"] = "GENERIC_EFFECT"
    with pytest.raises(ValueError, match="kind"):
        _parse(_manifest("1.2", unknown))


@pytest.mark.parametrize("field", ["initial_skill_points", "max_skill_points", "amount"])
@pytest.mark.parametrize("invalid", [True, False, 1.5, "3", None])
def test_skill_point_gain_resource_values_require_exact_integers(field, invalid):
    setup = _skill_point_setup()
    setup[field] = invalid

    with pytest.raises(ValueError, match=field):
        _parse(_manifest("1.2", setup))


@pytest.mark.parametrize("invalid", [True, False, -1, 0.0, "0", None])
def test_skill_point_gain_action_index_requires_exact_nonnegative_integer(invalid):
    setup = _skill_point_setup()
    setup["action_index"] = invalid

    with pytest.raises(ValueError, match="action_index"):
        _parse(_manifest("1.2", setup))


def test_skill_point_gain_action_index_must_address_declared_action():
    setup = _skill_point_setup()
    setup["action_index"] = 1

    with pytest.raises(ValueError, match="declared action"):
        _parse(_manifest("1.2", setup))


def test_locked_v1_2_manifest_contains_exact_three_reviewed_cases():
    manifest = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)

    assert [case.case_id for case in manifest.cases] == [
        "arch-017-reviewed-static-action-session",
        "arch-021-reviewed-static-clamped-energy",
        "arch-023-reviewed-static-clamped-skill-point",
    ]
    first, second, third = manifest.cases
    assert first.setup is None
    assert second.setup == RuntimeActionSessionRegressionEnergyGainSetup(
        target_id="resource-target",
        target_name="resource-target",
        team="ally",
        base_speed=100,
        initial_energy=90,
        max_energy=100,
        action_index=0,
        amount=25,
    )
    assert third.expected_sha256 == ARCH_023_SHA256
    assert third.stream_id == "arch-023-reviewed-resource"
    assert third.actor_id == "sp-actor"
    assert [action.action_id for action in third.actions] == [
        "reviewed-clamped-skill-point"
    ]
    assert [action.ends_turn for action in third.actions] == [False]
    assert third.setup == RuntimeActionSessionRegressionSkillPointGainSetup(
        initial_skill_points=4,
        max_skill_points=5,
        action_index=0,
        amount=3,
    )


def test_locked_runtime_lane_passes_three_of_three_with_expected_record_counts():
    report = run_runtime_action_session_regression(
        load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    )

    assert report.passed is True
    assert report.total == 3
    assert report.passed_count == 3
    assert report.failed_count == 0
    assert [result.case_id for result in report.results] == [
        "arch-017-reviewed-static-action-session",
        "arch-021-reviewed-static-clamped-energy",
        "arch-023-reviewed-static-clamped-skill-point",
    ]
    assert [result.details["record_count"] for result in report.results] == [4, 3, 3]
    assert [result.details["expected_sha256"] for result in report.results] == [
        ARCH_017_SHA256,
        ARCH_021_SHA256,
        ARCH_023_SHA256,
    ]


def test_skill_point_harness_change_surfaces_reviewed_requested_delta_divergence():
    locked = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    case = locked.cases[2]
    assert isinstance(case.setup, RuntimeActionSessionRegressionSkillPointGainSetup)
    changed = replace(case, setup=replace(case.setup, amount=2))

    report = run_runtime_action_session_regression(
        RuntimeActionSessionRegressionManifest(
            manifest_id="arch-024-controlled-sp-mismatch",
            path=ROOT / "arch_024_controlled_sp_mismatch.json",
            cases=(changed,),
        )
    )

    assert report.passed is False
    result = report.results[0]
    assert result.error == "Runtime action-session Golden mismatch."
    assert result.details["record_count"] == 3
    assert result.details["first_divergence_record_index"] == 1
    assert result.details["first_divergence_path"] == (
        "/event/payload/legacy_data/requested_delta"
    )


def test_all_three_reviewed_fixture_byte_identities_remain_exact():
    expected = (
        (ARCH_017_PATH, 3013, ARCH_017_SHA256),
        (ARCH_021_PATH, 2759, ARCH_021_SHA256),
        (ARCH_023_PATH, 2744, ARCH_023_SHA256),
    )
    for path, size, digest in expected:
        payload = path.read_bytes()
        assert len(payload) == size
        assert hashlib.sha256(payload).hexdigest() == digest


def test_runtime_regression_setup_remains_closed_and_non_generic():
    manifest_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "manifest.py"
    ).read_text(encoding="utf-8")
    runner_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "runner.py"
    ).read_text(encoding="utf-8")
    combined = manifest_source + runner_source

    assert "ENERGY_GAIN" in combined
    assert "SKILL_POINT_GAIN" in combined
    assert "GainEnergy" in runner_source
    assert "GainSkillPoint" in runner_source
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


def test_legacy_regression_and_trace_evidence_are_unchanged():
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
