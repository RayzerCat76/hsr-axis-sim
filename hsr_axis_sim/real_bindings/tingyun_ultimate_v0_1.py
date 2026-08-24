from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from hsr_axis_sim.real_bindings.pela_skill_v0_1 import load_json
from hsr_axis_sim.sim import (
    Action,
    BattleState,
    ConsumeEnergy,
    GainEnergy,
    TurnContext,
    Unit,
    execute_interrupt_action,
)
from hsr_axis_sim.sim.targeting import normalize_and_validate_target_ids


ATOMIC_FACT_SHA256 = "b17a5f295cb8902883d6e8ddaa70c626bdbddf60572db8ce28da6eb3c555491f"
ALLOWED_FACT_IDS = {
    "tingyun.ultimate.target_scope",
    "tingyun.ultimate.energy_cost",
    "tingyun.ultimate.target_energy_restore",
}
REQUIRED_UNRESOLVED_IDS = {
    "tingyun.ultimate.damage_buff_duration",
    "tingyun.ultimate.observed_target",
}
REQUIRED_UNRESOLVED_FIELDS = {
    "damage_buff_magnitude",
    "damage_buff_duration_decrement_and_expiration",
    "observed_real_video_target",
    "real_video_initial_energy_and_combat_state",
}
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BINDING = Path(__file__).resolve().parent / "data" / "tingyun_ultimate_partial_v0_1.json"
DEFAULT_ATOMS = ROOT / "data" / "manual_video_traces" / "normalized_character_facts" / "real_video_trace_001_atomic_facts_v0_1.json"
DEFAULT_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "tingyun_ultimate_partial_v0_1_synthetic.json"
WARNING = (
    "PARTIAL RESOURCE/INTERRUPT SHELL ONLY. No damage buff, damage, toughness, "
    "real-video target, or complete Ultimate semantics are implemented."
)


@dataclass(frozen=True)
class SyntheticFixtureResult:
    fixture_id: str
    actor_energy_before: float
    actor_energy_after: float
    target_energy_before: float
    target_energy_after: float
    skill_points_before: int
    skill_points_after: int
    global_av_before: float
    global_av_after: float
    unit_av_before: dict[str, float]
    unit_av_after: dict[str, float]
    hp_before: dict[str, float]
    hp_after: dict[str, float]
    toughness_before: dict[str, float]
    toughness_after: dict[str, float]
    buff_ids_before: dict[str, list[str]]
    buff_ids_after: dict[str, list[str]]
    is_interrupt: bool
    should_end_turn: bool
    normal_turn_ended: bool


@dataclass(frozen=True)
class BindingAuditReport:
    binding_id: str
    version: str
    warning: str
    binding_scope: str
    complete_game_skill: bool
    complete_character_kit: bool
    atomic_fields_bound: list[str]
    atomic_fields_not_bound: list[str]
    generic_primitives_used: list[str]
    synthetic_fixture_result: SyntheticFixtureResult
    real_trace_executable: bool
    real_trace_blockers: list[str]


def validate_binding(
    binding: dict[str, Any],
    atoms: dict[str, Any],
    atomic_path: str | Path | None = None,
) -> None:
    issues: list[str] = []
    if atomic_path is not None:
        digest = hashlib.sha256(Path(atomic_path).read_bytes()).hexdigest()
        if digest != ATOMIC_FACT_SHA256:
            issues.append("Accepted 002I atomic-fact artifact digest changed.")

    binding_data = binding if isinstance(binding, dict) else {}
    if not isinstance(binding, dict):
        issues.append("Binding must be an object.")
    facts = _validated_atomic_facts(atoms, issues)
    source_ids = _validated_string_id_set(
        binding_data.get("source_atomic_fact_ids"), "source_atomic_fact_ids", issues
    )
    unresolved_ids = _validated_string_id_set(
        binding_data.get("unresolved_atomic_fact_ids"), "unresolved_atomic_fact_ids", issues
    )
    unresolved_fields = _validated_string_id_set(
        binding_data.get("unresolved_fields"), "unresolved_fields", issues
    )
    if source_ids is None or source_ids != ALLOWED_FACT_IDS:
        issues.append(f"source_atomic_fact_ids must equal {sorted(ALLOWED_FACT_IDS)}.")
        source_set: set[str] = set()
    else:
        source_set = source_ids
    if unresolved_ids is None or unresolved_ids != REQUIRED_UNRESOLVED_IDS:
        issues.append(f"unresolved_atomic_fact_ids must equal {sorted(REQUIRED_UNRESOLVED_IDS)}.")
        unresolved_set: set[str] = set()
    else:
        unresolved_set = unresolved_ids
    if unresolved_fields is None or unresolved_fields != REQUIRED_UNRESOLVED_FIELDS:
        issues.append(f"unresolved_fields must equal {sorted(REQUIRED_UNRESOLVED_FIELDS)}.")

    if any(fact_id not in facts for fact_id in source_set | unresolved_set):
        issues.append("Binding contains dangling atomic fact IDs.")
    if any(
        facts.get(fact_id, {}).get("normalized_value") is None
        or facts.get(fact_id, {}).get("verification_status") in {"missing", "conflicting"}
        for fact_id in source_set
    ):
        issues.append("Binding cannot use missing, null, or conflicting atomic facts.")

    expected_facts = {
        "tingyun.ultimate.target_scope": "single_ally",
        "tingyun.ultimate.energy_cost": 130,
        "tingyun.ultimate.target_energy_restore": 50,
    }
    for fact_id, expected in expected_facts.items():
        if facts.get(fact_id, {}).get("normalized_value") != expected:
            issues.append(f"Atomic fact {fact_id!r} does not match accepted value {expected!r}.")

    required_values = {
        "binding_scope": "partial_resource_interrupt_shell",
        "actor_id": "tingyun",
        "action_category": "ultimate",
        "target_type": "single_ally",
        "actor_energy_cost": 130,
        "target_energy_restore": 50,
        "timing_classification": "ultimate_interrupt",
        "complete_game_skill": False,
        "complete_character_kit": False,
        "synthetic_only": True,
        "real_trace_executable": False,
        "damage_effect": False,
        "toughness_effect": False,
        "buff_effect": False,
    }
    boolean_fields = {
        "complete_game_skill",
        "complete_character_kit",
        "synthetic_only",
        "real_trace_executable",
        "damage_effect",
        "toughness_effect",
        "buff_effect",
    }
    for field, expected in required_values.items():
        value = binding_data.get(field)
        if field in boolean_fields and type(value) is not bool:
            issues.append(f"binding.{field} must be an exact boolean.")
        elif value != expected:
            issues.append(f"binding.{field} must be {expected!r}.")

    if issues:
        raise ValueError(
            "Tingyun Ultimate partial binding validation failed:\n"
            + "\n".join(f"- {issue}" for issue in issues)
        )


def _validated_string_id_set(value: Any, field: str, issues: list[str]) -> set[str] | None:
    if not isinstance(value, list):
        issues.append(f"binding.{field} must be a list of unique non-empty strings.")
        return None
    if any(not isinstance(item, str) or not item for item in value):
        issues.append(f"binding.{field} must contain only non-empty strings.")
        return None
    values = set(value)
    if len(values) != len(value):
        issues.append(f"binding.{field} must not contain duplicate values.")
        return None
    return values


def _validated_atomic_facts(atoms: Any, issues: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(atoms, dict):
        issues.append("Atomic fact artifact must be an object.")
        return {}
    atomic_facts = atoms.get("atomic_facts")
    if not isinstance(atomic_facts, list):
        issues.append("Atomic fact artifact must contain an atomic_facts list.")
        return {}
    entries: list[tuple[str, dict[str, Any]]] = []
    for index, item in enumerate(atomic_facts):
        if not isinstance(item, dict):
            issues.append(f"atomic_facts[{index}] must be an object.")
            continue
        fact_id = item.get("atomic_fact_id")
        if not isinstance(fact_id, str) or not fact_id:
            issues.append(f"atomic_facts[{index}].atomic_fact_id must be a non-empty string.")
            continue
        entries.append((fact_id, item))
    if len({fact_id for fact_id, _ in entries}) != len(entries):
        issues.append("atomic_facts contains duplicate atomic_fact_id values.")
        return {}
    if len(entries) != len(atomic_facts):
        return {}
    return {fact_id: item for fact_id, item in entries}


def execute_partial_binding(
    binding: dict[str, Any],
    state: BattleState,
    target_ids: list[str],
    turn_context: TurnContext | None = None,
) -> tuple[TurnContext, str | None]:
    if turn_context is not None:
        raise ValueError("Tingyun Ultimate reviewed execution creates its own interrupt context.")
    selected = normalize_and_validate_target_ids(
        state, binding["actor_id"], binding["target_type"], target_ids
    )
    action = Action(
        id=binding["binding_id"],
        name="Tingyun Ultimate Partial Resource/Interrupt Shell",
        actor_id="tingyun",
        target_ids=selected,
        effects=[
            ConsumeEnergy(amount=binding["actor_energy_cost"], target_ref="actor"),
            GainEnergy(amount=binding["target_energy_restore"], target_ref="action_targets"),
        ],
        ends_turn=False,
    )
    return execute_interrupt_action(state, action), None


def build_fixture_state(fixture: dict[str, Any]) -> BattleState:
    def unit(data: dict[str, Any]) -> Unit:
        result = Unit(
            id=data["id"],
            name=data["id"].title(),
            team=data["team"],
            base_speed=data["speed"],
            energy=data.get("energy", 0),
            max_energy=data.get("max_energy", 100),
            hp=data["hp"],
            max_hp=data["hp"],
            max_toughness=data.get("toughness", 0),
            current_toughness=data.get("toughness", 0),
        )
        result.current_av = data["current_av"]
        return result

    state = BattleState(
        [unit(fixture["actor"]), unit(fixture["ally"]), unit(fixture["enemy"])],
        global_av=fixture["global_av"],
        skill_points=fixture["skill_points"],
    )
    return state


def run_synthetic_fixture(
    binding: dict[str, Any], fixture: dict[str, Any]
) -> SyntheticFixtureResult:
    state = build_fixture_state(fixture)
    actor = state.get_unit("tingyun")
    target = state.get_unit(fixture["selected_target_id"])
    before = _snapshot(state)
    context, _ = execute_partial_binding(binding, state, [target.id])
    after = _snapshot(state)
    return SyntheticFixtureResult(
        fixture_id=fixture["fixture_id"],
        actor_energy_before=before["energy"][actor.id],
        actor_energy_after=after["energy"][actor.id],
        target_energy_before=before["energy"][target.id],
        target_energy_after=after["energy"][target.id],
        skill_points_before=before["skill_points"],
        skill_points_after=after["skill_points"],
        global_av_before=before["global_av"],
        global_av_after=after["global_av"],
        unit_av_before=before["av"],
        unit_av_after=after["av"],
        hp_before=before["hp"],
        hp_after=after["hp"],
        toughness_before=before["toughness"],
        toughness_after=after["toughness"],
        buff_ids_before=before["buffs"],
        buff_ids_after=after["buffs"],
        is_interrupt=context.is_interrupt,
        should_end_turn=context.should_end_turn,
        normal_turn_ended=any(log.startswith("normal_turn_end:") for log in state.logs),
    )


def _snapshot(state: BattleState) -> dict[str, Any]:
    return {
        "energy": {unit.id: unit.energy for unit in state.units},
        "skill_points": state.skill_points,
        "global_av": state.global_av,
        "av": {unit.id: unit.current_av for unit in state.units},
        "hp": {unit.id: unit.hp for unit in state.units},
        "toughness": {unit.id: unit.current_toughness for unit in state.units},
        "buffs": {unit.id: sorted(unit.buffs) for unit in state.units},
    }


def build_audit_report(
    binding: dict[str, Any],
    atoms: dict[str, Any],
    fixture: dict[str, Any],
    atomic_path: str | Path | None = None,
) -> BindingAuditReport:
    validate_binding(binding, atoms, atomic_path)
    return BindingAuditReport(
        binding_id=binding["binding_id"],
        version=binding["version"],
        warning=WARNING,
        binding_scope=binding["binding_scope"],
        complete_game_skill=False,
        complete_character_kit=False,
        atomic_fields_bound=sorted(binding["source_atomic_fact_ids"]),
        atomic_fields_not_bound=sorted(
            binding["unresolved_atomic_fact_ids"] + binding["unresolved_fields"]
        ),
        generic_primitives_used=[
            "single-ally target validation",
            "actor Energy consumption",
            "selected-target Energy gain with max-Energy clamp",
            "Ultimate interrupt execution",
        ],
        synthetic_fixture_result=run_synthetic_fixture(binding, fixture),
        real_trace_executable=False,
        real_trace_blockers=[
            "The observed real-video target and initial Energy state are unknown.",
            "Damage-buff magnitude, duration decrement, and expiration semantics are not bound.",
            "This shell is synthetic-only and is not a complete Tingyun Ultimate or kit.",
        ],
    )


def render_json(report: BindingAuditReport) -> str:
    return json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n"


def render_markdown(report: BindingAuditReport) -> str:
    result = report.synthetic_fixture_result
    lines = [
        f"# Tingyun Ultimate Partial Binding Audit: {report.binding_id}",
        "",
        f"> {report.warning}",
        "",
        "## Bound Atomic Fields",
        "",
        *(f"- `{item}`" for item in report.atomic_fields_bound),
        "",
        "## Deliberately Not Bound",
        "",
        *(f"- `{item}`" for item in report.atomic_fields_not_bound),
        "",
        "## Generic Primitives Used",
        "",
        *(f"- {item}" for item in report.generic_primitives_used),
        "",
        "## Synthetic Fixture Result",
        "",
        f"- Tingyun Energy: {result.actor_energy_before} -> {result.actor_energy_after}",
        f"- Selected ally Energy: {result.target_energy_before} -> {result.target_energy_after}",
        f"- SP: {result.skill_points_before} -> {result.skill_points_after}",
        f"- Global AV: {result.global_av_before} -> {result.global_av_after}",
        f"- Interrupt: `{str(result.is_interrupt).lower()}`",
        f"- Should end turn: `{str(result.should_end_turn).lower()}`",
        f"- Normal turn ended: `{str(result.normal_turn_ended).lower()}`",
        "",
        "## Real Trace Status",
        "",
        "- Executable: `false`",
        *(f"- {item}" for item in report.real_trace_blockers),
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Tingyun Ultimate partial binding shell.")
    parser.add_argument("--binding", default=str(DEFAULT_BINDING))
    parser.add_argument("--atomic-facts", default=str(DEFAULT_ATOMS))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--format", choices=["markdown", "json"], required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        binding = load_json(args.binding)
        atoms = load_json(args.atomic_facts)
        fixture = load_json(args.fixture)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR Tingyun binding input failure: {exc}", file=sys.stderr)
        return 2
    try:
        report = build_audit_report(binding, atoms, fixture, args.atomic_facts)
    except ValueError as exc:
        print(f"FAIL Tingyun binding validation: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR Tingyun binding audit could not run: {exc}", file=sys.stderr)
        return 2
    rendered = render_markdown(report) if args.format == "markdown" else render_json(report)
    try:
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except OSError as exc:
        print(f"ERROR Tingyun binding output failure: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
