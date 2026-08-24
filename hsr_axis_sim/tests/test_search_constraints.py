from hsr_axis_sim.search import SearchConstraints, filter_action_choices
from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.action_generator import ActionChoice


def make_choice(actor_id, skill_id, target_ids):
    return ActionChoice(
        actor_id=actor_id,
        skill_id=skill_id,
        skill_type="skill",
        target_ids=list(target_ids),
        action=Action(
            id=skill_id,
            name=skill_id,
            actor_id=actor_id,
            target_ids=list(target_ids),
        ),
    )


def test_no_constraints_preserves_choices():
    choices = [
        make_choice("a", "basic", ["enemy_1"]),
        make_choice("b", "skill", ["enemy_2"]),
    ]

    assert filter_action_choices(choices, None) == choices
    assert filter_action_choices(choices, SearchConstraints()) == choices


def test_disabled_actor_removes_choices_for_that_actor():
    choices = [
        make_choice("a", "basic", ["enemy_1"]),
        make_choice("b", "skill", ["enemy_1"]),
    ]

    filtered = filter_action_choices(
        choices,
        SearchConstraints(disabled_actor_ids={"a"}),
    )

    assert [choice.actor_id for choice in filtered] == ["b"]


def test_allowed_actor_permits_only_that_actor():
    choices = [
        make_choice("a", "basic", ["enemy_1"]),
        make_choice("b", "skill", ["enemy_1"]),
    ]

    filtered = filter_action_choices(
        choices,
        SearchConstraints(allowed_actor_ids={"a"}),
    )

    assert [choice.actor_id for choice in filtered] == ["a"]


def test_disabled_skill_id_removes_matching_choices():
    choices = [
        make_choice("a", "basic", ["enemy_1"]),
        make_choice("a", "skill", ["enemy_1"]),
    ]

    filtered = filter_action_choices(
        choices,
        SearchConstraints(disabled_skill_ids={"skill"}),
    )

    assert [choice.skill_id for choice in filtered] == ["basic"]


def test_per_actor_disabled_skill_only_affects_that_actor():
    choices = [
        make_choice("a", "skill", ["enemy_1"]),
        make_choice("b", "skill", ["enemy_1"]),
    ]

    filtered = filter_action_choices(
        choices,
        SearchConstraints(disabled_skill_ids_by_actor={"a": {"skill"}}),
    )

    assert [(choice.actor_id, choice.skill_id) for choice in filtered] == [("b", "skill")]


def test_disabled_target_removes_groups_containing_target():
    choices = [
        make_choice("a", "blast", ["enemy_1", "enemy_2"]),
        make_choice("a", "single", ["enemy_1"]),
    ]

    filtered = filter_action_choices(
        choices,
        SearchConstraints(disabled_target_ids={"enemy_2"}),
    )

    assert [choice.skill_id for choice in filtered] == ["single"]


def test_allowed_target_permits_only_groups_fully_contained_in_allow_list():
    choices = [
        make_choice("a", "blast", ["enemy_1", "enemy_2"]),
        make_choice("a", "single", ["enemy_1"]),
    ]

    filtered = filter_action_choices(
        choices,
        SearchConstraints(allowed_target_ids={"enemy_1"}),
    )

    assert [choice.skill_id for choice in filtered] == ["single"]


def test_max_choices_per_node_caps_choices_deterministically():
    choices = [
        make_choice("b", "skill", ["enemy_2"]),
        make_choice("a", "skill", ["enemy_1"]),
        make_choice("a", "basic", ["enemy_1"]),
    ]

    filtered = filter_action_choices(
        choices,
        SearchConstraints(max_choices_per_node=2),
    )

    assert [(choice.actor_id, choice.skill_id) for choice in filtered] == [
        ("a", "basic"),
        ("a", "skill"),
    ]
