from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from hsr_axis_sim.search.evaluator import Evaluator, ScoreBreakdown, format_score_breakdown
from hsr_axis_sim.search.node import ActionRecord, SearchNode, SearchResult
from hsr_axis_sim.search.timeline_snapshot import BattleSnapshot, UnitSnapshot


@dataclass
class AxisStepReport:
    step: int
    actor_id: str
    action_id: str
    target_ids: list[str]
    global_av_before: float
    global_av_after: float
    skill_points_after: int
    score_after: float
    line: str
    snapshot_before: BattleSnapshot | None = None
    snapshot_after: BattleSnapshot | None = None


@dataclass
class BeamCandidateReport:
    rank: int
    score: float
    depth: int
    terminal_reason: str | None
    action_count: int
    final_global_av: float
    last_action_key: str | None


@dataclass
class SearchReport:
    best_score: float
    best_terminal_reason: str | None
    search_terminated_reason: str | None
    nodes_expanded: int
    depth_reached: int
    final_beam_count: int
    best_axis_steps: list[AxisStepReport] = field(default_factory=list)
    final_score_breakdown: ScoreBreakdown | None = None
    top_candidates: list[BeamCandidateReport] = field(default_factory=list)


def build_search_report(
    result: SearchResult,
    evaluator: Evaluator | None = None,
    top_k: int = 5,
) -> SearchReport:
    best_node = result.best_node
    return SearchReport(
        best_score=best_node.score,
        best_terminal_reason=best_node.reason,
        search_terminated_reason=result.terminated_reason,
        nodes_expanded=result.nodes_expanded,
        depth_reached=result.depth_reached,
        final_beam_count=len(result.final_beam),
        best_axis_steps=_axis_steps(best_node),
        final_score_breakdown=(
            evaluator.evaluate_breakdown(best_node.state, depth=best_node.depth)
            if evaluator is not None
            else None
        ),
        top_candidates=_candidate_reports(result.final_beam, top_k=top_k),
    )


def format_axis_text(report: SearchReport, include_snapshots: bool = False) -> str:
    lines = [
        "HSR Axis Search Report",
        "",
        "Summary",
        f"- Best score: {report.best_score:.3f}",
        f"- Best terminal reason: {report.best_terminal_reason or '-'}",
        f"- Search terminated reason: {report.search_terminated_reason or '-'}",
        f"- Nodes expanded: {report.nodes_expanded}",
        f"- Depth reached: {report.depth_reached}",
        f"- Final beam candidates: {report.final_beam_count}",
        "",
        "Best Axis",
    ]
    lines.extend(step.line for step in report.best_axis_steps)
    if not report.best_axis_steps:
        lines.append("-")

    if include_snapshots:
        lines.extend(_format_text_snapshots(report))

    if report.final_score_breakdown is not None:
        lines.extend(["", "Score Breakdown", format_score_breakdown(report.final_score_breakdown)])

    lines.extend(["", "Final Beam Candidates"])
    if report.top_candidates:
        for candidate in report.top_candidates:
            lines.append(
                f"{candidate.rank}. score={candidate.score:.3f} "
                f"depth={candidate.depth} reason={candidate.terminal_reason or '-'} "
                f"actions={candidate.action_count} av={candidate.final_global_av:.3f} "
                f"last={candidate.last_action_key or '-'}"
            )
    else:
        lines.append("-")
    return "\n".join(lines)


def format_axis_markdown(report: SearchReport, include_snapshots: bool = False) -> str:
    lines = [
        "# HSR Axis Search Report",
        "",
        "## Summary",
        f"- Best score: {report.best_score:.3f}",
        f"- Best terminal reason: {report.best_terminal_reason or '-'}",
        f"- Search terminated reason: {report.search_terminated_reason or '-'}",
        f"- Nodes expanded: {report.nodes_expanded}",
        f"- Depth reached: {report.depth_reached}",
        f"- Final beam candidates: {report.final_beam_count}",
        "",
        "## Best Axis",
        "",
        "| Step | AV before | Actor | Action | Targets | AV after | SP | Score |",
        "|---:|---:|---|---|---|---:|---:|---:|",
    ]
    if report.best_axis_steps:
        for step in report.best_axis_steps:
            lines.append(
                f"| {step.step} | {step.global_av_before:.3f} | {step.actor_id} | "
                f"{step.action_id} | {_targets_text(step.target_ids)} | "
                f"{step.global_av_after:.3f} | {step.skill_points_after} | "
                f"{step.score_after:.3f} |"
            )
    else:
        lines.append("| - | - | - | - | - | - | - | - |")

    if include_snapshots:
        lines.extend(_format_markdown_snapshots(report))

    if report.final_score_breakdown is not None:
        lines.extend(
            [
                "",
                "## Score Breakdown",
                "",
                "```text",
                format_score_breakdown(report.final_score_breakdown),
                "```",
            ]
        )

    lines.extend(
        [
            "",
            "## Final Beam Candidates",
            "",
            "| Rank | Score | Depth | Reason | Actions | Final AV | Last Action |",
            "|---:|---:|---:|---|---:|---:|---|",
        ]
    )
    if report.top_candidates:
        for candidate in report.top_candidates:
            lines.append(
                f"| {candidate.rank} | {candidate.score:.3f} | {candidate.depth} | "
                f"{candidate.terminal_reason or '-'} | {candidate.action_count} | "
                f"{candidate.final_global_av:.3f} | {candidate.last_action_key or '-'} |"
            )
    else:
        lines.append("| - | - | - | - | - | - | - |")
    return "\n".join(lines)


def search_report_to_dict(report: SearchReport) -> dict[str, Any]:
    return asdict(report)


def _axis_steps(node: SearchNode) -> list[AxisStepReport]:
    return [_axis_step_report(index, record) for index, record in enumerate(node.actions_taken, 1)]


def _axis_step_report(step: int, record: ActionRecord) -> AxisStepReport:
    action_id = record.skill_id or record.action_id or "<unknown>"
    targets = _targets_text(record.target_ids)
    line = (
        f"AV {record.global_av_before:.3f} | {record.actor_id} uses "
        f"{action_id} on {targets} | SP={record.skill_points_after} | "
        f"score={record.score_after:.3f}"
    )
    return AxisStepReport(
        step=step,
        actor_id=record.actor_id,
        action_id=action_id,
        target_ids=list(record.target_ids),
        global_av_before=record.global_av_before,
        global_av_after=record.global_av_after,
        skill_points_after=record.skill_points_after,
        score_after=record.score_after,
        line=line,
        snapshot_before=record.snapshot_before,
        snapshot_after=record.snapshot_after,
    )


def _candidate_reports(nodes: list[SearchNode], top_k: int) -> list[BeamCandidateReport]:
    limited_nodes = nodes[: max(0, top_k)]
    return [
        BeamCandidateReport(
            rank=index,
            score=node.score,
            depth=node.depth,
            terminal_reason=node.reason,
            action_count=len(node.actions_taken),
            final_global_av=node.state.global_av,
            last_action_key=(
                node.actions_taken[-1].action_key if node.actions_taken else None
            ),
        )
        for index, node in enumerate(limited_nodes, 1)
    ]


def _targets_text(target_ids: list[str]) -> str:
    return ",".join(target_ids) if target_ids else "-"


def _format_text_snapshots(report: SearchReport) -> list[str]:
    lines = ["", "Timeline Snapshots"]
    snapshots_added = False
    for step in report.best_axis_steps:
        if step.snapshot_after is None:
            continue
        snapshots_added = True
        lines.append(f"After Step {step.step}")
        lines.extend(_format_text_snapshot(step.snapshot_after))
    if not snapshots_added:
        lines.append("-")
    return lines


def _format_text_snapshot(snapshot: BattleSnapshot) -> list[str]:
    lines = [
        f"Global AV={snapshot.global_av:.3f} SP={snapshot.skill_points}",
        "Unit | Team | HP | Energy | AV | Toughness | Broken | Alive",
    ]
    for unit in snapshot.units:
        lines.append(
            f"{unit.unit_id} | {unit.team} | {_hp_text(unit)} | "
            f"{unit.energy:.3f} | {unit.current_av:.3f} | "
            f"{_toughness_text(unit)} | {unit.is_broken} | {unit.is_alive}"
        )
    return lines


def _format_markdown_snapshots(report: SearchReport) -> list[str]:
    lines = ["", "## Timeline Snapshots"]
    snapshots_added = False
    for step in report.best_axis_steps:
        if step.snapshot_after is None:
            continue
        snapshots_added = True
        lines.extend(
            [
                "",
                f"### After Step {step.step}",
                "",
                f"- Global AV: {step.snapshot_after.global_av:.3f}",
                f"- Skill points: {step.snapshot_after.skill_points}",
                "",
                "| Unit | Team | HP | Energy | AV | Toughness | Broken | Alive |",
                "|---|---|---:|---:|---:|---:|---|---|",
            ]
        )
        for unit in step.snapshot_after.units:
            lines.append(
                f"| {unit.unit_id} | {unit.team} | {_hp_text(unit)} | "
                f"{unit.energy:.3f} | {unit.current_av:.3f} | "
                f"{_toughness_text(unit)} | {unit.is_broken} | {unit.is_alive} |"
            )
    if not snapshots_added:
        lines.extend(["", "-"])
    return lines


def _hp_text(unit: UnitSnapshot) -> str:
    return f"{unit.hp:.3f}/{unit.max_hp:.3f}"


def _toughness_text(unit: UnitSnapshot) -> str:
    if unit.current_toughness is None or unit.max_toughness is None:
        return "-"
    return f"{unit.current_toughness:.3f}/{unit.max_toughness:.3f}"
