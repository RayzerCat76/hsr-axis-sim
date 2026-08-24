"""Deterministic composition of strict loading, comparison, and divergence reporting."""

from __future__ import annotations

from hsr_axis_sim.runtime_comparators import compare_runtime_trace_documents
from hsr_axis_sim.runtime_contracts.serialization import canonical_json_dumps
from hsr_axis_sim.runtime_divergence import (
    build_first_divergence_report,
    render_first_divergence_text,
)
from hsr_axis_sim.runtime_loaders import (
    RuntimeTraceLoadConfig,
    TraceDigestPolicy,
    load_runtime_trace_bytes,
)

from .model import (
    GoldenReplayValidationConfig,
    GoldenReplayValidationInputError,
    GoldenReplayValidationResult,
)


def validate_golden_replay_bytes(
    expected_payload_bytes: bytes,
    actual_payload_bytes: bytes,
    *,
    config: GoldenReplayValidationConfig,
) -> GoldenReplayValidationResult:
    """Validate actual canonical trace bytes against one integrity-pinned golden trace."""

    if not isinstance(config, GoldenReplayValidationConfig):
        raise GoldenReplayValidationInputError("config must be GoldenReplayValidationConfig")

    expected_load = load_runtime_trace_bytes(
        expected_payload_bytes,
        config=RuntimeTraceLoadConfig(
            canonical_form_policy=config.canonical_form_policy,
            digest_policy=TraceDigestPolicy.REQUIRE_MATCH,
            expected_sha256=config.expected_sha256,
            max_bytes=config.max_bytes,
        ),
    )
    actual_load = load_runtime_trace_bytes(
        actual_payload_bytes,
        config=RuntimeTraceLoadConfig(
            canonical_form_policy=config.canonical_form_policy,
            digest_policy=TraceDigestPolicy.VERIFY_IF_PROVIDED,
            expected_sha256=None,
            max_bytes=config.max_bytes,
        ),
    )

    comparison = compare_runtime_trace_documents(
        expected_load.artifact.document,
        actual_load.artifact.document,
    )
    first_divergence = build_first_divergence_report(comparison)
    return GoldenReplayValidationResult(
        config=config,
        expected_load=expected_load,
        actual_load=actual_load,
        comparison=comparison,
        first_divergence=first_divergence,
    )


def render_golden_replay_validation_text(result: GoldenReplayValidationResult) -> str:
    """Render deterministic replay-level provenance plus the accepted ARCH-006 report."""

    if not isinstance(result, GoldenReplayValidationResult):
        raise GoldenReplayValidationInputError("result must be GoldenReplayValidationResult")

    lines = [
        "GOLDEN_REPLAY_PASS" if result.matches else "GOLDEN_REPLAY_FAIL",
        f"replay_id={canonical_json_dumps(result.config.replay_id, pretty=False)}",
        f"expected_sha256={canonical_json_dumps(result.expected_sha256, pretty=False)}",
        f"actual_sha256={canonical_json_dumps(result.actual_sha256, pretty=False)}",
        f"expected_canonical_form={result.expected_load.canonical_form.value}",
        f"actual_canonical_form={result.actual_load.canonical_form.value}",
        f"expected_digest_status={result.expected_load.digest_status.value}",
        f"actual_digest_status={result.actual_load.digest_status.value}",
        "FIRST_DIVERGENCE_REPORT",
    ]
    divergence_text = render_first_divergence_text(result.first_divergence).rstrip("\n")
    lines.append(divergence_text)
    return "\n".join(lines) + "\n"
