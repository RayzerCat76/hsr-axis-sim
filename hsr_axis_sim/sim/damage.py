from __future__ import annotations

from dataclasses import dataclass, field

from .rng import RngContext
from .stats import EffectiveStats, effective_stats
from .unit import Unit


@dataclass
class DamageSpec:
    multiplier: float
    stat: str = "atk"
    flat_damage: float = 0
    can_crit: bool = True
    damage_type: str | None = None
    element: str | None = None
    damage_bonus_key: str | None = None
    defense_ignore: float = 0
    resistance_penetration: float = 0
    vulnerability: float = 0


@dataclass
class DamageResult:
    amount: float
    did_crit: bool
    damage_type: str | None = None
    element: str | None = None
    formula_parts: dict[str, float | bool | str | None] = field(default_factory=dict)


def calculate_damage(
    attacker: Unit,
    target: Unit,
    spec: DamageSpec,
    rng_context: RngContext,
) -> DamageResult:
    attacker_stats = effective_stats(attacker)
    target_stats = effective_stats(target)

    scaling_stat_value = attacker_stats.get(spec.stat)
    base_damage = scaling_stat_value * spec.multiplier + spec.flat_damage
    damage_bonus = attacker_stats.damage_bonus_for(
        damage_type=spec.damage_type,
        element=spec.element,
        damage_bonus_key=spec.damage_bonus_key,
    )
    after_bonus = base_damage * (1 + damage_bonus)
    did_crit = spec.can_crit and rng_context.crit()
    crit_multiplier = 1 + attacker_stats.crit_dmg if did_crit else 1
    after_crit = after_bonus * crit_multiplier

    defense_ignore = spec.defense_ignore + attacker_stats.stat_mods.get("def_ignore", 0)
    defense_multiplier = calculate_defense_multiplier(
        attacker=attacker,
        target=target,
        target_stats=target_stats,
        defense_ignore=defense_ignore,
    )
    after_defense = after_crit * defense_multiplier

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

    vulnerability = (
        spec.vulnerability
        + target_stats.stat_mods.get("vulnerability", 0)
    )
    final_damage = after_resistance * (1 + vulnerability)

    return DamageResult(
        amount=final_damage,
        did_crit=did_crit,
        damage_type=spec.damage_type,
        element=spec.element,
        formula_parts={
            "scaling_stat": spec.stat,
            "scaling_stat_value": scaling_stat_value,
            "multiplier": spec.multiplier,
            "flat_damage": spec.flat_damage,
            "base_damage": base_damage,
            "damage_bonus": damage_bonus,
            "after_bonus": after_bonus,
            "crit_multiplier": crit_multiplier,
            "after_crit": after_crit,
            "defense_ignore": defense_ignore,
            "defense_multiplier": defense_multiplier,
            "after_defense": after_defense,
            "target_resistance": target_resistance,
            "resistance_penetration": resistance_penetration,
            "resistance_multiplier": resistance_multiplier,
            "after_resistance": after_resistance,
            "vulnerability": vulnerability,
            "final_damage": final_damage,
        },
    )


def calculate_defense_multiplier(
    attacker: Unit,
    target: Unit,
    target_stats: EffectiveStats,
    defense_ignore: float = 0,
) -> float:
    attacker_level = getattr(attacker, "level", 80) or 80
    attacker_level_factor = attacker_level * 10 + 200
    def_reduction = target_stats.stat_mods.get("def_reduction", 0)
    effective_target_defense = max(
        0,
        target_stats.defense * (1 - def_reduction) * (1 - defense_ignore),
    )
    return attacker_level_factor / (attacker_level_factor + effective_target_defense)


def calculate_resistance_multiplier(
    target_resistance: float,
    resistance_penetration: float = 0,
) -> float:
    # MVP policy: do not clamp resistance; negative resistance intentionally
    # increases damage and high resistance can reduce or invert damage.
    effective_resistance = target_resistance - resistance_penetration
    return 1 - effective_resistance
