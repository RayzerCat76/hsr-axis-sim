# HSR-AXIS-001B Preview — Golden Replay Validator

Start this only after HSR-AXIS-001A-FIX passes.

Goal:
Create a replay validator that can load a manually recorded battle trace and compare simulator output step by step.

The validator should check:

- expected actor
- action id
- target ids
- global AV
- current AV of all tracked units
- skill points
- energy values
- alive/dead state
- optional HP / toughness values
- optional buff/debuff state later
- forced RNG hooks later

Do not implement real damage yet. Damage can remain placeholder or be skipped in early replay checks.

Suggested files:

```text
hsr_axis_sim/
  sim/
    replay.py
  data/
    golden_replays/
      sample_av_replay_001.json
  tests/
    test_replay_validator.py
```

The first replay should be a synthetic deterministic AV replay, not a real Bilibili video yet.
