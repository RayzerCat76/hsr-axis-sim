from __future__ import annotations

from dataclasses import dataclass, field

from hsr_axis_sim.search.timeline_snapshot import BattleSnapshot
from hsr_axis_sim.sim.state import BattleState


@dataclass
class ActionRecord:
    actor_id: str
    skill_id: str | None = None
    action_id: str | None = None
    target_ids: list[str] = field(default_factory=list)
    global_av_before: float = 0
    global_av_after: float = 0
    skill_points_after: int = 0
    score_after: float = 0
    action_key: str = ""
    snapshot_before: BattleSnapshot | None = None
    snapshot_after: BattleSnapshot | None = None


@dataclass
class SearchNode:
    state: BattleState
    actions_taken: list[ActionRecord] = field(default_factory=list)
    score: float = 0
    depth: int = 0
    terminal: bool = False
    reason: str | None = None


@dataclass
class SearchResult:
    best_node: SearchNode
    final_beam: list[SearchNode]
    nodes_expanded: int
    depth_reached: int
    terminated_reason: str | None = None


def format_axis(node: SearchNode) -> str:
    lines: list[str] = []
    for record in node.actions_taken:
        action_name = record.skill_id or record.action_id or "<unknown>"
        targets = ",".join(record.target_ids) if record.target_ids else "-"
        lines.append(
            f"AV {record.global_av_before:.3f} | {record.actor_id} uses "
            f"{action_name} on {targets} | SP={record.skill_points_after} | "
            f"score={record.score_after:.3f}"
        )
    return "\n".join(lines)
