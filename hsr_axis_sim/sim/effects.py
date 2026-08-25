from __future__ import annotations

from dataclasses import dataclass

from .break_logic import apply_toughness_damage
from .break_damage import BreakDamageResult, BreakDamageSpec, calculate_break_damage
from .buffs import Buff
from .damage import DamageResult, DamageSpec, calculate_damage
from .events import Event
from .rng import RngContext
from .state import BattleState
from .stats import effective_stats
from .targets import resolve_target_ids
from .turn_context import TurnContext
from .unit import Unit


class Effect:
    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        raise NotImplementedError


@dataclass
class UnitEffect(Effect):
    target_ids: list[str] | None = None
    target_ref: str | None = None

    def target_units(self, state: BattleState, action: object) -> list[Unit]:
        target_ids = resolve_target_ids(
            state=state,
            action=action,
            turn_context=None,
            target_ref=self.target_ref,
            target_ids=self.target_ids,
        )
        return [state.get_unit(unit_id) for unit_id in target_ids]


@dataclass
class GainEnergy(UnitEffect):
    amount: float = 0

    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        for unit in self.target_units(state, action):
            before = unit.energy
            unit.energy = min(unit.max_energy, unit.energy + self.amount)
            after = unit.energy
            state.emit_event(
                Event(
                    "energy_changed",
                    {
                        "actor_id": getattr(action, "actor_id"),
                        "action_id": getattr(action, "id"),
                        "resource_kind": "ENERGY",
                        "scope": "UNIT",
                        "before": before,
                        "after": after,
                        "requested_delta": self.amount,
                        "applied_delta": after - before,
                        "cap": unit.max_energy,
                        "unit_id": unit.id,
                    },
                ),
                turn_context,
            )


@dataclass
class ConsumeEnergy(UnitEffect):
    amount: float = 0

    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        for unit in self.target_units(state, action):
            if unit.energy < self.amount:
                raise ValueError(
                    f"Unit {unit.id!r} has insufficient energy: "
                    f"{unit.energy} available, {self.amount} required."
                )
            before = unit.energy
            unit.energy -= self.amount
            after = unit.energy
            state.emit_event(
                Event(
                    "energy_changed",
                    {
                        "actor_id": getattr(action, "actor_id"),
                        "action_id": getattr(action, "id"),
                        "resource_kind": "ENERGY",
                        "scope": "UNIT",
                        "before": before,
                        "after": after,
                        "requested_delta": -self.amount,
                        "applied_delta": after - before,
                        "cap": unit.max_energy,
                        "unit_id": unit.id,
                    },
                ),
                turn_context,
            )


@dataclass
class GainSkillPoint(Effect):
    amount: int = 1

    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        before = state.skill_points
        state.skill_points = min(state.max_skill_points, state.skill_points + self.amount)
        after = state.skill_points
        state.emit_event(
            Event(
                "skill_points_changed",
                {
                    "actor_id": getattr(action, "actor_id"),
                    "action_id": getattr(action, "id"),
                    "resource_kind": "SKILL_POINTS",
                    "scope": "TEAM",
                    "before": before,
                    "after": after,
                    "requested_delta": self.amount,
                    "applied_delta": after - before,
                    "cap": state.max_skill_points,
                    "unit_id": None,
                },
            ),
            turn_context,
        )


@dataclass
class ConsumeSkillPoint(Effect):
    amount: int = 1

    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        if state.skill_points < self.amount:
            raise ValueError(
                "Insufficient skill points: "
                f"{state.skill_points} available, {self.amount} required."
            )
        before = state.skill_points
        state.skill_points -= self.amount
        after = state.skill_points
        state.emit_event(
            Event(
                "skill_points_changed",
                {
                    "actor_id": getattr(action, "actor_id"),
                    "action_id": getattr(action, "id"),
                    "resource_kind": "SKILL_POINTS",
                    "scope": "TEAM",
                    "before": before,
                    "after": after,
                    "requested_delta": -self.amount,
                    "applied_delta": after - before,
                    "cap": state.max_skill_points,
                    "unit_id": None,
                },
            ),
            turn_context,
        )


@dataclass
class AdvanceAction(UnitEffect):
    percent: float = 0

    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        for unit in self.target_units(state, action):
            before_av = unit.current_av
            base_av = unit.base_av
            requested_delta_av = -(base_av * self.percent)
            unit.current_av = max(0, before_av + requested_delta_av)
            after_av = unit.current_av
            state.emit_event(
                Event(
                    "action_advanced",
                    {
                        "actor_id": getattr(action, "actor_id"),
                        "action_id": getattr(action, "id"),
                        "target_id": unit.id,
                        "before_av": before_av,
                        "after_av": after_av,
                        "base_av": base_av,
                        "requested_percent": self.percent,
                        "requested_delta_av": requested_delta_av,
                        "applied_delta_av": after_av - before_av,
                        "clamped_to_zero": before_av + requested_delta_av < 0,
                    },
                ),
                turn_context,
            )


@dataclass
class DelayAction(UnitEffect):
    percent: float = 0

    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        for unit in self.target_units(state, action):
            unit.current_av += unit.base_av * self.percent


@dataclass
class ChangeSpeed(UnitEffect):
    new_speed: float = 0

    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        if self.new_speed <= 0:
            raise ValueError("New speed must be greater than zero.")

        for unit in self.target_units(state, action):
            old_speed = unit.speed
            unit.current_av = unit.current_av * old_speed / self.new_speed
            unit.speed = self.new_speed


@dataclass
class ImmediateAction(UnitEffect):
    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        for unit in self.target_units(state, action):
            unit.current_av = 0


@dataclass
class GrantExtraTurn(UnitEffect):
    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        for unit in self.target_units(state, action):
            state.extra_turn_stack.append(unit.id)


class DoesNotEndTurn(Effect):
    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        turn_context.should_end_turn = False


@dataclass
class AddBuff(UnitEffect):
    id: str = ""
    name: str = ""
    source_id: str | None = None
    duration_type: str = "target_normal_turns"
    remaining_turns: int | None = 1
    stacks: int = 1
    max_stacks: int = 1
    data: dict | None = None
    refresh_policy: str = "refresh"

    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        for unit in self.target_units(state, action):
            _add_status(
                unit.buffs,
                status_id=self.id,
                name=self.name,
                target_id=unit.id,
                source_id=self.source_id or getattr(action, "actor_id"),
                kind="buff",
                duration_type=self.duration_type,
                remaining_turns=self.remaining_turns,
                stacks=self.stacks,
                max_stacks=self.max_stacks,
                data=dict(self.data or {}),
                refresh_policy=self.refresh_policy,
            )


@dataclass
class AddDebuff(UnitEffect):
    id: str = ""
    name: str = ""
    source_id: str | None = None
    duration_type: str = "target_normal_turns"
    remaining_turns: int | None = 1
    stacks: int = 1
    max_stacks: int = 1
    data: dict | None = None
    refresh_policy: str = "refresh"

    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        for unit in self.target_units(state, action):
            _add_status(
                unit.debuffs,
                status_id=self.id,
                name=self.name,
                target_id=unit.id,
                source_id=self.source_id or getattr(action, "actor_id"),
                kind="debuff",
                duration_type=self.duration_type,
                remaining_turns=self.remaining_turns,
                stacks=self.stacks,
                max_stacks=self.max_stacks,
                data=dict(self.data or {}),
                refresh_policy=self.refresh_policy,
            )


@dataclass
class RemoveBuff(UnitEffect):
    id: str = ""

    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        for unit in self.target_units(state, action):
            unit.buffs.pop(self.id, None)


@dataclass
class RemoveDebuff(UnitEffect):
    id: str = ""

    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        for unit in self.target_units(state, action):
            unit.debuffs.pop(self.id, None)


@dataclass
class DealDamage(UnitEffect):
    amount: float | None = None
    multiplier: float | None = None
    stat: str = "atk"
    flat_damage: float = 0
    can_crit: bool = True
    damage_type: str | None = None
    element: str | None = None
    damage_bonus_key: str | None = None
    defense_ignore: float = 0
    resistance_penetration: float = 0
    vulnerability: float = 0

    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        attacker = state.get_unit(getattr(action, "actor_id"))
        for unit in self.target_units(state, action):
            was_alive = unit.is_alive
            damage_result = self._damage_result(attacker, unit, turn_context)
            unit.hp = max(0, unit.hp - damage_result.amount)
            if unit.hp <= 0:
                unit.is_alive = False
            state.emit_event(
                Event(
                    "damage_dealt",
                    {
                        "source_id": attacker.id,
                        "target_id": unit.id,
                        "amount": damage_result.amount,
                        "damage_type": damage_result.damage_type,
                        "element": damage_result.element,
                        "is_crit": damage_result.did_crit,
                        "formula_parts": damage_result.formula_parts,
                    },
                ),
                turn_context,
            )
            if was_alive and not unit.is_alive:
                state.emit_event(
                    Event(
                        "unit_defeated",
                        {
                            "killer_id": attacker.id,
                            "target_id": unit.id,
                        },
                    ),
                    turn_context,
                )

    def _damage_result(
        self,
        attacker: Unit,
        target: Unit,
        turn_context: TurnContext,
    ) -> DamageResult:
        if self.amount is not None:
            return DamageResult(
                amount=self.amount,
                did_crit=False,
                damage_type=self.damage_type,
                element=self.element,
            )
        if self.multiplier is None:
            return DamageResult(
                amount=0,
                did_crit=False,
                damage_type=self.damage_type,
                element=self.element,
            )

        return calculate_damage(
            attacker=attacker,
            target=target,
            spec=DamageSpec(
                multiplier=self.multiplier,
                stat=self.stat,
                flat_damage=self.flat_damage,
                can_crit=self.can_crit,
                damage_type=self.damage_type,
                element=self.element,
                damage_bonus_key=self.damage_bonus_key,
                defense_ignore=self.defense_ignore,
                resistance_penetration=self.resistance_penetration,
                vulnerability=self.vulnerability,
            ),
            rng_context=RngContext.from_dict(turn_context.forced_rng),
        )


@dataclass
class DealToughnessDamage(UnitEffect):
    amount: float = 0
    element: str | None = None
    ignore_weakness: bool = False
    break_delay_percent: float = 0.25
    deal_break_damage: bool = False
    break_damage_element: str | None = None
    break_damage_base_override: float | None = None
    break_damage_defense_ignore: float = 0
    break_damage_resistance_penetration: float = 0
    break_damage_vulnerability: float = 0
    apply_elemental_break_effect: bool = False

    def apply(self, state: BattleState, action: object, turn_context: TurnContext) -> None:
        source_id = getattr(action, "actor_id")
        attacker = state.get_unit(source_id)
        attacker_stats = effective_stats(attacker)
        toughness_multiplier = (
            1
            + attacker_stats.stat_mods.get("toughness_damage_bonus", 0)
            + attacker_stats.stat_mods.get("break_efficiency", 0)
        )
        for unit in self.target_units(state, action):
            was_alive = unit.is_alive
            did_break = apply_toughness_damage(
                unit=unit,
                amount=self.amount * toughness_multiplier,
                element=self.element,
                ignore_weakness=self.ignore_weakness,
                break_delay_percent=self.break_delay_percent,
            )
            if did_break:
                break_damage_result: BreakDamageResult | None = None
                elemental_break_effect_id: str | None = None
                if self.deal_break_damage:
                    break_damage_element = self.break_damage_element or self.element
                    if break_damage_element is None:
                        raise ValueError(
                            "Break damage requires break_damage_element or element."
                        )
                    break_damage_result = calculate_break_damage(
                        attacker=attacker,
                        target=unit,
                        spec=BreakDamageSpec(
                            element=break_damage_element,
                            base_override=self.break_damage_base_override,
                            defense_ignore=self.break_damage_defense_ignore,
                            resistance_penetration=self.break_damage_resistance_penetration,
                            vulnerability=self.break_damage_vulnerability,
                        ),
                    )
                    unit.hp = max(0, unit.hp - break_damage_result.amount)
                    if unit.hp <= 0:
                        unit.is_alive = False
                    state.emit_event(
                        Event(
                            "damage_dealt",
                            {
                                "source_id": source_id,
                                "target_id": unit.id,
                                "amount": break_damage_result.amount,
                                "damage_type": "break",
                                "element": break_damage_result.element,
                                "is_crit": False,
                                "is_break_damage": True,
                                "formula_parts": break_damage_result.formula_parts,
                            },
                        ),
                        turn_context,
                    )
                    if was_alive and not unit.is_alive:
                        state.emit_event(
                            Event(
                                "unit_defeated",
                                {
                                    "killer_id": source_id,
                                    "target_id": unit.id,
                                },
                            ),
                            turn_context,
                        )

                if self.apply_elemental_break_effect:
                    elemental_break_effect_id = _apply_elemental_break_effect(
                        unit=unit,
                        source_id=source_id,
                        element=self.break_damage_element or self.element,
                    )

                state.logs.append(f"break:{unit.id}")
                state.emit_event(
                    Event(
                        "weakness_break",
                        {
                            "source_id": source_id,
                            "target_id": unit.id,
                            "element": self.element,
                            "break_damage_amount": (
                                break_damage_result.amount
                                if break_damage_result is not None
                                else 0
                            ),
                            "elemental_break_effect_id": elemental_break_effect_id,
                            "formula_parts": (
                                break_damage_result.formula_parts
                                if break_damage_result is not None
                                else {}
                            ),
                        },
                    ),
                    turn_context,
                )


def _add_status(
    statuses: dict[str, Buff],
    status_id: str,
    name: str,
    target_id: str,
    source_id: str | None,
    kind: str,
    duration_type: str,
    remaining_turns: int | None,
    stacks: int,
    max_stacks: int,
    data: dict,
    refresh_policy: str,
) -> None:
    if duration_type not in {"target_normal_turns", "current_turn"}:
        raise ValueError(f"Unsupported duration_type: {duration_type!r}.")
    if kind not in {"buff", "debuff"}:
        raise ValueError(f"Unsupported status kind: {kind!r}.")
    if max_stacks < 1:
        raise ValueError("max_stacks must be at least 1.")
    if stacks < 1:
        raise ValueError("stacks must be at least 1.")
    if refresh_policy not in {"refresh", "keep"}:
        raise ValueError(f"Unsupported refresh_policy: {refresh_policy!r}.")

    existing = statuses.get(status_id)
    if existing is None:
        statuses[status_id] = Buff(
            id=status_id,
            name=name,
            target_id=target_id,
            source_id=source_id,
            kind=kind,
            duration_type=duration_type,
            remaining_turns=remaining_turns,
            stacks=min(stacks, max_stacks),
            max_stacks=max_stacks,
            data=data,
        )
        return

    existing.name = name or existing.name
    existing.source_id = source_id
    existing.duration_type = duration_type
    existing.max_stacks = max_stacks
    existing.stacks = min(existing.stacks + stacks, existing.max_stacks)
    if refresh_policy == "refresh":
        existing.remaining_turns = remaining_turns
    existing.data = data


ELEMENTAL_BREAK_EFFECT_IDS = {
    "physical": "physical_break_bleed",
    "fire": "fire_break_burn",
    "ice": "ice_break_frozen",
    "lightning": "lightning_break_shock",
    "wind": "wind_break_wind_shear",
    "quantum": "quantum_break_entanglement",
    "imaginary": "imaginary_break_imprisonment",
}


def _apply_elemental_break_effect(
    unit: Unit,
    source_id: str,
    element: str | None,
) -> str:
    if element is None:
        raise ValueError("Elemental break effect requires an element.")
    effect_id = ELEMENTAL_BREAK_EFFECT_IDS.get(element)
    if effect_id is None:
        raise ValueError(f"Unsupported elemental break effect element: {element!r}.")

    _add_status(
        unit.debuffs,
        status_id=effect_id,
        name=effect_id.replace("_", " ").title(),
        target_id=unit.id,
        source_id=source_id,
        kind="debuff",
        duration_type="target_normal_turns",
        remaining_turns=1,
        stacks=1,
        max_stacks=1,
        data={
            "source": "elemental_break_effect_mvp",
            "element": element,
            "mvp_no_dot_tick": True,
        },
        refresh_policy="refresh",
    )
    return effect_id