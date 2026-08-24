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


def test_resource_observation_contract_is_not_wired_into_production_simulator_yet():
    hits = []
    for path in (ROOT / "hsr_axis_sim/sim").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if any(
            token in source
            for token in (
                "RuntimeResourceChangeObservation",
                "ENERGY_CHANGED",
                "SKILL_POINTS_CHANGED",
                "runtime_contracts.resource_observations",
            )
        ):
            hits.append(path)
    assert hits == []


def test_resource_observation_contract_is_not_wired_into_legacy_adapter_yet():
    hits = []
    for path in (ROOT / "hsr_axis_sim/runtime_adapters").rglob("*.py"):
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
            hits.append(path)
    assert hits == []


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
