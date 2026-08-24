import copy
import dataclasses
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

import hsr_axis_sim.real_bindings.registry as registry_module
from hsr_axis_sim.real_bindings.pela_skill_v0_1 import (
    DEFAULT_BINDING as PELA_BINDING,
    validate_binding as validate_pela_binding,
)
from hsr_axis_sim.real_bindings.registry import (
    DEFAULT_REGISTRY,
    ReviewedBindingRegistry,
    build_registry_audit_report,
    execute_reviewed_binding,
    get_reviewed_binding,
    list_reviewed_bindings,
    load_reviewed_binding_registry,
    render_json as render_registry_json,
    render_markdown as render_registry_markdown,
)
from hsr_axis_sim.real_bindings.tingyun_ultimate_v0_1 import (
    DEFAULT_ATOMS,
    DEFAULT_BINDING,
    DEFAULT_FIXTURE,
    build_audit_report,
    build_fixture_state,
    load_json,
    render_json,
    render_markdown,
    validate_binding,
)


BASE = Path(__file__).resolve().parents[1]
AUDITS = BASE / "data" / "manual_video_traces" / "real_binding_audits"
TINGYUN_ID = "tingyun_ultimate_partial_resource_interrupt_shell_v0_1"
PELA_ID = "pela_skill_partial_resource_target_dispel_shell_v0_1"
HISTORICAL_HASHES = {
    BASE / "real_bindings" / "registry_v0_1.json": "66c9d3ea8f502fd6ad6eec783dd41d44b1ee6fadb71516c862aaa0fd5c907858",
    AUDITS / "reviewed_binding_registry_v0_1.md": "64aa1d5cd13d83ec1c91066295abe83fa3fe86cb52033c0d54df103bdd6d8831",
    AUDITS / "reviewed_binding_registry_v0_1.json": "ae5ba824df5e9fc7d89fa44ea008e94a7e454eb7ce4456b22771db3644536117",
    AUDITS / "pela_skill_partial_v0_1.md": "cfe4b5286afbacbfec97f2ed9a1600f59d91d323c472438d6f80bef15879a7c1",
    AUDITS / "pela_skill_partial_v0_1.json": "4920c0e7468151f155651ad25f09686a5617fdaa91e4786a2bc8d16279b80f55",
}


def test_registry_v02_has_two_immutable_ordered_partial_bindings():
    registry = load_reviewed_binding_registry()
    handles = list_reviewed_bindings(registry)
    assert registry.registry_version == "0.2"
    assert [handle.binding_id for handle in handles] == [PELA_ID, TINGYUN_ID]
    assert all(handle.complete_game_skill is False for handle in handles)
    assert all(handle.complete_character_kit is False for handle in handles)
    assert all(handle.synthetic_only is True for handle in handles)
    assert all(handle.real_trace_executable is False for handle in handles)
    with pytest.raises(dataclasses.FrozenInstanceError):
        handles[1].binding_id = "forged"


def test_tingyun_fixture_exact_interrupt_result_and_no_combat_mutations():
    binding = load_json(DEFAULT_BINDING)
    fixture = load_json(DEFAULT_FIXTURE)
    state = build_fixture_state(fixture)
    before = {
        "sp": state.skill_points,
        "global_av": state.global_av,
        "av": {unit.id: unit.current_av for unit in state.units},
        "hp": {unit.id: unit.hp for unit in state.units},
        "toughness": {unit.id: unit.current_toughness for unit in state.units},
        "buffs": {unit.id: dict(unit.buffs) for unit in state.units},
    }
    context, extra = execute_reviewed_binding(
        TINGYUN_ID, state, [fixture["selected_target_id"]]
    )
    assert extra is None
    assert state.get_unit("tingyun").energy == 0
    assert state.get_unit("ally").energy == 90
    assert state.skill_points == before["sp"]
    assert state.global_av == before["global_av"]
    assert {unit.id: unit.current_av for unit in state.units} == before["av"]
    assert {unit.id: unit.hp for unit in state.units} == before["hp"]
    assert {unit.id: unit.current_toughness for unit in state.units} == before["toughness"]
    assert {unit.id: unit.buffs for unit in state.units} == before["buffs"]
    assert context.is_interrupt is True
    assert context.should_end_turn is False
    assert not any(log.startswith("normal_turn_end:") for log in state.logs)


def test_target_energy_clamp_and_insufficient_actor_energy_is_fail_safe():
    fixture = load_json(DEFAULT_FIXTURE)
    fixture["ally"]["energy"] = 80
    state = build_fixture_state(fixture)
    execute_reviewed_binding(TINGYUN_ID, state, ["ally"])
    assert state.get_unit("ally").energy == 100

    fixture["actor"]["energy"] = 129
    fixture["ally"]["energy"] = 40
    state = build_fixture_state(fixture)
    with pytest.raises(ValueError, match="insufficient energy"):
        execute_reviewed_binding(TINGYUN_ID, state, ["ally"])
    assert state.get_unit("ally").energy == 40
    assert state.get_unit("tingyun").energy == 129


def test_enemy_target_rejected():
    state = build_fixture_state(load_json(DEFAULT_FIXTURE))
    with pytest.raises(ValueError, match="not an ally"):
        execute_reviewed_binding(TINGYUN_ID, state, ["enemy"])


def test_handler_specific_validators_reject_wrong_tingyun_and_pela_data():
    atoms = load_json(DEFAULT_ATOMS)
    tingyun = load_json(DEFAULT_BINDING)
    tingyun["target_energy_restore"] = 49
    with pytest.raises(ValueError, match="target_energy_restore"):
        validate_binding(tingyun, atoms, DEFAULT_ATOMS)

    pela = load_json(PELA_BINDING)
    pela["actor_energy_gain"] = 29
    with pytest.raises(ValueError, match="actor_energy_gain"):
        validate_pela_binding(pela, atoms, DEFAULT_ATOMS)


def test_forged_handler_cannot_bypass_selected_binding_validation():
    registry = load_reviewed_binding_registry()
    handle = get_reviewed_binding(TINGYUN_ID, registry)
    forged = dataclasses.replace(handle, handler_key="pela_skill_partial_v0_1")
    forged_registry = ReviewedBindingRegistry(registry.registry_version, (forged,))
    state = build_fixture_state(load_json(DEFAULT_FIXTURE))
    with pytest.raises(ValueError, match="Pela Skill partial binding validation failed"):
        execute_reviewed_binding(TINGYUN_ID, state, ["ally"], registry=forged_registry)


def test_registry_handler_dispatch_revalidates_data_before_execution(monkeypatch):
    registry = load_reviewed_binding_registry()
    handle = get_reviewed_binding(TINGYUN_ID, registry)
    original_load_json = registry_module.load_json

    def altered_load_json(path):
        data = original_load_json(path)
        if Path(path) == handle.binding_data_path:
            data = copy.deepcopy(data)
            data["actor_energy_cost"] = 129
        return data

    monkeypatch.setattr(registry_module, "load_json", altered_load_json)
    state = build_fixture_state(load_json(DEFAULT_FIXTURE))
    with pytest.raises(ValueError, match="actor_energy_cost"):
        execute_reviewed_binding(TINGYUN_ID, state, ["ally"], registry=registry)
    assert state.get_unit("tingyun").energy == 130
    assert state.get_unit("ally").energy == 40


def test_v02_and_tingyun_audits_are_deterministic_and_committed():
    registry_report = build_registry_audit_report(load_reviewed_binding_registry())
    tingyun_report = build_audit_report(
        load_json(DEFAULT_BINDING),
        load_json(DEFAULT_ATOMS),
        load_json(DEFAULT_FIXTURE),
        DEFAULT_ATOMS,
    )
    assert render_registry_markdown(registry_report) == (
        AUDITS / "reviewed_binding_registry_v0_2.md"
    ).read_text(encoding="utf-8")
    assert render_registry_json(registry_report) == (
        AUDITS / "reviewed_binding_registry_v0_2.json"
    ).read_text(encoding="utf-8")
    assert render_markdown(tingyun_report) == (
        AUDITS / "tingyun_ultimate_partial_v0_1.md"
    ).read_text(encoding="utf-8")
    assert render_json(tingyun_report) == (
        AUDITS / "tingyun_ultimate_partial_v0_1.json"
    ).read_text(encoding="utf-8")


def test_registry_input_order_is_deterministic(tmp_path):
    data = load_json(DEFAULT_REGISTRY)
    data["entries"].reverse()
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    expected = render_registry_json(build_registry_audit_report(load_reviewed_binding_registry()))
    actual = render_registry_json(
        build_registry_audit_report(load_reviewed_binding_registry(path))
    )
    assert actual == expected


def test_historical_v01_and_pela_audits_are_byte_identical():
    for path, expected in HISTORICAL_HASHES.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected


def test_tingyun_cli_stdout_and_file_output(tmp_path):
    command = [sys.executable, "-m", "hsr_axis_sim.real_bindings.tingyun_ultimate_v0_1"]
    markdown = subprocess.run(
        command + ["--format", "markdown"], capture_output=True, text=True
    )
    output = tmp_path / "audit.json"
    json_result = subprocess.run(
        command + ["--format", "json", "--output", str(output)],
        capture_output=True,
        text=True,
    )
    assert markdown.returncode == json_result.returncode == 0
    assert markdown.stdout == (AUDITS / "tingyun_ultimate_partial_v0_1.md").read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8") == (AUDITS / "tingyun_ultimate_partial_v0_1.json").read_text(encoding="utf-8")
