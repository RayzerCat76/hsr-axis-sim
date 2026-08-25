import hashlib
import math
from dataclasses import replace
from pathlib import Path

import pytest

from hsr_axis_sim.regression.manifest import load_regression_manifest
from hsr_axis_sim.regression.runner import run_regression
from hsr_axis_sim.runtime_action_session_regression.manifest import (
    RUNTIME_ACTION_SESSION_REGRESSION_LEGACY_VERSION,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_1,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_2,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_3,
    RuntimeActionSessionRegressionCase,
    RuntimeActionSessionRegressionEnergyGainSetup,
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
ARCH_017_PATH = (
    ROOT
    / "hsr_axis_sim"
    / "data"
    / "runtime_golden_fixtures"
    / "arch_017_reviewed_action_session_expected.json"
)
ARCH_021_PATH = (
    ROOT
    / "hsr_axis_sim"
    / "data"
    / "runtime_golden_fixtures"
    / "arch_021_reviewed_clamped_energy_expected.json"
)
ARCH_017_SHA256 = "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66"
ARCH_021_SHA256 = "4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605"
ARCH_017_RELATIVE = (
    "hsr_axis_sim/data/runtime_golden_fixtures/"
    "arch_017_reviewed_action_session_expected.json"
)
ARCH_021_RELATIVE = (
    "hsr_axis_sim/data/runtime_golden_fixtures/"
    "arch_021_reviewed_clamped_energy_expected.json"
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
            },
            {
                "action_id": "reviewed-action-b",
                "name": "reviewed-action-b",
                "ends_turn": False,
            },
        ],
    }


def _manifest(version: str, *, setup_marker=...):
    case = _base_case()
    if setup_marker is not ...:
        case["setup"] = setup_marker
    return {
        "schema": "hsr_runtime_action_session_regression",
        "version": version,
        "manifest_id": "arch-022-test",
        "cases": [case],
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


def _parse(data):
    return runtime_action_session_regression_manifest_from_dict(
        data,
        ROOT / "arch_022_synthetic_manifest.json",
    )


def test_manifest_versions_preserve_v1_0_and_explicit_v1_1_contract():
    assert RUNTIME_ACTION_SESSION_REGRESSION_LEGACY_VERSION == "1.0"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_1 == "1.1"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_2 == "1.2"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_3 == "1.3"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION == "1.4"

    parsed = _parse(_manifest("1.0"))

    assert len(parsed.cases) == 1
    assert parsed.cases[0].setup is None
    assert [action.action_id for action in parsed.cases[0].actions] == [
        "reviewed-action-a",
        "reviewed-action-b",
    ]


def test_v1_0_rejects_new_setup_and_v1_1_requires_setup():
    with pytest.raises(ValueError, match="unsupported field"):
        _parse(_manifest("1.0", setup_marker={"kind": "EMPTY"}))

    with pytest.raises(ValueError, match="missing required field"):
        _parse(_manifest("1.1"))


def test_v1_1_empty_setup_is_exact_and_maps_to_legacy_empty_state_semantics():
    parsed = _parse(_manifest("1.1", setup_marker={"kind": "EMPTY"}))
    assert parsed.cases[0].setup is None

    extra = _manifest("1.1", setup_marker={"kind": "EMPTY", "extra": True})
    with pytest.raises(ValueError, match="unsupported field"):
        _parse(extra)


def test_v1_1_energy_gain_setup_loads_exact_typed_contract():
    parsed = _parse(_manifest("1.1", setup_marker=_energy_setup()))
    setup = parsed.cases[0].setup

    assert isinstance(setup, RuntimeActionSessionRegressionEnergyGainSetup)
    assert setup == RuntimeActionSessionRegressionEnergyGainSetup(
        target_id="resource-target",
        target_name="resource-target",
        team="ally",
        base_speed=100,
        initial_energy=90,
        max_energy=100,
        action_index=0,
        amount=25,
    )


def test_v1_1_energy_gain_rejects_unknown_kind_and_unknown_or_missing_fields():
    unknown_kind = _energy_setup()
    unknown_kind["kind"] = "ARBITRARY_EFFECT"
    with pytest.raises(ValueError, match="kind"):
        _parse(_manifest("1.1", setup_marker=unknown_kind))

    unknown_field = _energy_setup()
    unknown_field["effect_class"] = "GainEnergy"
    with pytest.raises(ValueError, match="unsupported field"):
        _parse(_manifest("1.1", setup_marker=unknown_field))

    missing = _energy_setup()
    missing.pop("amount")
    with pytest.raises(ValueError, match="missing required field"):
        _parse(_manifest("1.1", setup_marker=missing))


@pytest.mark.parametrize(
    "field",
    ["base_speed", "initial_energy", "max_energy", "amount"],
)
@pytest.mark.parametrize("invalid", [True, math.nan, math.inf, -math.inf, "25", None])
def test_energy_gain_numeric_fields_require_finite_non_boolean_numbers(field, invalid):
    setup = _energy_setup()
    setup[field] = invalid

    with pytest.raises(ValueError, match=field):
        _parse(_manifest("1.1", setup_marker=setup))


@pytest.mark.parametrize("invalid", [0, -1, -100])
def test_energy_gain_base_speed_must_be_positive(invalid):
    setup = _energy_setup()
    setup["base_speed"] = invalid

    with pytest.raises(ValueError, match="base_speed"):
        _parse(_manifest("1.1", setup_marker=setup))


@pytest.mark.parametrize("invalid", [True, -1, 1.0, "0", None])
def test_energy_gain_action_index_requires_exact_nonnegative_integer(invalid):
    setup = _energy_setup()
    setup["action_index"] = invalid

    with pytest.raises(ValueError, match="action_index"):
        _parse(_manifest("1.1", setup_marker=setup))


def test_energy_gain_action_index_must_reference_declared_action():
    setup = _energy_setup()
    setup["action_index"] = 2

    with pytest.raises(ValueError, match="declared action"):
        _parse(_manifest("1.1", setup_marker=setup))


@pytest.mark.parametrize("field", ["target_id", "target_name", "team"])
@pytest.mark.parametrize("invalid", ["", None, 3, True])
def test_energy_gain_string_fields_must_be_nonempty_strings(field, invalid):
    setup = _energy_setup()
    setup[field] = invalid

    with pytest.raises(ValueError, match=field):
        _parse(_manifest("1.1", setup_marker=setup))


def test_current_locked_manifest_preserves_arch022_first_two_cases_unchanged():
    manifest = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)

    assert [case.case_id for case in manifest.cases[:2]] == [
        "arch-017-reviewed-static-action-session",
        "arch-021-reviewed-static-clamped-energy",
    ]
    first, second = manifest.cases[:2]
    assert first.setup is None
    assert first.expected_sha256 == ARCH_017_SHA256
    assert first.expected_relative_path == ARCH_017_RELATIVE

    assert second.expected_sha256 == ARCH_021_SHA256
    assert second.expected_relative_path == ARCH_021_RELATIVE
    assert second.stream_id == "arch-021-reviewed-resource"
    assert second.actor_id == "resource-actor"
    assert [action.action_id for action in second.actions] == ["reviewed-clamped-energy"]
    assert [action.ends_turn for action in second.actions] == [False]
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


def test_current_runtime_regression_still_passes_arch022_first_two_cases():
    report = run_runtime_action_session_regression(
        load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    )

    assert report.passed is True
    assert report.total == 5
    assert report.passed_count == 5
    assert report.failed_count == 0
    first, second = report.results[:2]
    assert first.case_id == "arch-017-reviewed-static-action-session"
    assert second.case_id == "arch-021-reviewed-static-clamped-energy"
    assert first.details["record_count"] == 4
    assert first.details["expected_sha256"] == ARCH_017_SHA256
    assert second.details["record_count"] == 3
    assert second.details["expected_sha256"] == ARCH_021_SHA256
    assert len(first.details["actual_sha256"]) == 64
    assert len(second.details["actual_sha256"]) == 64


def test_energy_gain_harness_change_surfaces_reviewed_resource_divergence():
    locked = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    case = locked.cases[1]
    assert isinstance(case.setup, RuntimeActionSessionRegressionEnergyGainSetup)
    changed = replace(case, setup=replace(case.setup, amount=20))
    report = run_runtime_action_session_regression(
        RuntimeActionSessionRegressionManifest(
            manifest_id="arch-022-controlled-resource-mismatch",
            path=ROOT / "arch_022_controlled_resource_mismatch.json",
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


def test_both_reviewed_fixture_byte_identities_remain_exact():
    arch_017 = ARCH_017_PATH.read_bytes()
    arch_021 = ARCH_021_PATH.read_bytes()

    assert len(arch_017) == 3013
    assert hashlib.sha256(arch_017).hexdigest() == ARCH_017_SHA256
    assert len(arch_021) == 2759
    assert hashlib.sha256(arch_021).hexdigest() == ARCH_021_SHA256


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


def test_runtime_regression_harness_stays_narrow_not_generic_effect_dsl():
    manifest_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "manifest.py"
    ).read_text(encoding="utf-8")
    runner_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "runner.py"
    ).read_text(encoding="utf-8")
    combined = manifest_source + runner_source

    assert "ENERGY_GAIN" in combined
    assert "GainEnergy" in runner_source
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


def test_production_lifo_compatibility_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])

    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == [
        "third",
        "second",
        "first",
    ]
