from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from hsr_axis_sim.sim.replay_lint import lint_manual_video_trace
from hsr_axis_sim.tools.trace_frame_anchors import validate_frame_anchors
from hsr_axis_sim.tools.trace_semantics import validate_semantic_map


REPORT_VERSION = "0.1"
POLICY_WARNING = (
    "Evidence-only and non-executable. Media timestamps are not AV or simulator "
    "time. Unknown combat values remain unknown; no damage, SP, energy, HP, "
    "toughness, speed, target, buff, debuff, or RNG value is inferred beyond the "
    "accepted source trace."
)


@dataclass(frozen=True)
class MediaEvidence:
    time_start_seconds: float
    time_end_seconds: float
    representative_frames: list[str]
    confidence: str
    notes: str


@dataclass(frozen=True)
class PrebattleEvidence:
    actor: str
    action: str
    source_notes: str | None
    semantic_label: str
    semantic_category: str
    known: list[str]
    unknown: list[str]
    media_evidence: MediaEvidence


@dataclass(frozen=True)
class StepEvidence:
    step: int
    actor: str
    action: str
    target: str
    target_confidence: str
    source_notes: str | None
    semantic_label: str
    semantic_category: str
    known: list[str]
    unknown: list[str]
    media_evidence: MediaEvidence


@dataclass(frozen=True)
class TraceEvidenceReport:
    report_id: str
    version: str
    source_trace_id: str
    source_video: dict[str, Any]
    scenario: dict[str, Any]
    team: list[dict[str, Any]]
    evidence_policy: dict[str, Any]
    prebattle: list[PrebattleEvidence]
    steps: list[StepEvidence]


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as json_file:
        value = json.load(json_file)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def build_trace_evidence_report(
    trace_data: dict[str, Any],
    semantic_map: dict[str, Any],
    frame_anchors: dict[str, Any],
) -> TraceEvidenceReport:
    _validate_inputs(trace_data, semantic_map, frame_anchors)
    semantic_prebattle = _index_items(semantic_map["prebattle"], ["actor", "action"])
    anchor_prebattle = _index_items(frame_anchors["prebattle"], ["actor", "action"])
    semantic_steps = _index_items(semantic_map["steps"], ["step", "actor", "action"])
    anchor_steps = _index_items(frame_anchors["steps"], ["step", "actor", "action"])

    prebattle = [
        _build_prebattle(item, semantic_prebattle[(item["actor"], item["action"])], anchor_prebattle[(item["actor"], item["action"])])
        for item in trace_data.get("prebattle", [])
    ]
    steps = [
        _build_step(
            item,
            semantic_steps[(item["step"], item["actor"], item["action"])],
            anchor_steps[(item["step"], item["actor"], item["action"])],
        )
        for item in trace_data["steps"]
    ]
    trace_id = trace_data["name"]
    return TraceEvidenceReport(
        report_id=f"{trace_id}_evidence_report_v0_1",
        version=REPORT_VERSION,
        source_trace_id=trace_id,
        source_video=dict(trace_data["source"]),
        scenario=dict(trace_data["scenario"]),
        team=[dict(unit) for unit in trace_data["team"]],
        evidence_policy={
            "evidence_only": True,
            "executable": False,
            "media_timestamps_are_simulator_time": False,
            "unknown_combat_values_remain_unknown": True,
            "warning": POLICY_WARNING,
        },
        prebattle=prebattle,
        steps=steps,
    )


def build_trace_evidence_report_files(
    trace_path: str | Path,
    semantic_map_path: str | Path,
    frame_anchor_path: str | Path,
) -> TraceEvidenceReport:
    return build_trace_evidence_report(
        load_json(trace_path), load_json(semantic_map_path), load_json(frame_anchor_path)
    )


def report_to_dict(report: TraceEvidenceReport) -> dict[str, Any]:
    return asdict(report)


def render_json(report: TraceEvidenceReport) -> str:
    return json.dumps(report_to_dict(report), ensure_ascii=False, indent=2) + "\n"


def render_markdown(report: TraceEvidenceReport) -> str:
    source = report.source_video
    scenario = report.scenario
    team = ", ".join(
        f"{unit['unit_id']} ({unit['character']})" for unit in report.team
    )
    lines = [
        f"# Trace Evidence Report: {report.source_trace_id}",
        "",
        f"Report ID: `{report.report_id}`  ",
        f"Version: `{report.version}`",
        "",
        "## Source Video",
        "",
        f"- Platform: {source['platform']}",
        f"- Title: {source['title']}",
        f"- URL: {source['url']}",
        "",
        "## Evidence Policy",
        "",
        f"> {report.evidence_policy['warning']}",
        "",
        "## Scenario and Team",
        "",
        f"- Game: {scenario['game_context']}",
        f"- Scenario: {scenario['mode']}, {scenario['floor']}, {scenario['side']}",
        f"- Team: {team}",
        "",
        "## Prebattle Evidence",
        "",
    ]
    for item in report.prebattle:
        lines.extend(_markdown_evidence_details(item, f"{item.actor} / {item.action}"))
    lines.extend(
        [
            "## Ordered Step Evidence",
            "",
            "| Step | Media evidence range (s) | Actor | Action | Semantic label | Category | Confidence | Representative frames |",
            "|---:|---|---|---|---|---|---|---|",
        ]
    )
    for step in report.steps:
        media = step.media_evidence
        lines.append(
            "| {step} | {start:.1f}-{end:.1f} | {actor} | {action} | {label} | {category} | {confidence} | {frames} |".format(
                step=step.step,
                start=media.time_start_seconds,
                end=media.time_end_seconds,
                actor=step.actor,
                action=step.action,
                label=step.semantic_label,
                category=step.semantic_category,
                confidence=media.confidence,
                frames=", ".join(media.representative_frames),
            )
        )
    lines.extend(["", "## Step Details", ""])
    for step in report.steps:
        lines.extend(_markdown_evidence_details(step, f"Step {step.step}: {step.actor} / {step.action}"))
    return "\n".join(lines) + "\n"


def _markdown_evidence_details(item: PrebattleEvidence | StepEvidence, heading: str) -> list[str]:
    media = item.media_evidence
    lines = [f"### {heading}", ""]
    if isinstance(item, StepEvidence):
        lines.append(f"- Target: `{item.target}` (confidence: `{item.target_confidence}`)")
    lines.extend(
        [
            f"- Semantic: {item.semantic_label} (`{item.semantic_category}`)",
            f"- Media evidence range: {media.time_start_seconds:.1f}-{media.time_end_seconds:.1f} seconds",
            f"- Representative frames: {', '.join(media.representative_frames)}",
            f"- Frame confidence: `{media.confidence}`",
            f"- Known: {'; '.join(item.known)}",
            f"- Unknown: {'; '.join(item.unknown)}",
            f"- Source notes: {item.source_notes or 'None'}",
            f"- Frame notes: {media.notes}",
            "",
        ]
    )
    return lines


def _build_prebattle(source: dict[str, Any], semantic: dict[str, Any], anchor: dict[str, Any]) -> PrebattleEvidence:
    return PrebattleEvidence(
        actor=source["actor"], action=source["action"], source_notes=source.get("notes"),
        semantic_label=semantic["semantic_label"], semantic_category=semantic["category"],
        known=list(semantic["known"]), unknown=list(semantic["unknown"]),
        media_evidence=_media_evidence(anchor),
    )


def _build_step(source: dict[str, Any], semantic: dict[str, Any], anchor: dict[str, Any]) -> StepEvidence:
    return StepEvidence(
        step=source["step"], actor=source["actor"], action=source["action"],
        target=source["target"], target_confidence=source["target_confidence"],
        source_notes=source.get("notes"), semantic_label=semantic["semantic_label"],
        semantic_category=semantic["category"], known=list(semantic["known"]),
        unknown=list(semantic["unknown"]), media_evidence=_media_evidence(anchor),
    )


def _media_evidence(anchor: dict[str, Any]) -> MediaEvidence:
    return MediaEvidence(
        time_start_seconds=anchor["time_start_seconds"], time_end_seconds=anchor["time_end_seconds"],
        representative_frames=list(anchor["representative_frames"]), confidence=anchor["confidence"],
        notes=anchor["notes"],
    )


def _index_items(items: list[dict[str, Any]], fields: list[str]) -> dict[tuple[Any, ...], dict[str, Any]]:
    return {tuple(item[field] for field in fields): item for item in items}


def _validate_inputs(trace: dict[str, Any], semantic_map: dict[str, Any], frame_anchors: dict[str, Any]) -> None:
    issues = lint_manual_video_trace(trace)
    issues.extend(validate_semantic_map(trace, semantic_map))
    validation_anchors = dict(frame_anchors)
    if isinstance(frame_anchors.get("steps"), list):
        # Anchor list order is presentation-independent; the trace supplies step order.
        validation_anchors["steps"] = sorted(
            frame_anchors["steps"], key=lambda item: item.get("step", -1)
            if isinstance(item, dict) else -1
        )
    issues.extend(validate_frame_anchors(trace, validation_anchors))
    if issues:
        raise ValueError("Trace evidence validation failed:\n" + "\n".join(f"- {issue}" for issue in issues))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a non-executable trace evidence report.")
    parser.add_argument("--trace", required=True)
    parser.add_argument("--semantic-map", required=True)
    parser.add_argument("--frame-anchors", required=True)
    parser.add_argument("--format", choices=["markdown", "json"], required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        trace_data = load_json(args.trace)
        semantic_map = load_json(args.semantic_map)
        frame_anchors = load_json(args.frame_anchors)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR trace evidence report input failure: {exc}", file=sys.stderr)
        return 2
    try:
        report = build_trace_evidence_report(trace_data, semantic_map, frame_anchors)
    except ValueError as exc:
        print(f"FAIL trace evidence report validation: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR trace evidence report could not run: {exc}", file=sys.stderr)
        return 2
    rendered = render_markdown(report) if args.format == "markdown" else render_json(report)
    try:
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except OSError as exc:
        print(f"ERROR trace evidence report output failure: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
