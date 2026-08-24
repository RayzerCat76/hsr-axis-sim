from hsr_axis_sim.search import Evaluator, beam_search, format_axis
from hsr_axis_sim.sim import BattleState, Unit
from hsr_axis_sim.sim.data_schema import SkillSpec


def make_skill(skill_id, amount):
    return SkillSpec(
        id=skill_id,
        name=skill_id,
        skill_type="skill",
        target_type="single_enemy",
        sp_delta=0,
        energy_delta=0,
        ends_turn=True,
        effects=[
            {
                "type": "DealDamage",
                "amount": amount,
                "target_ref": "action_targets",
            }
        ],
    )


def make_state():
    ally = Unit("carry", "Carry", "ally", 100, current_av=0, hp=1000, max_hp=1000)
    enemy = Unit("enemy", "Enemy", "enemy", 100, current_av=100, hp=50, max_hp=50)
    state = BattleState(units=[ally, enemy], skill_points=3)
    skills = {
        "carry": {
            "poke": make_skill("poke", 10),
            "kill": make_skill("kill", 100),
        }
    }
    return state, skills


def test_beam_search_can_find_kill_action():
    state, skills = make_state()

    result = beam_search(state, skills, max_depth=1, beam_width=2)

    assert result.best_node.actions_taken[-1].skill_id == "kill"
    assert result.best_node.reason == "all_enemies_defeated"


def test_beam_width_prunes_worse_branches():
    state, skills = make_state()

    result = beam_search(state, skills, max_depth=1, beam_width=1)

    assert len(result.final_beam) == 1
    assert result.final_beam[0].actions_taken[-1].skill_id == "kill"


def test_beam_search_result_axis_format_is_readable():
    state, skills = make_state()
    result = beam_search(state, skills, max_depth=1, beam_width=1)

    axis = format_axis(result.best_node)

    assert "AV 0.000" in axis
    assert "carry uses kill on enemy" in axis
    assert "SP=3" in axis


def test_beam_search_respects_max_nodes_expanded():
    state, skills = make_state()

    result = beam_search(
        state,
        skills,
        max_depth=3,
        beam_width=2,
        max_nodes_expanded=1,
    )

    assert result.nodes_expanded == 1
    assert result.terminated_reason == "max_nodes_expanded"


def test_beam_search_accepts_zero_cycle_evaluator():
    state, skills = make_state()

    result = beam_search(
        state,
        skills,
        max_depth=1,
        beam_width=2,
        evaluator=Evaluator(profile="zero_cycle"),
    )

    assert result.best_node.actions_taken[-1].skill_id == "kill"


def test_beam_search_respects_max_global_av():
    ally = Unit("carry", "Carry", "ally", 100, current_av=10, hp=1000, max_hp=1000)
    enemy = Unit("enemy", "Enemy", "enemy", 100, current_av=100, hp=100, max_hp=100)
    state = BattleState(units=[ally, enemy], skill_points=3)
    skills = {"carry": {"poke": make_skill("poke", 10)}}

    result = beam_search(
        state,
        skills,
        max_depth=3,
        beam_width=1,
        max_global_av=5,
    )

    assert result.final_beam[0].reason == "max_global_av"
