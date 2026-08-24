from __future__ import annotations

from dataclasses import dataclass, field

from .buffs import Buff


@dataclass
class Unit:
    id: str
    name: str
    team: str
    base_speed: float
    speed: float | None = None
    current_av: float | None = None
    energy: float = 0
    max_energy: float = 100
    hp: float = 1
    max_hp: float = 1
    is_alive: bool = True
    level: int = 80
    atk: float = 100
    defense: float = 0
    crit_rate: float = 0
    crit_dmg: float = 0.5
    dmg_bonus: float = 0
    break_effect: float = 0
    all_res: float = 0
    quantum_res: float = 0
    wind_res: float = 0
    fire_res: float = 0
    ice_res: float = 0
    lightning_res: float = 0
    physical_res: float = 0
    imaginary_res: float = 0
    element: str | None = None
    weaknesses: list[str] = field(default_factory=list)
    max_toughness: float = 0
    current_toughness: float | None = None
    is_broken: bool = False
    buffs: dict[str, Buff] = field(default_factory=dict)
    debuffs: dict[str, Buff] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.speed is None:
            self.speed = self.base_speed
        if self.speed <= 0:
            raise ValueError("Unit speed must be greater than zero.")
        if self.current_av is None:
            self.current_av = self.base_av
        if self.current_toughness is None:
            self.current_toughness = self.max_toughness
        self.current_toughness = max(0, self.current_toughness)

    @property
    def base_av(self) -> float:
        return 10000 / self.speed

    def get_buff(self, buff_id: str) -> Buff | None:
        return self.buffs.get(buff_id)

    def get_debuff(self, debuff_id: str) -> Buff | None:
        return self.debuffs.get(debuff_id)

    def tick_target_normal_turn_statuses(self) -> None:
        self._tick_target_normal_turn_collection(self.buffs)
        self._tick_target_normal_turn_collection(self.debuffs)

    def expire_current_turn_statuses(self) -> None:
        self._expire_current_turn_collection(self.buffs)
        self._expire_current_turn_collection(self.debuffs)

    def _tick_target_normal_turn_collection(self, statuses: dict[str, Buff]) -> None:
        expired_ids: list[str] = []
        for status_id, status in statuses.items():
            if status.duration_type != "target_normal_turns":
                continue
            if status.remaining_turns is None:
                continue
            status.remaining_turns -= 1
            if status.remaining_turns <= 0:
                expired_ids.append(status_id)

        for status_id in expired_ids:
            del statuses[status_id]

    def _expire_current_turn_collection(self, statuses: dict[str, Buff]) -> None:
        expired_ids = [
            status_id
            for status_id, status in statuses.items()
            if status.duration_type == "current_turn"
        ]
        for status_id in expired_ids:
            del statuses[status_id]
