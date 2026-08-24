from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.buffs import Buff
from hsr_axis_sim.sim.effects import AddBuff, AdvanceAction, DoesNotEndTurn, GainEnergy
from hsr_axis_sim.sim.enemy_ai import EnemyAIPlan, EnemyPatternStep
from hsr_axis_sim.sim.events import Event, Trigger
from hsr_axis_sim.sim.state import BattleState
from hsr_axis_sim.sim.timeline import Timeline
from hsr_axis_sim.sim.turn_context import TurnContext
from hsr_axis_sim.sim.ultimate_windows import execute_interrupt_action
from hsr_axis_sim.sim.unit import Unit


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
BASE = ROOT / "data" / "manual_video_traces"
DEFAULT_REVIEW = BASE / "normalized_character_facts" / "tingyun_ultimate_turn_entry_duration_gap_v0_1.json"
DEFAULT_BILIBILI_TEMPLATE = BASE / "normalized_character_facts" / "tingyun_ultimate_duration_bilibili_evidence_intake_template_v0_1.json"
CONCLUSION = "turn_entry_claim_normalized_current_engine_gap_confirmed_runtime_change_blocked"
WARNING = (
    "NON-EXECUTABLE DURATION EVIDENCE/GAP AUDIT. The turn-entry correction is accepted "
    "project-domain input pending independent frame verification; no runtime policy is selected."
)
PROJECT_PINS = {
    "timeline": ("sim/timeline.py", "511d7bebab2542cce45cec6a1ddbf1833c1664770bca5f76267f0561db6e0aa8"),
    "unit": ("sim/unit.py", "f4e100a12d1ae160fc58f9ef874fe188851d7f29284acef4c51273792f41eb62"),
    "buffs": ("sim/buffs.py", "7095d592ee4466396bcd2224d740aa780271e7f539cd9751949ee41c1f5837b5"),
    "effects": ("sim/effects.py", "3adb44ababa1725933c82a105706b388239d895a98f159db5c4691a12dfa9618"),
    "action": ("sim/action.py", "ad6994e79d8c8833304df4d4cc67ea84c07db988f4b9365840e0707dd5100f34"),
    "ultimate_windows": ("sim/ultimate_windows.py", "15b109774bfebd576d2614ec5bf1101563c40d87f0fab08fb4b9e11f45c98f53"),
    "state": ("sim/state.py", "7d91095f082e60da27730b713fed3b08e47d0f3c422c26ae18a507c63a8b236a"),
    "events": ("sim/events.py", "79e9a95d0788a1b87980f9de1fa58c48feccd34f4730a67798d6feb832f93525"),
    "turn_context": ("sim/turn_context.py", "a670688d83bf986c5b5edeb094124454d1e69c58c2953c2e11f79d133f68aeaa"),
    "002o_input": ("data/manual_video_traces/normalized_character_facts/tingyun_ultimate_damage_buff_semantic_readiness_v0_1.json", "29ece44c9bc051590c308f7b6774ce192a47e11ec5176cf5adf645336c3025f1"),
    "002o_report": ("data/manual_video_traces/real_binding_audits/tingyun_ultimate_damage_buff_semantic_readiness_v0_1.json", "d401cb85ff580d563ff44e415c1bd379957caa6e5a7a6f0353e68aef6e802a21"),
    "002p_tool": ("tools/trace_tingyun_ultimate_effect_order_irrelevance.py", "3154afec1a5e7cb2a3f162d7ab5c27d0dd356a6354e09046a7af1dc1e8cbf168"),
    "002p_input": ("data/manual_video_traces/normalized_character_facts/tingyun_ultimate_effect_order_irrelevance_review_v0_1.json", "ddb7cf48e45ae38c9ab9a11dd2dca65fdc1d21c7a2169e4a782b3eda72ea052a"),
    "002p_report": ("data/manual_video_traces/real_binding_audits/tingyun_ultimate_effect_order_irrelevance_v0_1.json", "493dddbe07de1a4e68fb30389c8efa1da9294e0d6d5fe2c26f3826d283879c4e"),
    "reviewed_registry": ("real_bindings/registry_v0_2.json", "0cd0c9f9d4594654aaae91fa834988a4a373674d8e6397e757165d4f76fd11b8"),
    "regression_manifest": ("data/regression_manifest.json", "acfb663d7dbd93f3b0bdba9838a8b2a0712df144da14aae513830c406f142a02"),
    "bilibili_template": ("data/manual_video_traces/normalized_character_facts/tingyun_ultimate_duration_bilibili_evidence_intake_template_v0_1.json", "bd59448abfeddbde1541fc025cd9a1dc411b7248f60909885e47a289f0e40391"),
}
LOCATOR_CONTRACT_DIGESTS = {
    "research_summary":"1ddd7f0bafdd22e49e16e356db93e3117321f5d345075c86c89456c867531860",
    "external_capture":"060d0f058cc8da0596e3ddd01ad5fae3f2faa8234308b1a55ba134a20c45d5b4",
    "engine_source_pins":"f8e65576c24aae1ca174de2d29cfce131406fb03356294e44b3d3f4e82c0f9be",
    "release_vs_engine":"9e268fbc57ce2396f447b008fc83e4c9995188115b04f8ec1c7404c6c1bcb1ec",
    "obsolete_notice":"f61c9491156a2139b45af70e925c8ddf43e5d17649e3bc3a56414fd7723f9979",
    "timeline":"001e428ffc2fbbda66eaaaf1b180ee8f16edebec41db26b8db5a274bdcd753ec",
    "unit":"c6ad7b7867689515ffae63964e4d1320ee83e31c820fca783728d29a2dd6dd14",
    "buffs":"8f8acc5fa643a3be4448cd711eced38d886bf02055396212484fb2eae5a10c55",
    "effects":"2fee3e016c49269b94186de4448cf5daed126f82508a506b46babbda0aa6d984",
    "action":"5c298054efbc91433f31edf9f1107d39f3645f30ea198fe3d4d70b608fdb86a7",
    "ultimate_windows":"447c2085269ca10dbe7a6288ec61066c341af943867e0a4527a7e43fb505b67c",
    "state":"20ec6b2150ff6ce25d32817df4c8ab93d947b4c928f30a3c72c3c8a70ccb5a32",
    "events":"2a46529615ba8a3bab06f2cff1ca02615fa06c3e26c0c026ad534d03fa67f2e4",
    "turn_context":"41eec6fc7d369b23613b8b1c2f195cd9b89afa8a2d336ac56eb5128486181172",
    "002o_input":"d2adbae973eb30990ad4981bd818c700dafc27d0c284b5cf7381c9a00533dabd",
    "002o_report":"8ba579afc413b24b05140a86d455a5cdc2b146e17b2260f09c537ca6ea050a7c",
    "002p_tool":"6af743647d0a946d038e002ec8834bde5c952700aa8f89f3cb2a3f10b39ce5a3",
    "002p_input":"f7846852a9eb7ffc0fdfea6241b59809ede20c976e579057786c232914262ba8",
    "002p_report":"a7f6c5caa53eeff725f96243d6c3fc1fedc256010c010c48532e421faed2fc1e",
    "reviewed_registry":"b67ed52c50bc986ad5755e3b19e112aeb0e5dabec1d47170084914cdce14371c",
    "regression_manifest":"ad708b079eb3f9692d9b5c5020e20785330e00db022fb2f120f6aa8e2c29252c",
    "bilibili_template":"df8234679debbba4a3300cb5c796b7fcd4ad7c0859245b16ba023f848362bd13",
}
CLAIM_CONTRACT_DIGESTS = {
    "duration_count_2":"93caffa59e88e189365bd36681999dd0790f07bfec2d1b8524f565f2b379336b",
    "turn_entry_settlement":"662e765406f69e1178d3541a0858e04336388d41886f8a96dd7123bc86b8f84f",
    "bilibili_candidate":"dd6f3a602d8393a889dfd4fae909c7c145acd29ada6214ae94441ed8c2512f73",
    "zero_counter_effect_lifetime":"ca2cefc8b0766e94891d94e8a06420bb0b6dfde82a85c7f1f78afc2f0b4b1c69",
    "extra_action_consumption":"f3576cb2e0dc2f4cd89e2621f5f3cfb44e42ffa889d96a5d8353799ad25e6d49",
    "extra_turn_consumption":"f157b3218729dd1c2ddd5f66c64d089b6c3e98f102c42b72cd74ffbcc704cbe0",
    "turn_started_event_order":"d92bd4a5402be3d55e10514a671ef4411808ae01d3c0b5c123e33a8797f52bc8",
    "same_id_refresh_active_turn":"e4ca6b55edbc59cb49f40764ab07cc48864109f3edf827dc67450b677ab9d72e",
}
CASE_CONTRACT_DIGESTS = {
    "applied_before_next_normal_turn":"0f4c75e0cfdb97b55e5b4f42ee55742633f60b85dd2e587a090e23588782bb08",
    "applied_during_active_normal_turn":"780e84e3c7ee013d5df9d5f3d3c1bb7081d031a7ddd9f015714f02e832dd40a3",
    "same_id_refresh_during_active_normal_turn":"577b5d6662ea1d97e5370ccb3c94f15886f22a524347fea3804946ff99e712e0",
    "non_ending_extra_action":"9f01a5042226895727f77412fb807c7bbd693583efc0f8dc9539d370fbd83650",
    "granted_extra_turn":"34bf4da7752da62ff9cf0a99708661831bb58a04474f78cf00d3be756d57ef16",
    "action_advanced_into_next_normal_turn":"9c417e54935d9aab575e8eb94b959ac792cc55b3c69cd6ff0868940df3989d16",
    "evidence_model_counter_transitions":"1e7a25aec6b9e04da2cd444fab62753306b072395fd49783218daf7a5a9cfc1e",
}
GAP_CONTRACT_DIGESTS = {
    "GAP_TARGET_NORMAL_TURN_TICK_BOUNDARY":"325ed637f03d71f6eeeca7ff33e39efe55bf8de409aff59121e41280a159f0b6",
    "GAP_ZERO_COUNTER_EFFECT_LIFETIME":"b3ebcd9ef6b9c7f06f6396399f887d92f9428ca791875664373a278c7e879ab4",
    "GAP_EXTRA_TURN_CONSUMPTION":"b0784a8e1abe6bcc7f4f98e4db7c3c8fe03112723f1547f7dca0a7fbea098ed7",
    "GAP_EXTRA_ACTION_CONSUMPTION":"22d70cdc419072d6ee2da506a1da1e59e4b3f4c55cb0348755ccc746469cd385",
    "GAP_TURN_STARTED_EVENT_ORDER":"d3cc309cd6c52ede33c3ec5c4d04993ce6312d29aee9a7917eccf46b50862b73",
    "GAP_SAME_ID_REFRESH_AT_ACTIVE_TURN":"109cb62e102d0bfbf5a2a1cc2a6e3a72dd8363a778c6cd43a55ccf3334c2fb8c",
    "GAP_GLOBAL_MIGRATION_IMPACT":"5481b4e1c6b2804390ed483c2502e7cf6bdb54558ad14774ee69edec64b58eed",
}
REFERENCE_PINS = {
    "research_summary": ("LUMEN_RESEARCH_HSR_AXIS_002Q_TINGYUN_DURATION.md", "ae1396289cc9434321567d93f39ebadc8e8e948e01a1fd60465e0fec8c1b9a3e"),
    "external_capture": ("REFERENCE_EXTERNAL_SOURCE_CAPTURE_HSR_AXIS_002Q.json", "aaf3e3a73c9b51f341afe0fb2857a86fe395e9415d1fa1f4365071660fbf7135"),
    "engine_source_pins": ("REFERENCE_CURRENT_ENGINE_SOURCE_PINS_HSR_AXIS_002Q.json", "2dd754b1e2997c48e9e5f7986589cad7ae6d1708ef48e1245cd784c8586bee91"),
    "release_vs_engine": ("REFERENCE_002Q_RELEASE_GAME_VS_ENGINE_CONTRACT.md", "e4237a2b546a5f8e89861f41502ee64d4e1916e3ac85181f0aa01ad6e206310d"),
    "obsolete_notice": ("OBSOLETE_OLD_002Q_NOTICE.md", "fe4e068f8f95bc68f40b8af4798524bf3a54584d428478ad02dac8d152e9fb7e"),
}
GAP_STATUSES = {
    "GAP_TARGET_NORMAL_TURN_TICK_BOUNDARY": "proven_current_engine_gap",
    "GAP_ZERO_COUNTER_EFFECT_LIFETIME": "unresolved",
    "GAP_EXTRA_TURN_CONSUMPTION": "unresolved",
    "GAP_EXTRA_ACTION_CONSUMPTION": "unresolved",
    "GAP_TURN_STARTED_EVENT_ORDER": "unresolved",
    "GAP_SAME_ID_REFRESH_AT_ACTIVE_TURN": "unresolved",
    "GAP_GLOBAL_MIGRATION_IMPACT": "unresolved",
}
CASE_IDS = {
    "applied_before_next_normal_turn",
    "applied_during_active_normal_turn",
    "same_id_refresh_during_active_normal_turn",
    "non_ending_extra_action",
    "granted_extra_turn",
    "action_advanced_into_next_normal_turn",
    "evidence_model_counter_transitions",
}
CLAIM_STATUSES = {
    "duration_count_2": "source_cross_checked",
    "turn_entry_settlement": "accepted_project_domain_correction_pending_independent_frame_verification",
    "bilibili_candidate": "candidate_identified_page_or_frames_not_retrieved",
    "zero_counter_effect_lifetime": "unresolved",
    "extra_action_consumption": "unresolved_not_infer_from_normal_turn_entry",
    "extra_turn_consumption": "unresolved_not_infer_from_normal_turn_entry",
    "turn_started_event_order": "unresolved",
    "same_id_refresh_active_turn": "unresolved",
}
CLAIM_FIELDS = {
    "claim_id", "claim_value", "claim_scope", "source_ids", "verification_status",
    "release_game_claim", "current_engine_behavior", "observable_boundary",
    "counter_transition", "effect_active_during_entered_turn", "extra_action_consumes",
    "extra_turn_consumes", "refresh_behavior", "event_order_relative_to_turn_started",
    "unresolved_fields", "simulator_binding_allowed",
}
ROOT_FIELDS = {
    "review_id", "version", "status", "supplied_references", "pinned_sources",
    "claims", "engine_audit", "gap_classifications", "boundary_cases", "conclusion",
    "old_002q_obsolete", "end_turn_dual_policy_selected", "release_game_duration_policy",
    "accepted_project_domain_boundary", "independent_frame_verification",
    "generic_binding_readiness", "accepted_video_binding_readiness",
    "accepted_video_target", "accepted_video_trace_level", "registry_expected_count",
    "manifest_expected_counts", "simulator_binding_allowed",
}
EXPECTED_MANIFEST_COUNTS = {"replays":12,"manual":1,"scenarios":2,"action_sequence_traces":1,"trace_evidence":2}
FORBIDDEN_KEYS = {
    "characterspec", "skillspec", "handlerkey", "bindingdatapath", "addbuffwiring",
    "executablepolicy", "executablebinding", "realtraceexecutable",
}


@dataclass(frozen=True)
class SourcePin:
    source_id: str
    scope: str
    path: str
    sha256: str
    locators: tuple[str, ...]


@dataclass(frozen=True)
class GapRecord:
    gap_id: str
    status: str
    summary: str


@dataclass(frozen=True)
class BoundaryResult:
    case_id: str
    evidence_settlement_boundary: str
    current_engine_mutation_boundary: str
    fully_decidable: bool
    unresolved_fields: tuple[str, ...]
    runtime_assertion_unsafe: bool
    counter_checkpoints: dict[str, Any]
    emitted_events: tuple[str, ...]
    state_digest: str


@dataclass(frozen=True)
class TurnEntryGapReport:
    review_id: str
    version: str
    warning: str
    conclusion: str
    supplied_references: tuple[SourcePin, ...]
    pinned_sources: tuple[SourcePin, ...]
    claims: tuple[dict[str, Any], ...]
    engine_audit: dict[str, Any]
    gaps: tuple[GapRecord, ...]
    boundary_matrix: tuple[BoundaryResult, ...]
    old_002q_obsolete: bool
    end_turn_dual_policy_selected: bool
    release_game_duration_policy: None
    accepted_project_domain_boundary: str
    independent_frame_verification: str
    generic_binding_readiness: str
    accepted_video_binding_readiness: str
    accepted_video_target: None
    accepted_video_trace_level: None
    simulator_binding_allowed: bool


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def build_report(data: Any, root: str | Path = ROOT, project_root: str | Path = PROJECT_ROOT) -> TurnEntryGapReport:
    issues: list[str] = []
    if not isinstance(data, dict):
        raise ValueError("Tingyun turn-entry duration audit validation failed:\n- review must be an object.")
    _reject_executable_schema(data, "review", issues)
    _reject_obsolete_policy_claims(data, "review", issues)
    if set(data) != ROOT_FIELDS:
        issues.append("review must contain the exact required root fields.")
    for field in ("review_id", "version", "status", "conclusion", "accepted_project_domain_boundary", "independent_frame_verification", "generic_binding_readiness", "accepted_video_binding_readiness"):
        _string(data.get(field), field, issues)
    if data.get("review_id") != "tingyun_ultimate_turn_entry_duration_gap_v0_1":
        issues.append("review_id must be 'tingyun_ultimate_turn_entry_duration_gap_v0_1'.")
    if data.get("version") != "0.1":
        issues.append("version must be '0.1'.")
    if data.get("status") != "non_executable_turn_entry_evidence_and_engine_gap_audit":
        issues.append("status is unsupported.")
    supplied = _source_pins(data.get("supplied_references"), REFERENCE_PINS, Path(project_root), "external_reference", issues)
    pinned = _source_pins(data.get("pinned_sources"), PROJECT_PINS, Path(root), "project_source", issues)
    claims = _claims(data.get("claims"), set(supplied) | set(pinned), issues)
    engine_audit = _engine_audit(data.get("engine_audit"), issues)
    gaps = _gaps(data.get("gap_classifications"), issues)
    cases = _boundary_cases(data.get("boundary_cases"), issues)
    _validate_conclusion(data, issues)
    _validate_preserved_inputs(Path(root), issues)
    if issues:
        raise ValueError("Tingyun turn-entry duration audit validation failed:\n" + "\n".join(f"- {item}" for item in issues))
    matrix = tuple(_run_case(case_id, cases[case_id]) for case_id in sorted(cases))
    if not any(item.case_id == "applied_before_next_normal_turn" and item.counter_checkpoints.get("after_normal_turn_entry") == 2 and item.counter_checkpoints.get("after_normal_turn_end") == 1 for item in matrix):
        raise ValueError("Tingyun turn-entry duration audit validation failed:\n- current engine end-turn tick was not reproduced.")
    return TurnEntryGapReport(
        review_id=data["review_id"], version=data["version"], warning=WARNING,
        conclusion=CONCLUSION,
        supplied_references=tuple(sorted(supplied.values(), key=lambda item: item.source_id)),
        pinned_sources=tuple(sorted(pinned.values(), key=lambda item: item.source_id)),
        claims=tuple(sorted((_canonical_claim(item) for item in claims), key=lambda item: item["claim_id"])),
        engine_audit=engine_audit,
        gaps=tuple(sorted(gaps.values(), key=lambda item: item.gap_id)),
        boundary_matrix=matrix,
        old_002q_obsolete=True, end_turn_dual_policy_selected=False,
        release_game_duration_policy=None,
        accepted_project_domain_boundary="target_normal_turn_entry",
        independent_frame_verification="pending",
        generic_binding_readiness="blocked_by_duration_semantics",
        accepted_video_binding_readiness="blocked_by_unknown_target_and_trace_level",
        accepted_video_target=None, accepted_video_trace_level=None,
        simulator_binding_allowed=False,
    )


def _source_pins(value: Any, expected: dict[str, tuple[str, str]], base: Path, scope: str, issues: list[str]) -> dict[str, SourcePin]:
    if not isinstance(value, list):
        issues.append(f"{scope} pins must be a list.")
        return {}
    result: dict[str, SourcePin] = {}
    paths: set[str] = set()
    for index, item in enumerate(value):
        label = f"{scope}[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{label} must be an object.")
            continue
        if set(item) != {"source_id", "path", "sha256", "locators"}:
            issues.append(f"{label} must contain exact source-pin fields.")
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
        contract = expected.get(source_id)
        if contract is None or path != contract[0] or digest != contract[1]:
            issues.append(f"{label} does not match the accepted source pin.")
            continue
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            issues.append(f"{label}.sha256 must be a lowercase SHA-256 digest.")
            continue
        try:
            actual = hashlib.sha256((base / path).read_bytes()).hexdigest()
        except OSError as exc:
            issues.append(f"{label} cannot read source: {exc}")
            continue
        if actual != digest:
            issues.append(f"{label}.sha256 is stale.")
            continue
        if _locator_digest(locators) != LOCATOR_CONTRACT_DIGESTS.get(source_id):
            issues.append(f"{label}.locators do not match the exact accepted locator contract.")
            continue
        paths.add(path)
        result[source_id] = SourcePin(source_id, scope, path, digest, tuple(sorted(locators)))
    if set(result) != set(expected):
        issues.append(f"{scope} pins must contain every required source.")
    return result


def _claims(value: Any, source_ids: set[str], issues: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        issues.append("claims must be a list.")
        return []
    result: list[dict[str, Any]] = []
    ids: set[str] = set()
    for index, item in enumerate(value):
        label = f"claims[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{label} must be an object.")
            continue
        if set(item) != CLAIM_FIELDS:
            issues.append(f"{label} must contain the exact claim fields.")
        claim_id = item.get("claim_id")
        _string(claim_id, f"{label}.claim_id", issues)
        if not isinstance(claim_id, str) or not claim_id:
            continue
        if claim_id in ids:
            issues.append(f"duplicate claim ID {claim_id!r}.")
            continue
        ids.add(claim_id)
        expected_status = CLAIM_STATUSES.get(claim_id)
        status = item.get("verification_status")
        if not isinstance(status, str) or not status:
            issues.append(f"{label}.verification_status must be a non-empty string.")
        elif expected_status is None or status != expected_status:
            issues.append(f"{label}.verification_status must preserve the exact accepted status.")
        for field in ("claim_scope", "release_game_claim", "current_engine_behavior", "observable_boundary"):
            _string(item.get(field), f"{label}.{field}", issues)
        _nullable_scalar(item.get("claim_value"), f"{label}.claim_value", issues)
        for field in ("counter_transition", "effect_active_during_entered_turn", "extra_action_consumes", "extra_turn_consumes", "refresh_behavior", "event_order_relative_to_turn_started"):
            _nullable_string(item.get(field), f"{label}.{field}", issues)
        claim_sources = _string_list(item.get("source_ids"), f"{label}.source_ids", issues)
        if any(source_id not in source_ids for source_id in claim_sources):
            issues.append(f"{label}.source_ids contains a dangling source reference.")
        _string_list(item.get("unresolved_fields"), f"{label}.unresolved_fields", issues, allow_empty=True)
        if item.get("simulator_binding_allowed") is not False:
            issues.append(f"{label}.simulator_binding_allowed must be false.")
        if _claim_is_safe_for_digest(item) and _claim_digest(item) != CLAIM_CONTRACT_DIGESTS.get(claim_id):
            issues.append(f"{label} does not match the exact accepted semantic contract.")
        result.append(item)
    if ids != set(CLAIM_STATUSES):
        issues.append("claims must contain the exact required claim IDs.")
    _validate_claim_semantics(result, issues)
    return result


def _validate_claim_semantics(claims: list[dict[str, Any]], issues: list[str]) -> None:
    rows = {item.get("claim_id"): item for item in claims if isinstance(item.get("claim_id"), str)}
    expected_values = {
        "duration_count_2": 2,
        "turn_entry_settlement": "target_normal_turn_entry",
        "bilibili_candidate": "BV1yz4y1t79s",
        "zero_counter_effect_lifetime": None,
        "extra_action_consumption": None,
        "extra_turn_consumption": None,
        "turn_started_event_order": None,
        "same_id_refresh_active_turn": None,
    }
    for claim_id, expected in expected_values.items():
        row = rows.get(claim_id)
        if row is not None and (type(row.get("claim_value")) is not type(expected) or row.get("claim_value") != expected):
            issues.append(f"claim {claim_id!r} must preserve value {expected!r} with exact type.")
    bilibili = rows.get("bilibili_candidate", {})
    if bilibili.get("counter_transition") is not None or bilibili.get("effect_active_during_entered_turn") is not None:
        issues.append("Bilibili candidate must not claim retrieved timestamp/frame observations.")
    for row in rows.values():
        release_claim = row.get("release_game_claim")
        if isinstance(release_claim, str):
            lowered = release_claim.lower()
            if "community simulator" in lowered and ("authority" in lowered or "proves" in lowered):
                issues.append("A community simulator must not be treated as release-game authority.")


def _engine_audit(value: Any, issues: list[str]) -> dict[str, Any]:
    expected = {
        "normal_turn_actor_selection": "Timeline._select_next_normal_actor",
        "normal_turn_started_emission": "Timeline.next_turn emits turn_started after selecting the normal actor",
        "extra_turn_started_emission": "Timeline.next_turn emits turn_started for a popped extra-turn actor",
        "target_normal_turn_tick_boundary": "Timeline.end_turn after a normal turn",
        "current_turn_expiration_boundary": "Timeline.end_turn for every unit after normal or extra turn end",
        "same_id_refresh_behavior": "_add_status directly refreshes remaining_turns when refresh_policy is refresh",
        "buff_application_turn_marker_present": False,
        "target_normal_turn_entry_tick_path_present": False,
        "current_engine_conforms_to_accepted_boundary": False,
    }
    _validate_template(value, expected, "engine_audit", issues)
    return expected


def _gaps(value: Any, issues: list[str]) -> dict[str, GapRecord]:
    if not isinstance(value, list):
        issues.append("gap_classifications must be a list.")
        return {}
    result: dict[str, GapRecord] = {}
    for index, item in enumerate(value):
        label = f"gap_classifications[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{label} must be an object.")
            continue
        if set(item) != {"gap_id", "status", "summary"}:
            issues.append(f"{label} must contain exact gap fields.")
        gap_id, status, summary = item.get("gap_id"), item.get("status"), item.get("summary")
        for field, raw in (("gap_id", gap_id), ("status", status), ("summary", summary)):
            _string(raw, f"{label}.{field}", issues)
        if not all(isinstance(raw, str) and raw for raw in (gap_id, status, summary)):
            continue
        if gap_id in result:
            issues.append(f"duplicate gap ID {gap_id!r}.")
            continue
        if GAP_STATUSES.get(gap_id) != status:
            issues.append(f"{label} has an inconsistent gap classification.")
            continue
        if _gap_is_safe_for_digest(item) and _contract_digest(item) != GAP_CONTRACT_DIGESTS.get(gap_id):
            issues.append(f"{label} does not match the exact accepted gap contract.")
        result[gap_id] = GapRecord(gap_id, status, summary)
    if set(result) != set(GAP_STATUSES):
        issues.append("gap_classifications must include every required gap.")
    return result


def _boundary_cases(value: Any, issues: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        issues.append("boundary_cases must be a list.")
        return {}
    result: dict[str, dict[str, Any]] = {}
    required = {"case_id", "evidence_settlement_boundary", "current_engine_mutation_boundary", "fully_decidable", "unresolved_fields", "runtime_assertion_unsafe"}
    for index, item in enumerate(value):
        label = f"boundary_cases[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{label} must be an object.")
            continue
        if set(item) != required:
            issues.append(f"{label} must contain exact case fields.")
        case_id = item.get("case_id")
        _string(case_id, f"{label}.case_id", issues)
        for field in ("evidence_settlement_boundary", "current_engine_mutation_boundary"):
            _string(item.get(field), f"{label}.{field}", issues)
        if type(item.get("fully_decidable")) is not bool:
            issues.append(f"{label}.fully_decidable must be an exact boolean.")
        if item.get("runtime_assertion_unsafe") is not True:
            issues.append(f"{label}.runtime_assertion_unsafe must be true.")
        unresolved = _string_list(item.get("unresolved_fields"), f"{label}.unresolved_fields", issues, allow_empty=True)
        if not isinstance(case_id, str) or not case_id:
            continue
        if case_id in result:
            issues.append(f"duplicate boundary case ID {case_id!r}.")
            continue
        if case_id not in CASE_IDS:
            issues.append(f"unsupported boundary case ID {case_id!r}.")
            continue
        if item.get("evidence_settlement_boundary") != "target_normal_turn_entry":
            issues.append(f"{label} must preserve target-normal-turn-entry settlement.")
        if item.get("current_engine_mutation_boundary") != "target_normal_turn_end_or_absent_for_non_normal_turn_boundary":
            issues.append(f"{label} must preserve the audited current-engine boundary.")
        if item.get("fully_decidable") is not False or not unresolved:
            issues.append(f"{label} must retain explicit unresolved semantics.")
        if _case_is_safe_for_digest(item) and _case_digest(item) != CASE_CONTRACT_DIGESTS.get(case_id):
            issues.append(f"{label} does not match the exact accepted boundary-case contract.")
        result[case_id] = item
    if set(result) != CASE_IDS:
        issues.append("boundary_cases must contain the exact required matrix cases.")
    return result


def _validate_conclusion(data: dict[str, Any], issues: list[str]) -> None:
    expected = {
        "conclusion": CONCLUSION,
        "old_002q_obsolete": True,
        "end_turn_dual_policy_selected": False,
        "release_game_duration_policy": None,
        "accepted_project_domain_boundary": "target_normal_turn_entry",
        "independent_frame_verification": "pending",
        "generic_binding_readiness": "blocked_by_duration_semantics",
        "accepted_video_binding_readiness": "blocked_by_unknown_target_and_trace_level",
        "accepted_video_target": None,
        "accepted_video_trace_level": None,
        "registry_expected_count": 2,
        "simulator_binding_allowed": False,
    }
    for field, expected_value in expected.items():
        actual = data.get(field)
        if type(actual) is not type(expected_value) or actual != expected_value:
            issues.append(f"{field} must be {expected_value!r} with exact type.")
    _validate_template(data.get("manifest_expected_counts"), EXPECTED_MANIFEST_COUNTS, "manifest_expected_counts", issues)


def _validate_preserved_inputs(root: Path, issues: list[str]) -> None:
    try:
        template = load_json(root / PROJECT_PINS["bilibili_template"][0])
        _validate_bilibili_template(template, issues)
        registry = load_json(root / PROJECT_PINS["reviewed_registry"][0])
        entries = registry.get("entries")
        if registry.get("registry_version") != "0.2" or not isinstance(entries, list) or len(entries) != 2:
            issues.append("reviewed registry changed.")
        manifest = load_json(root / PROJECT_PINS["regression_manifest"][0])
        groups = manifest.get("groups")
        if not isinstance(groups, dict):
            issues.append("regression manifest groups must be an object.")
        else:
            counts = {key: len(rows) for key, rows in groups.items() if isinstance(key, str) and isinstance(rows, list)}
            if counts != EXPECTED_MANIFEST_COUNTS:
                issues.append("regression manifest counts changed.")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        issues.append(f"preserved-input validation failed: {exc}")


def _validate_bilibili_template(value: Any, issues: list[str]) -> None:
    if not isinstance(value, dict):
        issues.append("Bilibili evidence template must be an object.")
        return
    required_null = {
        "uploader", "publication_date", "game_version_or_build", "timestamp_start_seconds",
        "timestamp_end_seconds", "target_identity_evidence", "target_active_turn_state_evidence",
        "visible_buff_icon_or_counter_evidence", "damage_based_observable",
        "transition_2_to_1_observation", "transition_1_to_0_observation",
        "effect_active_during_entered_turn_observation", "extra_action_classification",
        "extra_turn_classification",
    }
    if value.get("verification_status") != "candidate_identified_page_or_frames_not_retrieved":
        issues.append("Bilibili candidate verification status was overstated.")
    if value.get("bvid") != "BV1yz4y1t79s" or value.get("direct_url") != "https://www.bilibili.com/video/BV1yz4y1t79s":
        issues.append("Bilibili candidate identity changed.")
    for field in required_null:
        if value.get(field) is not None:
            issues.append(f"Bilibili template {field} must remain null pending evidence.")
    for field in ("frame_range", "target_normal_turn_entry_boundaries"):
        if value.get(field) != []:
            issues.append(f"Bilibili template {field} must remain empty pending evidence.")
    if value.get("simulator_binding_allowed") is not False:
        issues.append("Bilibili template simulator_binding_allowed must be false.")


def _run_case(case_id: str, contract: dict[str, Any]) -> BoundaryResult:
    checkpoints, events, state = _observe_current_engine(case_id)
    return BoundaryResult(
        case_id=case_id,
        evidence_settlement_boundary=contract["evidence_settlement_boundary"],
        current_engine_mutation_boundary=contract["current_engine_mutation_boundary"],
        fully_decidable=False,
        unresolved_fields=tuple(sorted(contract["unresolved_fields"])),
        runtime_assertion_unsafe=True,
        counter_checkpoints=checkpoints,
        emitted_events=tuple(events),
        state_digest=_state_digest(state),
    )


def _observe_current_engine(case_id: str) -> tuple[dict[str, Any], list[str], BattleState]:
    state = _base_state()
    target = state.get_unit("target")
    checkpoints: dict[str, Any] = {}
    if case_id == "applied_before_next_normal_turn":
        _apply_probe_interrupt(state)
        checkpoints["after_application"] = _counter(target)
        turn = Timeline.next_turn(state)
        checkpoints["after_normal_turn_entry"] = _counter(target)
        Timeline.end_turn(state, turn)
        checkpoints["after_normal_turn_end"] = _counter(target)
    elif case_id == "applied_during_active_normal_turn":
        turn = Timeline.next_turn(state)
        checkpoints["before_application_after_entry"] = _counter(target)
        _apply_probe_interrupt(state)
        checkpoints["after_interrupt_application"] = _counter(target)
        Timeline.end_turn(state, turn)
        checkpoints["after_active_normal_turn_end"] = _counter(target)
    elif case_id == "same_id_refresh_during_active_normal_turn":
        _put_probe(target, 1)
        turn = Timeline.next_turn(state)
        checkpoints["after_entry_before_refresh"] = _counter(target)
        _apply_probe_interrupt(state)
        checkpoints["after_same_id_refresh"] = _counter(target)
        Timeline.end_turn(state, turn)
        checkpoints["after_active_normal_turn_end"] = _counter(target)
    elif case_id == "non_ending_extra_action":
        _put_probe(target, 2)
        context = TurnContext(actor_id="target", should_end_turn=False, actions_taken=["prior"])
        Action("synthetic_non_ending_extra_action", "Synthetic Non-ending Extra Action", "target", effects=[DoesNotEndTurn()], ends_turn=False).execute(state, context)
        checkpoints["after_non_ending_action"] = _counter(target)
    elif case_id == "granted_extra_turn":
        _put_probe(target, 2)
        state.extra_turn_stack.append("target")
        turn = Timeline.next_turn(state)
        checkpoints["after_extra_turn_entry"] = _counter(target)
        Timeline.end_turn(state, turn)
        checkpoints["after_extra_turn_end"] = _counter(target)
    elif case_id == "action_advanced_into_next_normal_turn":
        _put_probe(target, 2)
        target.current_av = 50
        Action("synthetic_advance", "Synthetic Advance", "tingyun", ["target"], [AdvanceAction(percent=1, target_ref="action_targets")], False).execute(state, TurnContext("tingyun", is_interrupt=True, should_end_turn=False))
        checkpoints["after_action_advance"] = _counter(target)
        turn = Timeline.next_turn(state)
        checkpoints["after_normal_turn_entry"] = _counter(target)
        Timeline.end_turn(state, turn)
        checkpoints["after_normal_turn_end"] = _counter(target)
    else:
        _put_probe(target, 1)
        checkpoints["evidence_model_candidate_transition_2_to_1"] = "target_normal_turn_entry"
        checkpoints["evidence_model_candidate_transition_1_to_0"] = "target_normal_turn_entry"
        turn = Timeline.next_turn(state)
        checkpoints["current_engine_after_entry_from_1"] = _counter(target)
        Timeline.end_turn(state, turn)
        checkpoints["current_engine_after_end_from_1"] = _counter(target)
    events = [event.type for event in state.pending_events]
    return checkpoints, events, state


def _base_state() -> BattleState:
    units = [
        Unit("target", "Target", "ally", 100, current_av=0, energy=31, max_energy=120, hp=701, max_hp=900, atk=444, defense=222),
        Unit("tingyun", "Tingyun", "ally", 110, current_av=30, energy=130, max_energy=130, hp=630, max_hp=800, atk=500, defense=200),
        Unit("observer", "Observer", "ally", 95, current_av=60, energy=17, max_energy=100, hp=555, max_hp=700, atk=321, defense=333),
        Unit("enemy", "Enemy", "enemy", 90, current_av=80, energy=0, max_energy=100, hp=1200, max_hp=1500, max_toughness=120, current_toughness=77, weaknesses=["lightning"]),
    ]
    state = BattleState(
        units, global_av=19.5, skill_points=3, max_skill_points=7,
        logs=["preexisting:duration-audit"],
        pending_events=[Event("preexisting_event", {"marker":"duration-audit"})],
        trigger_fire_counts={"preexisting":2}, event_dispatch_count=4,
        enemy_ai_cursors={"enemy":1},
    )
    state.get_unit("target").buffs["unrelated_buff"] = Buff("unrelated_buff", "Unrelated Buff", "target", "observer", "buff", "target_normal_turns", 3, data={"marker":1})
    state.get_unit("target").debuffs["unrelated_debuff"] = Buff("unrelated_debuff", "Unrelated Debuff", "target", "enemy", "debuff", "target_normal_turns", 2, data={"marker":2})
    state.triggers = [Trigger("turn_started_probe", "observer", "turn_started", {"type":"always"}, [GainEnergy(amount=1, target_ids=["observer"])], 10, True)]
    state.enemy_ai_plans["enemy"] = EnemyAIPlan([EnemyPatternStep("enemy_probe_skill")], True)
    return state


def _apply_probe_interrupt(state: BattleState) -> None:
    action = Action(
        "synthetic_tingyun_duration_probe", "Synthetic Tingyun Duration Probe", "tingyun", ["target"],
        [AddBuff(id="synthetic_tingyun_duration_probe", name="Synthetic Duration Probe", target_ref="action_targets", duration_type="target_normal_turns", remaining_turns=2, data={"audit_only":True})],
        False,
    )
    execute_interrupt_action(state, action)


def _put_probe(target: Unit, remaining: int) -> None:
    target.buffs["synthetic_tingyun_duration_probe"] = Buff(
        "synthetic_tingyun_duration_probe", "Synthetic Duration Probe", "target", "tingyun",
        "buff", "target_normal_turns", remaining, data={"audit_only":True},
    )


def _counter(target: Unit) -> int | None:
    buff = target.get_buff("synthetic_tingyun_duration_probe")
    return None if buff is None else buff.remaining_turns


def _state_digest(state: BattleState) -> str:
    value = {
        "global_av":state.global_av, "skill_points":state.skill_points,
        "extra_turn_stack":state.extra_turn_stack, "logs":state.logs,
        "events":[asdict(event) for event in state.pending_events],
        "trigger_fire_counts":state.trigger_fire_counts, "event_dispatch_count":state.event_dispatch_count,
        "triggers":[{
            "id":trigger.id, "owner_id":trigger.owner_id, "event_type":trigger.event_type,
            "condition":trigger.condition, "effect_types":[type(effect).__name__ for effect in trigger.effects],
            "max_triggers_per_action":trigger.max_triggers_per_action, "enabled":trigger.enabled,
        } for trigger in state.triggers],
        "enemy_ai_plans":{key:asdict(value) for key, value in state.enemy_ai_plans.items()},
        "enemy_ai_cursors":state.enemy_ai_cursors,
        "units":[asdict(unit) for unit in sorted(state.units, key=lambda item:item.id)],
    }
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _locator_digest(locators: list[str]) -> str:
    return _contract_digest(sorted(locators))


def _contract_digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _claim_is_safe_for_digest(item: dict[str, Any]) -> bool:
    if set(item) != CLAIM_FIELDS:
        return False
    if any(not isinstance(item.get(field), str) or not item[field] for field in ("claim_id", "claim_scope", "verification_status", "release_game_claim", "current_engine_behavior", "observable_boundary")):
        return False
    value = item.get("claim_value")
    if not (value is None or type(value) in {str, int, float}):
        return False
    if isinstance(value, float) and not math.isfinite(value):
        return False
    for field in ("counter_transition", "effect_active_during_entered_turn", "extra_action_consumes", "extra_turn_consumes", "refresh_behavior", "event_order_relative_to_turn_started"):
        if item.get(field) is not None and (not isinstance(item[field], str) or not item[field]):
            return False
    for field in ("source_ids", "unresolved_fields"):
        value = item.get(field)
        if not isinstance(value, list) or any(not isinstance(entry, str) or not entry for entry in value) or len(set(value)) != len(value):
            return False
    return item.get("simulator_binding_allowed") is False


def _claim_digest(item: dict[str, Any]) -> str:
    normalized = dict(item)
    normalized["source_ids"] = sorted(normalized["source_ids"])
    normalized["unresolved_fields"] = sorted(normalized["unresolved_fields"])
    return _contract_digest(normalized)


def _case_is_safe_for_digest(item: dict[str, Any]) -> bool:
    required = {"case_id", "evidence_settlement_boundary", "current_engine_mutation_boundary", "fully_decidable", "unresolved_fields", "runtime_assertion_unsafe"}
    return (
        set(item) == required
        and all(isinstance(item.get(field), str) and item[field] for field in ("case_id", "evidence_settlement_boundary", "current_engine_mutation_boundary"))
        and type(item.get("fully_decidable")) is bool
        and type(item.get("runtime_assertion_unsafe")) is bool
        and isinstance(item.get("unresolved_fields"), list)
        and all(isinstance(entry, str) and entry for entry in item["unresolved_fields"])
        and len(set(item["unresolved_fields"])) == len(item["unresolved_fields"])
    )


def _case_digest(item: dict[str, Any]) -> str:
    normalized = dict(item)
    normalized["unresolved_fields"] = sorted(normalized["unresolved_fields"])
    return _contract_digest(normalized)


def _gap_is_safe_for_digest(item: dict[str, Any]) -> bool:
    return set(item) == {"gap_id", "status", "summary"} and all(isinstance(item.get(field), str) and item[field] for field in ("gap_id", "status", "summary"))


def _validate_template(value: Any, expected: Any, label: str, issues: list[str]) -> bool:
    if isinstance(expected, dict):
        if not isinstance(value, dict):
            issues.append(f"{label} must be an object.")
            return False
        if set(value) != set(expected):
            issues.append(f"{label} must contain exact required fields.")
            return False
        valid = True
        for key, expected_value in expected.items():
            if not _validate_template(value[key], expected_value, f"{label}.{key}", issues):
                valid = False
        return valid
    if expected is None:
        if value is not None:
            issues.append(f"{label} must be null.")
            return False
        return True
    if type(expected) is bool:
        if type(value) is not bool or value != expected:
            issues.append(f"{label} must be {expected!r} with exact type.")
            return False
        return True
    if type(expected) in {int, float}:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value != expected:
            issues.append(f"{label} must be finite number {expected!r}.")
            return False
        return True
    if not isinstance(value, str) or value != expected:
        issues.append(f"{label} must be {expected!r}.")
        return False
    return True


def _nullable_scalar(value: Any, label: str, issues: list[str]) -> None:
    if value is None or (type(value) in {str, int, float} and not (isinstance(value, float) and not math.isfinite(value))):
        return
    issues.append(f"{label} must be a string, finite number, or null.")


def _nullable_string(value: Any, label: str, issues: list[str]) -> None:
    if value is not None and (not isinstance(value, str) or not value):
        issues.append(f"{label} must be a non-empty string or null.")


def _string(value: Any, label: str, issues: list[str]) -> None:
    if not isinstance(value, str) or not value:
        issues.append(f"{label} must be a non-empty string.")


def _string_list(value: Any, label: str, issues: list[str], allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        issues.append(f"{label} must be a {'list' if allow_empty else 'non-empty list'} of non-empty strings.")
        return []
    if any(not isinstance(item, str) or not item for item in value):
        issues.append(f"{label} must contain only non-empty strings.")
        return []
    if len(set(value)) != len(value):
        issues.append(f"{label} must not contain duplicates.")
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


def _reject_obsolete_policy_claims(value: Any, label: str, issues: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _reject_obsolete_policy_claims(child, f"{label}.{key}", issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_obsolete_policy_claims(child, f"{label}[{index}]", issues)
    elif isinstance(value, str) and value.strip().lower() in {"policy a", "policy b"}:
        issues.append(f"{label} includes an obsolete end-turn Policy A/Policy B assertion.")


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {key:_canonical(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    return value


def _canonical_claim(value: dict[str, Any]) -> dict[str, Any]:
    result = _canonical(value)
    result["source_ids"] = sorted(result["source_ids"])
    result["unresolved_fields"] = sorted(result["unresolved_fields"])
    return result


def render_json(report: TurnEntryGapReport) -> str:
    return json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n"


def render_markdown(report: TurnEntryGapReport) -> str:
    lines = [
        "# Tingyun Ultimate Turn-Entry Duration Evidence and Engine-Gap Audit", "", f"> {report.warning}", "",
        f"Conclusion: `{report.conclusion}`  ",
        f"Accepted project-domain boundary: `{report.accepted_project_domain_boundary}`  ",
        f"Generic readiness: `{report.generic_binding_readiness}`", "",
        "## Evidence Status", "", "| Claim | Value | Status |", "|---|---|---|",
    ]
    for claim in report.claims:
        lines.append(f"| {claim['claim_id']} | `{json.dumps(claim['claim_value'], ensure_ascii=False)}` | {claim['verification_status']} |")
    lines.extend(["", "## Current Engine Audit", ""])
    lines.extend(f"- {key}: `{json.dumps(value)}`" for key, value in report.engine_audit.items())
    lines.extend(["", "## Gap Classification", "", "| Gap | Status | Summary |", "|---|---|---|"])
    for gap in report.gaps:
        lines.append(f"| {gap.gap_id} | {gap.status} | {gap.summary} |")
    lines.extend(["", "## Synthetic Boundary Matrix", "", "| Case | Evidence boundary | Current engine boundary | Decidable | Unsafe runtime assertion | Checkpoints |", "|---|---|---|---|---|---|"])
    for case in report.boundary_matrix:
        lines.append(f"| {case.case_id} | {case.evidence_settlement_boundary} | {case.current_engine_mutation_boundary} | `{str(case.fully_decidable).lower()}` | `{str(case.runtime_assertion_unsafe).lower()}` | `{json.dumps(case.counter_checkpoints, sort_keys=True)}` |")
    lines.extend(["", "## Runtime Boundary", "", "- Old 002Q obsolete: `true`", "- End-turn dual policy selected: `false`", "- Executable release-game duration policy: `null`", "- Independent frame verification: `pending`", f"- Accepted-video readiness: `{report.accepted_video_binding_readiness}`", "- Accepted-video target: `null`", "- Accepted-video trace level: `null`", "- Simulator binding allowed: `false`"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the non-executable Tingyun turn-entry duration evidence/gap audit.")
    parser.add_argument("--review", default=str(DEFAULT_REVIEW))
    parser.add_argument("--format", choices=["markdown", "json"], required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        data = load_json(args.review)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR Tingyun turn-entry duration input failure: {exc}", file=sys.stderr)
        return 2
    try:
        report = build_report(data)
    except ValueError as exc:
        print(f"FAIL Tingyun turn-entry duration validation: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR Tingyun turn-entry duration audit could not run: {exc}", file=sys.stderr)
        return 2
    rendered = render_markdown(report) if args.format == "markdown" else render_json(report)
    try:
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except OSError as exc:
        print(f"ERROR Tingyun turn-entry duration output failure: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
