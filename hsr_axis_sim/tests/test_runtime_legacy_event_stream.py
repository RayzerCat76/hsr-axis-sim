import pytest

from hsr_axis_sim.runtime_adapters import (
    AmbiguousLegacyEventPolicy,
    LegacyEventAdapterConfig,
    LegacyEventSchemaError,
    UnknownLegacyEventPolicy,
    adapt_legacy_event_stream,
)
from hsr_axis_sim.runtime_contracts import RuntimeEventType, canonical_json_bytes
from hsr_axis_sim.sim import Action, BattleState, DealDamage, Unit
from hsr_axis_sim.sim.events import Event


CONFIG = LegacyEventAdapterConfig(
    "battle-observation",
    UnknownLegacyEventPolicy.REJECT,
    AmbiguousLegacyEventPolicy.REJECT,
)


class SinglePassIterable:
    def __init__(self, events):
        self.events = events
        self.iterations = 0

    def __iter__(self):
        self.iterations += 1
        if self.iterations > 1:
            raise AssertionError("iterable consumed more than once")
        yield from self.events


def test_invalid_config_is_rejected_before_empty_or_nonempty_stream_consumption():
    with pytest.raises(LegacyEventSchemaError):
        adapt_legacy_event_stream([], start_sequence=0, config=object())

    iterable = SinglePassIterable([Event("turn_started", {"actor_id": "a"})])
    with pytest.raises(LegacyEventSchemaError):
        adapt_legacy_event_stream(iterable, start_sequence=0, config=object())
    assert iterable.iterations == 0


def test_stream_order_sequence_tuple_single_pass_and_input_preservation():
    source = [
        Event("turn_started", {"actor_id": "a", "is_extra_turn": False}),
        Event("turn_ended", {"actor_id": "a", "is_extra_turn": False}),
    ]
    iterable = SinglePassIterable(source)
    before = list(source)
    result = adapt_legacy_event_stream(iterable, start_sequence=4, config=CONFIG)
    assert isinstance(result, tuple)
    assert iterable.iterations == 1
    assert source == before
    assert [event.event_type for event in result] == [RuntimeEventType.TURN_START, RuntimeEventType.TURN_END]
    assert [event.sequence for event in result] == [4, 5]
    assert [event.event_id for event in result] == ["legacy:battle-observation:4", "legacy:battle-observation:5"]


def test_repeated_stream_adaptation_is_byte_identical():
    source = [Event("action_started", {"actor_id": "a", "action_id": "x"}), Event("action_finished", {"actor_id": "a", "action_id": "x"})]
    first = adapt_legacy_event_stream(source, start_sequence=0, config=CONFIG)
    second = adapt_legacy_event_stream(source, start_sequence=0, config=CONFIG)
    assert canonical_json_bytes(first) == canonical_json_bytes(second)


def test_real_mvp_action_is_manually_observed_without_mutating_legacy_events():
    actor = Unit("dps", "DPS", "ally", 100)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=1000, max_hp=1000)
    state = BattleState(units=[actor, target])
    Action(
        id="normal-hit", name="Normal Hit", actor_id="dps", target_ids=["enemy"],
        effects=[DealDamage(amount=100)], ends_turn=False,
    ).execute(state)
    legacy_before = [(event.type, dict(event.data)) for event in state.pending_events]

    adapted = adapt_legacy_event_stream(state.pending_events, start_sequence=0, config=CONFIG)

    assert [event.event_type for event in adapted] == [
        RuntimeEventType.ACTION_START,
        RuntimeEventType.DAMAGE_RESOLVED,
        RuntimeEventType.ACTION_END,
    ]
    assert [(event.type, dict(event.data)) for event in state.pending_events] == legacy_before
    assert all(event.attack_id is None and event.hit_id is None for event in adapted)
    assert not any(hasattr(event, name) for event in adapted for name in ("action_context", "attack_context", "hit_context"))
