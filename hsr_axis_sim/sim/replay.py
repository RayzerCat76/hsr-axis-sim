from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .action import Action
from .data_loader import action_from_skill, build_battle_state_from_files
from .enemy_ai import execute_enemy_ai_action
from .events import Trigger
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
from .state import BattleState
from .timeline import Timeline
from .unit import Unit
from .ultimate_windows import execute_interrupt_action


class ReplayValidationError(ValueError):
    pass


@dataclass
class ReplayCheckResult:
    passed: bool
    replay_name: str
    checked_steps: int
    mismatches: list[str] = field(default_factory=list)


class ReplayValidator:
    effect_types: dict[str, type[Effect]] = {
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

    unit_effect_types = {
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

    def load_replay(self, path: str | Path) -> dict[str, Any]:
        with Path(path).open(encoding="utf-8") as replay_file:
            return json.load(replay_file)

    def run_replay(self, replay_data: dict[str, Any]) -> ReplayCheckResult:
        return self.validate(replay_data)

    def validate(self, replay_data: dict[str, Any]) -> ReplayCheckResult:
        replay_name = replay_data.get("name", "<unnamed replay>")
        if replay_data.get("check_mode") == "action_sequence_only":
            return self._validate_action_sequence_only(replay_data)

        tolerance = float(replay_data.get("tolerance", 1e-6))
        mismatches: list[str] = []
        checked_steps = 0

        try:
            state, skill_lookup = self._initial_state_and_skills(replay_data)
        except (ReplayValidationError, ValueError) as exc:
            return ReplayCheckResult(False, replay_name, checked_steps, [str(exc)])

        action_specs = replay_data.get("actions", {})
        for step_data in replay_data.get("steps", []):
            step_label = self._step_label(step_data)
            step_type = step_data.get("step_type", "normal")

            if step_type == "interrupt":
                actor_id = step_data.get("actor_id", step_data.get("expected_actor"))
                if actor_id is None:
                    mismatches.append(
                        f"{step_label}: interrupt step requires actor_id or expected_actor."
                    )
                    break
                turn_context = None
            elif step_type == "normal":
                try:
                    turn_context = Timeline.next_turn(state)
                except (KeyError, ValueError) as exc:
                    mismatches.append(f"{step_label}: failed to select next actor: {exc}")
                    break
                turn_context.forced_rng = dict(step_data.get("forced_rng", {}))
                actor_id = turn_context.actor_id

                expected_actor = step_data.get("expected_actor")
                if expected_actor is not None and actor_id != expected_actor:
                    mismatches.append(
                        f"{step_label}: expected actor {expected_actor!r}, "
                        f"got {actor_id!r}."
                    )
            else:
                mismatches.append(f"{step_label}: unsupported step_type {step_type!r}.")
                break

            if step_data.get("use_enemy_ai") and step_type != "normal":
                mismatches.append(f"{step_label}: use_enemy_ai is only supported on normal steps.")
                break

            if (
                step_data.get("use_enemy_ai")
                and "skill_id" not in step_data
                and "action_id" not in step_data
            ):
                try:
                    execute_enemy_ai_action(
                        state,
                        skill_lookup,
                        actor_id,
                        turn_context,
                        forced_rng=dict(step_data.get("forced_rng", {})),
                    )
                except (KeyError, ValueError) as exc:
                    mismatches.append(f"{step_label}: enemy AI action failed: {exc}")
                    break

                self._compare_expectations(
                    state,
                    step_data.get("expect", {}),
                    tolerance,
                    step_label,
                    mismatches,
                )
                checked_steps += 1
                continue

            try:
                if "skill_id" in step_data:
                    if step_type == "interrupt":
                        skill = self._loaded_skill(
                            skill_lookup,
                            actor_id,
                            step_data["skill_id"],
                        )
                        if (
                            skill.skill_type != "ultimate"
                            and not step_data.get("allow_non_ultimate_interrupt", False)
                        ):
                            raise ReplayValidationError(
                                f"Interrupt skill {skill.id!r} must have skill_type "
                                "'ultimate'."
                            )
                    action = self._action_from_loaded_skill(
                        state,
                        skill_lookup,
                        actor_id,
                        step_data["skill_id"],
                        list(step_data.get("target_ids", [])),
                    )
                    action_id = step_data["skill_id"]
                else:
                    action_id = step_data.get("action_id")
                    if action_id not in action_specs:
                        mismatches.append(f"{step_label}: unknown action {action_id!r}.")
                        break
                    action = self.action_from_spec(action_specs[action_id])
                    if (
                        step_type == "interrupt"
                        and not step_data.get("allow_non_ultimate_interrupt", False)
                        and action_specs[action_id].get("skill_type") != "ultimate"
                    ):
                        raise ReplayValidationError(
                            f"Interrupt action {action_id!r} must declare "
                            "skill_type 'ultimate'."
                        )
            except (ReplayValidationError, ValueError) as exc:
                mismatches.append(f"{step_label}: {exc}")
                break

            if "target_ids" in step_data and "skill_id" not in step_data:
                action.target_ids = list(step_data["target_ids"])

            try:
                if step_type == "interrupt":
                    execute_interrupt_action(
                        state,
                        action,
                        forced_rng=dict(step_data.get("forced_rng", {})),
                    )
                else:
                    action.execute(state, turn_context)
            except (KeyError, ValueError) as exc:
                mismatches.append(f"{step_label}: action {action_id!r} failed: {exc}")
                break

            self._compare_expectations(
                state,
                step_data.get("expect", {}),
                tolerance,
                step_label,
                mismatches,
            )
            checked_steps += 1

        return ReplayCheckResult(
            passed=not mismatches,
            replay_name=replay_name,
            checked_steps=checked_steps,
            mismatches=mismatches,
        )

    def _validate_action_sequence_only(
        self,
        replay_data: dict[str, Any],
    ) -> ReplayCheckResult:
        replay_name = replay_data.get("name", "<unnamed replay>")
        mismatches: list[str] = []
        checked_steps = 0

        if replay_data.get("numeric_expectations") != "skip":
            mismatches.append(
                "action_sequence_only replay validation requires "
                "numeric_expectations='skip'."
            )

        steps = replay_data.get("steps")
        if not isinstance(steps, list) or not steps:
            mismatches.append("action_sequence_only trace requires non-empty steps.")
            return ReplayCheckResult(False, replay_name, checked_steps, mismatches)

        for index, step_data in enumerate(steps):
            if not isinstance(step_data, dict):
                mismatches.append(f"steps[{index}] must be an object.")
                continue
            step_label = self._step_label(step_data)
            if "actor" not in step_data:
                mismatches.append(f"{step_label}: missing actor.")
            if "action" not in step_data:
                mismatches.append(f"{step_label}: missing action.")
            if "actor" in step_data and "action" in step_data:
                checked_steps += 1

        return ReplayCheckResult(
            passed=not mismatches,
            replay_name=replay_name,
            checked_steps=checked_steps,
            mismatches=mismatches,
        )

    def _initial_state_and_skills(
        self,
        replay_data: dict[str, Any],
    ) -> tuple[BattleState, dict[str, dict[str, Any]]]:
        data_sources = replay_data.get("data_sources")
        if not data_sources:
            return self.state_from_replay(replay_data), {}

        try:
            return build_battle_state_from_files(
                team_path=data_sources["team"],
                characters_dir=data_sources["characters_dir"],
            )
        except KeyError as exc:
            raise ReplayValidationError(
                f"data_sources missing required field {exc}."
            ) from exc

    def _action_from_loaded_skill(
        self,
        state: BattleState,
        skill_lookup: dict[str, dict[str, Any]],
        actor_id: str,
        skill_id: str,
        target_ids: list[str],
    ) -> Action:
        actor_skills = skill_lookup.get(actor_id)
        if actor_skills is None:
            raise ReplayValidationError(f"No loaded skills for actor {actor_id!r}.")
        skill = actor_skills.get(skill_id)
        if skill is None:
            raise ReplayValidationError(
                f"Unknown skill id {skill_id!r} for actor {actor_id!r}."
            )
        return action_from_skill(
            skill,
            actor_id=actor_id,
            target_ids=target_ids,
            state=state,
            validate_targets=True,
        )

    def _loaded_skill(
        self,
        skill_lookup: dict[str, dict[str, Any]],
        actor_id: str,
        skill_id: str,
    ) -> Any:
        actor_skills = skill_lookup.get(actor_id)
        if actor_skills is None:
            raise ReplayValidationError(f"No loaded skills for actor {actor_id!r}.")
        skill = actor_skills.get(skill_id)
        if skill is None:
            raise ReplayValidationError(
                f"Unknown skill id {skill_id!r} for actor {actor_id!r}."
            )
        return skill

    def state_from_replay(self, replay_data: dict[str, Any]) -> BattleState:
        initial_state = replay_data.get("initial_state")
        if not isinstance(initial_state, dict):
            raise ReplayValidationError("Replay is missing initial_state.")

        unit_specs = initial_state.get("units", [])
        self._validate_unique_unit_ids(unit_specs)
        units = [self.unit_from_spec(unit_spec) for unit_spec in unit_specs]
        if not units:
            raise ReplayValidationError("Replay initial_state must include at least one unit.")
        triggers = [
            self.trigger_from_spec(trigger_spec)
            for trigger_spec in initial_state.get("triggers", [])
        ]
        for unit_spec in unit_specs:
            for trigger_spec in unit_spec.get("triggers", []):
                owned_trigger_spec = dict(trigger_spec)
                owned_trigger_spec.setdefault("owner_id", unit_spec.get("id"))
                triggers.append(self.trigger_from_spec(owned_trigger_spec))

        return BattleState(
            units=units,
            global_av=initial_state.get("global_av", 0),
            skill_points=initial_state.get("skill_points", 0),
            max_skill_points=initial_state.get("max_skill_points", 5),
            extra_turn_stack=list(initial_state.get("extra_turn_stack", [])),
            logs=list(initial_state.get("logs", [])),
            triggers=triggers,
        )

    def unit_from_spec(self, spec: dict[str, Any]) -> Unit:
        try:
            return Unit(
                id=spec["id"],
                name=spec["name"],
                team=spec["team"],
                base_speed=spec["base_speed"],
                speed=spec.get("speed"),
                current_av=spec.get("current_av"),
                energy=spec.get("energy", 0),
                max_energy=spec.get("max_energy", 100),
                hp=spec.get("hp", 1),
                max_hp=spec.get("max_hp", 1),
                is_alive=spec.get("is_alive", True),
                level=spec.get("level", 80),
                atk=spec.get("atk", 100),
                defense=spec.get("defense", spec.get("def", 0)),
                crit_rate=spec.get("crit_rate", 0),
                crit_dmg=spec.get("crit_dmg", 0.5),
                dmg_bonus=spec.get("dmg_bonus", 0),
                break_effect=spec.get("break_effect", 0),
                all_res=spec.get("all_res", 0),
                quantum_res=spec.get("quantum_res", 0),
                wind_res=spec.get("wind_res", 0),
                fire_res=spec.get("fire_res", 0),
                ice_res=spec.get("ice_res", 0),
                lightning_res=spec.get("lightning_res", 0),
                physical_res=spec.get("physical_res", 0),
                imaginary_res=spec.get("imaginary_res", 0),
                element=spec.get("element"),
                weaknesses=list(spec.get("weaknesses", [])),
                max_toughness=spec.get("max_toughness", 0),
                current_toughness=spec.get("current_toughness"),
                is_broken=spec.get("is_broken", False),
            )
        except KeyError as exc:
            raise ReplayValidationError(f"Unit spec is missing required field {exc}.") from exc

    def action_from_spec(self, spec: dict[str, Any]) -> Action:
        try:
            return Action(
                id=spec["id"],
                name=spec["name"],
                actor_id=spec["actor_id"],
                target_ids=list(spec.get("target_ids", [])),
                effects=[self.effect_from_spec(effect) for effect in spec.get("effects", [])],
                ends_turn=spec.get("ends_turn", True),
            )
        except KeyError as exc:
            raise ReplayValidationError(f"Action spec is missing required field {exc}.") from exc

    def trigger_from_spec(self, spec: dict[str, Any]) -> Trigger:
        try:
            return Trigger(
                id=spec["id"],
                owner_id=spec["owner_id"],
                event_type=spec["event_type"],
                condition=dict(spec.get("condition", {"type": "always"})),
                effects=[self.effect_from_spec(effect) for effect in spec.get("effects", [])],
                max_triggers_per_action=spec.get("max_triggers_per_action", 1),
                enabled=spec.get("enabled", True),
            )
        except KeyError as exc:
            raise ReplayValidationError(f"Trigger spec is missing required field {exc}.") from exc

    def effect_from_spec(self, spec: dict[str, Any]) -> Effect:
        effect_type = spec.get("type")
        effect_class = self.effect_types.get(effect_type)
        if effect_class is None:
            raise ReplayValidationError(f"Unsupported effect type: {effect_type!r}.")

        kwargs = {key: value for key, value in spec.items() if key != "type"}
        if effect_type not in self.unit_effect_types:
            kwargs.pop("target_ids", None)
            kwargs.pop("target_ref", None)

        return effect_class(**kwargs)

    def _compare_expectations(
        self,
        state: BattleState,
        expected: dict[str, Any],
        tolerance: float,
        step_label: str,
        mismatches: list[str],
    ) -> None:
        supported_state_fields = {
            "enemy_ai_cursors": state.enemy_ai_cursors,
            "global_av": state.global_av,
            "skill_points": state.skill_points,
            "extra_turn_stack": state.extra_turn_stack,
        }

        for field_name, expected_value in expected.items():
            if field_name == "units":
                self._compare_unit_expectations(
                    state,
                    expected_value,
                    tolerance,
                    step_label,
                    mismatches,
                )
            elif field_name == "logs_contains":
                self._compare_logs_contains(
                    state.logs,
                    expected_value,
                    step_label,
                    mismatches,
                )
            elif field_name in supported_state_fields:
                self._compare_value(
                    supported_state_fields[field_name],
                    expected_value,
                    f"{step_label}: {field_name}",
                    tolerance,
                    mismatches,
                )
            else:
                mismatches.append(f"{step_label}: unsupported expected field {field_name!r}.")

    def _compare_unit_expectations(
        self,
        state: BattleState,
        expected_units: dict[str, dict[str, Any]],
        tolerance: float,
        step_label: str,
        mismatches: list[str],
    ) -> None:
        supported_unit_fields = {
            "buffs",
            "current_av",
            "current_toughness",
            "debuffs",
            "element",
            "speed",
            "base_av",
            "energy",
            "hp",
            "is_alive",
            "is_broken",
            "max_toughness",
            "weaknesses",
        }

        for unit_id, unit_expectations in expected_units.items():
            try:
                unit = state.get_unit(unit_id)
            except KeyError:
                mismatches.append(f"{step_label}: unknown expected unit {unit_id!r}.")
                continue

            for field_name, expected_value in unit_expectations.items():
                if field_name not in supported_unit_fields:
                    mismatches.append(
                        f"{step_label}: unsupported expected unit field "
                        f"{unit_id!r}.{field_name!r}."
                    )
                    continue

                if field_name == "buffs":
                    self._compare_status_expectations(
                        unit.buffs,
                        expected_value,
                        tolerance,
                        f"{step_label}: unit {unit_id}.buffs",
                        mismatches,
                    )
                    continue

                if field_name == "debuffs":
                    self._compare_status_expectations(
                        unit.debuffs,
                        expected_value,
                        tolerance,
                        f"{step_label}: unit {unit_id}.debuffs",
                        mismatches,
                    )
                    continue

                actual_value = getattr(unit, field_name)
                self._compare_value(
                    actual_value,
                    expected_value,
                    f"{step_label}: unit {unit_id}.{field_name}",
                    tolerance,
                    mismatches,
                )

    def _compare_value(
        self,
        actual_value: Any,
        expected_value: Any,
        label: str,
        tolerance: float,
        mismatches: list[str],
    ) -> None:
        if isinstance(expected_value, bool):
            if actual_value is not expected_value:
                mismatches.append(f"{label}: expected {expected_value!r}, got {actual_value!r}.")
            return

        if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
            if abs(actual_value - expected_value) > tolerance:
                mismatches.append(
                    f"{label}: expected {expected_value}, got {actual_value} "
                    f"(tolerance {tolerance})."
                )
            return

        if actual_value != expected_value:
            mismatches.append(f"{label}: expected {expected_value!r}, got {actual_value!r}.")

    def _compare_logs_contains(
        self,
        logs: list[str],
        expected_entries: list[str],
        step_label: str,
        mismatches: list[str],
    ) -> None:
        for expected_entry in expected_entries:
            if expected_entry not in logs:
                mismatches.append(
                    f"{step_label}: expected logs to contain {expected_entry!r}."
                )

    def _compare_status_expectations(
        self,
        actual_statuses: dict[str, Any],
        expected_statuses: dict[str, dict[str, Any]],
        tolerance: float,
        label: str,
        mismatches: list[str],
    ) -> None:
        if expected_statuses == {}:
            if actual_statuses:
                actual_ids = sorted(actual_statuses)
                mismatches.append(f"{label}: expected empty collection, got {actual_ids!r}.")
            return

        supported_status_fields = {
            "data",
            "duration_type",
            "kind",
            "remaining_turns",
            "source_id",
            "stacks",
        }
        for status_id, status_expectations in expected_statuses.items():
            status = actual_statuses.get(status_id)
            if status is None:
                mismatches.append(f"{label}.{status_id}: expected status to exist.")
                continue

            for field_name, expected_value in status_expectations.items():
                if field_name not in supported_status_fields:
                    mismatches.append(
                        f"{label}.{status_id}: unsupported expected status field "
                        f"{field_name!r}."
                    )
                    continue

                actual_value = getattr(status, field_name)
                self._compare_value(
                    actual_value,
                    expected_value,
                    f"{label}.{status_id}.{field_name}",
                    tolerance,
                    mismatches,
                )

    def _step_label(self, step_data: dict[str, Any]) -> str:
        return f"step {step_data.get('step', '?')}"

    def _validate_unique_unit_ids(self, unit_specs: list[dict[str, Any]]) -> None:
        seen_ids: set[str] = set()
        duplicate_ids: set[str] = set()
        for unit_spec in unit_specs:
            unit_id = unit_spec.get("id")
            if unit_id in seen_ids:
                duplicate_ids.add(unit_id)
            seen_ids.add(unit_id)

        if duplicate_ids:
            duplicates = ", ".join(repr(unit_id) for unit_id in sorted(duplicate_ids))
            raise ReplayValidationError(f"Duplicate unit id in initial_state.units: {duplicates}.")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Usage: python -m hsr_axis_sim.sim.replay <replay.json>", file=sys.stderr)
        return 2

    validator = ReplayValidator()
    try:
        replay_data = validator.load_replay(args[0])
    except OSError as exc:
        print(f"Failed to load replay: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"Failed to parse replay JSON: {exc}", file=sys.stderr)
        return 2

    result = validator.validate(replay_data)
    if result.passed:
        print(f"PASS {result.replay_name}: checked {result.checked_steps} step(s).")
        return 0

    print(f"FAIL {result.replay_name}: checked {result.checked_steps} step(s).")
    for mismatch in result.mismatches:
        print(f"- {mismatch}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
