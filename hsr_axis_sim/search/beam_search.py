from __future__ import annotations

from hsr_axis_sim.search.constraints import SearchConstraints
from hsr_axis_sim.search.evaluator import Evaluator
from hsr_axis_sim.search.node import SearchNode, SearchResult
from hsr_axis_sim.search.search_engine import SearchConfig, SearchEngine
from hsr_axis_sim.sim.data_schema import SkillSpec
from hsr_axis_sim.sim.state import BattleState


def beam_search(
    initial_state: BattleState,
    skill_lookup: dict[str, dict[str, SkillSpec]],
    max_depth: int,
    beam_width: int,
    evaluator: Evaluator | None = None,
    max_nodes_expanded: int | None = None,
    max_global_av: float | None = None,
    include_ultimates: bool = False,
    constraints: SearchConstraints | None = None,
) -> SearchResult:
    config = SearchConfig(
        max_depth=max_depth,
        max_global_av=max_global_av,
        max_nodes_expanded=max_nodes_expanded,
        include_ultimates=include_ultimates,
        constraints=constraints,
    )
    engine = SearchEngine(skill_lookup=skill_lookup, evaluator=evaluator, config=config)
    root = engine.make_root(initial_state)
    beam = [root]
    best_node = root
    nodes_expanded = 0
    depth_reached = 0
    terminated_reason: str | None = root.reason
    budget_exhausted = False

    for _ in range(max_depth):
        candidates: list[SearchNode] = []
        for node in beam:
            engine.mark_terminal(node, nodes_expanded=nodes_expanded)
            if node.terminal:
                candidates.append(node)
                terminated_reason = node.reason
                continue
            if max_nodes_expanded is not None and nodes_expanded >= max_nodes_expanded:
                node.terminal = True
                node.reason = "max_nodes_expanded"
                candidates.append(node)
                terminated_reason = "max_nodes_expanded"
                continue

            children = engine.expand_node(node)
            nodes_expanded += 1
            candidates.extend(children or [node])
            if max_nodes_expanded is not None and nodes_expanded >= max_nodes_expanded:
                terminated_reason = "max_nodes_expanded"
                budget_exhausted = True
                break

        if not candidates:
            terminated_reason = "no_candidates"
            break

        beam = sorted(candidates, key=_node_sort_key)[:beam_width]
        best_node = min([best_node, *beam], key=_node_sort_key)
        depth_reached = max(depth_reached, max(node.depth for node in beam))

        if budget_exhausted:
            break

        if all(node.terminal for node in beam):
            terminated_reason = beam[0].reason
            break

    return SearchResult(
        best_node=best_node,
        final_beam=beam,
        nodes_expanded=nodes_expanded,
        depth_reached=depth_reached,
        terminated_reason=terminated_reason,
    )


def _node_sort_key(node: SearchNode) -> tuple[float, float, int, str]:
    action_key = node.actions_taken[-1].action_key if node.actions_taken else ""
    return (-node.score, node.state.global_av, len(node.actions_taken), action_key)
