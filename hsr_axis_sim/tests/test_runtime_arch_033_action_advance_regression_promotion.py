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
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_4,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5,
    RuntimeActionSessionRegressionActionAdvanceSetup,
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
)

ARCH_033_CASE_IDS = [
    "arch-017-reviewed-static-action-session",
    "arch-021-reviewed-static-clamped-energy",
    "arch-023-reviewed-static-clamped-skill-point",
    "arch-025-reviewed-static-energy-consume",
    "arch-027-reviewed-static-skill-point-consume",
    "arch-032-reviewed-static-action-advance",
]


def _base_case():
    return {
        "id": "arch-032-reviewed-static-action-advance",
        "expected_path": (
            "hsr_axis_sim/data/runtime_golden_fixtures/"
            "arch_032_reviewed_action_advance_expected.json"
        ),
        "expected_sha256": FIXTURES[-1][2],
        "stream_id": "arch-032-reviewed-axis",
        "actor_id": "advance-actor",
        "actions": [
            {
                "action_id": "reviewed-action-advance",
                "name": "reviewed-action-advance",
                "ends_turn": False,
            }
        ],
    }


def _action_advance_setup(*, percent=0.5):
    return {
        "kind": "ACTION_ADVANCE",
        "target_id": "advance-actor",
        "target_name": "Advance Actor",
        "team": "ally",
        "base_speed": 100,
        "initial_av": 80,
        "action_index": 0,
        "percent": percent,
    }


def _manifest(version: str, setup_marker=...):
    case = _base_case()
    if setup_marker is not ...:
        case["setup"] = setup_marker
    return {
        "schema": "hsr_runtime_action_session_regression",
        "version": version,
        "manifest_id": "arch-033-version-probe",
        "cases": [case],
    }


def _parse(data):
    return runtime_action_session_regression_manifest_from_dict(
        data,
        ROOT / "arch_033_synthetic_manifest.json",
    )


def test_supported_versions_now_extend_v1_5_history_with_v1_6():
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_4 == "1.4"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5 == "1.5"
    assert RUNTIME_ACTION_SESSION_REGRESSION_VERSION == "1.6"
    assert RUNTIME_ACTION_SESSION_REGRESSION_SUPPORTED_VERSIONS == (
        "1.0",
        "1.1",
        "1.2",
        "1.3",
        "1.4",
        "1.5",
        "1.6",
    )


def test_v1_4_explicitly_rejects_action_advance_as_v1_5_syntax():
    with pytest.raises(ValueError, match="requires manifest version '1.5'"):
        _parse(
            _manifest(
                RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_4,
                _action_advance_setup(),
            )
        )


def test_v1_5_requires_setup_and_accepts_sixth_closed_action_advance_kind():
    with pytest.raises(ValueError, match="missing required field"):
        _parse(_manifest(RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5))

    parsed = _parse(
        _manifest(
            RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5,
            _action_advance_setup(),
        )
    )
    assert parsed.cases[0].setup == RuntimeActionSessionRegressionActionAdvanceSetup(
        target_id="advance-actor",
        target_name="Advance Actor",
        team="ally",
        base_speed=100,
        initial_av=80,
        action_index=0,
        percent=0.5,
    )

    current = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    assert isinstance(current.cases[1].setup, RuntimeActionSessionRegressionEnergyGainSetup)
    assert isinstance(
        current.cases[2].setup,
        RuntimeActionSessionRegressionSkillPointGainSetup,
    )
    assert isinstance(
        current.cases[3].setup,
        RuntimeActionSessionRegressionEnergyConsumeSetup,
    )
    assert isinstance(
        current.cases[4].setup,
        RuntimeActionSessionRegressionSkillPointConsumeSetup,
    )


def test_action_advance_setup_is_frozen():
    setup = RuntimeActionSessionRegressionActionAdvanceSetup(
        target_id="advance-actor",
        target_name="Advance Actor",
        team="ally",
        base_speed=100,
        initial_av=80,
        action_index=0,
        percent=0.5,
    )
    with pytest.raises(FrozenInstanceError):
        setup.percent = 0.4


def test_action_advance_fields_are_exact_and_unknown_kind_is_rejected():
    extra = _action_advance_setup()
    extra["mode"] = "advance"
    with pytest.raises(ValueError, match="unsupported field"):
        _parse(_manifest("1.5", extra))

    missing = _action_advance_setup()
    missing.pop("percent")
    with pytest.raises(ValueError, match="missing required field"):
        _parse(_manifest("1.5", missing))

    unknown = _action_advance_setup()
    unknown["kind"] = "GENERIC_AXIS_EFFECT"
    with pytest.raises(ValueError, match="kind"):
        _parse(_manifest("1.5", unknown))


@pytest.mark.parametrize("field", ["target_id", "target_name", "team"])
@pytest.mark.parametrize("invalid", ["", None, 1, False])
def test_action_advance_identity_fields_require_non_empty_strings(field, invalid):
    setup = _action_advance_setup()
    setup[field] = invalid
    with pytest.raises(ValueError, match=field):
        _parse(_manifest("1.5", setup))


@pytest.mark.parametrize("field", ["base_speed", "initial_av", "percent"])
@pytest.mark.parametrize(
    "invalid",
    [True, False, "1", None, math.inf, -math.inf, math.nan],
)
def test_action_advance_numeric_fields_require_finite_non_boolean_numbers(field, invalid):
    setup = _action_advance_setup()
    setup[field] = invalid
    with pytest.raises(ValueError, match=field):
        _parse(_manifest("1.5", setup))


@pytest.mark.parametrize("invalid", [0, 0.0, -1, -100.0])
def test_action_advance_base_speed_must_be_positive(invalid):
    setup = _action_advance_setup()
    setup["base_speed"] = invalid
    with pytest.raises(ValueError, match="greater than zero"):
        _parse(_manifest("1.5", setup))


@pytest.mark.parametrize("percent", [0, -0.1, -1.0])
def test_action_advance_percent_is_not_silently_restricted_positive(percent):
    parsed = _parse(_manifest("1.5", _action_advance_setup(percent=percent)))
    setup = parsed.cases[0].setup
    assert isinstance(setup, RuntimeActionSessionRegressionActionAdvanceSetup)
    assert setup.percent == percent


@pytest.mark.parametrize("initial_av", [0, -10.0])
def test_action_advance_initial_av_is_finite_but_not_newly_range_restricted(initial_av):
    setup = _action_advance_setup()
    setup["initial_av"] = initial_av
    parsed = _parse(_manifest("1.5", setup))
    assert parsed.cases[0].setup.initial_av == initial_av


@pytest.mark.parametrize("invalid", [True, False, -1, 0.0, "0", None])
def test_action_advance_action_index_requires_exact_nonnegative_integer(invalid):
    setup = _action_advance_setup()
    setup["action_index"] = invalid
    with pytest.raises(ValueError, match="action_index"):
        _parse(_manifest("1.5", setup))


def test_action_advance_action_index_must_address_declared_action():
    setup = _action_advance_setup()
    setup["action_index"] = 1
    with pytest.raises(ValueError, match="declared action"):
        _parse(_manifest("1.5", setup))


def test_current_manifest_preserves_exact_arch_033_six_case_prefix():
    manifest = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)

    assert len(manifest.cases) == 7
    assert [case.case_id for case in manifest.cases[:6]] == ARCH_033_CASE_IDS
    sixth = manifest.cases[5]
    assert sixth.expected_path == FIXTURES[-1][0].resolve()
    assert sixth.expected_sha256 == FIXTURES[-1][2]
    assert sixth.stream_id == "arch-032-reviewed-axis"
    assert sixth.actor_id == "advance-actor"
    assert [action.action_id for action in sixth.actions] == ["reviewed-action-advance"]
    assert [action.name for action in sixth.actions] == ["reviewed-action-advance"]
    assert [action.ends_turn for action in sixth.actions] == [False]
    assert sixth.setup == RuntimeActionSessionRegressionActionAdvanceSetup(
        target_id="advance-actor",
        target_name="Advance Actor",
        team="ally",
        base_speed=100,
        initial_av=80,
        action_index=0,
        percent=0.5,
    )


def test_current_runtime_lane_preserves_arch_033_six_case_prefix_results():
    report = run_runtime_action_session_regression(
        load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    )

    assert report.passed is True
    assert report.total == 7
    assert report.passed_count == 7
    assert report.failed_count == 0
    assert [result.case_id for result in report.results[:6]] == ARCH_033_CASE_IDS
    assert [result.details["record_count"] for result in report.results[:6]] == [
        4,
        3,
        3,
        3,
        3,
        3,
    ]
    assert [result.details["expected_sha256"] for result in report.results[:6]] == [
        item[2] for item in FIXTURES
    ]
    assert report.results[6].case_id == "arch-035-reviewed-static-action-delay"


def test_action_advance_harness_change_surfaces_structured_after_av_divergence():
    locked = load_runtime_action_session_regression_manifest(RUNTIME_MANIFEST_PATH)
    case = locked.cases[5]
    assert isinstance(case.setup, RuntimeActionSessionRegressionActionAdvanceSetup)
    changed = replace(case, setup=replace(case.setup, percent=0.4))

    report = run_runtime_action_session_regression(
        RuntimeActionSessionRegressionManifest(
            manifest_id="arch-033-controlled-action-advance-mismatch",
            path=ROOT / "arch_033_controlled_action_advance_mismatch.json",
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
        "/event/payload/action_advance/after_av"
    )


def test_arch_033_six_reviewed_fixture_byte_identities_remain_exact():
    for path, size, digest in FIXTURES:
        payload = path.read_bytes()
        assert len(payload) == size
        assert hashlib.sha256(payload).hexdigest() == digest


def test_action_advance_regression_harness_remains_explicit_after_delay_extension():
    manifest_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "manifest.py"
    ).read_text(encoding="utf-8")
    runner_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_regression" / "runner.py"
    ).read_text(encoding="utf-8")
    combined = manifest_source + runner_source

    assert "ACTION_ADVANCE" in manifest_source
    assert "RuntimeActionSessionRegressionActionAdvanceSetup" in manifest_source
    assert "AdvanceAction" in runner_source
    assert "target_ids=[setup.target_id]" in runner_source

    for forbidden in (
        "ChangeSpeed",
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
