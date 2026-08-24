# HSR-AXIS-002A — Real Video Trace Intake Worksheet

Use this before sending anything to Codex.

The goal is to capture one real gameplay video as a deterministic manual trace. Codex should not watch or browse the video. Ray/Lumen records the data, then Codex only wires the provided JSON fixture into the project.

## Good first video criteria

Choose a video with:

- Low RNG.
- Few or no follow-up attacks.
- Few summons.
- Clear character builds shown at the end or beginning.
- Stable enemy behavior.
- Clear SP, HP, energy, action order, and target choices.
- Prefer “无凹轴 / no-reset / stable clear” over high-roll showcase.

Avoid as first trace:

- Heavy Feixiao / Ratio / Aventurine follow-up chains.
- Heavy Acheron stack routing.
- Multi-target random bounce.
- Random enemy target behavior that is hard to observe.
- Missing build screen.
- Edited/cut video with skipped actions.

## Metadata to record

```text
Trace id:
Video platform:
Video URL:
Video title:
Uploader:
Recorded by:
Recorded date:
Game version if shown:
Mode: MoC / PF / AS / other
Stage / enemy wave:
Reason this video was chosen:
Known uncertainty:
```

## Builds to record

For each ally:

```text
unit_id:
Character:
Eidolon:
Light cone + superimposition:
Level:
Traces / key trace notes:
HP:
ATK:
DEF:
Speed:
Crit Rate:
Crit DMG:
Break Effect:
Energy Regen:
Effect Hit Rate:
Effect RES:
Elemental DMG bonus if visible:
Relic sets:
Important relic main stats:
Notes / uncertainty:
```

For each enemy:

```text
enemy_id:
Enemy name:
Level if known:
HP estimate or exact HP:
Speed if known / estimated:
Weaknesses:
Max toughness:
Initial toughness:
Resistance assumptions:
Action pattern if observable:
```

## Step table to record

Use one row per player/enemy action. Include ultimates as interrupt steps when they happen.

```text
Step:
Video timestamp:
Expected actor:
Skill id / action:
Target ids:
Forced RNG:
  crit: true/false/unknown
  effect_hit: true/false/unknown
  enemy_target: unit_id if relevant
Observed SP after step:
Observed energy after step:
Observed HP after step:
Observed toughness after step:
Observed AV/action order after step:
Buff/debuff changes:
Notes:
```

## Minimal JSON skeleton

Create a first real trace using this shape. Use the existing template in the repo as the authoritative format.

```json
{
  "name": "first_real_video_trace_001",
  "trace_type": "manual_video_trace",
  "source": {
    "platform": "bilibili",
    "url": "PASTE_VIDEO_URL_HERE",
    "video_title": "PASTE_VIDEO_TITLE_HERE",
    "uploader": "PASTE_UPLOADER_HERE",
    "recorded_by": "Ray/Lumen",
    "recorded_at": "YYYY-MM-DD",
    "notes": "Manual transcription. Codex did not browse or download the video."
  },
  "assumptions": [
    "List exact uncertainties here.",
    "All non-observed RNG outcomes are forced or explicitly marked unknown."
  ],
  "builds": {},
  "enemy_setup": {
    "notes": "Describe wave and enemy assumptions."
  },
  "transcription": {
    "step_source": "manual_video_trace",
    "fields_recorded": [
      "actor",
      "skill_id",
      "target_ids",
      "forced_rng",
      "expected_hp",
      "expected_energy",
      "expected_skill_points",
      "expected_current_av",
      "expected_toughness",
      "buffs_or_debuffs"
    ],
    "notes": "Record timestamps and uncertainty in step notes."
  },
  "tolerance": 0.001,
  "data_sources": {
    "characters_dir": "hsr_axis_sim/data/character_kits/kit_001_mechanic_representatives",
    "team": "PATH_TO_TEAM_JSON_USED_FOR_THIS_TRACE"
  },
  "steps": []
}
```

## When the trace is ready

Put the completed JSON somewhere like:

```text
incoming_manual_video_traces/first_real_video_trace_001.json
```

Then use the 002A Codex prompt. If the incoming JSON is not ready, do not start 002A with Codex yet.
