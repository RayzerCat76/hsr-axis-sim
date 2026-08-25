from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

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
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
)
from hsr_axis_sim.runtime_golden_replays import GoldenReplayValidationConfig
from hsr_axis_sim.runtime_loaders import TraceCanonicalFormPolicy
from hsr_axis_sim.runtime_trace_stitching import CapturedTraceStitchConfig
from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.effects import (
    AdvanceAction,
    ConsumeEnergy,
    ConsumeSkillPoint,
    DelayAction,
    GainEnergy,
    GainSkillPoint,
)
from hsr_axis_sim.sim.state import BattleState
from hsr_axis_sim.sim.unit import Unit

from .manifest import (
    RuntimeActionSessionRegressionActionAdvanceSetup,
    RuntimeActionSessionRegressionActionDelaySetup,
    RuntimeActionSessionRegressionCase,
    RuntimeActionSessionRegressionEnergyConsumeSetup,
    RuntimeActionSessionRegressionEnergyGainSetup,
    RuntimeActionSessionRegressionManifest,
    RuntimeActionSessionRegressionSkillPointConsumeSetup,
    RuntimeActionSessionRegressionSkillPointGainSetup,
    load_runtime_action_session_regression_manifest,
)


@dataclass(frozen=True)
class RuntimeActionSessionRegressionCheckResult:
    case_id: str
    expected_path: str
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass(frozen=True)
class RuntimeActionSessionRegressionReport:
    manifest_id: str
    manifest_path: str
    passed: bool
    total: int
    passed_count: int
    failed_count: int
    results: tuple[RuntimeActionSessionRegressionCheckResult, ...]


def run_runtime_action_session_regression(
    manifest: RuntimeActionSessionRegressionManifest,
    *,
    fail_fast: bool = False,
) -> RuntimeActionSessionRegressionReport:
    if not isinstance(manifest, RuntimeActionSessionRegressionManifest):
        raise TypeError("manifest must be a RuntimeActionSessionRegressionManifest")
    if type(fail_fast) is not bool:
        raise TypeError("fail_fast must be a boolean")

    results: list[RuntimeActionSessionRegressionCheckResult] = []
    for case in manifest.cases:
        result = _run_case(case)
        results.append(result)
        if fail_fast and not result.passed:
            break
    return _build_report(manifest, results)


def format_runtime_action_session_regression_text(
    report: RuntimeActionSessionRegressionReport,
) -> str:
    _require_report(report)
    status = "PASS" if report.passed else "FAIL"
    lines = [
        "HSR Runtime Action-Session Regression Report",
        f"Manifest: {report.manifest_id}",
        f"Manifest path: {report.manifest_path}",
        f"{status} {report.passed_count}/{report.total} runtime action-session Golden checks",
        "",
    ]
    for result in report.results:
        item_status = "PASS" if result.passed else "FAIL"
        details = " ".join(f"{key}={value}" for key, value in result.details.items())
        error = f" error={result.error}" if result.error else ""
        lines.append(
            f"[{item_status}] runtime_action_sessions {result.case_id} "
            f"{details}{error}".rstrip()
        )
    return "\n".join(lines)


def format_runtime_action_session_regression_json(
    report: RuntimeActionSessionRegressionReport,
) -> str:
    _require_report(report)
    return json.dumps(asdict(report), indent=2, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run locked runtime action-session Golden regressions."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--output")
    parser.add_argument("--fail-fast", action="store_true")
    args = parser.parse_args(argv)

    try:
        manifest = load_runtime_action_session_regression_manifest(args.manifest)
        report = run_runtime_action_session_regression(
            manifest,
            fail_fast=args.fail_fast,
        )
        rendered = (
            format_runtime_action_session_regression_text(report)
            if args.format == "text"
            else format_runtime_action_session_regression_json(report)
        )
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered)
        return 0 if report.passed else 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


def _run_case(
    case: RuntimeActionSessionRegressionCase,
) -> RuntimeActionSessionRegressionCheckResult:
    details: dict[str, Any] = {
        "action_count": len(case.actions),
        "expected_sha256": case.expected_sha256,
    }
    try:
        state = _build_state(case)
        steps = tuple(
            ExplicitActionCaptureStep(_build_action(case, index))
            for index in range(len(case.actions))
        )
        adapter_config = LegacyEventAdapterConfig(
            case.stream_id,
            UnknownLegacyEventPolicy.REJECT,
            AmbiguousLegacyEventPolicy.REJECT,
        )
        segment_configs = tuple(
            TraceExportConfig(
                f"{case.case_id}-segment-{index}",
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"fixture_id": case.case_id, "segment": index},
            )
            for index in range(len(steps))
        )
        session_config = MultiActionCaptureSessionConfig(
            PendingEventCaptureCursor(0, 0),
            adapter_config,
            segment_configs,
            False,
        )
        stitch_config = CapturedTraceStitchConfig(
            TraceExportConfig(
                f"{case.case_id}-runtime-actual",
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"fixture_id": case.case_id, "source": "locked-runtime-regression"},
            ),
            False,
        )
        golden_config = GoldenReplayValidationConfig(
            case.case_id,
            case.expected_sha256,
            TraceCanonicalFormPolicy.COMPACT_ONLY,
            100_000,
        )
        result = run_action_session_validation(
            state,
            steps,
            session_config=session_config,
            stitch_config=stitch_config,
            expected_payload_bytes=case.expected_path.read_bytes(),
            golden_config=golden_config,
        )
        golden = result.validation_result.validation_result.validation_result
        details["actual_sha256"] = golden.actual_sha256
        details["record_count"] = golden.actual_load.artifact.document.record_count
        if result.matches:
            return RuntimeActionSessionRegressionCheckResult(
                case_id=case.case_id,
                expected_path=case.expected_relative_path,
                passed=True,
                details=details,
            )

        divergence = golden.first_divergence.divergence
        if divergence is not None:
            details["first_divergence_record_index"] = divergence.record_index
            if divergence.first_field_difference is not None:
                details["first_divergence_path"] = divergence.first_field_difference.path
        return RuntimeActionSessionRegressionCheckResult(
            case_id=case.case_id,
            expected_path=case.expected_relative_path,
            passed=False,
            details=details,
            error="Runtime action-session Golden mismatch.",
        )
    except Exception as exc:
        return RuntimeActionSessionRegressionCheckResult(
            case_id=case.case_id,
            expected_path=case.expected_relative_path,
            passed=False,
            details=details,
            error=str(exc),
        )


def _build_state(case: RuntimeActionSessionRegressionCase) -> BattleState:
    setup = case.setup
    if setup is None:
        return BattleState([])
    if isinstance(
        setup,
        (
            RuntimeActionSessionRegressionEnergyGainSetup,
            RuntimeActionSessionRegressionEnergyConsumeSetup,
        ),
    ):
        return BattleState(
            [
                Unit(
                    id=setup.target_id,
                    name=setup.target_name,
                    team=setup.team,
                    base_speed=setup.base_speed,
                    energy=setup.initial_energy,
                    max_energy=setup.max_energy,
                )
            ]
        )
    if isinstance(
        setup,
        (
            RuntimeActionSessionRegressionSkillPointGainSetup,
            RuntimeActionSessionRegressionSkillPointConsumeSetup,
        ),
    ):
        return BattleState(
            [],
            skill_points=setup.initial_skill_points,
            max_skill_points=setup.max_skill_points,
        )
    if isinstance(
        setup,
        (
            RuntimeActionSessionRegressionActionAdvanceSetup,
            RuntimeActionSessionRegressionActionDelaySetup,
        ),
    ):
        return BattleState(
            [
                Unit(
                    id=setup.target_id,
                    name=setup.target_name,
                    team=setup.team,
                    base_speed=setup.base_speed,
                    current_av=setup.initial_av,
                )
            ]
        )
    raise TypeError("Unsupported runtime action-session regression setup.")


def _build_action(case: RuntimeActionSessionRegressionCase, index: int) -> Action:
    action = case.actions[index]
    effects = []
    setup = case.setup
    if isinstance(setup, RuntimeActionSessionRegressionEnergyGainSetup) and setup.action_index == index:
        effects = [GainEnergy(target_ids=[setup.target_id], amount=setup.amount)]
    elif (
        isinstance(setup, RuntimeActionSessionRegressionEnergyConsumeSetup)
        and setup.action_index == index
    ):
        effects = [ConsumeEnergy(target_ids=[setup.target_id], amount=setup.amount)]
    elif (
        isinstance(setup, RuntimeActionSessionRegressionSkillPointGainSetup)
        and setup.action_index == index
    ):
        effects = [GainSkillPoint(amount=setup.amount)]
    elif (
        isinstance(setup, RuntimeActionSessionRegressionSkillPointConsumeSetup)
        and setup.action_index == index
    ):
        effects = [ConsumeSkillPoint(amount=setup.amount)]
    elif (
        isinstance(setup, RuntimeActionSessionRegressionActionAdvanceSetup)
        and setup.action_index == index
    ):
        effects = [
            AdvanceAction(target_ids=[setup.target_id], percent=setup.percent)
        ]
    elif (
        isinstance(setup, RuntimeActionSessionRegressionActionDelaySetup)
        and setup.action_index == index
    ):
        effects = [DelayAction(target_ids=[setup.target_id], percent=setup.percent)]
    return Action(
        action.action_id,
        action.name,
        case.actor_id,
        effects=effects,
        ends_turn=action.ends_turn,
    )


def _build_report(
    manifest: RuntimeActionSessionRegressionManifest,
    results: list[RuntimeActionSessionRegressionCheckResult],
) -> RuntimeActionSessionRegressionReport:
    passed_count = sum(result.passed for result in results)
    failed_count = len(results) - passed_count
    return RuntimeActionSessionRegressionReport(
        manifest_id=manifest.manifest_id,
        manifest_path=str(manifest.path),
        passed=failed_count == 0,
        total=len(results),
        passed_count=passed_count,
        failed_count=failed_count,
        results=tuple(results),
    )


def _require_report(report: RuntimeActionSessionRegressionReport) -> None:
    if not isinstance(report, RuntimeActionSessionRegressionReport):
        raise TypeError("report must be a RuntimeActionSessionRegressionReport")


if __name__ == "__main__":
    raise SystemExit(main())
