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
from hsr_axis_sim.sim.state import BattleState


PACKAGE_ROOT = Path(__file__).parents[1]
EXPECTED_PATH = (
    PACKAGE_ROOT
    / "data"
    / "runtime_golden_fixtures"
    / "arch_017_reviewed_action_session_expected.json"
)
REGRESSION_MANIFEST = PACKAGE_ROOT / "data" / "regression_manifest.json"
EXPECTED_SHA256 = "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66"
EXPECTED_SIZE_BYTES = 3013
FIXTURE_ID = "arch-017-reviewed-static-action-session"
STREAM_ID = "arch-017-reviewed-static"
ACTOR_ID = "reviewed-actor"


def _expected_bytes() -> bytes:
    return EXPECTED_PATH.read_bytes()


def _runtime_inputs(second_action_id: str = "reviewed-action-b"):
    steps = (
        ExplicitActionCaptureStep(
            Action(
                "reviewed-action-a",
                "reviewed-action-a",
                ACTOR_ID,
                ends_turn=False,
            )
        ),
        ExplicitActionCaptureStep(
            Action(
                second_action_id,
                second_action_id,
                ACTOR_ID,
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
                "arch-017-segment-0",
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"fixture_id": FIXTURE_ID, "segment": 0},
            ),
            TraceExportConfig(
                "arch-017-segment-1",
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"fixture_id": FIXTURE_ID, "segment": 1},
            ),
        ),
        False,
    )
    stitch_config = CapturedTraceStitchConfig(
        TraceExportConfig(
            "arch-017-runtime-actual",
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


def test_static_fixture_has_exact_reviewed_bytes_digest_and_strict_schema():
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
    assert loaded.artifact.document.trace_id == "arch-017-reviewed-static-expected"
    assert loaded.artifact.document.record_count == 4
    assert [record.sequence for record in loaded.artifact.document.records] == [0, 1, 2, 3]
    assert [record.event.event_type for record in loaded.artifact.document.records] == [
        RuntimeEventType.ACTION_START,
        RuntimeEventType.ACTION_END,
        RuntimeEventType.ACTION_START,
        RuntimeEventType.ACTION_END,
    ]
    assert [record.event.action_id for record in loaded.artifact.document.records] == [
        "reviewed-action-a",
        "reviewed-action-a",
        "reviewed-action-b",
        "reviewed-action-b",
    ]


def test_arch_016_production_action_session_matches_static_reviewed_fixture():
    expected = _expected_bytes()
    steps, session_config, stitch_config, golden_config = _runtime_inputs()
    state = BattleState([])

    result = run_action_session_validation(
        state,
        steps,
        session_config=session_config,
        stitch_config=stitch_config,
        expected_payload_bytes=expected,
        golden_config=golden_config,
    )

    assert result.matches is True
    assert len(state.pending_events) == 4
    assert result.session_result.final_cursor == PendingEventCaptureCursor(4, 4)
    golden = result.validation_result.validation_result.validation_result
    assert golden.expected_sha256 == EXPECTED_SHA256
    assert golden.comparison.matches is True
    assert golden.first_divergence.matches is True


def test_changed_second_production_action_reports_first_divergence_against_same_static_fixture():
    expected = _expected_bytes()
    steps, session_config, stitch_config, golden_config = _runtime_inputs(
        "reviewed-action-c"
    )

    result = run_action_session_validation(
        BattleState([]),
        steps,
        session_config=session_config,
        stitch_config=stitch_config,
        expected_payload_bytes=expected,
        golden_config=golden_config,
    )

    assert result.matches is False
    golden = result.validation_result.validation_result.validation_result
    divergence = golden.first_divergence.divergence
    assert divergence is not None
    assert divergence.record_index == 2
    assert divergence.first_field_difference is not None
    assert divergence.first_field_difference.path == "/event/action_id"
    assert divergence.first_field_difference.expected_value == "reviewed-action-b"
    assert divergence.first_field_difference.actual_value == "reviewed-action-c"


def test_fixture_is_not_promoted_into_locked_regression_manifest():
    manifest_text = REGRESSION_MANIFEST.read_text()
    assert FIXTURE_ID not in manifest_text
    assert EXPECTED_PATH.name not in manifest_text
    assert "runtime_golden_fixtures" not in manifest_text


def test_arch_017_test_source_has_no_runtime_expected_generation_path():
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
