import hashlib
from pathlib import Path

from hsr_axis_sim.runtime_contracts import RuntimeEventType
from hsr_axis_sim.sim import BattleState, Timeline, Unit


ROOT = Path(__file__).parents[2]
REFERENCE_HASHES = {
    "REFERENCE_LEGACY_EVENT_SURFACE_HSR_RUNTIME_ARCH_002.md": "6d28569b81c11c6620c6bb69984e3cf9da1162f2169fc4b1022198519abbb7fe",
    "REFERENCE_LEGACY_EVENT_SURFACE_HSR_RUNTIME_ARCH_002.json": "97142cfc8e8834c99f53ae9bf133e73b723e96fefe30b9c4649c92304e2d4b19",
}
# ARCH-019 explicitly authorizes additive changes to runtime_contracts/__init__.py
# and runtime_contracts/enums.py. Historical ARCH-002 evidence remains pinned,
# while every untouched runtime-contract source stays byte-for-byte protected.
CONTRACT_HASHES = {
    "contexts.py": "b2cd5c4783dc5fced63a206fcc9723f2c53d499265c2f66870847b25715a3c71",
    "events.py": "4146e68bbb27b733db13355334d4263e920af7c15a814e2df4a738d018798b43",
    "gates.py": "529b9bc8233e556902f60a821db5719451c0d5b595616be872e71eb17e4b4941",
    "serialization.py": "626a885857b5e7fd90ae5f56ec0ee712bbdca2f28b4f28ea33bbf8be12c0937d",
    "trace.py": "ca14ac00a999c3c9ab7dc2ed5e2c9442d4926494feffa2cd4575457fafeb061e",
}
ARCH_001_RUNTIME_EVENT_VALUES = [
    "BATTLE_START", "WAVE_START", "TURN_ENTRY", "TURN_START", "ACTION_QUEUED",
    "ACTION_START", "ATTACK_DECLARED", "ATTACK_CONTACT", "TARGET_ATTACKED",
    "HIT_RESOLVED", "BEFORE_DAMAGE", "DAMAGE_RESOLVED", "SHIELD_CHANGED",
    "SHIELD_DAMAGED", "HP_CHANGED", "HP_DAMAGED", "HP_LOST",
    "TOUGHNESS_REDUCED", "WEAKNESS_BROKEN", "EFFECT_APPLICATION_ATTEMPT",
    "EFFECT_APPLIED", "EFFECT_RESISTED", "EFFECT_IMMUNE", "EFFECT_REMOVED",
    "EFFECT_TRANSFORMED", "FOLLOW_UP_QUEUED", "COUNTER_QUEUED",
    "EXTRA_TURN_QUEUED", "ACTION_END", "TURN_END", "BEFORE_LETHAL",
    "LETHAL_INTERCEPTED", "DOWNED", "KNOCKED_DOWN", "DEATH", "REVIVE",
    "WAVE_END", "BATTLE_END", "CONTENT_DEFINED",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_supplied_reference_hashes_are_exact():
    directory = ROOT / "docs/runtime/research"
    assert {name: digest(directory / name) for name in REFERENCE_HASHES} == REFERENCE_HASHES


def test_runtime_contract_sources_not_authorized_by_arch_019_are_unchanged():
    directory = ROOT / "hsr_axis_sim/runtime_contracts"
    assert {name: digest(directory / name) for name in CONTRACT_HASHES} == CONTRACT_HASHES


def test_arch_001_runtime_event_vocabulary_is_preserved_in_original_order():
    current = [
        member.value
        for member in RuntimeEventType
        if member not in {
            RuntimeEventType.ENERGY_CHANGED,
            RuntimeEventType.SKILL_POINTS_CHANGED,
        }
    ]
    assert current == ARCH_001_RUNTIME_EVENT_VALUES


def test_no_production_module_imports_runtime_adapters():
    protected = ["sim", "search", "regression", "adapters", "real_bindings", "data"]
    hits = []
    for area in protected:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_adapters" in path.read_text():
                hits.append(path)
    assert hits == []


def test_existing_extra_turn_stack_is_still_lifo():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
