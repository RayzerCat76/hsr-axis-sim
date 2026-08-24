from __future__ import annotations

from dataclasses import dataclass

from hsr_axis_sim.sim.state import BattleState


@dataclass
class ScoreConfig:
    defeated_enemy_bonus: float = 100000
    enemy_hp_missing_weight: float = 1
    global_av_penalty: float = 10
    depth_penalty: float = 100
    skill_point_bonus: float = 50
    alive_ally_bonus: float = 500


@dataclass
class ScoreProfile:
    id: str
    defeated_enemy_bonus: float
    all_enemies_defeated_bonus: float
    enemy_hp_missing_weight: float
    global_av_penalty: float
    depth_penalty: float
    skill_point_bonus: float
    alive_ally_bonus: float
    ally_hp_remaining_weight: float
    defeated_ally_penalty: float


@dataclass
class ScoreBreakdown:
    profile_id: str
    total: float
    components: dict[str, float]


BUILTIN_PROFILES: dict[str, ScoreProfile] = {
    "generic_kill": ScoreProfile(
        id="generic_kill",
        defeated_enemy_bonus=100000,
        all_enemies_defeated_bonus=0,
        enemy_hp_missing_weight=1,
        global_av_penalty=10,
        depth_penalty=100,
        skill_point_bonus=50,
        alive_ally_bonus=500,
        ally_hp_remaining_weight=0,
        defeated_ally_penalty=0,
    ),
    "zero_cycle": ScoreProfile(
        id="zero_cycle",
        defeated_enemy_bonus=120000,
        all_enemies_defeated_bonus=250000,
        enemy_hp_missing_weight=1,
        global_av_penalty=80,
        depth_penalty=500,
        skill_point_bonus=20,
        alive_ally_bonus=500,
        ally_hp_remaining_weight=0,
        defeated_ally_penalty=50000,
    ),
    "damage_race": ScoreProfile(
        id="damage_race",
        defeated_enemy_bonus=100000,
        all_enemies_defeated_bonus=50000,
        enemy_hp_missing_weight=5,
        global_av_penalty=20,
        depth_penalty=100,
        skill_point_bonus=5,
        alive_ally_bonus=250,
        ally_hp_remaining_weight=0.05,
        defeated_ally_penalty=25000,
    ),
    "survival_safe": ScoreProfile(
        id="survival_safe",
        defeated_enemy_bonus=40000,
        all_enemies_defeated_bonus=25000,
        enemy_hp_missing_weight=1,
        global_av_penalty=10,
        depth_penalty=100,
        skill_point_bonus=25,
        alive_ally_bonus=2500,
        ally_hp_remaining_weight=1,
        defeated_ally_penalty=150000,
    ),
    "sp_conservative": ScoreProfile(
        id="sp_conservative",
        defeated_enemy_bonus=80000,
        all_enemies_defeated_bonus=25000,
        enemy_hp_missing_weight=1,
        global_av_penalty=10,
        depth_penalty=100,
        skill_point_bonus=500,
        alive_ally_bonus=500,
        ally_hp_remaining_weight=0,
        defeated_ally_penalty=25000,
    ),
}


class Evaluator:
    def __init__(
        self,
        profile: str | ScoreProfile | None = None,
        config: ScoreConfig | None = None,
    ) -> None:
        if config is not None and profile is not None:
            raise ValueError("Pass either profile or config, not both.")
        if config is not None:
            self.profile = ScoreProfile(
                id="custom_config",
                defeated_enemy_bonus=config.defeated_enemy_bonus,
                all_enemies_defeated_bonus=0,
                enemy_hp_missing_weight=config.enemy_hp_missing_weight,
                global_av_penalty=config.global_av_penalty,
                depth_penalty=config.depth_penalty,
                skill_point_bonus=config.skill_point_bonus,
                alive_ally_bonus=config.alive_ally_bonus,
                ally_hp_remaining_weight=0,
                defeated_ally_penalty=0,
            )
        elif isinstance(profile, ScoreProfile):
            self.profile = profile
        else:
            profile_id = profile or "generic_kill"
            try:
                self.profile = BUILTIN_PROFILES[profile_id]
            except KeyError as exc:
                raise ValueError(f"Unknown score profile: {profile_id!r}.") from exc

    def evaluate(self, state: BattleState, depth: int) -> float:
        return self.evaluate_breakdown(state, depth=depth).total

    def evaluate_breakdown(self, state: BattleState, depth: int) -> ScoreBreakdown:
        profile = self.profile
        enemies = [unit for unit in state.units if unit.team == "enemy"]
        allies = [unit for unit in state.units if unit.team == "ally"]
        defeated_enemies = sum(1 for unit in enemies if not unit.is_alive)
        alive_enemies = len(enemies) - defeated_enemies
        enemy_hp_missing = sum(max(0, unit.max_hp - unit.hp) for unit in enemies)
        alive_allies = sum(1 for unit in allies if unit.is_alive)
        defeated_allies = len(allies) - alive_allies
        ally_hp_remaining = sum(max(0, unit.hp) for unit in allies if unit.is_alive)

        components = {
            "defeated_enemies": defeated_enemies * profile.defeated_enemy_bonus,
            "all_enemies_defeated": (
                profile.all_enemies_defeated_bonus if enemies and alive_enemies == 0 else 0
            ),
            "enemy_hp_missing": enemy_hp_missing * profile.enemy_hp_missing_weight,
            "global_av_penalty": -state.global_av * profile.global_av_penalty,
            "depth_penalty": -depth * profile.depth_penalty,
            "skill_points": state.skill_points * profile.skill_point_bonus,
            "alive_allies": alive_allies * profile.alive_ally_bonus,
            "ally_hp_remaining": ally_hp_remaining * profile.ally_hp_remaining_weight,
            "defeated_allies": -defeated_allies * profile.defeated_ally_penalty,
        }
        total = sum(components.values())
        return ScoreBreakdown(
            profile_id=profile.id,
            total=total,
            components=components,
        )


def get_score_profile(profile_id: str) -> ScoreProfile:
    try:
        return BUILTIN_PROFILES[profile_id]
    except KeyError as exc:
        raise ValueError(f"Unknown score profile: {profile_id!r}.") from exc


def format_score_breakdown(breakdown: ScoreBreakdown) -> str:
    lines = [f"{breakdown.profile_id} total={breakdown.total:.3f}"]
    for key in sorted(breakdown.components):
        lines.append(f"  {key}={breakdown.components[key]:.3f}")
    return "\n".join(lines)
