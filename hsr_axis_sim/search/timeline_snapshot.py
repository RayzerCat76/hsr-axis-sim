from __future__ import annotations

from dataclasses import dataclass, field

from hsr_axis_sim.sim.state import BattleState


@dataclass
class UnitSnapshot:
    unit_id: str
    team: str
    hp: float
    max_hp: float
    energy: float
    current_av: float
    speed: float
    current_toughness: float | None
    max_toughness: float | None
    is_broken: bool
    is_alive: bool
    buffs: list[str] = field(default_factory=list)
    debuffs: list[str] = field(default_factory=list)


@dataclass
class BattleSnapshot:
    global_av: float
    skill_points: int
    units: list[UnitSnapshot] = field(default_factory=list)


def snapshot_battle_state(state: BattleState) -> BattleSnapshot:
    return BattleSnapshot(
        global_av=state.global_av,
        skill_points=state.skill_points,
        units=[
            UnitSnapshot(
                unit_id=unit.id,
                team=unit.team,
                hp=unit.hp,
                max_hp=unit.max_hp,
                energy=unit.energy,
                current_av=unit.current_av,
                speed=unit.speed,
                current_toughness=getattr(unit, "current_toughness", None),
                max_toughness=getattr(unit, "max_toughness", None),
                is_broken=getattr(unit, "is_broken", False),
                is_alive=unit.is_alive,
                buffs=sorted(unit.buffs),
                debuffs=sorted(unit.debuffs),
            )
            for unit in state.units
        ],
    )
