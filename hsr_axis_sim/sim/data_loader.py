from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from .action import Action
from .data_schema import CharacterSpec, SkillSpec, TeamSpec, TriggerSpec, UnitInstanceSpec
from .effects import (
    AddBuff,
    AddDebuff,
    AdvanceAction,
    ChangeSpeed,
    ConsumeEnergy,
    ConsumeSkillPoint,
    DealDamage,
    DealToughnessDamage,
    DelayAction,
    DoesNotEndTurn,
    Effect,
    GainEnergy,
    GainSkillPoint,
    GrantExtraTurn,
    ImmediateAction,
    RemoveBuff,
    RemoveDebuff,
)
from .events import Trigger
from .state import BattleState
from .targeting import normalize_and_validate_target_ids
from .unit import Unit


EFFECT_TYPES: dict[str, type[Effect]] = {
    "AddBuff": AddBuff,
    "AddDebuff": AddDebuff,
    "AdvanceAction": AdvanceAction,
    "ChangeSpeed": ChangeSpeed,
    "ConsumeEnergy": ConsumeEnergy,
    "ConsumeSkillPoint": ConsumeSkillPoint,
    "DealDamage": DealDamage,
    "DealToughnessDamage": DealToughnessDamage,
    "DelayAction": DelayAction,
    "DoesNotEndTurn": DoesNotEndTurn,
    "GainEnergy": GainEnergy,
    "GainSkillPoint": GainSkillPoint,
    "GrantExtraTurn": GrantExtraTurn,
    "ImmediateAction": ImmediateAction,
    "RemoveBuff": RemoveBuff,
    "RemoveDebuff": RemoveDebuff,
}

UNIT_EFFECT_TYPES = {
    "AddBuff",
    "AddDebuff",
    "AdvanceAction",
    "ChangeSpeed",
    "ConsumeEnergy",
    "DealDamage",
    "DealToughnessDamage",
    "DelayAction",
    "GainEnergy",
    "GrantExtraTurn",
    "ImmediateAction",
    "RemoveBuff",
    "RemoveDebuff",
}

KNOWN_STAT_OVERRIDES = {
    "hp",
    "level",
    "atk",
    "defense",
    "base_speed",
    "max_energy",
    "crit_rate",
    "crit_dmg",
    "dmg_bonus",
    "break_effect",
    "all_res",
    "quantum_res",
    "wind_res",
    "fire_res",
    "ice_res",
    "lightning_res",
    "physical_res",
    "imaginary_res",
    "max_toughness",
    "weaknesses",
    "element",
}


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as data_file:
        return json.load(data_file)


def load_character_spec(path: str | Path) -> CharacterSpec:
    return CharacterSpec.from_dict(load_json(path))


def load_team_spec(path: str | Path) -> TeamSpec:
    return TeamSpec.from_dict(load_json(path))


def load_character_specs_from_dir(characters_dir: str | Path) -> dict[str, CharacterSpec]:
    specs: dict[str, CharacterSpec] = {}
    for path in sorted(Path(characters_dir).glob("*.json")):
        spec = load_character_spec(path)
        specs[spec.id] = spec
    return specs


def instantiate_unit(character: CharacterSpec, unit_ref: UnitInstanceSpec) -> Unit:
    unknown_overrides = sorted(set(unit_ref.stat_overrides) - KNOWN_STAT_OVERRIDES)
    if unknown_overrides:
        raise ValueError(f"Unknown stat override(s): {unknown_overrides}.")

    stats = replace(character.base_stats)
    element = character.element
    for field_name, value in unit_ref.stat_overrides.items():
        if field_name == "element":
            element = value
        else:
            setattr(stats, field_name, value)

    return Unit(
        id=unit_ref.unit_id,
        name=character.name,
        team=unit_ref.team,
        base_speed=stats.base_speed,
        current_av=unit_ref.initial_current_av,
        energy=unit_ref.initial_energy or 0,
        max_energy=stats.max_energy,
        hp=unit_ref.initial_hp if unit_ref.initial_hp is not None else stats.hp,
        max_hp=stats.hp,
        level=unit_ref.level if unit_ref.level is not None else stats.level,
        atk=stats.atk,
        defense=stats.defense,
        crit_rate=stats.crit_rate,
        crit_dmg=stats.crit_dmg,
        dmg_bonus=stats.dmg_bonus,
        break_effect=stats.break_effect,
        all_res=stats.all_res,
        quantum_res=stats.quantum_res,
        wind_res=stats.wind_res,
        fire_res=stats.fire_res,
        ice_res=stats.ice_res,
        lightning_res=stats.lightning_res,
        physical_res=stats.physical_res,
        imaginary_res=stats.imaginary_res,
        element=element,
        weaknesses=list(stats.weaknesses),
        max_toughness=stats.max_toughness,
        current_toughness=unit_ref.initial_toughness,
    )


def build_battle_state_from_team(
    team: TeamSpec,
    characters: dict[str, CharacterSpec],
) -> tuple[BattleState, dict[str, dict[str, SkillSpec]]]:
    unit_ids = [unit_ref.unit_id for unit_ref in team.unit_refs]
    duplicate_unit_ids = sorted({unit_id for unit_id in unit_ids if unit_ids.count(unit_id) > 1})
    if duplicate_unit_ids:
        raise ValueError(f"Duplicate unit id(s): {duplicate_unit_ids}.")

    units: list[Unit] = []
    triggers: list[Trigger] = []
    skill_lookup: dict[str, dict[str, SkillSpec]] = {}
    enemy_ai_plans: dict[str, object] = {}
    enemy_ai_cursors: dict[str, int] = {}
    for unit_ref in team.unit_refs:
        character = characters.get(unit_ref.character_id)
        if character is None:
            raise ValueError(f"Unknown character id: {unit_ref.character_id!r}.")
        unit = instantiate_unit(character, unit_ref)
        units.append(unit)
        skill_lookup[unit.id] = {skill.id: skill for skill in character.skills}
        if character.enemy_ai is not None:
            from .enemy_ai import enemy_ai_plan_from_spec

            enemy_ai_plans[unit.id] = enemy_ai_plan_from_spec(character.enemy_ai)
            enemy_ai_cursors[unit.id] = 0
        for trigger_template in character.triggers:
            triggers.append(trigger_from_spec(trigger_template, owner_id=unit.id))

    state = BattleState(
        units=units,
        skill_points=team.initial_skill_points,
        max_skill_points=team.max_skill_points,
        triggers=triggers,
        enemy_ai_plans=enemy_ai_plans,
        enemy_ai_cursors=enemy_ai_cursors,
    )
    return state, skill_lookup


def build_battle_state_from_files(
    team_path: str | Path,
    characters_dir: str | Path,
) -> tuple[BattleState, dict[str, dict[str, SkillSpec]]]:
    return build_battle_state_from_team(
        team=load_team_spec(team_path),
        characters=load_character_specs_from_dir(characters_dir),
    )


def action_from_skill(
    skill: SkillSpec,
    actor_id: str,
    target_ids: list[str] | None = None,
    state: BattleState | None = None,
    validate_targets: bool = False,
) -> Action:
    action_target_ids = list(target_ids or [])
    if state is not None and validate_targets:
        action_target_ids = normalize_and_validate_target_ids(
            state=state,
            actor_id=actor_id,
            target_type=skill.target_type,
            target_ids=action_target_ids,
        )

    effects = [effect_from_spec(effect_spec) for effect_spec in skill.effects]
    return Action(
        id=skill.id,
        name=skill.name,
        actor_id=actor_id,
        target_ids=action_target_ids,
        effects=effects,
        ends_turn=skill.ends_turn,
    )


def effect_from_spec(spec: dict[str, Any]) -> Effect:
    effect_type = spec.get("type")
    effect_class = EFFECT_TYPES.get(effect_type)
    if effect_class is None:
        raise ValueError(f"Unknown effect type: {effect_type!r}.")
    kwargs = {key: value for key, value in spec.items() if key != "type"}
    if effect_type not in UNIT_EFFECT_TYPES:
        kwargs.pop("target_ids", None)
        kwargs.pop("target_ref", None)
    return effect_class(**kwargs)


def trigger_from_spec(spec: TriggerSpec, owner_id: str | None = None) -> Trigger:
    trigger_owner_id = owner_id or spec.owner_id
    if trigger_owner_id is None:
        raise ValueError(f"Trigger {spec.id!r} is missing owner_id.")
    return Trigger(
        id=spec.id,
        owner_id=trigger_owner_id,
        event_type=spec.event_type,
        condition=dict(spec.condition),
        effects=[effect_from_spec(effect_spec) for effect_spec in spec.effects],
        max_triggers_per_action=spec.max_triggers_per_action,
        enabled=spec.enabled,
    )
