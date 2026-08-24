from __future__ import annotations

import copy
from dataclasses import dataclass

from hsr_axis_sim.search.constraints import SearchConstraints, filter_action_choices
from hsr_axis_sim.search.evaluator import Evaluator
from hsr_axis_sim.search.node import ActionRecord, SearchNode
from hsr_axis_sim.search.timeline_snapshot import BattleSnapshot, snapshot_battle_state
from hsr_axis_sim.sim.action_generator import legal_action_choices_for_actor
from hsr_axis_sim.sim.data_schema import SkillSpec
from hsr_axis_sim.sim.enemy_ai import execute_enemy_ai_action
from hsr_axis_sim.sim.state import BattleState
from hsr_axis_sim.sim.timeline import Timeline
from hsr_axis_sim.sim.ultimate_windows import execute_interrupt_action, legal_ultimate_choices


def clone_state_for_search(state: BattleState) -> BattleState:
    return copy.deepcopy(state)


@dataclass
class SearchConfig:
    max_depth: int = 3
    max_global_av: float | None = None
    max_nodes_expanded: int | None = None
    include_ultimates: bool = False
    constraints: SearchConstraints | None = None


class SearchEngine:
    def __init__(
        self,
        skill_lookup: dict[str, dict[str, SkillSpec]],
        evaluator: Evaluator | None = None,
        config: SearchConfig | None = None,
    ) -> None:
        self.skill_lookup = skill_lookup
        self.evaluator = evaluator or Evaluator()
        self.config = config or SearchConfig()

    def make_root(self, state: BattleState) -> SearchNode:
        root_state = clone_state_for_search(state)
        root = SearchNode(state=root_state, depth=0)
        root.score = self.evaluator.evaluate(root_state, depth=0)
        self.mark_terminal(root)
        return root

    def expand_node(self, node: SearchNode) -> list[SearchNode]:
        self.mark_terminal(node)
        if node.terminal:
            return []

        children: list[SearchNode] = []
        if self.config.include_ultimates:
            children.extend(self._expand_ultimates(node))
        children.extend(self._expand_next_normal_action(node))
        if not children:
            node.terminal = True
            node.reason = (
                "constraints_no_choices"
                if self.config.constraints is not None
                else "no_legal_choices"
            )
        return children

    def mark_terminal(
        self,
        node: SearchNode,
        nodes_expanded: int | None = None,
    ) -> None:
        reason = self.terminal_reason(node, nodes_expanded=nodes_expanded)
        node.terminal = reason is not None
        node.reason = reason

    def terminal_reason(
        self,
        node: SearchNode,
        nodes_expanded: int | None = None,
    ) -> str | None:
        alive_enemies = [
            unit for unit in node.state.units if unit.team == "enemy" and unit.is_alive
        ]
        alive_allies = [
            unit for unit in node.state.units if unit.team == "ally" and unit.is_alive
        ]
        if not alive_enemies:
            return "all_enemies_defeated"
        if not alive_allies:
            return "all_allies_defeated"
        if node.depth >= self.config.max_depth:
            return "max_depth"
        if (
            self.config.max_global_av is not None
            and node.state.global_av >= self.config.max_global_av
        ):
            return "max_global_av"
        if (
            nodes_expanded is not None
            and self.config.max_nodes_expanded is not None
            and nodes_expanded >= self.config.max_nodes_expanded
        ):
            return "max_nodes_expanded"
        return None

    def _expand_next_normal_action(self, node: SearchNode) -> list[SearchNode]:
        state_after_turn_select = clone_state_for_search(node.state)
        global_av_before = state_after_turn_select.global_av
        turn_context = Timeline.next_turn(state_after_turn_select)
        actor = state_after_turn_select.get_unit(turn_context.actor_id)

        if actor.team == "enemy" and actor.id in state_after_turn_select.enemy_ai_plans:
            branch_state = clone_state_for_search(state_after_turn_select)
            branch_turn_context = copy.deepcopy(turn_context)
            choice = execute_enemy_ai_action(
                branch_state,
                self.skill_lookup,
                actor.id,
                branch_turn_context,
            )
            return [
                self._child_from_branch(
                    parent=node,
                    branch_state=branch_state,
                    actor_id=choice.actor_id,
                    skill_id=choice.skill_id,
                    action_id=choice.action.id,
                    target_ids=choice.target_ids,
                    global_av_before=global_av_before,
                    snapshot_before=snapshot_battle_state(state_after_turn_select),
                )
            ]

        actor_skills = self.skill_lookup.get(actor.id)
        if actor_skills is None:
            raise ValueError(f"No loaded skills for actor {actor.id!r}.")

        choices = legal_action_choices_for_actor(
            state_after_turn_select,
            actor.id,
            actor_skills,
        )
        choices = filter_action_choices(choices, self.config.constraints)
        children: list[SearchNode] = []
        for choice in choices:
            branch_state = clone_state_for_search(state_after_turn_select)
            branch_turn_context = copy.deepcopy(turn_context)
            choice.action.execute(branch_state, branch_turn_context)
            children.append(
                self._child_from_branch(
                    parent=node,
                    branch_state=branch_state,
                    actor_id=choice.actor_id,
                    skill_id=choice.skill_id,
                    action_id=choice.action.id,
                    target_ids=choice.target_ids,
                    global_av_before=global_av_before,
                    snapshot_before=snapshot_battle_state(state_after_turn_select),
                )
            )
        return children

    def _expand_ultimates(self, node: SearchNode) -> list[SearchNode]:
        choices = filter_action_choices(
            legal_ultimate_choices(node.state, self.skill_lookup),
            self.config.constraints,
        )
        children: list[SearchNode] = []
        for choice in choices:
            branch_state = clone_state_for_search(node.state)
            global_av_before = branch_state.global_av
            execute_interrupt_action(branch_state, choice.action)
            children.append(
                self._child_from_branch(
                    parent=node,
                    branch_state=branch_state,
                    actor_id=choice.actor_id,
                    skill_id=choice.skill_id,
                    action_id=choice.action.id,
                    target_ids=choice.target_ids,
                    global_av_before=global_av_before,
                    snapshot_before=snapshot_battle_state(node.state),
                )
            )
        return children

    def _child_from_branch(
        self,
        parent: SearchNode,
        branch_state: BattleState,
        actor_id: str,
        skill_id: str | None,
        action_id: str | None,
        target_ids: list[str],
        global_av_before: float,
        snapshot_before: BattleSnapshot,
    ) -> SearchNode:
        depth = parent.depth + 1
        score = self.evaluator.evaluate(branch_state, depth=depth)
        action_key = _action_key(actor_id, skill_id or action_id or "", target_ids)
        record = ActionRecord(
            actor_id=actor_id,
            skill_id=skill_id,
            action_id=action_id,
            target_ids=list(target_ids),
            global_av_before=global_av_before,
            global_av_after=branch_state.global_av,
            skill_points_after=branch_state.skill_points,
            score_after=score,
            action_key=action_key,
            snapshot_before=snapshot_before,
            snapshot_after=snapshot_battle_state(branch_state),
        )
        child = SearchNode(
            state=branch_state,
            actions_taken=[*parent.actions_taken, record],
            score=score,
            depth=depth,
        )
        self.mark_terminal(child)
        return child


def _action_key(actor_id: str, action_id: str, target_ids: list[str]) -> str:
    return f"{actor_id}:{action_id}:{','.join(target_ids)}"
