from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.effects import AddBuff, GainEnergy
from hsr_axis_sim.sim.events import Trigger
from hsr_axis_sim.sim.state import BattleState
from hsr_axis_sim.sim.unit import Unit


def _unit(unit_id: str) -> Unit:
    return Unit(
        id=unit_id,
        name=unit_id,
        team="ally",
        base_speed=100,
        energy=0,
        max_energy=100,
    )


def _run(order: str):
    target = _unit("target")
    state = BattleState(
        [target],
        triggers=[
            Trigger(
                id="resource-observer",
                owner_id="observer",
                event_type="energy_changed",
                condition={"type": "always"},
                effects=[
                    AddBuff(
                        id="shared-buff",
                        name="Trigger Buff",
                        target_ids=["target"],
                        remaining_turns=1,
                        stacks=1,
                        max_stacks=2,
                        data={"source": "resource-trigger"},
                        refresh_policy="refresh",
                    )
                ],
            )
        ],
    )
    gain = GainEnergy(target_ids=["target"], amount=10)
    main_buff = AddBuff(
        id="shared-buff",
        name="Main Buff",
        target_ids=["target"],
        remaining_turns=2,
        stacks=1,
        max_stacks=2,
        data={"source": "main-action"},
        refresh_policy="refresh",
    )
    effects = [gain, main_buff] if order == "energy_then_buff" else [main_buff, gain]
    Action(
        id=f"order-{order}",
        name=order,
        actor_id="actor",
        effects=effects,
        ends_turn=False,
    ).execute(state)
    return state.get_unit("target").buffs["shared-buff"], state


def test_arch_020_resource_event_creates_a_real_current_contract_order_observation_point():
    energy_first, state_a = _run("energy_then_buff")
    buff_first, state_b = _run("buff_then_energy")

    assert [event.type for event in state_a.pending_events] == [
        "action_started",
        "energy_changed",
        "action_finished",
    ]
    assert [event.type for event in state_b.pending_events] == [
        "action_started",
        "energy_changed",
        "action_finished",
    ]
    assert state_a.trigger_fire_counts == {"resource-observer": 1}
    assert state_b.trigger_fire_counts == {"resource-observer": 1}

    assert energy_first.stacks == buff_first.stacks == 2
    assert energy_first.remaining_turns == 2
    assert buff_first.remaining_turns == 1
    assert energy_first.source_id == "actor"
    assert buff_first.source_id == "observer"
    assert energy_first.data == {"source": "main-action"}
    assert buff_first.data == {"source": "resource-trigger"}


def test_historical_002p_generic_irrelevance_premise_is_no_longer_current():
    # The archived 002P proof explicitly depended on GainEnergy having no event
    # emission and on there being no observable event between ordered effects.
    # ARCH-020 intentionally invalidates those premises; this test supplies an
    # executable counterexample without asserting any release-game Tingyun rule.
    energy_first, _ = _run("energy_then_buff")
    buff_first, _ = _run("buff_then_energy")
    assert (
        energy_first.remaining_turns,
        energy_first.source_id,
        energy_first.data,
    ) != (
        buff_first.remaining_turns,
        buff_first.source_id,
        buff_first.data,
    )
