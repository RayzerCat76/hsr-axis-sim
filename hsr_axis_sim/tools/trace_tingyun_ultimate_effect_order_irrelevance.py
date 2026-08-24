from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import asdict, dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any

from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.buffs import Buff
from hsr_axis_sim.sim.effects import AddBuff, AddDebuff, GainEnergy
from hsr_axis_sim.sim.enemy_ai import EnemyAIPlan, EnemyPatternStep
from hsr_axis_sim.sim.events import Event, Trigger
from hsr_axis_sim.sim.state import BattleState
from hsr_axis_sim.sim.turn_context import TurnContext
from hsr_axis_sim.sim.unit import Unit


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "manual_video_traces"
DEFAULT_REVIEW = BASE / "normalized_character_facts" / "tingyun_ultimate_effect_order_irrelevance_review_v0_1.json"
PROBE_BUFF_ID = "synthetic_tingyun_order_probe"
CONCLUSION = "proven_irrelevant_under_current_simulator_contract"
WARNING = (
    "NON-EXECUTABLE CURRENT-CONTRACT PROOF. Release-game effect order and duration "
    "semantics remain unknown; this report does not authorize a Tingyun DMG buff."
)
PINNED_PATHS = {
    "action": "sim/action.py",
    "effects": "sim/effects.py",
    "events": "sim/events.py",
    "state": "sim/state.py",
    "turn_context": "sim/turn_context.py",
    "targets": "sim/targets.py",
    "buffs": "sim/buffs.py",
    "unit": "sim/unit.py",
    "enemy_ai": "sim/enemy_ai.py",
    "tingyun_partial_binding": "real_bindings/tingyun_ultimate_v0_1.py",
    "semantic_readiness_input": "data/manual_video_traces/normalized_character_facts/tingyun_ultimate_damage_buff_semantic_readiness_v0_1.json",
    "semantic_readiness_report": "data/manual_video_traces/real_binding_audits/tingyun_ultimate_damage_buff_semantic_readiness_v0_1.json",
    "reviewed_registry": "real_bindings/registry_v0_2.json",
    "regression_manifest": "data/regression_manifest.json",
}
EXPECTED_MANIFEST_COUNTS = {
    "replays": 12,
    "manual": 1,
    "scenarios": 2,
    "action_sequence_traces": 1,
    "trace_evidence": 2,
}
CASE_CONTRACTS = {
    "below_cap_no_existing_probe": (10, 100, False),
    "near_cap_no_existing_probe": (80, 100, False),
    "at_cap_no_existing_probe": (100, 100, False),
    "below_cap_existing_probe_refresh": (10, 100, True),
    "near_cap_existing_probe_refresh": (80, 100, True),
    "at_cap_existing_probe_refresh": (100, 100, True),
}
STATE_FIELDS = tuple(field.name for field in fields(BattleState))
UNIT_FIELDS = tuple(field.name for field in fields(Unit))
BUFF_FIELDS = tuple(field.name for field in fields(Buff))
EVENT_FIELDS = tuple(field.name for field in fields(Event))
TRIGGER_FIELDS = tuple(field.name for field in fields(Trigger))
TURN_CONTEXT_FIELDS = tuple(field.name for field in fields(TurnContext))
SNAPSHOT_FIELDS = ("state", "turn_context", "action_result")
ACTION_RESULT_FIELDS = ("return_type", "returned_same_context")
ROOT_FIELDS = {
    "review_id", "version", "status", "pinned_sources", "implementation_locators",
    "observation_contract", "synthetic_fixture", "comparison_cases", "conclusion",
    "derived_generic_readiness", "accepted_video_binding_readiness",
    "release_game_order_known", "same_current_turn_duration_resolved",
    "accepted_video_target", "accepted_video_trace_level", "registry_expected_count",
    "manifest_expected_counts", "proof_boundaries", "simulator_binding_allowed",
}
FORBIDDEN_KEYS = {
    "characterspec", "skillspec", "handlerkey", "bindingdatapath",
    "realtraceexecutable", "executablebinding", "selectedtracelevel",
}


EXPECTED_FIXTURE = {
    "fixture_id": "synthetic_tingyun_effect_order_contract_probe_v0_1",
    "energy_restore_amount": 50,
    "probe_buff": {
        "id": PROBE_BUFF_ID,
        "name": "Synthetic Tingyun Order Probe",
        "duration_type": "target_normal_turns",
        "remaining_turns": 2,
        "stacks": 1,
        "max_stacks": 2,
        "refresh_policy": "refresh",
        "data": {"synthetic_probe": True, "dmg_bonus_ratio": 0.5},
    },
    "state": {
        "global_av": 37.5,
        "skill_points": 3,
        "max_skill_points": 7,
        "extra_turn_stack": ["observer", "target"],
        "logs": ["preexisting:log"],
        "event_dispatch_limit": 100,
        "trigger_fire_counts": {"preexisting_counter": 4},
        "event_dispatch_count": 9,
        "enemy_ai_cursors": {"enemy": 2},
    },
    "units": [
        {"id":"tingyun","name":"Tingyun","team":"ally","base_speed":112,"speed":113,"current_av":41.25,"energy":130,"max_energy":130,"hp":777,"max_hp":1000,"is_alive":True,"level":80,"atk":432,"defense":321,"crit_rate":0.17,"crit_dmg":0.71,"dmg_bonus":0.12,"break_effect":0.24,"all_res":0.01,"element":"lightning","weaknesses":["ice"],"max_toughness":0,"current_toughness":0,"is_broken":False},
        {"id":"target","name":"Selected Ally","team":"ally","base_speed":101,"speed":103,"current_av":22.75,"energy":10,"max_energy":100,"hp":654,"max_hp":900,"is_alive":True,"level":79,"atk":555,"defense":222,"crit_rate":0.33,"crit_dmg":0.88,"dmg_bonus":0.27,"break_effect":0.19,"all_res":0.02,"element":"wind","weaknesses":["fire","ice"],"max_toughness":0,"current_toughness":0,"is_broken":False},
        {"id":"observer","name":"Observer Ally","team":"ally","base_speed":97,"speed":99,"current_av":63.5,"energy":11,"max_energy":120,"hp":501,"max_hp":800,"is_alive":True,"level":78,"atk":333,"defense":444,"crit_rate":0.09,"crit_dmg":0.59,"dmg_bonus":0.08,"break_effect":0.31,"all_res":0.03,"element":"ice","weaknesses":["lightning"],"max_toughness":0,"current_toughness":0,"is_broken":False},
        {"id":"enemy","name":"Synthetic Enemy","team":"enemy","base_speed":88,"speed":89,"current_av":74.25,"energy":19,"max_energy":90,"hp":1234,"max_hp":1500,"is_alive":True,"level":77,"atk":600,"defense":500,"crit_rate":0.05,"crit_dmg":0.55,"dmg_bonus":0.04,"break_effect":0.07,"all_res":0.1,"element":"fire","weaknesses":["lightning","wind"],"max_toughness":120,"current_toughness":73,"is_broken":False},
    ],
    "unrelated_statuses": [
        {"owner_id":"target","collection":"buffs","id":"unrelated_target_buff","name":"Unrelated Target Buff","source_id":"observer","kind":"buff","duration_type":"target_normal_turns","remaining_turns":3,"stacks":2,"max_stacks":4,"data":{"marker":"target-buff","value":7}},
        {"owner_id":"target","collection":"debuffs","id":"unrelated_target_debuff","name":"Unrelated Target Debuff","source_id":"enemy","kind":"debuff","duration_type":"target_normal_turns","remaining_turns":1,"stacks":1,"max_stacks":1,"data":{"marker":"target-debuff"}},
        {"owner_id":"enemy","collection":"buffs","id":"unrelated_enemy_buff","name":"Unrelated Enemy Buff","source_id":"enemy","kind":"buff","duration_type":"current_turn","remaining_turns":None,"stacks":1,"max_stacks":1,"data":{"marker":"enemy-buff"}},
    ],
    "pending_events": [
        {"type":"preexisting_event","data":{"marker":"before-action","nested":{"sequence":3,"enabled":True}}}
    ],
    "triggers": [
        {"id":"order_probe_action_started","owner_id":"observer","event_type":"action_started","condition":{"type":"always"},"effect_kind":"gain_energy","target_id":"observer","amount":7,"max_triggers_per_action":1,"enabled":True},
        {"id":"order_probe_action_finished","owner_id":"observer","event_type":"action_finished","condition":{"type":"always"},"effect_kind":"add_debuff","target_id":"enemy","status_id":"synthetic_finished_marker","max_triggers_per_action":1,"enabled":True},
    ],
    "enemy_ai_plan": {"owner_id":"enemy","pattern":[{"skill_id":"enemy_probe_skill","target_strategy":"first_legal","target_ids":None}],"repeat":True},
    "turn_context": {"actor_id":"tingyun","is_extra_turn":False,"is_interrupt":True,"should_end_turn":False,"actions_taken":["prior_interrupt_action"],"forced_rng":{"marker":17,"nested":{"choice":"fixed"}}},
}


EXPECTED_OBSERVATION_CONTRACT = {
    "snapshot_fields": sorted(SNAPSHOT_FIELDS),
    "state_fields": sorted(STATE_FIELDS),
    "unit_fields": sorted(UNIT_FIELDS),
    "buff_fields": sorted(BUFF_FIELDS),
    "event_fields": sorted(EVENT_FIELDS),
    "trigger_fields": sorted(TRIGGER_FIELDS),
    "turn_context_fields": sorted(TURN_CONTEXT_FIELDS),
    "action_result_fields": sorted(ACTION_RESULT_FIELDS),
    "excluded_fields": [],
}


@dataclass(frozen=True)
class PinnedSource:
    source_id: str
    path: str
    sha256: str
    locators: tuple[str, ...]


@dataclass(frozen=True)
class ComparisonResult:
    case_id: str
    target_energy_before: float
    target_max_energy: float
    existing_probe_buff: bool
    equal: bool
    order_a_snapshot_sha256: str
    order_b_snapshot_sha256: str
    order_a_snapshot: dict[str, Any]
    order_b_snapshot: dict[str, Any]


@dataclass(frozen=True)
class EffectOrderProofReport:
    review_id: str
    version: str
    warning: str
    conclusion: str
    pinned_sources: tuple[PinnedSource, ...]
    implementation_locators: tuple[str, ...]
    observation_contract: dict[str, Any]
    comparison_results: tuple[ComparisonResult, ...]
    every_case_equal: bool
    derived_generic_readiness: str
    accepted_video_binding_readiness: str
    release_game_order_known: bool
    same_current_turn_duration_resolved: bool
    accepted_video_target: None
    accepted_video_trace_level: None
    proof_boundaries: tuple[str, ...]
    simulator_binding_allowed: bool


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def build_report(data: Any, root: str | Path = ROOT) -> EffectOrderProofReport:
    issues: list[str] = []
    if not isinstance(data, dict):
        raise ValueError("Tingyun effect-order proof validation failed:\n- review must be an object.")
    _reject_executable_schema(data, "review", issues)
    if set(data) != ROOT_FIELDS:
        issues.append("review must contain the exact required root fields.")
    for field in ("review_id", "version", "status", "conclusion", "derived_generic_readiness", "accepted_video_binding_readiness"):
        _string(data.get(field), field, issues)
    if data.get("status") != "non_executable_current_contract_proof":
        issues.append("status must be 'non_executable_current_contract_proof'.")
    sources = _pinned_sources(data.get("pinned_sources"), Path(root), issues)
    locators = _string_list(data.get("implementation_locators"), "implementation_locators", issues)
    _validate_observation_contract(data.get("observation_contract"), issues)
    fixture_valid = _validate_against_template(data.get("synthetic_fixture"), EXPECTED_FIXTURE, "synthetic_fixture", issues)
    cases = _comparison_cases(data.get("comparison_cases"), issues)
    _validate_safety_conclusions(data, issues)
    _validate_registry_and_manifest(data, Path(root), issues)
    _validate_002o(data, Path(root), issues)
    boundaries = _string_list(data.get("proof_boundaries"), "proof_boundaries", issues)
    if len(boundaries) < 4:
        issues.append("proof_boundaries must contain at least four explicit limits.")
    if issues:
        raise ValueError("Tingyun effect-order proof validation failed:\n" + "\n".join(f"- {item}" for item in issues))

    results: list[ComparisonResult] = []
    if fixture_valid:
        for case_id in sorted(cases):
            energy, maximum, existing = cases[case_id]
            order_a = run_comparison_case(EXPECTED_FIXTURE, energy, maximum, existing, "energy_then_buff")
            order_b = run_comparison_case(EXPECTED_FIXTURE, energy, maximum, existing, "buff_then_energy")
            _validate_snapshot(order_a, f"comparison_cases[{case_id}].order_a_snapshot")
            _validate_snapshot(order_b, f"comparison_cases[{case_id}].order_b_snapshot")
            equal = order_a == order_b
            results.append(ComparisonResult(
                case_id, energy, maximum, existing, equal,
                _json_digest(order_a), _json_digest(order_b), order_a, order_b,
            ))
    every_equal = bool(results) and all(result.equal for result in results)
    if data["conclusion"] == CONCLUSION and (set(cases) != set(CASE_CONTRACTS) or not every_equal):
        raise ValueError("Tingyun effect-order proof validation failed:\n- positive conclusion requires every required comparison case to be present and equal.")
    return EffectOrderProofReport(
        review_id=data["review_id"], version=data["version"], warning=WARNING,
        conclusion=data["conclusion"],
        pinned_sources=tuple(sorted(sources.values(), key=lambda item: item.source_id)),
        implementation_locators=tuple(sorted(locators)),
        observation_contract=EXPECTED_OBSERVATION_CONTRACT,
        comparison_results=tuple(results), every_case_equal=every_equal,
        derived_generic_readiness=data["derived_generic_readiness"],
        accepted_video_binding_readiness=data["accepted_video_binding_readiness"],
        release_game_order_known=False, same_current_turn_duration_resolved=False,
        accepted_video_target=None, accepted_video_trace_level=None,
        proof_boundaries=tuple(sorted(boundaries)), simulator_binding_allowed=False,
    )


def _pinned_sources(value: Any, root: Path, issues: list[str]) -> dict[str, PinnedSource]:
    if not isinstance(value, list):
        issues.append("pinned_sources must be a list.")
        return {}
    result: dict[str, PinnedSource] = {}
    paths: set[str] = set()
    for index, item in enumerate(value):
        label = f"pinned_sources[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{label} must be an object.")
            continue
        if set(item) != {"source_id", "path", "sha256", "locators"}:
            issues.append(f"{label} must contain the exact source fields.")
        source_id, path, digest = item.get("source_id"), item.get("path"), item.get("sha256")
        for field, raw in (("source_id", source_id), ("path", path), ("sha256", digest)):
            _string(raw, f"{label}.{field}", issues)
        locators = _string_list(item.get("locators"), f"{label}.locators", issues)
        if not all(isinstance(raw, str) and raw for raw in (source_id, path, digest)):
            continue
        if source_id in result:
            issues.append(f"duplicate source ID {source_id!r}.")
            continue
        if path in paths:
            issues.append(f"duplicate source path {path!r}.")
            continue
        expected_path = PINNED_PATHS.get(source_id)
        if expected_path is None or path != expected_path:
            issues.append(f"{label}.path does not match the required pinned source.")
            continue
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            issues.append(f"{label}.sha256 must be a lowercase SHA-256 digest.")
            continue
        try:
            actual = hashlib.sha256((root / path).read_bytes()).hexdigest()
        except OSError as exc:
            issues.append(f"{label} cannot read pinned source: {exc}")
            continue
        if actual != digest:
            issues.append(f"{label}.sha256 is stale.")
            continue
        paths.add(path)
        result[source_id] = PinnedSource(source_id, path, digest, tuple(sorted(locators)))
    if set(result) != set(PINNED_PATHS):
        issues.append("pinned_sources must contain every required current-contract source.")
    return result


def _comparison_cases(value: Any, issues: list[str]) -> dict[str, tuple[float, float, bool]]:
    if not isinstance(value, list):
        issues.append("comparison_cases must be a list.")
        return {}
    result: dict[str, tuple[float, float, bool]] = {}
    for index, item in enumerate(value):
        label = f"comparison_cases[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{label} must be an object.")
            continue
        if set(item) != {"case_id", "target_energy", "target_max_energy", "existing_probe_buff", "expected_equal"}:
            issues.append(f"{label} must contain the exact case fields.")
        case_id = item.get("case_id")
        _string(case_id, f"{label}.case_id", issues)
        energy = _number(item.get("target_energy"), f"{label}.target_energy", issues)
        maximum = _number(item.get("target_max_energy"), f"{label}.target_max_energy", issues)
        existing, expected_equal = item.get("existing_probe_buff"), item.get("expected_equal")
        if type(existing) is not bool:
            issues.append(f"{label}.existing_probe_buff must be an exact boolean.")
        if type(expected_equal) is not bool:
            issues.append(f"{label}.expected_equal must be an exact boolean.")
        elif expected_equal is not True:
            issues.append(f"{label}.expected_equal must be true for a positive conclusion.")
        if not isinstance(case_id, str) or not case_id or energy is None or maximum is None or type(existing) is not bool:
            continue
        if case_id in result:
            issues.append(f"duplicate case ID {case_id!r}.")
            continue
        expected = CASE_CONTRACTS.get(case_id)
        if expected is None or (energy, maximum, existing) != expected:
            issues.append(f"{label} does not match the required comparison case contract.")
            continue
        result[case_id] = (energy, maximum, existing)
    if set(result) != set(CASE_CONTRACTS):
        issues.append("comparison_cases must contain the exact six required cases.")
    return result


def _validate_safety_conclusions(data: dict[str, Any], issues: list[str]) -> None:
    expected = {
        "conclusion": CONCLUSION,
        "derived_generic_readiness": "blocked_by_duration_semantics",
        "accepted_video_binding_readiness": "blocked_by_unknown_target_and_trace_level",
        "release_game_order_known": False,
        "same_current_turn_duration_resolved": False,
        "accepted_video_target": None,
        "accepted_video_trace_level": None,
        "registry_expected_count": 2,
        "simulator_binding_allowed": False,
    }
    for field, expected_value in expected.items():
        actual = data.get(field)
        if type(actual) is not type(expected_value) or actual != expected_value:
            issues.append(f"{field} must be {expected_value!r} with exact type.")
    _validate_against_template(data.get("manifest_expected_counts"), EXPECTED_MANIFEST_COUNTS, "manifest_expected_counts", issues)


def _validate_observation_contract(value: Any, issues: list[str]) -> None:
    if not isinstance(value, dict):
        issues.append("observation_contract must be an object.")
        return
    if set(value) != set(EXPECTED_OBSERVATION_CONTRACT):
        issues.append("observation_contract must contain the exact required field groups.")
        return
    for field, expected in EXPECTED_OBSERVATION_CONTRACT.items():
        actual = value.get(field)
        if field == "excluded_fields":
            if actual != []:
                issues.append("observation_contract.excluded_fields must be an empty list.")
            continue
        rows = _string_list(actual, f"observation_contract.{field}", issues)
        if set(rows) != set(expected):
            issues.append(f"observation_contract.{field} must contain every required observable field.")


def _validate_registry_and_manifest(data: dict[str, Any], root: Path, issues: list[str]) -> None:
    try:
        registry = load_json(root / PINNED_PATHS["reviewed_registry"])
        entries = registry.get("entries")
        if registry.get("registry_version") != "0.2" or not isinstance(entries, list) or len(entries) != 2:
            issues.append("reviewed registry must remain version 0.2 with exactly two entries.")
        manifest = load_json(root / PINNED_PATHS["regression_manifest"])
        groups = manifest.get("groups")
        if not isinstance(groups, dict):
            issues.append("regression manifest groups must remain an object.")
        else:
            counts = {name: len(items) for name, items in groups.items() if isinstance(name, str) and isinstance(items, list)}
            if counts != EXPECTED_MANIFEST_COUNTS:
                issues.append("regression manifest counts changed.")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        issues.append(f"registry/manifest validation failed: {exc}")


def _validate_002o(data: dict[str, Any], root: Path, issues: list[str]) -> None:
    try:
        evidence = load_json(root / PINNED_PATHS["semantic_readiness_input"])
        report = load_json(root / PINNED_PATHS["semantic_readiness_report"])
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        issues.append(f"002O evidence validation failed: {exc}")
        return
    for source, label in ((evidence, "002O evidence"), (report, "002O report")):
        if source.get("generic_binding_readiness") != "blocked_by_both_semantics":
            issues.append(f"{label} generic readiness changed.")
        if source.get("accepted_video_binding_readiness") != "blocked_by_unknown_target_and_trace_level":
            issues.append(f"{label} accepted-video readiness changed.")
        if source.get("selected_magnitude_level") is not None:
            issues.append(f"{label} selected a magnitude level.")


def run_comparison_case(fixture: dict[str, Any], target_energy: float, target_max_energy: float, existing_probe: bool, order: str) -> dict[str, Any]:
    state, context = _build_state(fixture, target_energy, target_max_energy, existing_probe)
    gain = GainEnergy(amount=fixture["energy_restore_amount"], target_ref="action_targets")
    probe = fixture["probe_buff"]
    buff = AddBuff(
        id=probe["id"], name=probe["name"], duration_type=probe["duration_type"],
        remaining_turns=probe["remaining_turns"], stacks=probe["stacks"],
        max_stacks=probe["max_stacks"], data=dict(probe["data"]),
        refresh_policy=probe["refresh_policy"], target_ref="action_targets",
    )
    if order == "energy_then_buff":
        effects = [gain, buff]
    elif order == "buff_then_energy":
        effects = [buff, gain]
    else:
        raise ValueError(f"Unsupported synthetic comparison order: {order!r}.")
    action = Action(
        id="synthetic_tingyun_order_probe_action", name="Synthetic Tingyun Order Probe",
        actor_id="tingyun", target_ids=["target"], effects=effects, ends_turn=False,
    )
    returned = action.execute(state, context)
    return canonical_snapshot(state, context, returned is context)


def _build_state(fixture: dict[str, Any], target_energy: float, target_max_energy: float, existing_probe: bool) -> tuple[BattleState, TurnContext]:
    units: list[Unit] = []
    for row in fixture["units"]:
        values = dict(row)
        if values["id"] == "target":
            values["energy"], values["max_energy"] = target_energy, target_max_energy
        units.append(Unit(**values))
    state_data = fixture["state"]
    state = BattleState(
        units=units, global_av=state_data["global_av"], skill_points=state_data["skill_points"],
        max_skill_points=state_data["max_skill_points"], extra_turn_stack=list(state_data["extra_turn_stack"]),
        logs=list(state_data["logs"]), pending_events=[Event(item["type"], _canonical(item["data"])) for item in fixture["pending_events"]],
        trigger_fire_counts=dict(state_data["trigger_fire_counts"]), event_dispatch_count=state_data["event_dispatch_count"],
        event_dispatch_limit=state_data["event_dispatch_limit"], enemy_ai_cursors=dict(state_data["enemy_ai_cursors"]),
    )
    for status in fixture["unrelated_statuses"]:
        collection = getattr(state.get_unit(status["owner_id"]), status["collection"])
        values = {key: value for key, value in status.items() if key not in {"owner_id", "collection"}}
        values["target_id"] = status["owner_id"]
        collection[status["id"]] = Buff(**values)
    if existing_probe:
        probe = fixture["probe_buff"]
        state.get_unit("target").buffs[PROBE_BUFF_ID] = Buff(
            id=PROBE_BUFF_ID, name="Old Synthetic Probe", target_id="target", source_id="old_source",
            kind="buff", duration_type="target_normal_turns", remaining_turns=1, stacks=1,
            max_stacks=2, data={"synthetic_probe": True, "old": True},
        )
    state.triggers = [_build_trigger(item) for item in fixture["triggers"]]
    ai = fixture["enemy_ai_plan"]
    state.enemy_ai_plans[ai["owner_id"]] = EnemyAIPlan(
        pattern=[EnemyPatternStep(**step) for step in ai["pattern"]], repeat=ai["repeat"]
    )
    return state, TurnContext(**_canonical(fixture["turn_context"]))


def _build_trigger(item: dict[str, Any]) -> Trigger:
    if item["effect_kind"] == "gain_energy":
        effects = [GainEnergy(amount=item["amount"], target_ids=[item["target_id"]])]
    else:
        effects = [AddDebuff(
            id=item["status_id"], name="Synthetic Finished Marker", target_ids=[item["target_id"]],
            duration_type="target_normal_turns", remaining_turns=1, data={"synthetic_probe": True},
        )]
    return Trigger(
        id=item["id"], owner_id=item["owner_id"], event_type=item["event_type"],
        condition=dict(item["condition"]), effects=effects,
        max_triggers_per_action=item["max_triggers_per_action"], enabled=item["enabled"],
    )


def canonical_snapshot(state: BattleState, context: TurnContext, returned_same_context: bool) -> dict[str, Any]:
    state_row = {field: _canonical(getattr(state, field)) for field in STATE_FIELDS}
    state_row["units"] = sorted(state_row["units"], key=lambda item: item["id"])
    state_row["triggers"] = sorted((_canonical_trigger(item) for item in state.triggers), key=lambda item: item["id"])
    snapshot = {
        "state": state_row,
        "turn_context": _canonical(context),
        "action_result": {"return_type": type(context).__name__, "returned_same_context": returned_same_context},
    }
    _validate_snapshot(snapshot, "generated_snapshot")
    return snapshot


def _canonical_trigger(trigger: Trigger) -> dict[str, Any]:
    return {
        "id": trigger.id, "owner_id": trigger.owner_id, "event_type": trigger.event_type,
        "condition": _canonical(trigger.condition),
        "effects": [
            {"effect_type": type(effect).__name__, "fields": _canonical(effect)}
            for effect in trigger.effects
        ],
        "max_triggers_per_action": trigger.max_triggers_per_action, "enabled": trigger.enabled,
    }


def _canonical(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _canonical(asdict(value))
    if isinstance(value, dict):
        return {str(key): _canonical(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if value is None or type(value) in {str, int, float, bool}:
        return value
    raise ValueError(f"Unsupported canonical observable type: {type(value).__name__}.")


def _validate_snapshot(snapshot: Any, label: str) -> None:
    issues: list[str] = []
    if not isinstance(snapshot, dict):
        raise ValueError(f"{label} must be an object.")
    if set(snapshot) != set(SNAPSHOT_FIELDS):
        issues.append(f"{label} omits or adds a required snapshot field.")
    state = snapshot.get("state")
    if not isinstance(state, dict) or set(state) != set(STATE_FIELDS):
        issues.append(f"{label}.state omits or adds a required BattleState field.")
    else:
        units = state.get("units")
        if not isinstance(units, list) or any(not isinstance(unit, dict) or set(unit) != set(UNIT_FIELDS) for unit in units):
            issues.append(f"{label}.state.units contains a malformed or incomplete Unit snapshot.")
        else:
            for unit in units:
                for collection in ("buffs", "debuffs"):
                    statuses = unit.get(collection)
                    if not isinstance(statuses, dict) or any(not isinstance(status, dict) or set(status) != set(BUFF_FIELDS) for status in statuses.values()):
                        issues.append(f"{label} contains a malformed or incomplete Buff snapshot.")
        events = state.get("pending_events")
        if not isinstance(events, list) or any(not isinstance(event, dict) or set(event) != set(EVENT_FIELDS) or not isinstance(event.get("data"), dict) for event in events):
            issues.append(f"{label} contains a malformed or incomplete Event snapshot.")
        triggers = state.get("triggers")
        if not isinstance(triggers, list) or any(not isinstance(trigger, dict) or set(trigger) != set(TRIGGER_FIELDS) or not isinstance(trigger.get("effects"), list) for trigger in triggers):
            issues.append(f"{label} contains a malformed or incomplete Trigger snapshot.")
    context = snapshot.get("turn_context")
    if not isinstance(context, dict) or set(context) != set(TURN_CONTEXT_FIELDS):
        issues.append(f"{label}.turn_context omits or adds a required field.")
    result = snapshot.get("action_result")
    if not isinstance(result, dict) or set(result) != set(ACTION_RESULT_FIELDS):
        issues.append(f"{label}.action_result omits or adds a required field.")
    if issues:
        raise ValueError("Tingyun effect-order snapshot validation failed:\n" + "\n".join(f"- {item}" for item in issues))


def _validate_against_template(value: Any, template: Any, label: str, issues: list[str]) -> bool:
    if isinstance(template, dict):
        if not isinstance(value, dict):
            issues.append(f"{label} must be an object.")
            return False
        if set(value) != set(template):
            issues.append(f"{label} must contain the exact required fields.")
            return False
        return all(_validate_against_template(value[key], expected, f"{label}.{key}", issues) for key, expected in template.items())
    if isinstance(template, list):
        if not isinstance(value, list) or len(value) != len(template):
            issues.append(f"{label} must be a list with exactly {len(template)} items.")
            return False
        return all(_validate_against_template(actual, expected, f"{label}[{index}]", issues) for index, (actual, expected) in enumerate(zip(value, template)))
    if template is None:
        if value is not None:
            issues.append(f"{label} must be null.")
            return False
        return True
    if type(template) is bool:
        if type(value) is not bool or value != template:
            issues.append(f"{label} must be {template!r} with exact type.")
            return False
        return True
    if type(template) in {int, float}:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value != template:
            issues.append(f"{label} must be the finite number {template!r}.")
            return False
        return True
    if not isinstance(value, str) or value != template:
        issues.append(f"{label} must be {template!r}.")
        return False
    return True


def _string(value: Any, label: str, issues: list[str]) -> None:
    if not isinstance(value, str) or not value:
        issues.append(f"{label} must be a non-empty string.")


def _string_list(value: Any, label: str, issues: list[str]) -> list[str]:
    if not isinstance(value, list) or not value:
        issues.append(f"{label} must be a non-empty list of non-empty strings.")
        return []
    if any(not isinstance(item, str) or not item for item in value):
        issues.append(f"{label} must contain only non-empty strings.")
        return []
    if len(set(value)) != len(value):
        issues.append(f"{label} must not contain duplicates.")
    return value


def _number(value: Any, label: str, issues: list[str]) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        issues.append(f"{label} must be a finite nonnegative number.")
        return None
    return value


def _reject_executable_schema(value: Any, label: str, issues: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z]", "", str(key).lower())
            if normalized in FORBIDDEN_KEYS:
                issues.append(f"{label}.{key} is an executable schema key and is forbidden.")
            _reject_executable_schema(child, f"{label}.{key}", issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_executable_schema(child, f"{label}[{index}]", issues)


def _json_digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def render_json(report: EffectOrderProofReport) -> str:
    return json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n"


def render_markdown(report: EffectOrderProofReport) -> str:
    lines = [
        "# Tingyun Ultimate Current-Contract Effect-Order Proof", "", f"> {report.warning}", "",
        f"Conclusion: `{report.conclusion}`  ",
        f"Derived generic readiness: `{report.derived_generic_readiness}`  ",
        f"Accepted-video readiness: `{report.accepted_video_binding_readiness}`", "",
        "## Pinned Sources", "", "| Source | Path | SHA-256 |", "|---|---|---|",
    ]
    for source in report.pinned_sources:
        lines.append(f"| {source.source_id} | `{source.path}` | `{source.sha256}` |")
    lines.extend(["", "## Current Observable Contract", ""])
    for name, values in report.observation_contract.items():
        lines.append(f"- {name}: `{', '.join(values) if values else 'none'}`")
    lines.extend(["", "## Synthetic Comparisons", "", "| Case | Energy | Max | Existing probe | Equal | Snapshot SHA-256 |", "|---|---:|---:|---|---|---|"])
    for item in report.comparison_results:
        lines.append(f"| {item.case_id} | {item.target_energy_before} | {item.target_max_energy} | `{str(item.existing_probe_buff).lower()}` | `{str(item.equal).lower()}` | `{item.order_a_snapshot_sha256}` |")
    lines.extend(["", "## Proof Boundary", ""])
    lines.extend(f"- {item}" for item in report.proof_boundaries)
    lines.extend(["", "- Release-game order known: `false`", "- Same-current-turn duration resolved: `false`", "- Accepted-video target: `null`", "- Accepted-video trace level: `null`", "- Simulator binding allowed: `false`"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the non-executable current-contract Tingyun effect-order proof.")
    parser.add_argument("--review", default=str(DEFAULT_REVIEW))
    parser.add_argument("--format", choices=["markdown", "json"], required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        data = load_json(args.review)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR Tingyun effect-order proof input failure: {exc}", file=sys.stderr)
        return 2
    try:
        report = build_report(data)
    except ValueError as exc:
        print(f"FAIL Tingyun effect-order proof validation: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR Tingyun effect-order proof could not run: {exc}", file=sys.stderr)
        return 2
    rendered = render_markdown(report) if args.format == "markdown" else render_json(report)
    try:
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except OSError as exc:
        print(f"ERROR Tingyun effect-order proof output failure: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
