from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .action_generator import ActionChoice, is_skill_affordable, skill_affordability
from .data_schema import SkillSpec
from .state import BattleState
from .targeting import legal_target_groups, normalize_and_validate_target_ids
from .turn_context import TurnContext


@dataclass
class EnemyPatternStep:
    skill_id: str
    target_strategy: str = "first_legal"
    target_ids: list[str] | None = None


@dataclass
class EnemyAIPlan:
    pattern: list[EnemyPatternStep] = field(default_factory=list)
    repeat: bool = True


def enemy_ai_plan_from_spec(spec: dict[str, Any]) -> EnemyAIPlan:
    return EnemyAIPlan(
        pattern=[
            EnemyPatternStep(
                skill_id=step["skill_id"],
                target_strategy=step.get("target_strategy", "first_legal"),
                target_ids=list(step["target_ids"]) if "target_ids" in step else None,
            )
            for step in spec["pattern"]
        ],
        repeat=spec.get("repeat", True),
    )


def choose_enemy_action(
    state: BattleState,
    skill_lookup: dict[str, dict[str, SkillSpec]],
    actor_id: str,
    forced_rng: dict[str, Any] | None = None,
) -> ActionChoice:
    actor = _get_alive_actor(state, actor_id)
    plan = state.enemy_ai_plans.get(actor.id)
    if plan is None:
        raise ValueError(f"Enemy actor {actor_id!r} has no enemy AI plan.")
    if not isinstance(plan, EnemyAIPlan):
        raise ValueError(f"Enemy actor {actor_id!r} has an invalid enemy AI plan.")
    if not plan.pattern:
        raise ValueError(f"Enemy actor {actor_id!r} has an empty enemy AI pattern.")

    cursor = state.enemy_ai_cursors.get(actor.id, 0)
    step = _pattern_step_at_cursor(plan, cursor, actor.id)
    actor_skills = skill_lookup.get(actor.id)
    if actor_skills is None:
        raise ValueError(f"No loaded skills for enemy actor {actor_id!r}.")
    skill = actor_skills.get(step.skill_id)
    if skill is None:
        raise ValueError(
            f"Enemy AI pattern for {actor_id!r} references unknown skill "
            f"{step.skill_id!r}."
        )

    affordability = skill_affordability(state, actor.id, skill)
    if not affordability.affordable:
        reasons = "; ".join(affordability.reasons)
        raise ValueError(
            f"Enemy actor {actor_id!r} cannot afford skill {skill.id!r}: {reasons}"
        )

    target_ids = resolve_enemy_target_ids(
        state,
        actor.id,
        skill,
        step,
        forced_rng=forced_rng,
    )
    from .data_loader import action_from_skill

    action = action_from_skill(
        skill,
        actor_id=actor.id,
        target_ids=target_ids,
        state=state,
        validate_targets=True,
    )
    return ActionChoice(
        actor_id=actor.id,
        skill_id=skill.id,
        skill_type=skill.skill_type,
        target_ids=list(action.target_ids),
        action=action,
    )


def execute_enemy_ai_action(
    state: BattleState,
    skill_lookup: dict[str, dict[str, SkillSpec]],
    actor_id: str,
    turn_context: TurnContext,
    forced_rng: dict[str, Any] | None = None,
) -> ActionChoice:
    if turn_context.actor_id != actor_id:
        raise ValueError(
            "Enemy AI actor_id must match the active turn context actor_id: "
            f"{actor_id!r} != {turn_context.actor_id!r}."
        )

    choice = choose_enemy_action(
        state,
        skill_lookup,
        actor_id,
        forced_rng=forced_rng,
    )
    choice.action.execute(state, turn_context)
    state.enemy_ai_cursors[actor_id] = state.enemy_ai_cursors.get(actor_id, 0) + 1
    return choice


def resolve_enemy_target_ids(
    state: BattleState,
    actor_id: str,
    skill: SkillSpec,
    pattern_step: EnemyPatternStep,
    forced_rng: dict[str, Any] | None = None,
) -> list[str]:
    legal_groups = legal_target_groups(state, actor_id, skill.target_type)
    if not legal_groups:
        raise ValueError(
            f"No legal target groups for actor {actor_id!r} and target_type "
            f"{skill.target_type!r}."
        )
    if legal_groups == [[]]:
        return []

    strategy = pattern_step.target_strategy
    if strategy == "first_legal":
        return list(legal_groups[0])
    if strategy == "last_legal":
        return list(legal_groups[-1])
    if strategy == "lowest_hp_legal":
        return _single_target_by_hp(state, legal_groups, lowest=True)
    if strategy == "highest_hp_legal":
        return _single_target_by_hp(state, legal_groups, lowest=False)
    if strategy == "explicit":
        if pattern_step.target_ids is None:
            raise ValueError("Enemy AI explicit target strategy requires target_ids.")
        return normalize_and_validate_target_ids(
            state,
            actor_id,
            skill.target_type,
            pattern_step.target_ids,
        )
    if strategy == "forced_rng_target":
        forced_rng = forced_rng or {}
        target_id = forced_rng.get("enemy_target_id", forced_rng.get("target_id"))
        if target_id is None:
            raise ValueError(
                "Enemy AI forced_rng_target strategy requires forced_rng "
                "'enemy_target_id' or 'target_id'."
            )
        return normalize_and_validate_target_ids(
            state,
            actor_id,
            skill.target_type,
            [target_id],
        )

    raise ValueError(f"Unsupported enemy AI target_strategy: {strategy!r}.")


def _pattern_step_at_cursor(
    plan: EnemyAIPlan,
    cursor: int,
    actor_id: str,
) -> EnemyPatternStep:
    if plan.repeat:
        return plan.pattern[cursor % len(plan.pattern)]
    if cursor >= len(plan.pattern):
        return plan.pattern[-1]
    return plan.pattern[cursor]


def _single_target_by_hp(
    state: BattleState,
    legal_groups: list[list[str]],
    lowest: bool,
) -> list[str]:
    single_target_groups = [group for group in legal_groups if len(group) == 1]
    if not single_target_groups:
        raise ValueError("HP target strategy requires single-target legal groups.")

    def sort_key(group: list[str]) -> tuple[float, int]:
        unit = state.get_unit(group[0])
        original_index = legal_groups.index(group)
        hp_key = unit.hp if lowest else -unit.hp
        return hp_key, original_index

    return list(min(single_target_groups, key=sort_key))


def _get_alive_actor(state: BattleState, actor_id: str):
    try:
        actor = state.get_unit(actor_id)
    except KeyError as exc:
        raise ValueError(f"Unknown enemy actor id: {actor_id!r}.") from exc
    if not actor.is_alive:
        raise ValueError(f"Enemy actor {actor_id!r} is not alive.")
    return actor
