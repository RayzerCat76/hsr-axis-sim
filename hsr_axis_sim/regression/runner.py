from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from hsr_axis_sim.regression.manifest import (
    RegressionManifest,
    RegressionManifestEntry,
    load_regression_manifest,
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
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
)
from hsr_axis_sim.runtime_golden_replays import GoldenReplayValidationConfig
from hsr_axis_sim.runtime_loaders import TraceCanonicalFormPolicy
from hsr_axis_sim.runtime_trace_stitching import CapturedTraceStitchConfig
from hsr_axis_sim.search.scenario import (
    load_search_scenario,
    render_search_scenario_report,
    run_search_scenario,
)
from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.replay import ReplayValidator
from hsr_axis_sim.sim.replay_lint import load_and_lint_manual_video_trace
from hsr_axis_sim.sim.state import BattleState
from hsr_axis_sim.tools.trace_frame_anchors import validate_frame_anchor_files
from hsr_axis_sim.tools.trace_semantics import validate_semantic_map_files


VALID_GROUPS = {
    "replays",
    "manual",
    "scenarios",
    "action_sequence_traces",
    "runtime_action_sessions",
    "trace_evidence",
}
REPORT_GROUPS = [
    "replays",
    "manual",
    "scenarios",
    "action_sequence_traces",
    "runtime_action_sessions",
    "trace_evidence",
]
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PACKAGE_ROOT / "data"


@dataclass
class RegressionCheckResult:
    group: str
    name: str
    path: str
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class RegressionReport:
    passed: bool
    total: int
    passed_count: int
    failed_count: int
    results: list[RegressionCheckResult] = field(default_factory=list)
    manifest_id: str | None = None
    manifest_path: str | None = None
    manifest_counts: dict[str, int] = field(default_factory=dict)


def run_regression(
    only: str | None = None,
    fail_fast: bool = False,
    replay_paths: list[Path] | None = None,
    manual_paths: list[Path] | None = None,
    scenario_paths: list[Path] | None = None,
    action_sequence_paths: list[Path] | None = None,
    runtime_action_session_entries: list[RegressionManifestEntry] | None = None,
    trace_evidence_entries: list[RegressionManifestEntry] | None = None,
    manifest: RegressionManifest | None = None,
) -> RegressionReport:
    groups = _selected_groups(only)
    results: list[RegressionCheckResult] = []
    action_sequence_entries: list[RegressionManifestEntry] | None = None
    if manifest is not None:
        replay_paths = manifest.paths_for_group("replays")
        manual_paths = manifest.paths_for_group("manual")
        scenario_paths = manifest.paths_for_group("scenarios")
        action_sequence_entries = manifest.groups.get("action_sequence_traces", [])
        runtime_action_session_entries = manifest.groups.get("runtime_action_sessions", [])
        trace_evidence_entries = manifest.groups.get("trace_evidence", [])

    if "replays" in groups:
        for path in replay_paths or discover_replay_paths():
            results.append(_check_replay(path))
            if fail_fast and not results[-1].passed:
                return _report_from_results(results, manifest=manifest)

    if "manual" in groups:
        for path in manual_paths or discover_manual_paths():
            for check in _check_manual_trace(path):
                results.append(check)
                if fail_fast and not check.passed:
                    return _report_from_results(results, manifest=manifest)

    if "scenarios" in groups:
        for path in scenario_paths or discover_scenario_paths():
            results.append(_check_scenario(path))
            if fail_fast and not results[-1].passed:
                return _report_from_results(results, manifest=manifest)

    if "action_sequence_traces" in groups:
        entries = action_sequence_entries
        if entries is None:
            entries = [
                RegressionManifestEntry(
                    id=path.stem,
                    path=path,
                    checks=["lint", "action_sequence"],
                )
                for path in action_sequence_paths or discover_action_sequence_trace_paths()
            ]
        for entry in entries:
            for check in _check_action_sequence_trace(entry):
                results.append(check)
                if fail_fast and not check.passed:
                    return _report_from_results(results, manifest=manifest)

    if "runtime_action_sessions" in groups:
        for entry in runtime_action_session_entries or []:
            result = _check_runtime_action_session(entry)
            results.append(result)
            if fail_fast and not result.passed:
                return _report_from_results(results, manifest=manifest)

    if "trace_evidence" in groups:
        for entry in trace_evidence_entries or []:
            result = _check_trace_evidence(entry)
            results.append(result)
            if fail_fast and not result.passed:
                return _report_from_results(results, manifest=manifest)

    return _report_from_results(results, manifest=manifest)


def discover_replay_paths() -> list[Path]:
    return sorted((DATA_ROOT / "golden_replays").glob("*.json"))


def discover_manual_paths() -> list[Path]:
    return sorted((DATA_ROOT / "manual_video_traces" / "samples").glob("*.json"))


def discover_scenario_paths() -> list[Path]:
    return sorted((DATA_ROOT / "search_scenarios").glob("*.json"))


def discover_action_sequence_trace_paths() -> list[Path]:
    return sorted(
        (DATA_ROOT / "manual_video_traces" / "intake").glob(
            "*action_sequence_only.json"
        )
    )


def format_regression_text(report: RegressionReport) -> str:
    lines = ["HSR Axis Regression Report"]
    if report.manifest_id is not None:
        lines.append(f"Manifest: {report.manifest_id}")
        lines.append(f"Manifest path: {report.manifest_path}")
        lines.append(f"Manifest counts: {_details_text(report.manifest_counts)}")
    for group in REPORT_GROUPS:
        group_results = [result for result in report.results if result.group == group]
        if not group_results:
            continue
        passed = sum(1 for result in group_results if result.passed)
        label = _group_label(group)
        status = "PASS" if passed == len(group_results) else "FAIL"
        lines.append(f"{status} {passed}/{len(group_results)} {label}")

    lines.append("")
    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(
            f"[{status}] {result.group} {result.name} "
            f"{_details_text(result.details)}{_error_text(result.error)}".rstrip()
        )
    return "\n".join(lines)


def format_regression_markdown(report: RegressionReport) -> str:
    lines = [
        "# HSR Axis Regression Report",
        "",
    ]
    if report.manifest_id is not None:
        lines.extend(
            [
                "## Manifest",
                f"- ID: {report.manifest_id}",
                f"- Path: {report.manifest_path}",
                f"- Counts: {_details_text(report.manifest_counts)}",
                "",
            ]
        )
    lines.extend(
        [
            "## Summary",
            "| Group | Passed | Failed | Total |",
            "|---|---:|---:|---:|",
        ]
    )
    for group in REPORT_GROUPS:
        group_results = [result for result in report.results if result.group == group]
        if not group_results:
            continue
        passed = sum(1 for result in group_results if result.passed)
        failed = len(group_results) - passed
        lines.append(f"| {group} | {passed} | {failed} | {len(group_results)} |")

    lines.extend(
        [
            "",
            "## Checks",
            "| Status | Group | Name | Details |",
            "|---|---|---|---|",
        ]
    )
    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        details = _details_text(result.details)
        if result.error:
            details = f"{details} error={result.error}".strip()
        lines.append(f"| {status} | {result.group} | {result.name} | {details} |")
    return "\n".join(lines)


def format_regression_json(report: RegressionReport) -> str:
    return json.dumps(asdict(report), indent=2, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run HSR Axis fixture regressions.")
    parser.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    parser.add_argument("--output")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--manifest")
    parser.add_argument("--only")
    args = parser.parse_args(argv)

    try:
        manifest = load_regression_manifest(args.manifest) if args.manifest else None
        report = run_regression(
            only=args.only,
            fail_fast=args.fail_fast,
            manifest=manifest,
        )
        rendered = _render_report(report, args.format)
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered)
        return 0 if report.passed else 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


def _check_replay(path: Path) -> RegressionCheckResult:
    validator = ReplayValidator()
    try:
        data = validator.load_replay(path)
        result = validator.validate(data)
        return RegressionCheckResult(
            group="replays",
            name=result.replay_name,
            path=str(path),
            passed=result.passed,
            details={"checked_steps": result.checked_steps},
            error="; ".join(result.mismatches) if result.mismatches else None,
        )
    except Exception as exc:
        return RegressionCheckResult(
            group="replays",
            name=path.stem,
            path=str(path),
            passed=False,
            error=str(exc),
        )


def _check_manual_trace(path: Path) -> list[RegressionCheckResult]:
    lint_result = _check_manual_lint(path)
    replay_result = _check_manual_replay(path)
    return [lint_result, replay_result]


def _check_manual_lint(path: Path) -> RegressionCheckResult:
    try:
        issues = load_and_lint_manual_video_trace(path)
        return RegressionCheckResult(
            group="manual",
            name=f"{path.stem}:lint",
            path=str(path),
            passed=not issues,
            details={"check": "lint"},
            error="; ".join(issues) if issues else None,
        )
    except Exception as exc:
        return RegressionCheckResult(
            group="manual",
            name=f"{path.stem}:lint",
            path=str(path),
            passed=False,
            details={"check": "lint"},
            error=str(exc),
        )


def _check_manual_replay(path: Path) -> RegressionCheckResult:
    validator = ReplayValidator()
    try:
        result = validator.validate(validator.load_replay(path))
        return RegressionCheckResult(
            group="manual",
            name=f"{result.replay_name}:replay",
            path=str(path),
            passed=result.passed,
            details={"check": "replay", "checked_steps": result.checked_steps},
            error="; ".join(result.mismatches) if result.mismatches else None,
        )
    except Exception as exc:
        return RegressionCheckResult(
            group="manual",
            name=f"{path.stem}:replay",
            path=str(path),
            passed=False,
            details={"check": "replay"},
            error=str(exc),
        )


def _check_scenario(path: Path) -> RegressionCheckResult:
    try:
        scenario = load_search_scenario(path)
        report = run_search_scenario(scenario)
        render_search_scenario_report(report, "json")
        return RegressionCheckResult(
            group="scenarios",
            name=scenario.id,
            path=str(path),
            passed=True,
            details={
                "best_score": report.best_score,
                "terminal_reason": report.best_terminal_reason,
                "depth_reached": report.depth_reached,
                "nodes_expanded": report.nodes_expanded,
            },
        )
    except Exception as exc:
        return RegressionCheckResult(
            group="scenarios",
            name=path.stem,
            path=str(path),
            passed=False,
            error=str(exc),
        )


def _check_action_sequence_trace(entry: RegressionManifestEntry) -> list[RegressionCheckResult]:
    checks: list[RegressionCheckResult] = []
    selected_checks = entry.checks or ["lint", "action_sequence"]
    if "lint" in selected_checks:
        checks.append(_check_action_sequence_lint(entry.path))
    if "action_sequence" in selected_checks:
        checks.append(_check_action_sequence_replay(entry.path))
    return checks


def _check_action_sequence_lint(path: Path) -> RegressionCheckResult:
    try:
        issues = load_and_lint_manual_video_trace(path)
        return RegressionCheckResult(
            group="action_sequence_traces",
            name=f"{path.stem}:lint",
            path=str(path),
            passed=not issues,
            details={"check": "lint"},
            error="; ".join(issues) if issues else None,
        )
    except Exception as exc:
        return RegressionCheckResult(
            group="action_sequence_traces",
            name=f"{path.stem}:lint",
            path=str(path),
            passed=False,
            details={"check": "lint"},
            error=str(exc),
        )


def _check_action_sequence_replay(path: Path) -> RegressionCheckResult:
    validator = ReplayValidator()
    try:
        data = validator.load_replay(path)
        expected_steps = len(data.get("steps", [])) if isinstance(data.get("steps"), list) else 0
        result = validator.validate(data)
        passed = result.passed and result.checked_steps == expected_steps
        error_parts = list(result.mismatches)
        if result.passed and result.checked_steps != expected_steps:
            error_parts.append(
                f"expected checked_steps={expected_steps}, got {result.checked_steps}."
            )
        return RegressionCheckResult(
            group="action_sequence_traces",
            name=f"{result.replay_name}:action_sequence",
            path=str(path),
            passed=passed,
            details={
                "check": "action_sequence",
                "checked_steps": result.checked_steps,
                "expected_steps": expected_steps,
            },
            error="; ".join(error_parts) if error_parts else None,
        )
    except Exception as exc:
        return RegressionCheckResult(
            group="action_sequence_traces",
            name=f"{path.stem}:action_sequence",
            path=str(path),
            passed=False,
            details={"check": "action_sequence"},
            error=str(exc),
        )


def _check_runtime_action_session(entry: RegressionManifestEntry) -> RegressionCheckResult:
    details: dict[str, Any] = {
        "check": "runtime_action_session_golden",
        "action_count": len(entry.actions),
        "expected_sha256": entry.expected_sha256,
    }
    try:
        if entry.expected_sha256 is None or entry.stream_id is None or entry.actor_id is None:
            raise ValueError("Runtime action-session regression entry is incomplete.")

        steps = tuple(
            ExplicitActionCaptureStep(
                Action(
                    action.action_id,
                    action.name,
                    entry.actor_id,
                    ends_turn=action.ends_turn,
                )
            )
            for action in entry.actions
        )
        adapter = LegacyEventAdapterConfig(
            entry.stream_id,
            UnknownLegacyEventPolicy.REJECT,
            AmbiguousLegacyEventPolicy.REJECT,
        )
        trace_configs = tuple(
            TraceExportConfig(
                f"{entry.id}-segment-{index}",
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"fixture_id": entry.id, "segment": index},
            )
            for index in range(len(steps))
        )
        session_config = MultiActionCaptureSessionConfig(
            PendingEventCaptureCursor(0, 0),
            adapter,
            trace_configs,
            False,
        )
        stitch_config = CapturedTraceStitchConfig(
            TraceExportConfig(
                f"{entry.id}-runtime-actual",
                TraceSequencePolicy.CONTIGUOUS,
                EmptyTracePolicy.REJECT,
                {"fixture_id": entry.id, "source": "locked-regression"},
            ),
            False,
        )
        golden_config = GoldenReplayValidationConfig(
            entry.id,
            entry.expected_sha256,
            TraceCanonicalFormPolicy.COMPACT_ONLY,
            100_000,
        )
        result = run_action_session_validation(
            BattleState([]),
            steps,
            session_config=session_config,
            stitch_config=stitch_config,
            expected_payload_bytes=entry.path.read_bytes(),
            golden_config=golden_config,
        )
        golden = result.validation_result.validation_result.validation_result
        details["actual_sha256"] = golden.actual_sha256
        details["record_count"] = golden.actual_load.artifact.document.record_count

        if result.matches:
            return RegressionCheckResult(
                group="runtime_action_sessions",
                name=entry.id,
                path=str(entry.path),
                passed=True,
                details=details,
            )

        divergence = golden.first_divergence.divergence
        if divergence is not None:
            details["first_divergence_record_index"] = divergence.record_index
            if divergence.first_field_difference is not None:
                details["first_divergence_path"] = divergence.first_field_difference.path
        return RegressionCheckResult(
            group="runtime_action_sessions",
            name=entry.id,
            path=str(entry.path),
            passed=False,
            details=details,
            error="Runtime action-session Golden mismatch.",
        )
    except Exception as exc:
        return RegressionCheckResult(
            group="runtime_action_sessions",
            name=entry.id,
            path=str(entry.path),
            passed=False,
            details=details,
            error=str(exc),
        )


def _check_trace_evidence(entry: RegressionManifestEntry) -> RegressionCheckResult:
    source_trace_path = entry.source_trace_path
    details = {
        "check": entry.check,
        "source_trace_path": str(source_trace_path) if source_trace_path else None,
    }
    try:
        if entry.check == "semantic_map":
            issues = validate_semantic_map_files(source_trace_path, entry.path)
        elif entry.check == "frame_anchors":
            issues = validate_frame_anchor_files(source_trace_path, entry.path)
        else:
            raise ValueError(f"Unsupported trace evidence check: {entry.check!r}.")
        return RegressionCheckResult(
            group="trace_evidence",
            name=entry.id,
            path=str(entry.path),
            passed=not issues,
            details=details,
            error="; ".join(issues) if issues else None,
        )
    except Exception as exc:
        return RegressionCheckResult(
            group="trace_evidence",
            name=entry.id,
            path=str(entry.path),
            passed=False,
            details=details,
            error=str(exc),
        )


def _selected_groups(only: str | None) -> list[str]:
    if only is None:
        return list(REPORT_GROUPS)
    if only not in VALID_GROUPS:
        raise ValueError(f"Invalid --only group {only!r}; expected one of {sorted(VALID_GROUPS)}.")
    return [only]


def _report_from_results(
    results: list[RegressionCheckResult],
    manifest: RegressionManifest | None = None,
) -> RegressionReport:
    passed_count = sum(1 for result in results if result.passed)
    failed_count = len(results) - passed_count
    return RegressionReport(
        passed=failed_count == 0,
        total=len(results),
        passed_count=passed_count,
        failed_count=failed_count,
        results=results,
        manifest_id=manifest.manifest_id if manifest is not None else None,
        manifest_path=str(manifest.path) if manifest is not None else None,
        manifest_counts=manifest.counts_by_group() if manifest is not None else {},
    )


def _render_report(report: RegressionReport, format_name: str) -> str:
    if format_name == "text":
        return format_regression_text(report)
    if format_name == "markdown":
        return format_regression_markdown(report)
    if format_name == "json":
        return format_regression_json(report)
    raise ValueError(f"Unknown regression report format: {format_name!r}.")


def _details_text(details: dict[str, Any]) -> str:
    return " ".join(f"{key}={value}" for key, value in details.items())


def _group_label(group: str) -> str:
    if group == "replays":
        return "golden replays"
    if group == "manual":
        return "manual checks"
    if group == "scenarios":
        return "search scenarios"
    if group == "action_sequence_traces":
        return "action-sequence trace checks"
    if group == "runtime_action_sessions":
        return "runtime action-session Golden checks"
    if group == "trace_evidence":
        return "trace evidence checks"
    return group


def _error_text(error: str | None) -> str:
    return f" error={error}" if error else ""


if __name__ == "__main__":
    raise SystemExit(main())
