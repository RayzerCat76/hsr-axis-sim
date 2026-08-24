from hsr_axis_sim.search import Evaluator, SearchConfig, SearchEngine, clone_state_for_search
from hsr_axis_sim.sim import BattleState, Unit
from hsr_axis_sim.sim.data_schema import SkillSpec
from hsr_axis_sim.sim.enemy_ai import EnemyAIPlan, EnemyPatternStep


def make_skill(skill_id, amount, target_type="single_enemy"):
    return SkillSpec(
        id=skill_id,
        name=skill_id,
        skill_type="skill",
        target_type=target_type,
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


def make_kill_state():
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


def test_clone_state_for_search_is_deep_copy():
    state, _ = make_kill_state()

    clone = clone_state_for_search(state)
    clone.get_unit("enemy").hp = 1
    clone.logs.append("changed")

    assert state.get_unit("enemy").hp == 50
    assert state.logs == []


def test_expand_child_does_not_mutate_parent_state():
    state, skills = make_kill_state()
    engine = SearchEngine(skills, config=SearchConfig(max_depth=2))
    root = engine.make_root(state)

    children = engine.expand_node(root)

    assert len(children) == 2
    assert state.get_unit("enemy").hp == 50
    assert root.state.get_unit("enemy").hp == 50
    assert state.global_av == 0


def test_sibling_branches_do_not_share_mutable_state():
    state, skills = make_kill_state()
    engine = SearchEngine(skills, config=SearchConfig(max_depth=2))
    children = engine.expand_node(engine.make_root(state))

    children[0].state.get_unit("enemy").hp = 999

    assert children[1].state.get_unit("enemy").hp != 999


def test_search_expansion_marks_all_enemies_defeated_terminal():
    state, skills = make_kill_state()
    engine = SearchEngine(skills, config=SearchConfig(max_depth=2))

    children = engine.expand_node(engine.make_root(state))
    kill_child = [child for child in children if child.actions_taken[-1].skill_id == "kill"][0]

    assert kill_child.terminal is True
    assert kill_child.reason == "all_enemies_defeated"


def test_max_depth_terminal_reason_on_child():
    state, skills = make_kill_state()
    engine = SearchEngine(skills, config=SearchConfig(max_depth=1))

    children = engine.expand_node(engine.make_root(state))
    poke_child = [child for child in children if child.actions_taken[-1].skill_id == "poke"][0]

    assert poke_child.terminal is True
    assert poke_child.reason == "max_depth"


def test_enemy_auto_action_expansion_uses_enemy_ai():
    enemy = Unit("enemy", "Enemy", "enemy", 100, current_av=0, hp=1000, max_hp=1000)
    ally = Unit("ally", "Ally", "ally", 100, current_av=100, hp=1000, max_hp=1000)
    state = BattleState(
        units=[enemy, ally],
        enemy_ai_plans={
            "enemy": EnemyAIPlan(pattern=[EnemyPatternStep(skill_id="basic")])
        },
        enemy_ai_cursors={"enemy": 0},
    )
    skills = {"enemy": {"basic": make_skill("basic", 100)}}
    engine = SearchEngine(skills, config=SearchConfig(max_depth=2))

    children = engine.expand_node(engine.make_root(state))

    assert len(children) == 1
    child = children[0]
    assert child.actions_taken[-1].actor_id == "enemy"
    assert child.actions_taken[-1].skill_id == "basic"
    assert child.state.get_unit("ally").hp == 900
    assert child.state.enemy_ai_cursors["enemy"] == 1


def test_terminal_all_enemies_defeated_on_root():
    ally = Unit("ally", "Ally", "ally", 100)
    enemy = Unit("enemy", "Enemy", "enemy", 100, hp=0, max_hp=100, is_alive=False)
    state = BattleState(units=[ally, enemy])
    engine = SearchEngine({}, config=SearchConfig(max_depth=2))

    root = engine.make_root(state)

    assert root.terminal is True
    assert root.reason == "all_enemies_defeated"
