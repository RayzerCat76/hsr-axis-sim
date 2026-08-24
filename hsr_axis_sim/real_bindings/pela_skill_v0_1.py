from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from hsr_axis_sim.sim import Action, BattleState, Buff, ConsumeSkillPoint, GainEnergy, RemoveBuff, TurnContext, Unit
from hsr_axis_sim.sim.targeting import normalize_and_validate_target_ids

ATOMIC_FACT_SHA256 = "b17a5f295cb8902883d6e8ddaa70c626bdbddf60572db8ce28da6eb3c555491f"
ALLOWED_FACT_IDS = {"pela.skill.target_scope", "pela.skill.sp_delta", "pela.skill.energy_generation", "pela.skill.dispel_count"}
REQUIRED_UNRESOLVED_IDS = {"pela.skill.observed_target_and_level", "pela.skill.toughness_native"}
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BINDING = Path(__file__).resolve().parent / "data" / "pela_skill_partial_v0_1.json"
DEFAULT_ATOMS = ROOT / "data" / "manual_video_traces" / "normalized_character_facts" / "real_video_trace_001_atomic_facts_v0_1.json"
DEFAULT_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "pela_skill_partial_v0_1_synthetic.json"
WARNING = "PARTIAL BINDING SHELL ONLY. complete_game_skill=false; no damage or toughness semantics are implemented."

@dataclass(frozen=True)
class SyntheticFixtureResult:
    fixture_id: str
    removed_buff_id: str | None
    skill_points_before: int
    skill_points_after: int
    actor_energy_before: float
    actor_energy_after: float
    target_hp_before: float
    target_hp_after: float
    target_toughness_before: float
    target_toughness_after: float
    actor_av_before: float
    actor_av_after: float
    normal_turn_ended: bool

@dataclass(frozen=True)
class BindingAuditReport:
    binding_id: str
    version: str
    warning: str
    binding_scope: str
    complete_game_skill: bool
    atomic_fields_bound: list[str]
    atomic_fields_not_bound: list[str]
    generic_primitives_used: list[str]
    generic_extensions_added: list[str]
    synthetic_fixture_result: SyntheticFixtureResult
    real_trace_executable: bool
    real_trace_blockers: list[str]

def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value

def validate_binding(binding: dict[str, Any], atoms: dict[str, Any], atomic_path: str | Path | None = None) -> None:
    issues: list[str] = []
    if atomic_path is not None and hashlib.sha256(Path(atomic_path).read_bytes()).hexdigest() != ATOMIC_FACT_SHA256:
        issues.append("Accepted 002I atomic-fact artifact digest changed.")

    binding_data = binding if isinstance(binding, dict) else {}
    if not isinstance(binding, dict):
        issues.append("Binding must be an object.")
    facts = _validated_atomic_facts(atoms, issues)
    source_ids = _validated_string_id_set(binding_data.get("source_atomic_fact_ids"), "source_atomic_fact_ids", issues)
    unresolved_ids = _validated_string_id_set(binding_data.get("unresolved_atomic_fact_ids"), "unresolved_atomic_fact_ids", issues)
    _validated_string_id_set(binding_data.get("unresolved_fields"), "unresolved_fields", issues)

    if source_ids is None:
        source_ids = set()
    if unresolved_ids is None:
        unresolved_ids = set()
    if source_ids != ALLOWED_FACT_IDS:
        issues.append(f"source_atomic_fact_ids must equal {sorted(ALLOWED_FACT_IDS)}.")
    if any(fact_id not in facts for fact_id in source_ids | unresolved_ids):
        issues.append("Binding contains dangling atomic fact IDs.")
    if any(facts.get(fact_id, {}).get("normalized_value") is None or facts.get(fact_id, {}).get("verification_status") in {"missing", "conflicting"} for fact_id in source_ids):
        issues.append("Binding cannot use missing, null, or conflicting atomic facts.")
    expected = {"pela.skill.target_scope":"single_enemy", "pela.skill.sp_delta":-1, "pela.skill.energy_generation":30, "pela.skill.dispel_count":1}
    for fact_id, value in expected.items():
        if facts.get(fact_id, {}).get("normalized_value") != value:
            issues.append(f"Atomic fact {fact_id!r} does not match accepted value {value!r}.")
    if not REQUIRED_UNRESOLVED_IDS <= unresolved_ids:
        issues.append("Binding must preserve unresolved target/level and toughness facts.")
    required = {"binding_scope":"partial_resource_target_dispel_shell", "complete_game_skill":False, "target_type":"single_enemy", "skill_point_cost":1, "actor_energy_gain":30, "dispel_count":1, "damage_effect":False, "toughness_effect":False, "synthetic_only":True}
    for field, value in required.items():
        if binding_data.get(field) != value:
            issues.append(f"binding.{field} must be {value!r}.")
    if binding_data.get("actor_id") != "pela" or binding_data.get("action_category") != "skill":
        issues.append("Binding actor/category must remain pela/skill.")
    if issues:
        raise ValueError("Pela Skill partial binding validation failed:\n" + "\n".join(f"- {issue}" for issue in issues))


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

def execute_partial_binding(binding: dict[str, Any], state: BattleState, target_ids: list[str], turn_context: TurnContext | None = None) -> tuple[TurnContext, str | None]:
    selected = normalize_and_validate_target_ids(state, binding["actor_id"], binding["target_type"], target_ids)
    target = state.get_unit(selected[0])
    removable = sorted(buff_id for buff_id, buff in target.buffs.items() if buff.data.get("removable") is True)
    removed_id = removable[0] if removable else None
    effects = [ConsumeSkillPoint(amount=1), GainEnergy(amount=30, target_ref="actor")]
    if removed_id is not None:
        effects.append(RemoveBuff(id=removed_id, target_ref="action_targets"))
    action = Action(id=binding["binding_id"], name="Pela Skill Partial Resource/Dispel Shell", actor_id="pela", target_ids=selected, effects=effects, ends_turn=True)
    return action.execute(state, turn_context or TurnContext(actor_id="pela")), removed_id

def register_as_complete_kit(binding: dict[str, Any]) -> None:
    raise ValueError(f"Partial binding {binding.get('binding_id')!r} cannot be registered as a complete Pela kit.")

def build_fixture_state(fixture: dict[str, Any]) -> BattleState:
    def unit(data: dict[str, Any]) -> Unit:
        return Unit(data["id"], data["id"].title(), data["team"], data["speed"], energy=data.get("energy",0), max_energy=data.get("max_energy",100), hp=data["hp"], max_hp=data["hp"], max_toughness=data.get("toughness",0), current_toughness=data.get("toughness",0))
    actor, ally, target = unit(fixture["actor"]), unit(fixture["ally"]), unit(fixture["target"])
    for spec in fixture["target"].get("buffs", []):
        target.buffs[spec["id"]] = Buff(spec["id"], spec["name"], target.id, None, "buff", "target_normal_turns", 3, data={"removable": spec["removable"]})
    actor.current_av = 0
    return BattleState([actor, ally, target], skill_points=fixture["skill_points"])

def run_synthetic_fixture(binding: dict[str, Any], fixture: dict[str, Any]) -> SyntheticFixtureResult:
    state = build_fixture_state(fixture); actor=state.get_unit("pela"); target=state.get_unit("enemy")
    before=(state.skill_points,actor.energy,target.hp,target.current_toughness,actor.current_av)
    context, removed = execute_partial_binding(binding,state,["enemy"],TurnContext(actor_id="pela"))
    return SyntheticFixtureResult(fixture["fixture_id"],removed,before[0],state.skill_points,before[1],actor.energy,before[2],target.hp,before[3],target.current_toughness,before[4],actor.current_av,"normal_turn_end:pela" in state.logs and context.should_end_turn)

def build_audit_report(binding: dict[str, Any], atoms: dict[str, Any], fixture: dict[str, Any], atomic_path: str | Path | None = None) -> BindingAuditReport:
    validate_binding(binding, atoms, atomic_path)
    result=run_synthetic_fixture(binding,fixture)
    return BindingAuditReport(binding["binding_id"],binding["version"],WARNING,binding["binding_scope"],False,sorted(binding["source_atomic_fact_ids"]),sorted(binding["unresolved_atomic_fact_ids"]+binding["unresolved_fields"]),["single-enemy target validation","skill-point consumption","actor energy gain","ID-specific buff removal","normal turn completion"],[],result,False,["Observed real-video target is unknown.","Damage, normalized toughness, trace level, build, and initial state remain unresolved.","This shell is synthetic-only and is not a complete Pela skill or kit."])

def render_json(report: BindingAuditReport) -> str:
    return json.dumps(asdict(report),ensure_ascii=False,indent=2)+"\n"

def render_markdown(report: BindingAuditReport) -> str:
    r=report.synthetic_fixture_result
    lines=[f"# Pela Skill Partial Binding Audit: {report.binding_id}","",f"> {report.warning}","","## Bound Atomic Fields","",*(f"- `{x}`" for x in report.atomic_fields_bound),"","## Deliberately Not Bound","",*(f"- `{x}`" for x in report.atomic_fields_not_bound),"","## Generic Primitives Used","",*(f"- {x}" for x in report.generic_primitives_used),"","## Generic Extensions Added","", "- None.","","## Synthetic Fixture Result","",f"- Removed buff: `{r.removed_buff_id}`",f"- SP: {r.skill_points_before} -> {r.skill_points_after}",f"- Pela Energy: {r.actor_energy_before} -> {r.actor_energy_after}",f"- Target HP: {r.target_hp_before} -> {r.target_hp_after}",f"- Target toughness: {r.target_toughness_before} -> {r.target_toughness_after}",f"- Normal turn ended: `{str(r.normal_turn_ended).lower()}`","","## Real Trace Status","","- Executable: `false`",*(f"- {x}" for x in report.real_trace_blockers)]
    return "\n".join(lines)+"\n"

def main(argv: list[str] | None=None) -> int:
    p=argparse.ArgumentParser(description="Audit Pela Skill partial binding shell."); p.add_argument("--binding",default=str(DEFAULT_BINDING)); p.add_argument("--atomic-facts",default=str(DEFAULT_ATOMS)); p.add_argument("--fixture",default=str(DEFAULT_FIXTURE)); p.add_argument("--format",choices=["markdown","json"],required=True); p.add_argument("--output"); a=p.parse_args(argv)
    try: binding,atoms,fixture=load_json(a.binding),load_json(a.atomic_facts),load_json(a.fixture)
    except (OSError,json.JSONDecodeError,ValueError) as exc: print(f"ERROR Pela binding input failure: {exc}",file=sys.stderr); return 2
    try: report=build_audit_report(binding,atoms,fixture,a.atomic_facts)
    except ValueError as exc: print(f"FAIL Pela binding validation: {exc}",file=sys.stderr); return 1
    except Exception as exc: print(f"ERROR Pela binding audit could not run: {exc}",file=sys.stderr); return 2
    text=render_markdown(report) if a.format=="markdown" else render_json(report)
    try: Path(a.output).write_text(text,encoding="utf-8") if a.output else print(text,end="")
    except OSError as exc: print(f"ERROR Pela binding output failure: {exc}",file=sys.stderr); return 2
    return 0

if __name__ == "__main__": raise SystemExit(main())
