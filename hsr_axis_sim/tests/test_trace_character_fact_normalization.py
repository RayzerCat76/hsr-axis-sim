import copy
import inspect
import json
import subprocess
import sys
from pathlib import Path

from hsr_axis_sim.tools.trace_character_fact_normalization import build_normalization_report, load_json, render_json, render_markdown

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "manual_video_traces"
REGISTRY = BASE / "source_registry" / "reports" / "real_video_trace_001_character_source_registry_v0_1.json"
GAPS = BASE / "binding_inventories" / "real_video_trace_001_botu_dilemma_binding_gap_inventory_v0_1.json"
ATOMS = BASE / "normalized_character_facts" / "real_video_trace_001_atomic_facts_v0_1.json"
REPORTS = BASE / "normalized_character_facts" / "reports"

def inputs(): return load_json(REGISTRY), load_json(GAPS), load_json(ATOMS)

def expect_error(values, text):
    try: build_normalization_report(*values)
    except ValueError as exc: assert text in str(exc)
    else: raise AssertionError("Expected normalization validation failure.")

def test_atomic_coverage_and_compound_atomization():
    report = build_normalization_report(*inputs())
    assert len(report.readiness) == 10
    assert [(x.actor, x.action) for x in report.readiness] == [("pela","technique"),("tingyun","ultimate"),("pela","skill"),("remembrance_trailblazer","skill"),("tingyun","skill"),("pela","ultimate"),("naxia","ultimate"),("naxia","basic_plus_extra_skill"),("mem","advance_naxia"),("naxia","skill_plus_extra_skill")]
    assert all(x.normalized_field_name not in {"action_structure","action_and_trigger_structure"} for x in report.atomic_facts)
    assert all(x.simulator_binding_allowed is False for x in report.atomic_facts)

def test_field_provenance_downgrades_and_mem_separation():
    report = build_normalization_report(*inputs()); facts = {x.atomic_fact_id:x for x in report.atomic_facts}
    assert facts["pela.skill.sp_delta"].verification_status == "verified_structured_data"
    assert len(facts["pela.skill.sp_delta"].provenance) == 1
    mem_ids = {"mem.support.charge_readiness_threshold","mem.support.charge_cost","mem.support.own_immediate_action","mem.support.target_action_advance"}
    assert mem_ids <= set(facts)
    assert facts["mem.support.charge_cost"].verification_status == "missing"
    assert facts["mem.support.charge_cost"].normalized_value is None
    assert facts["mem.support.own_immediate_action"].timing.classification == "immediate_action_self"
    assert facts["mem.support.target_action_advance"].timing.classification == "action_advance_target"

def test_toughness_native_convention_and_conversion_rule():
    values=list(inputs()); toughness=next(x for x in values[2]["atomic_facts"] if x.get("toughness"))
    assert toughness["toughness"]["normalized_value"] is None
    toughness["toughness"]["normalized_value"]=30
    expect_error(values,"documented conversion rule")

def test_vocabulary_provenance_reference_and_boundary_rules():
    for field, value, text in [("action_category","bad","action_category"),("target_scope","bad","target_scope")]:
        values=list(inputs()); values[2]["atomic_facts"][0][field]=value; expect_error(values,text)
    values=list(inputs()); values[2]["atomic_facts"][0]["timing"]={"classification":"bad"}; expect_error(values,"timing.classification")
    values=list(inputs()); values[2]["atomic_facts"][0]["duration"]={"value":1,"unit":"turn","anchor":"bad"}; expect_error(values,"duration.anchor")
    values=list(inputs()); values[2]["atomic_facts"][0]["source_registry_fact_ids"]=["bad"]; expect_error(values,"dangling source-registry")
    values=list(inputs()); values[2]["atomic_facts"][0]["verification_status"]="corroborated"; values[2]["atomic_facts"][0]["provenance"]=values[2]["atomic_facts"][0]["provenance"][:1]; expect_error(values,"two exact-field")

def test_missing_binding_and_executable_schema_rejected():
    values=list(inputs()); missing=next(x for x in values[2]["atomic_facts"] if x["verification_status"]=="missing"); missing["normalized_value"]=1; expect_error(values,"normalized_value null")
    values=list(inputs()); values[2]["atomic_facts"][0]["simulator_binding_allowed"]=True; expect_error(values,"must be false")
    values=list(inputs()); values[2]["CharacterSpec"]={}; expect_error(values,"executable schema key")

def test_order_determinism_and_committed_outputs():
    values=list(inputs()); expected=build_normalization_report(*values); values[2]["atomic_facts"].reverse(); actual=build_normalization_report(*values)
    assert render_json(actual)==render_json(expected); assert render_markdown(actual)==render_markdown(expected)
    assert (REPORTS/"real_video_trace_001_binding_readiness_v0_1.md").read_text(encoding="utf-8")==render_markdown(expected)
    assert (REPORTS/"real_video_trace_001_binding_readiness_v0_1.json").read_text(encoding="utf-8")==render_json(expected)

def test_cli_stdout_file_and_exit_codes(tmp_path):
    cmd=[sys.executable,"-m","hsr_axis_sim.tools.trace_character_fact_normalization","--source-registry",str(REGISTRY),"--gap-inventory",str(GAPS)]
    out=subprocess.run(cmd+["--format","markdown"],capture_output=True,text=True); path=tmp_path/"out.json"; written=subprocess.run(cmd+["--format","json","--output",str(path)],capture_output=True,text=True)
    invalid=subprocess.run([sys.executable,"-m","hsr_axis_sim.tools.trace_character_fact_normalization","--source-registry",str(REGISTRY),"--gap-inventory",str(REGISTRY),"--format","json"],capture_output=True,text=True)
    unreadable=subprocess.run([sys.executable,"-m","hsr_axis_sim.tools.trace_character_fact_normalization","--source-registry",str(tmp_path/"missing.json"),"--gap-inventory",str(GAPS),"--format","json"],capture_output=True,text=True)
    assert out.returncode==written.returncode==0; assert path.read_text(encoding="utf-8")==render_json(build_normalization_report(*inputs()))
    assert invalid.returncode==1; assert unreadable.returncode==2; assert "Traceback" not in invalid.stderr+unreadable.stderr
