# HSR-AXIS-002A Real Trace Input Checklist

Use this before sending Codex another 002A run.

## Choose the first video

Prefer:

- low RNG
- clear builds shown at the end or beginning
- few follow-up attacks
- few summons
- simple enemy behavior
- stable / no-reset / no-heavy-reroll clear
- visible SP, energy, HP, action order, and targets

Avoid as the first real trace:

- Feixiao / Ratio / Aventurine heavy follow-up chains
- Acheron stack-heavy routes
- random bounce attacks
- edited videos with skipped actions
- videos that hide builds or enemy setup

## Required video metadata

```text
trace_id:
platform:
video_url:
video_title:
uploader:
recorded_by:
recorded_at:
game_version_if_visible:
mode:
stage/wave:
why_this_video_was_chosen:
known_uncertainties:
```

## Required ally build fields

For each ally:

```text
unit_id:
character:
eidolon:
light_cone:
superimposition:
level:
HP:
ATK:
DEF:
SPD:
Crit Rate:
Crit DMG:
Break Effect:
Energy Regen:
Effect Hit Rate:
Effect RES:
Elemental DMG bonus if visible:
relic_sets:
important_main_stats:
trace/eidolon notes:
uncertainty:
```

## Required enemy fields

For each enemy:

```text
enemy_id:
enemy_name:
level_if_visible:
HP exact or estimated:
SPD exact or estimated:
weaknesses:
max_toughness:
initial_toughness:
resistance assumptions:
action pattern if observable:
uncertainty:
```

## Required per-step fields

Record one row for every player action, enemy action, and ultimate interrupt.

```text
step_number:
video_timestamp:
expected_actor:
action/skill_id:
target_ids:
forced_rng:
  crit:
  effect_hit:
  enemy_target:
observed_skill_points_after_step:
observed_energy_after_step:
observed_hp_after_step:
observed_toughness_after_step:
observed_action_order_or_AV_after_step:
buff/debuff changes:
notes:
```

## Output location for Codex

Place the completed JSON file at:

```text
incoming_manual_video_traces/<trace_id>.json
```

Then run 002A again with the resume prompt.

## Model and reasoning recommendation

For the resume run:

```text
Codex Reasoning: Medium
ChatGPT Model: GPT-5.5
```

Reason: the task is fixture intake, lint, replay, manifest update, and tests. It should not change simulator mechanics.

If replay fails due a suspected mechanism mismatch:

```text
Codex Reasoning: High
ChatGPT Model: GPT-5.5 Thinking
```

Reason: mismatch diagnosis may require tracing timeline, buffs, damage, toughness, enemy AI, or trigger semantics.
