import ast
import hashlib
from pathlib import Path

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
from hsr_axis_sim.sim.effects import GainEnergy
from hsr_axis_sim.sim.state import BattleState
from hsr_axis_sim.sim.timeline import Timeline
from hsr_axis_sim.sim.unit import Unit


PACKAGE_ROOT = Path(__file__).parents[1]
EXPECTED_PATH = (
    PACKAGE_ROOT
    / "data"
    / "runtime_golden_fixtures"
    / "arch_021_reviewed_clamped_energy_expected.json"
)
ARCH_017_PATH = (
    PACKAGE_ROOT
    / "data"
    / "runtime_golden_fixtures"
    / "arch_017_reviewed_action_session_expected.json"
)
LEGACY_REGRESSION_MANIFEST = PACKAGE_ROOT / "data" / "regression_manifest.json"
RUNTIME_REGRESSION_MANIFEST = (
    PACKAGE_ROOT / "data" / "runtime_action_session_regression_manifest.json"
)
EXPECTED_SHA256 = "4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605"
EXPECTED_SIZE_BYTES = 2759
ARCH_017_SHA256 = "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66"
FIXTURE_ID = "arch-021-reviewed-static-clamped-energy"
STREAM_ID = "arch-021-reviewed-resource"
ACTION_ID = "reviewed-clamped-energy"
ACTOR_ID = "resource-actor"
TARGET_ID = "resource-target"


def _expected_bytes() -> bytes:
    return EXPECTED_PATH.read_bytes()


def _state() -> BattleState:
    return BattleState(
        [
            Unit(
                id=TARGET_ID,
                name=TARGET_ID,
                team="ally",
                base_speed=100,
                energy=90,
                max_energy=100,
            )
        ]
    )


def _runtime_inputs(*, gain_amount: float = 25):
    steps = (
        ExplicitActionCaptureStep(
            Action(
                ACTION_ID,
                ACTION_ID,
                ACTOR_ID,
                effects=[GainEnergy(target_ids=[TARGET_ID], amount=gain_amount)],
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
                "arch-021-resource-segment-0",
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"fixture_id": FIXTURE_ID, "segment": 0},
            ),
        ),
        False,
    )
    stitch_config = CapturedTraceStitchConfig(
        TraceExportConfig(
            "arch-021-resource-runtime-actual",
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


def test_static_resource_fixture_has_exact_reviewed_bytes_digest_and_schema():
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
    assert document.trace_id == "arch-021-reviewed-static-expected"
    assert document.record_count == 3
    assert [record.sequence for record in document.records] == [0, 1, 2]
    assert [record.event.event_type for record in document.records] == [
        RuntimeEventType.ACTION_START,
        RuntimeEventType.ENERGY_CHANGED,
        RuntimeEventType.ACTION_END,
    ]
    assert [record.event.action_id for record in document.records] == [
        ACTION_ID,
        ACTION_ID,
        ACTION_ID,
    ]
    assert all(dict(record.numeric_values) == {} for record in document.records)

    resource = document.records[1].event
    assert resource.actor_id == ACTOR_ID
    assert resource.target_id == TARGET_ID
    assert dict(resource.payload["resource_change"]) == {
        "resource_kind": "ENERGY",
        "scope": "UNIT",
        "before": 90,
        "after": 100,
        "requested_delta": 25,
        "applied_delta": 10,
        "cap": 100,
        "unit_id": TARGET_ID,
    }
    assert dict(resource.payload["legacy_data"]) == {
        "actor_id": ACTOR_ID,
        "action_id": ACTION_ID,
        "resource_kind": "ENERGY",
        "scope": "UNIT",
        "before": 90,
        "after": 100,
        "requested_delta": 25,
        "applied_delta": 10,
        "cap": 100,
        "unit_id": TARGET_ID,
    }


def test_arch_016_production_clamped_energy_action_matches_static_fixture():
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
    assert state.get_unit(TARGET_ID).energy == 100
    assert [event.type for event in state.pending_events] == [
        "action_started",
        "energy_changed",
        "action_finished",
    ]
    assert result.session_result.final_cursor == PendingEventCaptureCursor(3, 3)
    golden = result.validation_result.validation_result.validation_result
    assert golden.expected_sha256 == EXPECTED_SHA256
    assert golden.comparison.matches is True
    assert golden.first_divergence.matches is True


def test_changed_requested_gain_reports_first_resource_divergence_against_same_fixture():
    expected = _expected_bytes()
    steps, session_config, stitch_config, golden_config = _runtime_inputs(gain_amount=20)
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
    assert state.get_unit(TARGET_ID).energy == 100
    golden = result.validation_result.validation_result.validation_result
    divergence = golden.first_divergence.divergence
    assert divergence is not None
    assert divergence.record_index == 1
    assert divergence.first_field_difference is not None
    assert divergence.first_field_difference.path == "/event/payload/legacy_data/requested_delta"
    assert divergence.first_field_difference.expected_value == 25
    assert divergence.first_field_difference.actual_value == 20

    expected_resource = golden.comparison.records[1].expected_record.event.payload[
        "resource_change"
    ]
    actual_resource = golden.comparison.records[1].actual_record.event.payload[
        "resource_change"
    ]
    assert expected_resource["after"] == actual_resource["after"] == 100
    assert expected_resource["applied_delta"] == actual_resource["applied_delta"] == 10
    assert expected_resource["requested_delta"] == 25
    assert actual_resource["requested_delta"] == 20


def test_resource_fixture_is_not_promoted_into_either_regression_manifest():
    for manifest in (LEGACY_REGRESSION_MANIFEST, RUNTIME_REGRESSION_MANIFEST):
        text = manifest.read_text(encoding="utf-8")
        assert FIXTURE_ID not in text
        assert EXPECTED_PATH.name not in text


def test_arch_021_test_source_has_no_runtime_expected_generation_path():
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


def test_arch_017_fixture_and_production_lifo_remain_unchanged():
    assert hashlib.sha256(ARCH_017_PATH.read_bytes()).hexdigest() == ARCH_017_SHA256

    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == [
        "third",
        "second",
        "first",
    ]
