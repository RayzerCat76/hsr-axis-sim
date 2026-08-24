import copy
import inspect
import json
import subprocess
import sys
from pathlib import Path

from hsr_axis_sim.real_bindings.pela_skill_v0_1 import *
from hsr_axis_sim.sim import Buff, TurnContext

BASE=Path(__file__).resolve().parents[1]
BINDING=BASE/"real_bindings/data/pela_skill_partial_v0_1.json"
ATOMS=BASE/"data/manual_video_traces/normalized_character_facts/real_video_trace_001_atomic_facts_v0_1.json"
FIXTURE=BASE/"real_bindings/fixtures/pela_skill_partial_v0_1_synthetic.json"
AUDITS=BASE/"data/manual_video_traces/real_binding_audits"

def values(): return load_json(BINDING),load_json(ATOMS),load_json(FIXTURE)
def expect_error(binding,atoms,text):
    try: validate_binding(binding,atoms)
    except ValueError as exc: assert text in str(exc)
    else: raise AssertionError("Expected binding validation failure")

def test_binding_load_validation_and_synthetic_execution():
    binding,atoms,fixture=values(); validate_binding(binding,atoms,ATOMS); result=run_synthetic_fixture(binding,fixture)
    assert result.removed_buff_id=="alpha_guard"; assert (result.skill_points_before,result.skill_points_after)==(3,2)
    assert (result.actor_energy_before,result.actor_energy_after)==(10,40)
    assert result.target_hp_before==result.target_hp_after==2000
    assert result.target_toughness_before==result.target_toughness_after==60
    assert result.normal_turn_ended is True; assert result.actor_av_after>result.actor_av_before

def test_insufficient_sp_rejects_without_energy_or_dispel():
    binding,_,fixture=values(); fixture["skill_points"]=0; state=build_fixture_state(fixture); before=set(state.get_unit("enemy").buffs)
    try: execute_partial_binding(binding,state,["enemy"],TurnContext(actor_id="pela"))
    except ValueError as exc: assert "Insufficient skill points" in str(exc)
    else: raise AssertionError("Expected insufficient SP")
    assert state.get_unit("pela").energy==10; assert set(state.get_unit("enemy").buffs)==before

def test_dead_ally_and_self_targets_are_rejected():
    binding,_,fixture=values(); state=build_fixture_state(fixture)
    for target in ["ally","pela"]:
        try: execute_partial_binding(binding,state,[target])
        except ValueError as exc: assert "not an enemy" in str(exc)
        else: raise AssertionError("Expected target rejection")
    state.get_unit("enemy").is_alive=False
    try: execute_partial_binding(binding,state,["enemy"])
    except ValueError as exc: assert "not alive" in str(exc)
    else: raise AssertionError("Expected dead target rejection")

def test_exactly_one_lexical_removable_buff_is_dispelled():
    binding,_,fixture=values(); state=build_fixture_state(fixture); _,removed=execute_partial_binding(binding,state,["enemy"])
    target=state.get_unit("enemy"); assert removed=="alpha_guard"; assert set(target.buffs)=={"zeta_power","innate_aura"}

def test_completion_damage_toughness_atomic_and_target_guards():
    for field,value,text in [("complete_game_skill",True,"complete_game_skill"),("damage_effect",True,"damage_effect"),("toughness_effect",True,"toughness_effect"),("target_type","single_ally","target_type"),("skill_point_cost",2,"skill_point_cost"),("actor_energy_gain",29,"actor_energy_gain"),("dispel_count",2,"dispel_count")]:
        binding,atoms,_=values(); binding[field]=value; expect_error(binding,atoms,text)
    binding,atoms,_=values(); binding["source_atomic_fact_ids"][0]="missing.fact"; expect_error(binding,atoms,"source_atomic_fact_ids")
    binding,atoms,_=values(); binding["source_atomic_fact_ids"].append("pela.skill.toughness_native"); expect_error(binding,atoms,"source_atomic_fact_ids")
    binding,atoms,_=values(); next(x for x in atoms["atomic_facts"] if x["atomic_fact_id"]=="pela.skill.target_scope")["atomic_fact_id"]="changed"; expect_error(binding,atoms,"dangling atomic")
    binding,_,_=values()
    try: register_as_complete_kit(binding)
    except ValueError as exc: assert "cannot be registered" in str(exc)
    else: raise AssertionError("Expected complete-kit guard")

def test_reports_are_deterministic_and_committed():
    binding,atoms,fixture=values(); report=build_audit_report(binding,atoms,fixture,ATOMS)
    assert render_json(report)==render_json(report); assert render_markdown(report)==render_markdown(report)
    assert (AUDITS/"pela_skill_partial_v0_1.md").read_text(encoding="utf-8")==render_markdown(report)
    assert (AUDITS/"pela_skill_partial_v0_1.json").read_text(encoding="utf-8")==render_json(report)

def test_cli_stdout_output_and_exit_codes(tmp_path):
    cmd=[sys.executable,"-m","hsr_axis_sim.real_bindings.pela_skill_v0_1"]
    stdout=subprocess.run(cmd+["--format","markdown"],capture_output=True,text=True); out=tmp_path/"audit.json"; written=subprocess.run(cmd+["--format","json","--output",str(out)],capture_output=True,text=True)
    bad=tmp_path/"bad.json"; b=load_json(BINDING); b["complete_game_skill"]=True; bad.write_text(json.dumps(b),encoding="utf-8")
    invalid=subprocess.run(cmd+["--binding",str(bad),"--format","json"],capture_output=True,text=True); unreadable=subprocess.run(cmd+["--binding",str(tmp_path/"missing.json"),"--format","json"],capture_output=True,text=True)
    assert stdout.returncode==written.returncode==0; assert out.read_text(encoding="utf-8")==render_json(build_audit_report(*values(),atomic_path=ATOMS))
    assert invalid.returncode==1; assert unreadable.returncode==2; assert "Traceback" not in invalid.stderr+unreadable.stderr
