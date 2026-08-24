from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .buffs import Buff
    from .unit import Unit


@dataclass
class EffectiveStats:
    atk: float
    defense: float
    crit_rate: float
    crit_dmg: float
    dmg_bonus: float
    break_effect: float
    stat_mods: dict[str, float] = field(default_factory=dict)

    def get(self, stat: str) -> float:
        if stat == "atk":
            return self.atk
        if stat in {"def", "defense"}:
            return self.defense
        raise ValueError(f"Unsupported damage stat: {stat!r}.")

    def damage_bonus_for(
        self,
        damage_type: str | None = None,
        element: str | None = None,
        damage_bonus_key: str | None = None,
    ) -> float:
        total = self.dmg_bonus
        bonus_keys: set[str] = set()
        if element:
            bonus_keys.add(f"{element}_dmg_bonus")
        if damage_type:
            bonus_keys.add(f"{damage_type}_dmg_bonus")
        if damage_bonus_key:
            bonus_keys.add(damage_bonus_key)

        for key in bonus_keys:
            total += self.stat_mods.get(key, 0)
        return total

    def resistance_for(self, element: str | None = None) -> float:
        resistance = self.stat_mods.get("all_res", 0)
        if element:
            resistance += self.stat_mods.get(f"{element}_res", 0)
        return resistance

    def resistance_penetration_for(self, element: str | None = None) -> float:
        penetration = self.stat_mods.get("all_res_pen", 0)
        if element:
            penetration += self.stat_mods.get(f"{element}_res_pen", 0)
        return penetration


def effective_stats(unit: Unit) -> EffectiveStats:
    stat_mods = _sum_status_mods(unit)
    atk_pct = stat_mods.get("atk_pct", 0)
    atk_flat = stat_mods.get("atk_flat", 0)
    defense_pct = stat_mods.get("def_pct", 0)
    defense_flat = stat_mods.get("def_flat", 0)

    return EffectiveStats(
        atk=unit.atk * (1 + atk_pct) + atk_flat,
        defense=unit.defense * (1 + defense_pct) + defense_flat,
        crit_rate=unit.crit_rate + stat_mods.get("crit_rate", 0),
        crit_dmg=unit.crit_dmg + stat_mods.get("crit_dmg", 0),
        dmg_bonus=unit.dmg_bonus + stat_mods.get("dmg_bonus", 0),
        break_effect=unit.break_effect + stat_mods.get("break_effect", 0),
        stat_mods=stat_mods,
    )


def _sum_status_mods(unit: Unit) -> dict[str, float]:
    totals: dict[str, float] = {
        "all_res": getattr(unit, "all_res", 0),
        "quantum_res": getattr(unit, "quantum_res", 0),
        "wind_res": getattr(unit, "wind_res", 0),
        "fire_res": getattr(unit, "fire_res", 0),
        "ice_res": getattr(unit, "ice_res", 0),
        "lightning_res": getattr(unit, "lightning_res", 0),
        "physical_res": getattr(unit, "physical_res", 0),
        "imaginary_res": getattr(unit, "imaginary_res", 0),
    }
    for status in [*unit.buffs.values(), *unit.debuffs.values()]:
        for stat_name, amount in _status_stat_mods(status).items():
            totals[stat_name] = totals.get(stat_name, 0) + amount
    return totals


def _status_stat_mods(status: Buff) -> dict[str, float]:
    stat_mods = status.data.get("stat_mods", {})
    if not isinstance(stat_mods, dict):
        return {}
    return {
        stat_name: amount
        for stat_name, amount in stat_mods.items()
        if isinstance(amount, (int, float))
    }
