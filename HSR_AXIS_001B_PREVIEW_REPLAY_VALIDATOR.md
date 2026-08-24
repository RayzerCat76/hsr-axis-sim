# HSR_AXIS_001B_PREVIEW_REPLAY_VALIDATOR

Do not give this to Codex until 001A passes review.

## Goal for 001B
Build a replay validator that can compare simulator output against a manually recorded gameplay trace.

## Golden replay idea
A golden replay JSON should contain:

- source video info
- character build notes
- initial battle state
- deterministic enemy setup
- ordered replay steps
- expected actor
- action taken
- target
- expected SP
- expected energy
- expected AV values
- expected buff/debuff durations
- optional HP/toughness checks
- forced RNG outcomes

## Example shape

```json
{
  "name": "sample_no_rng_axis_001",
  "source": {
    "type": "manual_video_trace",
    "platform": "bilibili",
    "url": "",
    "notes": "Builds and action order manually recorded."
  },
  "initial_state": {
    "skill_points": 3,
    "global_av": 0,
    "units": [
      {"id": "ally_fast", "team": "ally", "speed": 143, "energy": 60, "current_av": 69.9301},
      {"id": "ally_support", "team": "ally", "speed": 134, "energy": 80, "current_av": 74.6269},
      {"id": "enemy_1", "team": "enemy", "speed": 120, "hp": 100000, "toughness": 90, "current_av": 83.3333}
    ]
  },
  "steps": [
    {
      "step": 1,
      "expected_actor": "ally_fast",
      "action": "skill",
      "target": "enemy_1",
      "forced_rng": {"crit": true},
      "expect": {
        "skill_points": 2,
        "ally_fast_energy": 90,
        "enemy_1_toughness": 60
      }
    }
  ]
}
```

## Why this matters
Every time the simulator changes, run all golden replays. If a known replay breaks, the engine has regressed.
