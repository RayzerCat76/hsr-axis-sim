from hashlib import sha256
from pathlib import Path

from hsr_axis_sim.runtime_contracts import RuntimeEventType
from hsr_axis_sim.sim import BattleState, Timeline, Unit


ROOT = Path(__file__).parents[2]
FIXTURE = (
    ROOT
    / "hsr_axis_sim/data/runtime_golden_fixtures/arch_017_reviewed_action_session_expected.json"
)
FIXTURE_SHA256 = "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66"


def test_arch_020_wires_resource_events_only_through_production_effects_without_sidecar_import():
    sim_root = ROOT / "hsr_axis_sim/sim"
    resource_event_hits = []
    runtime_sidecar_hits = []
    for path in sim_root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if "energy_changed" in source or "skill_points_changed" in source:
            resource_event_hits.append(path.relative_to(sim_root).as_posix())
        if any(
            token in source
            for token in (
                "RuntimeResourceChangeObservation",
                "RuntimeResourceKind",
                "RuntimeResourceScope",
                "runtime_contracts",
            )
        ):
            runtime_sidecar_hits.append(path.relative_to(sim_root).as_posix())

    assert resource_event_hits == ["effects.py"]
    assert runtime_sidecar_hits == []


def test_arch_020_wires_arch_019_contract_only_in_legacy_event_adapter():
    adapter_root = ROOT / "hsr_axis_sim/runtime_adapters"
    hits = []
    for path in adapter_root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if any(
            token in source
            for token in (
                "RuntimeResourceChangeObservation",
                "ENERGY_CHANGED",
                "SKILL_POINTS_CHANGED",
                "energy_changed",
                "skill_points_changed",
            )
        ):
            hits.append(path.relative_to(adapter_root).as_posix())

    assert hits == ["legacy_events.py"]


def test_strict_loader_remains_generic_over_runtime_event_type_without_resource_contract_import():
    hits = []
    for path in (ROOT / "hsr_axis_sim/runtime_loaders").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if "RuntimeResourceChangeObservation" in source or "resource_observations" in source:
            hits.append(path)
    assert hits == []
    assert RuntimeEventType.ENERGY_CHANGED.value == "ENERGY_CHANGED"
    assert RuntimeEventType.SKILL_POINTS_CHANGED.value == "SKILL_POINTS_CHANGED"


def test_arch_017_static_golden_fixture_identity_is_unchanged():
    payload = FIXTURE.read_bytes()
    assert len(payload) == 3013
    assert sha256(payload).hexdigest() == FIXTURE_SHA256


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == [
        "third",
        "second",
        "first",
    ]
