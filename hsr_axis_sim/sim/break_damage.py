from __future__ import annotations

from dataclasses import dataclass, field

from .damage import calculate_defense_multiplier, calculate_resistance_multiplier
from .stats import effective_stats
from .unit import Unit


ELEMENT_BREAK_MULTIPLIERS = {
    "physical": 2.0,
    "fire": 2.0,
    "ice": 1.0,
    "lightning": 1.0,
    "wind": 1.5,
    "quantum": 0.5,
    "imaginary": 0.5,
}


@dataclass
class BreakDamageSpec:
    element: str
    base_override: float | None = None
    defense_ignore: float = 0
    resistance_penetration: float = 0
    vulnerability: float = 0


@dataclass
class BreakDamageResult:
    amount: float
    element: str
    formula_parts: dict[str, float | str] = field(default_factory=dict)


def calculate_break_damage(
    attacker: Unit,
    target: Unit,
    spec: BreakDamageSpec,
) -> BreakDamageResult:
    attacker_stats = effective_stats(attacker)
    target_stats = effective_stats(target)

    base_break_damage = (
        spec.base_override
        if spec.base_override is not None
        else level_break_base(attacker.level)
    )
    element_multiplier = element_break_multiplier(spec.element)
    after_element = base_break_damage * element_multiplier
    toughness_factor = break_toughness_factor(target)
    after_toughness = after_element * toughness_factor
    break_effect = attacker_stats.break_effect
    after_break_effect = after_toughness * (1 + break_effect)
    break_damage_bonus = attacker_stats.stat_mods.get("break_damage_bonus", 0)
    after_break_bonus = after_break_effect * (1 + break_damage_bonus)

    defense_ignore = spec.defense_ignore + attacker_stats.stat_mods.get("def_ignore", 0)
    defense_multiplier = calculate_defense_multiplier(
        attacker=attacker,
        target=target,
        target_stats=target_stats,
        defense_ignore=defense_ignore,
    )
    after_defense = after_break_bonus * defense_multiplier

    target_resistance = target_stats.resistance_for(spec.element)
    resistance_penetration = (
        spec.resistance_penetration
        + attacker_stats.resistance_penetration_for(spec.element)
    )
    resistance_multiplier = calculate_resistance_multiplier(
        target_resistance=target_resistance,
        resistance_penetration=resistance_penetration,
    )
    after_resistance = after_defense * resistance_multiplier

    vulnerability = spec.vulnerability + target_stats.stat_mods.get("vulnerability", 0)
    final_break_damage = after_resistance * (1 + vulnerability)

    return BreakDamageResult(
        amount=final_break_damage,
        element=spec.element,
        formula_parts={
            "base_break_damage": base_break_damage,
            "element": spec.element,
            "element_break_multiplier": element_multiplier,
            "after_element": after_element,
            "toughness_factor": toughness_factor,
            "after_toughness": after_toughness,
            "break_effect": break_effect,
            "after_break_effect": after_break_effect,
            "break_damage_bonus": break_damage_bonus,
            "after_break_bonus": after_break_bonus,
            "defense_ignore": defense_ignore,
            "defense_multiplier": defense_multiplier,
            "after_defense": after_defense,
            "target_resistance": target_resistance,
            "resistance_penetration": resistance_penetration,
            "resistance_multiplier": resistance_multiplier,
            "after_resistance": after_resistance,
            "vulnerability": vulnerability,
            "final_break_damage": final_break_damage,
        },
    )


def level_break_base(level: int) -> float:
    return level * 10


def element_break_multiplier(element: str) -> float:
    try:
        return ELEMENT_BREAK_MULTIPLIERS[element]
    except KeyError as exc:
        raise ValueError(f"Unsupported break damage element: {element!r}.") from exc


def break_toughness_factor(target: Unit) -> float:
    return max(1, target.max_toughness / 60)
