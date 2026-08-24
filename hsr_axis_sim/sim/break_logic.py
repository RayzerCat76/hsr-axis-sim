from __future__ import annotations

from .unit import Unit


def has_toughness_bar(unit: Unit) -> bool:
    return unit.max_toughness > 0


def apply_toughness_damage(
    unit: Unit,
    amount: float,
    element: str | None,
    ignore_weakness: bool,
    break_delay_percent: float,
) -> bool:
    if not has_toughness_bar(unit):
        return False
    if unit.is_broken:
        return False
    if not ignore_weakness and element not in unit.weaknesses:
        return False

    previous_toughness = unit.current_toughness
    unit.current_toughness = max(0, unit.current_toughness - amount)
    if previous_toughness > 0 and unit.current_toughness <= 0:
        unit.is_broken = True
        unit.current_toughness = 0
        unit.current_av += unit.base_av * break_delay_percent
        return True
    return False


def recover_break_if_needed(unit: Unit) -> None:
    if not unit.is_broken:
        return
    unit.is_broken = False
    unit.current_toughness = unit.max_toughness

