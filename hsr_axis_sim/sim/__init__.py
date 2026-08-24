from .action import Action
from .action_generator import (
    ActionChoice,
    AffordabilityResult,
    is_skill_affordable,
    legal_action_choices_for_actor,
    legal_actions_for_actor,
    skill_affordability,
)
from .effects import (
    AddBuff,
    AddDebuff,
    AdvanceAction,
    ChangeSpeed,
    ConsumeEnergy,
    ConsumeSkillPoint,
    DealDamage,
    DealToughnessDamage,
    DelayAction,
    DoesNotEndTurn,
    Effect,
    GainEnergy,
    GainSkillPoint,
    GrantExtraTurn,
    ImmediateAction,
    RemoveBuff,
    RemoveDebuff,
)
from .buffs import Buff
from .break_damage import (
    BreakDamageResult,
    BreakDamageSpec,
    calculate_break_damage,
    element_break_multiplier,
    level_break_base,
)
from .data_loader import (
    action_from_skill,
    build_battle_state_from_files,
    build_battle_state_from_team,
    instantiate_unit,
    load_character_spec,
    load_character_specs_from_dir,
    load_team_spec,
)
from .data_schema import BaseStatsSpec, CharacterSpec, SkillSpec, TeamSpec, UnitInstanceSpec
from .damage import DamageResult, DamageSpec, calculate_damage
from .enemy_ai import (
    EnemyAIPlan,
    EnemyPatternStep,
    choose_enemy_action,
    execute_enemy_ai_action,
)
from .events import Event, Trigger
from .rng import ForcedRng, RngContext
from .state import BattleState
from .stats import EffectiveStats, effective_stats
from .targets import resolve_target_ids
from .targeting import (
    TargetValidationError,
    legal_target_groups,
    normalize_and_validate_target_ids,
)
from .timeline import Timeline
from .turn_context import TurnContext
from .unit import Unit
from .ultimate_windows import (
    DecisionWindow,
    execute_interrupt_action,
    legal_ultimate_choices,
)

_REPLAY_EXPORTS = {
    "ReplayCheckResult",
    "ReplayValidationError",
    "ReplayValidator",
}

__all__ = [
    "Action",
    "ActionChoice",
    "AddBuff",
    "AddDebuff",
    "AdvanceAction",
    "AffordabilityResult",
    "BaseStatsSpec",
    "BattleState",
    "BreakDamageResult",
    "BreakDamageSpec",
    "Buff",
    "ChangeSpeed",
    "CharacterSpec",
    "ConsumeEnergy",
    "ConsumeSkillPoint",
    "DamageResult",
    "DamageSpec",
    "DealDamage",
    "DealToughnessDamage",
    "DecisionWindow",
    "DelayAction",
    "DoesNotEndTurn",
    "Effect",
    "EffectiveStats",
    "EnemyAIPlan",
    "EnemyPatternStep",
    "Event",
    "ForcedRng",
    "GainEnergy",
    "GainSkillPoint",
    "GrantExtraTurn",
    "ImmediateAction",
    "ReplayCheckResult",
    "ReplayValidationError",
    "ReplayValidator",
    "RemoveBuff",
    "RemoveDebuff",
    "RngContext",
    "SkillSpec",
    "TeamSpec",
    "TargetValidationError",
    "Timeline",
    "TurnContext",
    "Trigger",
    "Unit",
    "UnitInstanceSpec",
    "action_from_skill",
    "build_battle_state_from_files",
    "build_battle_state_from_team",
    "calculate_damage",
    "calculate_break_damage",
    "choose_enemy_action",
    "effective_stats",
    "element_break_multiplier",
    "execute_enemy_ai_action",
    "execute_interrupt_action",
    "instantiate_unit",
    "is_skill_affordable",
    "legal_action_choices_for_actor",
    "legal_actions_for_actor",
    "legal_ultimate_choices",
    "level_break_base",
    "load_character_spec",
    "load_character_specs_from_dir",
    "load_team_spec",
    "legal_target_groups",
    "normalize_and_validate_target_ids",
    "resolve_target_ids",
    "skill_affordability",
]


def __getattr__(name):
    if name in _REPLAY_EXPORTS:
        from . import replay

        return getattr(replay, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
