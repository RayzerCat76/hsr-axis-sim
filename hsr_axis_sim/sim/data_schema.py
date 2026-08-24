from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


KNOWN_EFFECT_TYPES = {
    "AddBuff",
    "AddDebuff",
    "AdvanceAction",
    "ChangeSpeed",
    "ConsumeEnergy",
    "ConsumeSkillPoint",
    "DealDamage",
    "DealToughnessDamage",
    "DelayAction",
    "DoesNotEndTurn",
    "GainEnergy",
    "GainSkillPoint",
    "GrantExtraTurn",
    "ImmediateAction",
    "RemoveBuff",
    "RemoveDebuff",
}

KNOWN_ENEMY_TARGET_STRATEGIES = {
    "explicit",
    "first_legal",
    "forced_rng_target",
    "highest_hp_legal",
    "last_legal",
    "lowest_hp_legal",
}


@dataclass
class BaseStatsSpec:
    hp: float
    atk: float
    defense: float
    base_speed: float
    max_energy: float
    crit_rate: float
    crit_dmg: float
    dmg_bonus: float
    level: int = 80
    break_effect: float = 0
    all_res: float = 0
    quantum_res: float = 0
    wind_res: float = 0
    fire_res: float = 0
    ice_res: float = 0
    lightning_res: float = 0
    physical_res: float = 0
    imaginary_res: float = 0
    max_toughness: float = 0
    weaknesses: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseStatsSpec":
        required = [
            "hp",
            "atk",
            "defense",
            "base_speed",
            "max_energy",
            "crit_rate",
            "crit_dmg",
            "dmg_bonus",
        ]
        _require_fields(data, required, "base_stats")
        return cls(
            hp=data["hp"],
            atk=data["atk"],
            defense=data["defense"],
            base_speed=data["base_speed"],
            max_energy=data["max_energy"],
            crit_rate=data["crit_rate"],
            crit_dmg=data["crit_dmg"],
            dmg_bonus=data["dmg_bonus"],
            level=data.get("level", 80),
            break_effect=data.get("break_effect", 0),
            all_res=data.get("all_res", 0),
            quantum_res=data.get("quantum_res", 0),
            wind_res=data.get("wind_res", 0),
            fire_res=data.get("fire_res", 0),
            ice_res=data.get("ice_res", 0),
            lightning_res=data.get("lightning_res", 0),
            physical_res=data.get("physical_res", 0),
            imaginary_res=data.get("imaginary_res", 0),
            max_toughness=data.get("max_toughness", 0),
            weaknesses=list(data.get("weaknesses", [])),
        )


@dataclass
class SkillSpec:
    id: str
    name: str
    skill_type: str
    target_type: str
    sp_delta: int | None
    energy_delta: float | None
    ends_turn: bool
    effects: list[dict[str, Any]]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillSpec":
        _require_fields(
            data,
            ["id", "name", "skill_type", "target_type", "ends_turn", "effects"],
            "skill",
        )
        for effect in data["effects"]:
            validate_effect_spec(effect)
        return cls(
            id=data["id"],
            name=data["name"],
            skill_type=data["skill_type"],
            target_type=data["target_type"],
            sp_delta=data.get("sp_delta"),
            energy_delta=data.get("energy_delta"),
            ends_turn=data["ends_turn"],
            effects=list(data["effects"]),
        )


@dataclass
class TriggerSpec:
    id: str
    owner_id: str | None
    event_type: str
    condition: dict[str, Any]
    effects: list[dict[str, Any]]
    max_triggers_per_action: int = 1
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TriggerSpec":
        _require_fields(data, ["id", "event_type", "condition", "effects"], "trigger")
        for effect in data["effects"]:
            validate_effect_spec(effect)
        return cls(
            id=data["id"],
            owner_id=data.get("owner_id"),
            event_type=data["event_type"],
            condition=dict(data["condition"]),
            effects=list(data["effects"]),
            max_triggers_per_action=data.get("max_triggers_per_action", 1),
            enabled=data.get("enabled", True),
        )


@dataclass
class CharacterSpec:
    id: str
    name: str
    team: str
    element: str | None
    path: str | None
    base_stats: BaseStatsSpec
    skills: list[SkillSpec]
    triggers: list[TriggerSpec] = field(default_factory=list)
    enemy_ai: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CharacterSpec":
        _require_fields(data, ["id", "name", "team", "base_stats", "skills"], "character")
        skills = [SkillSpec.from_dict(skill) for skill in data["skills"]]
        skill_ids = [skill.id for skill in skills]
        duplicate_skill_ids = sorted({skill_id for skill_id in skill_ids if skill_ids.count(skill_id) > 1})
        if duplicate_skill_ids:
            raise ValueError(f"Duplicate skill id(s): {duplicate_skill_ids}.")
        enemy_ai = data.get("enemy_ai")
        if enemy_ai is not None:
            validate_enemy_ai_spec(enemy_ai, set(skill_ids))

        return cls(
            id=data["id"],
            name=data["name"],
            team=data["team"],
            element=data.get("element"),
            path=data.get("path"),
            base_stats=BaseStatsSpec.from_dict(data["base_stats"]),
            skills=skills,
            triggers=[TriggerSpec.from_dict(trigger) for trigger in data.get("triggers", [])],
            enemy_ai=dict(enemy_ai) if enemy_ai is not None else None,
        )

    def get_skill(self, skill_id: str) -> SkillSpec:
        for skill in self.skills:
            if skill.id == skill_id:
                return skill
        raise KeyError(f"Unknown skill id {skill_id!r} for character {self.id!r}.")


@dataclass
class UnitInstanceSpec:
    character_id: str
    unit_id: str
    team: str
    level: int | None = None
    stat_overrides: dict[str, Any] = field(default_factory=dict)
    initial_energy: float | None = None
    initial_current_av: float | None = None
    initial_hp: float | None = None
    initial_toughness: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UnitInstanceSpec":
        _require_fields(data, ["character_id", "unit_id", "team"], "unit_ref")
        return cls(
            character_id=data["character_id"],
            unit_id=data["unit_id"],
            team=data["team"],
            level=data.get("level"),
            stat_overrides=dict(data.get("stat_overrides", {})),
            initial_energy=data.get("initial_energy"),
            initial_current_av=data.get("initial_current_av"),
            initial_hp=data.get("initial_hp"),
            initial_toughness=data.get("initial_toughness"),
        )


@dataclass
class TeamSpec:
    id: str
    name: str
    unit_refs: list[UnitInstanceSpec]
    initial_skill_points: int
    max_skill_points: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TeamSpec":
        _require_fields(
            data,
            ["id", "name", "unit_refs", "initial_skill_points", "max_skill_points"],
            "team",
        )
        return cls(
            id=data["id"],
            name=data["name"],
            unit_refs=[UnitInstanceSpec.from_dict(unit_ref) for unit_ref in data["unit_refs"]],
            initial_skill_points=data["initial_skill_points"],
            max_skill_points=data["max_skill_points"],
        )


def validate_effect_spec(effect: dict[str, Any]) -> None:
    effect_type = effect.get("type")
    if effect_type not in KNOWN_EFFECT_TYPES:
        raise ValueError(f"Unknown effect type: {effect_type!r}.")


def validate_enemy_ai_spec(enemy_ai: dict[str, Any], skill_ids: set[str]) -> None:
    if not isinstance(enemy_ai, dict):
        raise ValueError("enemy_ai must be an object.")
    pattern = enemy_ai.get("pattern")
    if not isinstance(pattern, list) or not pattern:
        raise ValueError("enemy_ai pattern must be a non-empty list.")

    for index, step in enumerate(pattern):
        if not isinstance(step, dict):
            raise ValueError(f"enemy_ai pattern step {index} must be an object.")
        _require_fields(step, ["skill_id"], f"enemy_ai pattern step {index}")
        if step["skill_id"] not in skill_ids:
            raise ValueError(
                f"enemy_ai pattern step {index} references unknown skill id "
                f"{step['skill_id']!r}."
            )
        target_strategy = step.get("target_strategy", "first_legal")
        if target_strategy not in KNOWN_ENEMY_TARGET_STRATEGIES:
            raise ValueError(
                f"enemy_ai pattern step {index} has unknown target_strategy "
                f"{target_strategy!r}."
            )
        if "target_ids" in step and not isinstance(step["target_ids"], list):
            raise ValueError(f"enemy_ai pattern step {index} target_ids must be a list.")


def _require_fields(data: dict[str, Any], fields: list[str], label: str) -> None:
    missing_fields = [field_name for field_name in fields if field_name not in data]
    if missing_fields:
        raise ValueError(f"{label} missing required field(s): {missing_fields}.")
