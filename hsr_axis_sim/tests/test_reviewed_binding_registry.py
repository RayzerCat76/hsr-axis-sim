import copy
import dataclasses
import inspect
import json
import subprocess
import sys
from pathlib import Path

from hsr_axis_sim.real_bindings.pela_skill_v0_1 import DEFAULT_FIXTURE, build_fixture_state, load_json
from hsr_axis_sim.real_bindings.registry import *
from hsr_axis_sim.sim import TurnContext

BASE=Path(__file__).resolve().parents[1]
REGISTRY=BASE/"real_bindings/registry_v0_2.json"
HISTORICAL_REGISTRY=BASE/"real_bindings/registry_v0_1.json"
AUDITS=BASE/"data/manual_video_traces/real_binding_audits"
BINDING_ID="pela_skill_partial_resource_target_dispel_shell_v0_1"

def write_registry(tmp_path,data,name="registry.json"):
    path=tmp_path/name; path.write_text(json.dumps(data),encoding="utf-8"); return path
def expect_load_error(tmp_path,data,text):
    try: load_reviewed_binding_registry(write_registry(tmp_path,data))
    except ValueError as exc: assert text in str(exc)
    else: raise AssertionError("Expected registry validation failure")

def test_load_list_get_and_immutable_handle():
    registry=load_reviewed_binding_registry(REGISTRY); assert registry.registry_version=="0.2"; assert len(list_reviewed_bindings(registry))==2
    handle=get_reviewed_binding(BINDING_ID,registry); assert handle.binding_id==BINDING_ID; assert isinstance(handle.source_atomic_fact_ids,tuple)
    try: handle.binding_id="changed"
    except dataclasses.FrozenInstanceError: pass
    else: raise AssertionError("Expected immutable handle")
    try: get_reviewed_binding("unknown",registry)
    except ValueError as exc: assert "Unknown reviewed binding" in str(exc)
    else: raise AssertionError("Expected unknown binding failure")

def test_duplicate_unknown_handler_and_binding_type_rejected(tmp_path):
    data=load_json(REGISTRY); data["entries"].append(copy.deepcopy(data["entries"][0])); expect_load_error(tmp_path,data,"duplicate registry entry")
    data=load_json(REGISTRY); data["entries"][0]["registry_entry_id"]="other"; data["entries"].append(copy.deepcopy(data["entries"][0])); data["entries"][1]["registry_entry_id"]="third"; expect_load_error(tmp_path,data,"duplicate binding")
    data=load_json(REGISTRY); data["entries"][0]["handler_key"]="arbitrary.module"; expect_load_error(tmp_path,data,"unknown handler")
    data=load_json(REGISTRY); data["entries"][0]["binding_type"]="full_kit"; expect_load_error(tmp_path,data,"unsupported binding type")

def test_paths_missing_files_metadata_and_digest_rejected(tmp_path):
    data=load_json(REGISTRY); data["entries"][0]["binding_data_path"]="../outside.json"; expect_load_error(tmp_path,data,"escapes package root")
    data=load_json(REGISTRY); data["entries"][0]["binding_data_path"]="real_bindings/data/missing.json"; expect_load_error(tmp_path,data,"does not exist")
    data=load_json(REGISTRY); data["entries"][0]["actor_id"]="tingyun"; expect_load_error(tmp_path,data,"metadata mismatch")
    data=load_json(REGISTRY); data["entries"][0]["accepted_atomic_fact_sha256"]="0"*64; expect_load_error(tmp_path,data,"digest mismatch")

def test_partial_synthetic_real_trace_and_semantics_guards(tmp_path):
    for field,value,text in [("complete_game_skill",True,"complete_game_skill"),("complete_character_kit",True,"complete_character_kit"),("synthetic_only",False,"synthetic_only"),("real_trace_executable",True,"real_trace_executable"),("damage_semantics_status","implemented","damage_semantics_status"),("toughness_semantics_status","implemented","toughness_semantics_status")]:
        data=load_json(REGISTRY); data["entries"][0][field]=value; expect_load_error(tmp_path,data,text)

def test_registry_execution_matches_accepted_fixture():
    registry=load_reviewed_binding_registry(REGISTRY); state=build_fixture_state(load_json(DEFAULT_FIXTURE)); actor=state.get_unit("pela"); target=state.get_unit("enemy")
    hp,toughness=target.hp,target.current_toughness; context,removed=execute_reviewed_binding(BINDING_ID,state,["enemy"],TurnContext(actor_id="pela"),registry)
    assert removed=="alpha_guard"; assert state.skill_points==2; assert actor.energy==40; assert target.hp==hp; assert target.current_toughness==toughness
    assert context.should_end_turn and "normal_turn_end:pela" in state.logs

def test_registry_execution_preserves_sp_and_target_failures():
    registry=load_reviewed_binding_registry(REGISTRY); fixture=load_json(DEFAULT_FIXTURE); fixture["skill_points"]=0; state=build_fixture_state(fixture)
    try: execute_reviewed_binding(BINDING_ID,state,["enemy"],registry=registry)
    except ValueError as exc: assert "Insufficient skill points" in str(exc)
    else: raise AssertionError("Expected SP failure")
    state=build_fixture_state(load_json(DEFAULT_FIXTURE))
    try: execute_reviewed_binding(BINDING_ID,state,["pela"],registry=registry)
    except ValueError as exc: assert "not an enemy" in str(exc)
    else: raise AssertionError("Expected target failure")

def test_reports_order_determinism_and_committed_bytes(tmp_path):
    registry=load_reviewed_binding_registry(REGISTRY); report=build_registry_audit_report(registry)
    assert render_markdown(report)==(AUDITS/"reviewed_binding_registry_v0_2.md").read_text(encoding="utf-8")
    assert render_json(report)==(AUDITS/"reviewed_binding_registry_v0_2.json").read_text(encoding="utf-8")
    data=load_json(REGISTRY); data["entries"].reverse(); assert render_json(build_registry_audit_report(load_reviewed_binding_registry(write_registry(tmp_path,data))))==render_json(report)

def test_cli_stdout_output_and_exit_codes(tmp_path):
    cmd=[sys.executable,"-m","hsr_axis_sim.real_bindings.registry"]
    stdout=subprocess.run(cmd+["--format","markdown"],capture_output=True,text=True); output=tmp_path/"audit.json"; written=subprocess.run(cmd+["--format","json","--output",str(output)],capture_output=True,text=True)
    bad=load_json(REGISTRY); bad["entries"][0]["complete_game_skill"]=True; bad_path=write_registry(tmp_path,bad,"bad.json")
    invalid=subprocess.run(cmd+["--registry",str(bad_path),"--format","json"],capture_output=True,text=True); unreadable=subprocess.run(cmd+["--registry",str(tmp_path/"missing.json"),"--format","json"],capture_output=True,text=True)
    assert stdout.returncode==written.returncode==0; assert stdout.stdout==(AUDITS/"reviewed_binding_registry_v0_2.md").read_text(encoding="utf-8"); assert output.read_text(encoding="utf-8")==render_json(build_registry_audit_report(load_reviewed_binding_registry()))
    assert invalid.returncode==1; assert unreadable.returncode==2; assert "Traceback" not in invalid.stderr+unreadable.stderr

def test_strict_root_and_entry_scalar_types(tmp_path):
    for data,text in [([],"must contain a JSON object"), ({"entries":[]},"registry_version"), ({"registry_version":"" ,"entries":[]},"registry_version"), ({"registry_version":0,"entries":[]},"registry_version"), ({"registry_version":"0.1","entries":{}},"entries must be a list")]:
        expect_load_error(tmp_path,data,text)
    for field,value in [("registry_entry_id",{}),("binding_id",{}),("registry_entry_id",""),("binding_id","")]:
        data=load_json(REGISTRY); data["entries"][0][field]=value; expect_load_error(tmp_path,data,f"{field} must be a non-empty string")
    data=load_json(REGISTRY); data["entries"][0]="not-an-entry"; expect_load_error(tmp_path,data,"entry must be an object")

def test_strict_booleans_lists_and_digest_types(tmp_path):
    for field in ["complete_game_skill","complete_character_kit","synthetic_only","real_trace_executable"]:
        for value in [0,1,"false",None]:
            data=load_json(REGISTRY); data["entries"][0][field]=value; expect_load_error(tmp_path,data,f"{field} must be a boolean")
    for field in ["source_atomic_fact_ids","unresolved_atomic_fact_ids","unresolved_fields"]:
        data=load_json(REGISTRY); data["entries"][0][field]="not-a-list"; expect_load_error(tmp_path,data,f"{field} must be a list")
        for value in [{},[],0,False,None]:
            data=load_json(REGISTRY); data["entries"][0][field]=[value]; expect_load_error(tmp_path,data,f"{field} must contain")
        data=load_json(REGISTRY); data["entries"][0][field].append(data["entries"][0][field][0]); expect_load_error(tmp_path,data,"contains duplicate")
    for value in ["A"*64,"a"*63,0,{}]:
        data=load_json(REGISTRY); data["entries"][0]["accepted_atomic_fact_sha256"]=value; expect_load_error(tmp_path,data,"accepted_atomic_fact_sha256")

def test_malformed_cli_and_manually_constructed_handle_cannot_bypass(tmp_path):
    data=load_json(REGISTRY); data["entries"][0]["registry_entry_id"]={"bad":True}; path=write_registry(tmp_path,data,"malformed.json")
    result=subprocess.run([sys.executable,"-m","hsr_axis_sim.real_bindings.registry","--registry",str(path),"--format","json"],capture_output=True,text=True)
    assert result.returncode==1; assert "Traceback" not in result.stderr
    registry=load_reviewed_binding_registry(REGISTRY); handle=get_reviewed_binding(BINDING_ID,registry)
    unsafe=ReviewedBindingHandle(
        registry_entry_id=handle.registry_entry_id,binding_id=handle.binding_id,version=handle.version,actor_id=handle.actor_id,
        action_category=handle.action_category,binding_scope=handle.binding_scope,binding_type=handle.binding_type,
        binding_data_path=handle.binding_data_path,handler_key=handle.handler_key,source_atomic_fact_artifact_path=handle.source_atomic_fact_artifact_path,
        accepted_atomic_fact_sha256=handle.accepted_atomic_fact_sha256,source_atomic_fact_ids=("bad",),unresolved_atomic_fact_ids=handle.unresolved_atomic_fact_ids,
        unresolved_fields=handle.unresolved_fields,complete_game_skill=0,complete_character_kit=False,synthetic_only=True,real_trace_executable=False,
        damage_semantics_status=handle.damage_semantics_status,toughness_semantics_status=handle.toughness_semantics_status)
    unsafe_registry=ReviewedBindingRegistry("0.1",(unsafe,)); state=build_fixture_state(load_json(DEFAULT_FIXTURE))
    try: execute_reviewed_binding(BINDING_ID,state,["enemy"],registry=unsafe_registry)
    except ValueError as exc: assert "boolean" in str(exc) or "must be False" in str(exc)
    else: raise AssertionError("Unsafe manually constructed handle bypassed validation")
