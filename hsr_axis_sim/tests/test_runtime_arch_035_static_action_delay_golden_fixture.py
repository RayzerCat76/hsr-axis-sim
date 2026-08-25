import ast
import hashlib
from pathlib import Path

import pytest

from hsr_axis_sim.regression.manifest import load_regression_manifest
from hsr_axis_sim.regression.runner import run_regression
from hsr_axis_sim.runtime_action_session_regression.manifest import (
    load_runtime_action_session_regression_manifest,
)
from hsr_axis_sim.runtime_action_session_regression.runner import (
    run_runtime_action_session_regression,
)
from hsr_axis_sim.runtime_action_session_validation import run_action_session_validation
from hsr_axis_sim.runtime_action_sessions import (
    ExplicitActionCaptureStep,
    MultiActionCaptureSessionConfig,
)
from hsr_axis_sim.runtime_adapters import (
    AmbiguousLegacyEventPolicy,
    LegacyEventAdapterConfig,
    UnknownLegacyEventPolicy,
)
from hsr_axis_sim.runtime_capture_cursors import PendingEventCaptureCursor
from hsr_axis_sim.runtime_contracts import RuntimeEventType
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
)
from hsr_axis_sim.runtime_golden_replays import GoldenReplayValidationConfig
from hsr_axis_sim.runtime_loaders import (
    RuntimeTraceLoadConfig,
    TraceCanonicalForm,
    TraceCanonicalFormPolicy,
    TraceDigestPolicy,
    TraceDigestStatus,
    load_runtime_trace_bytes,
)
from hsr_axis_sim.runtime_trace_stitching import CapturedTraceStitchConfig
from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.effects import DelayAction
from hsr_axis_sim.sim.state import BattleState
from hsr_axis_sim.sim.timeline import Timeline
from hsr_axis_sim.sim.unit import Unit


PACKAGE_ROOT = Path(__file__).parents[1]
FIXTURE_DIR = PACKAGE_ROOT / "data" / "runtime_golden_fixtures"
EXPECTED_PATH = FIXTURE_DIR / "arch_035_reviewed_action_delay_expected.json"
LEGACY_REGRESSION_MANIFEST = PACKAGE_ROOT / "data" / "regression_manifest.json"
RUNTIME_REGRESSION_MANIFEST = (
    PACKAGE_ROOT / "data" / "runtime_action_session_regression_manifest.json"
)

EXPECTED_SHA256 = "9efbb65defb5eacc12150d31d0530d9a94b43a42e2303ebca643911f98094c4d"
EXPECTED_SIZE_BYTES = 2728
FIXTURE_ID = "arch-035-reviewed-static-action-delay"
STREAM_ID = "arch-035-reviewed-axis"
ACTION_ID = "reviewed-action-delay"
ACTOR_ID = "delay-actor"

PRIOR_FIXTURES = (
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


def _expected_bytes() -> bytes:
    return EXPECTED_PATH.read_bytes()


def _state() -> BattleState:
    return BattleState([Unit(ACTOR_ID, "Delay Actor", "ally", 100, current_av=30)])


def _runtime_inputs(*, percent: float = 0.25):
    steps = (
        ExplicitActionCaptureStep(
            Action(
                ACTION_ID,
                ACTION_ID,
                ACTOR_ID,
                effects=[DelayAction(percent=percent)],
                ends_turn=False,
            )
        ),
    )
    adapter = LegacyEventAdapterConfig(
        STREAM_ID,
        UnknownLegacyEventPolicy.REJECT,
        AmbiguousLegacyEventPolicy.REJECT,
    )
    session_config = MultiActionCaptureSessionConfig(
        PendingEventCaptureCursor(0, 0),
        adapter,
        (
            TraceExportConfig(
                "arch-035-axis-segment-0",
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"fixture_id": FIXTURE_ID, "segment": 0},
            ),
        ),
        False,
    )
    stitch_config = CapturedTraceStitchConfig(
        TraceExportConfig(
            "arch-035-axis-runtime-actual",
            TraceSequencePolicy.CONTIGUOUS,
            EmptyTracePolicy.REJECT,
            {"fixture_id": FIXTURE_ID, "source": "production-action-session"},
        ),
        False,
    )
    golden_config = GoldenReplayValidationConfig(
        FIXTURE_ID,
        EXPECTED_SHA256,
        TraceCanonicalFormPolicy.COMPACT_ONLY,
        100_000,
    )
    return steps, session_config, stitch_config, golden_config


def test_static_delay_fixture_has_exact_reviewed_bytes_digest_and_schema():
    expected = _expected_bytes()

    assert len(expected) == EXPECTED_SIZE_BYTES
    assert hashlib.sha256(expected).hexdigest() == EXPECTED_SHA256
    assert not expected.endswith(b"\n")

    loaded = load_runtime_trace_bytes(
        expected,
        config=RuntimeTraceLoadConfig(
            TraceCanonicalFormPolicy.COMPACT_ONLY,
            TraceDigestPolicy.REQUIRE_MATCH,
            EXPECTED_SHA256,
            100_000,
        ),
    )

    assert loaded.canonical_form is TraceCanonicalForm.COMPACT
    assert loaded.digest_status is TraceDigestStatus.MATCHED
    document = loaded.artifact.document
    assert document.trace_id == "arch-035-reviewed-static-expected"
    assert document.schema_name == "hsr_runtime_trace"
    assert document.schema_version == "1.0"
    assert document.sequence_policy is TraceSequencePolicy.CONTIGUOUS
    assert document.record_count == 3
    assert [record.sequence for record in document.records] == [0, 1, 2]
    assert [record.event.event_type for record in document.records] == [
        RuntimeEventType.ACTION_START,
        RuntimeEventType.ACTION_VALUE_DELAYED,
        RuntimeEventType.ACTION_END,
    ]
    assert [record.event.action_id for record in document.records] == [
        ACTION_ID,
        ACTION_ID,
        ACTION_ID,
    ]
    assert [record.event.actor_id for record in document.records] == [
        ACTOR_ID,
        ACTOR_ID,
        ACTOR_ID,
    ]
    assert [record.event.target_id for record in document.records] == [
        None,
        ACTOR_ID,
        None,
    ]
    assert all(dict(record.numeric_values) == {} for record in document.records)

    delayed = document.records[1].event
    exact_observation = {
        "target_id": ACTOR_ID,
        "before_av": 30,
        "after_av": 55.0,
        "base_av": 100.0,
        "requested_percent": 0.25,
        "requested_delta_av": 25.0,
        "applied_delta_av": 25.0,
    }
    assert dict(delayed.payload["action_delay"]) == exact_observation
    assert dict(delayed.payload["legacy_data"]) == {
        "actor_id": ACTOR_ID,
        "action_id": ACTION_ID,
        **exact_observation,
    }
    assert "clamped_to_zero" not in delayed.payload["action_delay"]
    assert "clamped_to_zero" not in delayed.payload["legacy_data"]
    assert delayed.payload["adapter"]["legacy_event_type"] == "action_delayed"
    assert delayed.payload["adapter"]["mechanic_id"] == "LEGACY_EVENT.ACTION_DELAYED"
    assert delayed.payload["adapter"]["mapping_status"] == "BOUND"


def test_arch_016_production_delay_matches_static_fixture():
    expected = _expected_bytes()
    steps, session_config, stitch_config, golden_config = _runtime_inputs()
    state = _state()

    result = run_action_session_validation(
        state,
        steps,
        session_config=session_config,
        stitch_config=stitch_config,
        expected_payload_bytes=expected,
        golden_config=golden_config,
    )

    assert result.matches is True
    assert state.get_unit(ACTOR_ID).current_av == pytest.approx(55.0, abs=1e-12)
    assert [event.type for event in state.pending_events] == [
        "action_started",
        "action_delayed",
        "action_finished",
    ]
    assert result.session_result.final_cursor == PendingEventCaptureCursor(3, 3)
    golden = result.validation_result.validation_result.validation_result
    assert golden.expected_sha256 == EXPECTED_SHA256
    assert golden.comparison.matches is True
    assert golden.first_divergence.matches is True
    assert golden.first_divergence.divergence is None


def test_changed_delay_percent_reports_first_structured_divergence():
    expected = _expected_bytes()
    steps, session_config, stitch_config, golden_config = _runtime_inputs(percent=0.20)
    state = _state()

    result = run_action_session_validation(
        state,
        steps,
        session_config=session_config,
        stitch_config=stitch_config,
        expected_payload_bytes=expected,
        golden_config=golden_config,
    )

    assert result.matches is False
    assert state.get_unit(ACTOR_ID).current_av == pytest.approx(50.0, abs=1e-12)
    golden = result.validation_result.validation_result.validation_result
    divergence = golden.first_divergence.divergence
    assert divergence is not None
    assert divergence.record_index == 1
    assert divergence.first_field_difference is not None
    assert divergence.first_field_difference.path == "/event/payload/action_delay/after_av"
    assert divergence.first_field_difference.expected_value == 55.0
    assert divergence.first_field_difference.actual_value == 50.0

    expected_delay = golden.comparison.records[1].expected_record.event.payload[
        "action_delay"
    ]
    actual_delay = golden.comparison.records[1].actual_record.event.payload[
        "action_delay"
    ]
    assert expected_delay["before_av"] == actual_delay["before_av"] == 30
    assert expected_delay["after_av"] == 55.0
    assert actual_delay["after_av"] == 50.0
    assert expected_delay["requested_percent"] == 0.25
    assert actual_delay["requested_percent"] == 0.20
    assert expected_delay["requested_delta_av"] == 25.0
    assert actual_delay["requested_delta_av"] == 20.0
    assert expected_delay["applied_delta_av"] == 25.0
    assert actual_delay["applied_delta_av"] == 20.0
    assert "clamped_to_zero" not in expected_delay
    assert "clamped_to_zero" not in actual_delay


def test_arch_035_fixture_is_promoted_only_to_runtime_regression_manifest():
    legacy = LEGACY_REGRESSION_MANIFEST.read_text(encoding="utf-8")
    runtime = RUNTIME_REGRESSION_MANIFEST.read_text(encoding="utf-8")

    assert FIXTURE_ID not in legacy
    assert EXPECTED_PATH.name not in legacy
    assert FIXTURE_ID in runtime
    assert EXPECTED_PATH.name in runtime


def test_arch_035_test_source_has_no_runtime_expected_generation_path():
    tree = ast.parse(Path(__file__).read_text())
    called_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    forbidden_calls = {
        "build_runtime_trace_document",
        "build_runtime_trace_artifact",
        "canonical_json_bytes",
        "canonical_json_dumps",
        "adapt_legacy_event",
        "adapt_legacy_event_stream",
        "run_multi_action_capture_session",
        "stitch_successful_action_session",
        "validate_successful_session_against_golden",
        "write_bytes",
        "write_text",
        "dumps",
        "dump",
    }
    assert called_names.isdisjoint(forbidden_calls)


def test_prior_static_fixture_identities_and_promoted_runtime_lane_remain_accepted():
    for path, size, digest in PRIOR_FIXTURES:
        payload = path.read_bytes()
        assert len(payload) == size
        assert hashlib.sha256(payload).hexdigest() == digest

    payload = EXPECTED_PATH.read_bytes()
    assert len(payload) == EXPECTED_SIZE_BYTES
    assert hashlib.sha256(payload).hexdigest() == EXPECTED_SHA256

    report = run_runtime_action_session_regression(
        load_runtime_action_session_regression_manifest(RUNTIME_REGRESSION_MANIFEST)
    )
    assert report.passed is True
    assert report.total == 7
    assert report.passed_count == 7
    assert [result.case_id for result in report.results] == [
        "arch-017-reviewed-static-action-session",
        "arch-021-reviewed-static-clamped-energy",
        "arch-023-reviewed-static-clamped-skill-point",
        "arch-025-reviewed-static-energy-consume",
        "arch-027-reviewed-static-skill-point-consume",
        "arch-032-reviewed-static-action-advance",
        "arch-035-reviewed-static-action-delay",
    ]


def test_legacy_regression_and_trace_evidence_remain_unchanged():
    legacy = load_regression_manifest(LEGACY_REGRESSION_MANIFEST)
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
