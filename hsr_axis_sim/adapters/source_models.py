from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ImportWarning:
    code: str
    message: str
    path: str | None = None


@dataclass
class ImportReport:
    source: str
    source_character_id: str
    normalized_id: str
    skills_imported: int = 0
    warnings: list[ImportWarning] = field(default_factory=list)

    def add_warning(self, code: str, message: str, path: str | None = None) -> None:
        self.warnings.append(ImportWarning(code=code, message=message, path=path))


@dataclass
class RawExternalBaseStats:
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
    max_toughness: float = 0
    weaknesses: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RawExternalBaseStats":
        _require_fields(
            data,
            [
                "hp",
                "atk",
                "defense",
                "base_speed",
                "max_energy",
                "crit_rate",
                "crit_dmg",
                "dmg_bonus",
            ],
            "base_stats",
        )
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
            max_toughness=data.get("max_toughness", 0),
            weaknesses=list(data.get("weaknesses", [])),
        )

    def to_normalized_dict(self) -> dict[str, Any]:
        return {
            "hp": self.hp,
            "atk": self.atk,
            "defense": self.defense,
            "base_speed": self.base_speed,
            "max_energy": self.max_energy,
            "crit_rate": self.crit_rate,
            "crit_dmg": self.crit_dmg,
            "dmg_bonus": self.dmg_bonus,
            "level": self.level,
            "break_effect": self.break_effect,
            "max_toughness": self.max_toughness,
            "weaknesses": list(self.weaknesses),
        }


@dataclass
class RawExternalSkill:
    id: str
    name: str
    skill_type: str
    target_type: str
    ends_turn: bool
    effects: list[dict[str, Any]]
    sp_delta: int | None = None
    energy_delta: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RawExternalSkill":
        _require_fields(
            data,
            ["id", "name", "skill_type", "target_type", "ends_turn", "effects"],
            "skill",
        )
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
class RawExternalTrigger:
    id: str
    event_type: str
    condition: dict[str, Any]
    effects: list[dict[str, Any]]
    owner_id: str | None = None
    max_triggers_per_action: int = 1
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RawExternalTrigger":
        _require_fields(data, ["id", "event_type", "condition", "effects"], "trigger")
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
class RawExternalCharacter:
    source: str
    source_version: str
    source_character_id: str
    normalized_id: str
    name: str
    team: str
    element: str | None
    path: str | None
    base_stats: RawExternalBaseStats
    skills: list[RawExternalSkill]
    triggers: list[RawExternalTrigger] = field(default_factory=list)
    unparsed_notes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RawExternalCharacter":
        _require_fields(
            data,
            [
                "source",
                "source_version",
                "source_character_id",
                "normalized_id",
                "name",
                "team",
                "base_stats",
                "skills",
            ],
            "raw_external_character",
        )
        return cls(
            source=data["source"],
            source_version=data["source_version"],
            source_character_id=data["source_character_id"],
            normalized_id=data["normalized_id"],
            name=data["name"],
            team=data["team"],
            element=data.get("element"),
            path=data.get("path"),
            base_stats=RawExternalBaseStats.from_dict(data["base_stats"]),
            skills=[RawExternalSkill.from_dict(skill) for skill in data["skills"]],
            triggers=[
                RawExternalTrigger.from_dict(trigger)
                for trigger in data.get("triggers", [])
            ],
            unparsed_notes=list(data.get("unparsed_notes", [])),
        )


def _require_fields(data: dict[str, Any], fields: list[str], label: str) -> None:
    missing = [field_name for field_name in fields if field_name not in data]
    if missing:
        raise ValueError(f"{label} missing required field(s): {missing}.")
