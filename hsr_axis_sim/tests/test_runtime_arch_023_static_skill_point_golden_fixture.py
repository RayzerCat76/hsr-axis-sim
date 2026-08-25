import ast
import hashlib
from pathlib import Path

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
from hsr_axis_sim.sim.effects import GainSkillPoint
from hsr_axis_sim.sim.state import BattleState
from hsr_axis_sim.sim.timeline import Timeline
from hsr_axis_sim.sim.unit import Unit


PACKAGE_ROOT = Path(__file__).parents[1]
EXPECTED_PATH = (
    PACKAGE_ROOT
    / "data"
    / "runtime_golden_fixtures"
    / "arch_023_reviewed_clamped_skill_point_expected.json"
)
ARCH_017_PATH = (
    PACKAGE_ROOT
    / "data"
    / "runtime_golden_fixtures"
    / "arch_017_reviewed_action_session_expected.json"
)
ARCH_021_PATH = (
    PACKAGE_ROOT
    / "data"
    / "runtime_golden_fixtures"
    / "arch_021_reviewed_clamped_energy_expected.json"
)
LEGACY_REGRESSION_MANIFEST = PACKAGE_ROOT / "data" / "regression_manifest.json"
RUNTIME_REGRESSION_MANIFEST = (
    PACKAGE_ROOT / "data" / "runtime_action_session_regression_manifest.json"
)
EXPECTED_SHA256 = "fc359b367c2922ed39e059f89ad16845ba215508292cfa43ca2ab6031c4c9ba9"
EXPECTED_SIZE_BYTES = 2744
ARCH_017_SHA256 = "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66"
ARCH_021_SHA256 = "4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605"
FIXTURE_ID = "arch-023-reviewed-static-clamped-skill-point"
STREAM_ID = "arch-023-reviewed-resource"
ACTION_ID = "reviewed-clamped-skill-point"
ACTOR_ID = "sp-actor"


def _expected_bytes() -> bytes:
    return EXPECTED_PATH.read_bytes()


def _state() -> BattleState:
    return BattleState([], skill_points=4, max_skill_points=5)


def _runtime_inputs(*, gain_amount: int = 3):
    steps = (
        ExplicitActionCaptureStep(
            Action(
                ACTION_ID,
                ACTION_ID,
                ACTOR_ID,
                effects=[GainSkillPoint(amount=gain_amount)],
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
                "arch-023-resource-segment-0",
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"fixture_id": FIXTURE_ID, "segment": 0},
            ),
        ),
        False,
    )
    stitch_config = CapturedTraceStitchConfig(
        TraceExportConfig(
            "arch-023-resource-runtime-actual",
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


def test_static_skill_point_fixture_has_exact_reviewed_bytes_digest_and_schema():
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
    assert document.trace_id == "arch-023-reviewed-static-expected"
    assert document.schema_name == "hsr_runtime_trace"
    assert document.schema_version == "1.0"
    assert document.sequence_policy is TraceSequencePolicy.CONTIGUOUS
    assert document.record_count == 3
    assert [record.sequence for record in document.records] == [0, 1, 2]
    assert [record.event.event_type for record in document.records] == [
        RuntimeEventType.ACTION_START,
        RuntimeEventType.SKILL_POINTS_CHANGED,
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
    assert all(dict(record.numeric_values) == {} for record in document.records)

    resource = document.records[1].event
    assert resource.target_id is None
    assert dict(resource.payload["resource_change"]) == {
        "resource_kind": "SKILL_POINTS",
        "scope": "TEAM",
        "before": 4,
        "after": 5,
        "requested_delta": 3,
        "applied_delta": 1,
        "cap": 5,
        "unit_id": None,
    }
    assert dict(resource.payload["legacy_data"]) == {
        "actor_id": ACTOR_ID,
        "action_id": ACTION_ID,
        "resource_kind": "SKILL_POINTS",
        "scope": "TEAM",
        "before": 4,
        "after": 5,
        "requested_delta": 3,
        "applied_delta": 1,
        "cap": 5,
        "unit_id": None,
    }


def test_arch_016_production_clamped_skill_point_action_matches_static_fixture():
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
    assert state.skill_points == 5
    assert [event.type for event in state.pending_events] == [
        "action_started",
        "skill_points_changed",
        "action_finished",
    ]
    assert result.session_result.final_cursor == PendingEventCaptureCursor(3, 3)
    golden = result.validation_result.validation_result.validation_result
    assert golden.expected_sha256 == EXPECTED_SHA256
    assert golden.comparison.matches is True
    assert golden.first_divergence.matches is True


def test_changed_requested_skill_point_gain_reports_first_resource_divergence():
    expected = _expected_bytes()
    steps, session_config, stitch_config, golden_config = _runtime_inputs(gain_amount=2)
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
    assert state.skill_points == 5
    golden = result.validation_result.validation_result.validation_result
    divergence = golden.first_divergence.divergence
    assert divergence is not None
    assert divergence.record_index == 1
    assert divergence.first_field_difference is not None
    assert divergence.first_field_difference.path == "/event/payload/legacy_data/requested_delta"
    assert divergence.first_field_difference.expected_value == 3
    assert divergence.first_field_difference.actual_value == 2

    expected_resource = golden.comparison.records[1].expected_record.event.payload[
        "resource_change"
    ]
    actual_resource = golden.comparison.records[1].actual_record.event.payload[
        "resource_change"
    ]
    assert expected_resource["after"] == actual_resource["after"] == 5
    assert expected_resource["applied_delta"] == actual_resource["applied_delta"] == 1
    assert expected_resource["requested_delta"] == 3
    assert actual_resource["requested_delta"] == 2
    assert expected_resource["unit_id"] is actual_resource["unit_id"] is None


def test_skill_point_fixture_is_promoted_only_into_runtime_regression_manifest():
    legacy = LEGACY_REGRESSION_MANIFEST.read_text(encoding="utf-8")
    runtime = RUNTIME_REGRESSION_MANIFEST.read_text(encoding="utf-8")

    assert FIXTURE_ID not in legacy
    assert EXPECTED_PATH.name not in legacy
    assert FIXTURE_ID in runtime
    assert EXPECTED_PATH.name in runtime
    assert runtime.count(FIXTURE_ID) == 1
    assert runtime.count(EXPECTED_PATH.name) == 1


def test_arch_023_test_source_has_no_runtime_expected_generation_path():
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
    }
    assert called_names.isdisjoint(forbidden_calls)


def test_prior_static_fixtures_and_current_runtime_regression_lane_remain_accepted():
    assert len(ARCH_017_PATH.read_bytes()) == 3013
    assert hashlib.sha256(ARCH_017_PATH.read_bytes()).hexdigest() == ARCH_017_SHA256
    assert len(ARCH_021_PATH.read_bytes()) == 2759
    assert hashlib.sha256(ARCH_021_PATH.read_bytes()).hexdigest() == ARCH_021_SHA256

    report = run_runtime_action_session_regression(
        load_runtime_action_session_regression_manifest(RUNTIME_REGRESSION_MANIFEST)
    )
    assert report.passed is True
    assert report.total == 4
    assert report.passed_count == 4
    assert [result.case_id for result in report.results] == [
        "arch-017-reviewed-static-action-session",
        "arch-021-reviewed-static-clamped-energy",
        "arch-023-reviewed-static-clamped-skill-point",
        "arch-025-reviewed-static-energy-consume",
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
