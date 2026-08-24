import copy
import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from hsr_axis_sim.real_bindings.pela_skill_v0_1 import (
    DEFAULT_ATOMS,
    DEFAULT_BINDING as PELA_BINDING,
    load_json,
    validate_binding as validate_pela_binding,
)
from hsr_axis_sim.real_bindings.registry import DEFAULT_REGISTRY
from hsr_axis_sim.real_bindings.tingyun_ultimate_v0_1 import (
    DEFAULT_BINDING as TINGYUN_BINDING,
    validate_binding as validate_tingyun_binding,
)


BASE = Path(__file__).resolve().parents[1]


@pytest.fixture(params=[
    ("Tingyun Ultimate partial binding validation failed", TINGYUN_BINDING, validate_tingyun_binding),
    ("Pela Skill partial binding validation failed", PELA_BINDING, validate_pela_binding),
])
def validator_case(request):
    return request.param


def _valid_inputs(binding_path):
    return load_json(binding_path), load_json(DEFAULT_ATOMS)


def _assert_rejected(validator_case, binding, atoms):
    prefix, _, validator = validator_case
    with pytest.raises(ValueError, match=prefix):
        validator(binding, atoms, DEFAULT_ATOMS)


@pytest.mark.parametrize("binding, atoms", [
    ([], {"atomic_facts": []}),
    ({}, []),
    ({}, {"atomic_facts": "not-a-list"}),
])
def test_binding_and_atomic_artifact_roots_are_validated(validator_case, binding, atoms):
    _assert_rejected(validator_case, binding, atoms)


@pytest.mark.parametrize("bad_value", [{"bad": "value"}, ["bad"]])
def test_source_atomic_fact_ids_reject_non_string_members(validator_case, bad_value):
    _, binding_path, _ = validator_case
    binding, atoms = _valid_inputs(binding_path)
    binding["source_atomic_fact_ids"] = [bad_value]
    _assert_rejected(validator_case, binding, atoms)


def test_unresolved_atomic_fact_ids_reject_object_member(validator_case):
    _, binding_path, _ = validator_case
    binding, atoms = _valid_inputs(binding_path)
    binding["unresolved_atomic_fact_ids"] = [{"bad": "value"}]
    _assert_rejected(validator_case, binding, atoms)


def test_unresolved_fields_reject_object_member(validator_case):
    _, binding_path, _ = validator_case
    binding, atoms = _valid_inputs(binding_path)
    binding["unresolved_fields"] = [{"bad": "value"}]
    _assert_rejected(validator_case, binding, atoms)


@pytest.mark.parametrize("field", [
    "source_atomic_fact_ids",
    "unresolved_atomic_fact_ids",
    "unresolved_fields",
])
def test_binding_fact_lists_reject_duplicates_and_non_list_containers(validator_case, field):
    _, binding_path, _ = validator_case
    binding, atoms = _valid_inputs(binding_path)
    binding[field] = [binding[field][0], binding[field][0]]
    _assert_rejected(validator_case, binding, atoms)

    binding, atoms = _valid_inputs(binding_path)
    binding[field] = "not-a-list"
    _assert_rejected(validator_case, binding, atoms)


@pytest.mark.parametrize("atomic_facts", [
    ["not-an-object"],
    [{"atomic_fact_id": 1}],
])
def test_atomic_fact_items_require_objects_with_string_ids(validator_case, atomic_facts):
    _, binding_path, _ = validator_case
    binding, atoms = _valid_inputs(binding_path)
    atoms["atomic_facts"] = atomic_facts
    _assert_rejected(validator_case, binding, atoms)


def test_atomic_fact_ids_must_be_unique(validator_case):
    _, binding_path, _ = validator_case
    binding, atoms = _valid_inputs(binding_path)
    atoms["atomic_facts"].append(copy.deepcopy(atoms["atomic_facts"][0]))
    _assert_rejected(validator_case, binding, atoms)


@pytest.mark.parametrize("binding_name", ["tingyun", "pela"])
def test_registry_cli_rejects_package_contained_malformed_binding_without_traceback(
    tmp_path, binding_name
):
    entry_id = (
        "reviewed_tingyun_ultimate_partial_v0_1"
        if binding_name == "tingyun"
        else "reviewed_pela_skill_partial_v0_1"
    )
    source_path = TINGYUN_BINDING if binding_name == "tingyun" else PELA_BINDING
    malformed_binding = load_json(source_path)
    malformed_binding["source_atomic_fact_ids"] = [{"bad": "value"}]
    filename = f"_pytest_malformed_{binding_name}_{uuid.uuid4().hex}.json"
    package_path = BASE / "real_bindings" / "data" / filename
    registry_path = tmp_path / "registry.json"
    try:
        package_path.write_text(json.dumps(malformed_binding), encoding="utf-8")
        registry = load_json(DEFAULT_REGISTRY)
        entry = next(
            item for item in registry["entries"] if item["registry_entry_id"] == entry_id
        )
        entry["binding_data_path"] = f"real_bindings/data/{filename}"
        registry_path.write_text(json.dumps(registry), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "hsr_axis_sim.real_bindings.registry",
                "--registry",
                str(registry_path),
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
        )
    finally:
        package_path.unlink(missing_ok=True)
    assert result.returncode == 1
    assert "validation failed" in result.stderr.lower()
    assert "Traceback" not in result.stderr
