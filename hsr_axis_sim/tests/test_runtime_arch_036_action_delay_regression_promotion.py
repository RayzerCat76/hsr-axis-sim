import hashlib
import math
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from hsr_axis_sim.regression.manifest import load_regression_manifest
from hsr_axis_sim.regression.runner import run_regression
from hsr_axis_sim.runtime_action_session_regression.manifest import (
    RUNTIME_ACTION_SESSION_REGRESSION_SUPPORTED_VERSIONS,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_4,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_6,
    RuntimeActionSessionRegressionActionAdvanceSetup,
    RuntimeActionSessionRegressionActionDelaySetup,
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
)

CASE_IDS = [
    "arch-017-reviewed-static-action-session",
    "arch-021-reviewed-static-clamped-energy",
    "arch-023-reviewed-static-clamped-skill-point",
    "arch-025-reviewed-static-energy-consume",
    "arch-027-reviewed-static-skill-point-consume",
    "arch-032-reviewed-static-action-advance",
    "arch-035-reviewed-static-action-delay",
]


def _base_case():
    return {
        "id": "arch-035-reviewed-static-action-delay",
        "expected_path": (
            "hsr_axis_sim/data/runtime_golden_fixtures/"
            "arch_035_reviewed_action_delay_expected.json"
        ),
        "expected_sha256": FIXTURES[-1][2],
        "stream_id": "arch-035-reviewed-axis",
        "actor_id": "delay-actor",
        "actions": [
            {
                "action_id": "reviewed-action-delay",
                "name": "reviewed-action-delay",
                "ends_turn": False,
            }
        ],
    }


def _delay_setup(*, percent=0.25, initial_av=30):
    return {
        "kind": "ACTION_DELAY",
        "target_id": "delay-actor",
        "target_name": "Delay Actor",
        "team": "ally",
        "base_speed": 100,
        "initial_av": initial_av,
        "action_index": 0,
        "percent": percent,
    }


def _advance_setup():
    data = _delay_setup(percent=0.5, initial_av=80)
    data.update(
        {
            "kind": "ACTION_ADVANCE",
            "target_id": "advance-actor",
            "target_name": "Advance Actor",
        }
    )
    return data


def _manifest(version: str, setup):
    case = _base_case()
    case["setup"] = setup
    return {
        "schema": "hsr_runtime_action_session_regression",
        "version": version,
        "manifest_id": "arch-036-version-probe",
        "cases": [case],
    }


def _parse(data):
    return runtime_action_session_regression_manifest_from_dict(
        data,
        ROOT / "arch_036_synthetic_manifest.json",
    )


def test_arch_036_v1_6_remains_in_supported_version_history():
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5 == "1.5"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_6 == "1.6"
    assert RUNTIME_ACTION_SESSION_REGRESSION_SUPPORTED_VERSIONS[:7] == (
        "1.0",
        "1.1",
        "1.2",
        "1.3",
        "1.4",
        "1.5",
        "1.6",
    )


def test_v1_5_explicitly_rejects_action_delay_as_v1_6_syntax():
    with pytest.raises(ValueError, match="ACTION_DELAY.*requires manifest version '1.6'"):
        _parse(_manifest(RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5, _delay_setup()))


def test_v1_6_accepts_exact_frozen_action_delay_setup():
    parsed = _parse(
        _manifest(RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_6, _delay_setup())
    )
    assert parsed.cases[0].setup == RuntimeActionSessionRegressionActionDelaySetup(
        target_id="delay-actor",
        target_name="Delay Actor",
        team="ally",
        base_speed=100,
        initial_av=30,
        action_index=0,
        percent=0.25,
    )
    with pytest.raises(FrozenInstanceError):
        parsed.cases[0].setup.percent = 0.2


def test_action_advance_remains_v1_5_and_v1_6_syntax_but_not_v1_4():
    with pytest.raises(ValueError, match="ACTION_ADVANCE.*requires manifest version '1.5'"):
        _parse(_manifest(RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_4, _advance_setup()))

    for version in (
        RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5,
        RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_6,
    ):
        parsed = _parse(_manifest(version, _advance_setup()))
        assert isinstance(parsed.cases[0].setup, RuntimeActionSessionRegressionActionAdvanceSetup)


def test_action_delay_fields_are_exact():
    extra = _delay_setup()
    extra["mode"] = "delay"
    with pytest.raises(ValueError, match="unsupported field"):
        _parse(_manifest("1.6", extra))

    missing = _delay_setup()
    missing.pop("percent")
    with pytest.raises(ValueError, match="missing required field"):
        _parse(_manifest("1.6", missing))


@pytest.mark.parametrize("field", ["target_id", "target_name", "team"])
@pytest.mark.parametrize("invalid", ["", None, 1, False])
def test_action_delay_identity_fields_require_non_empty_strings(field, invalid):
    setup = _delay_setup()
    setup[field] = invalid
    with pytest.raises(ValueError, match=field):
        _parse(_manifest("1.6", setup))


@pytest.mark.parametrize("field", ["base_speed", "initial_av", "percent"])
@pytest.mark.parametrize(
    "invalid",
    [True, False, "1", None, math.inf, -math.inf, math.nan],
)
def test_action_delay_numeric_fields_require_finite_non_boolean_numbers(field, invalid):
    setup = _delay_setup()
    setup[field] = invalid
    with pytest.raises(ValueError, match=field):
        _parse(_manifest("1.6", setup))


@pytest.mark.parametrize("invalid", [0, 0.0, -1, -100.0])
def test_action_delay_base_speed_must_be_positive(invalid):
    setup = _delay_setup()
    setup["base_speed"] = invalid
    with pytest.raises(ValueError, match="greater than zero"):
        _parse(_manifest("1.6", setup))


@pytest.mark.parametrize("invalid", [True, False, -1, 0.0, "0", None])
def test_action_delay_action_index_requires_exact_nonnegative_integer(invalid):
    setup = _delay_setup()
    setup["action_index"] = invalid
    with pytest.raises(ValueError, match="action_index"):
        _parse(_manifest("1.6", setup))


def test_action_delay_action_index_must_address_declared_action():
    setup = _delay_setup()
    setup["action_index"] = 1
    with pytest.raises(ValueError, match="declared action"):
        _parse(_manifest("1.6", setup))


@pytest.mark.parametrize("percent", [0, -0.1, -1.0])
def test_action_delay_percent_is_not_silently_restricted_positive(percent):
    parsed = _parse(_manifest("1.6", _delay_setup(percent=percent)))
    setup = parsed.cases[0].setup
    assert isinstance(setup, RuntimeActionSessionRegressionActionDelaySetup)
    assert setup.percent == percent


@pytest.mark.parametrize("initial_av", [0, -10.0])
def test_action_delay_initial_av_is_finite_but_not_newly_range_restricted(initial_av):
    parsed = _parse(_manifest("1.6", _delay_setup(initial_av=initial_av)))
    assert parsed.cases[0].setup.initial_av == initial_av


def test_arch_036_first_seven_reviewed_cases_remain_exact_and_ordered():
    manifest = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)

    assert [case.case_id for case in manifest.cases[:7]] == CASE_IDS
    seventh = manifest.cases[6]
    assert seventh.expected_path == FIXTURES[-1][0].resolve()
    assert seventh.expected_sha256 == FIXTURES[-1][2]
    assert seventh.stream_id == "arch-035-reviewed-axis"
    assert seventh.actor_id == "delay-actor"
    assert [action.action_id for action in seventh.actions] == ["reviewed-action-delay"]
    assert [action.name for action in seventh.actions] == ["reviewed-action-delay"]
    assert [action.ends_turn for action in seventh.actions] == [False]
    assert seventh.setup == RuntimeActionSessionRegressionActionDelaySetup(
        target_id="delay-actor",
        target_name="Delay Actor",
        team="ally",
        base_speed=100,
        initial_av=30,
        action_index=0,
        percent=0.25,
    )


def test_arch_036_first_seven_cases_still_pass_seven_of_seven():
    locked = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    manifest = RuntimeActionSessionRegressionManifest(
        manifest_id="arch-036-preserved-seven",
        path=ROOT / "arch_036_preserved_seven.json",
        cases=locked.cases[:7],
    )
    report = run_runtime_action_session_regression(manifest)

    assert report.passed is True
    assert report.total == 7
    assert report.passed_count == 7
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
    ]
    assert [result.details["expected_sha256"] for result in report.results] == [
        item[2] for item in FIXTURES
    ]
    actual_sha256 = report.results[6].details["actual_sha256"]
    assert len(actual_sha256) == 64
    assert all(character in "0123456789abcdef" for character in actual_sha256)


def test_action_delay_harness_change_surfaces_structured_after_av_divergence():
    locked = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    case = locked.cases[6]
    assert isinstance(case.setup, RuntimeActionSessionRegressionActionDelaySetup)
    changed = replace(case, setup=replace(case.setup, percent=0.2))

    report = run_runtime_action_session_regression(
        RuntimeActionSessionRegressionManifest(
            manifest_id="arch-036-controlled-action-delay-mismatch",
            path=ROOT / "arch_036_controlled_action_delay_mismatch.json",
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
        "/event/payload/action_delay/after_av"
    )


def test_all_seven_reviewed_fixture_byte_identities_remain_exact():
    for path, size, digest in FIXTURES:
        payload = path.read_bytes()
        assert len(payload) == size
        assert hashlib.sha256(payload).hexdigest() == digest


def test_action_delay_regression_harness_is_closed_and_explicitly_targeted():
    manifest_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "manifest.py"
    ).read_text(encoding="utf-8")
    runner_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "runner.py"
    ).read_text(encoding="utf-8")
    combined = manifest_source + runner_source

    assert 'kind == "ACTION_DELAY"' in manifest_source
    assert "RuntimeActionSessionRegressionActionDelaySetup" in manifest_source
    assert "DelayAction" in runner_source
    assert "DelayAction(target_ids=[setup.target_id], percent=setup.percent)" in runner_source
    # Later authorized explicit setup kinds may be added without weakening ARCH-036.
    assert 'kind == "IMMEDIATE_ACTION"' in manifest_source
    assert "ImmediateAction" in runner_source

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


def test_arch_035_fixture_is_not_added_to_legacy_manifest():
    legacy_text = LEGACY_MANIFEST_PATH.read_text(encoding="utf-8")
    assert "arch_035_reviewed_action_delay_expected.json" not in legacy_text


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
