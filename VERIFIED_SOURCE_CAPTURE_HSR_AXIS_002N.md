# HSR-AXIS-002N Verified Source Capture Reference

This file is a reviewer-provided reference for Codex. It is not itself an executable simulator artifact.

## Source A

- ID suggestion: `mar7th_starrailres_v4_3_commit_7b349e39`
- Repository: `Mar-7th/StarRailRes`
- Commit: `7b349e39ee0f6f3bf814567995829b99c95e7a93`
- Commit qualification: commit message states update to version 4.3
- Path: `index_new/en/character_skills.json`
- Skill ID: `120203`
- Skill name: `Amidst the Rejoicing Clouds`
- Description locator: `content["120203"].desc`
- Level-count locator: `content["120203"].max_level`
- Raw table locator: `content["120203"].params`
- DMG magnitude locator per row: `content["120203"].params[row_index][2]`
- Immutable file URL:
  `https://github.com/Mar-7th/StarRailRes/blob/7b349e39ee0f6f3bf814567995829b99c95e7a93/index_new/en/character_skills.json`

## Source B

- ID suggestion: `kqm_srl_commit_de0e5c09`
- Repository: `KQM-git/SRL`
- Commit: `de0e5c09c8dbba9577367ad86e991fe91c4f0e36`
- Snapshot date: 2025-11-03 commit timestamp
- Path: `src/data/characters/Tingyun.json`
- Skill selector: `skills[]` where `name == "Amidst the Rejoicing Clouds"`
- Description locator: selected skill `.desc`
- Raw table locator: selected skill `.params`
- DMG magnitude locator per row: selected skill `.params[row_index][2]`
- Immutable file URL:
  `https://github.com/KQM-git/SRL/blob/de0e5c09c8dbba9577367ad86e991fe91c4f0e36/src/data/characters/Tingyun.json`

## Context-only source

- Gachabase release page: `https://hsr.gachabase.net/characters/1202/tingyun/release`
- Page identifies v4.3.0 release data.
- Ultimate Lv. 10 shown as: restore 50 Energy, increase target DMG by 50% for 2 turns.
- This page is context-only for this task because the parsed page does not expose the complete 15-row table.

## Raw tables

Both exact structured sources expose the same ordered 15 rows:

```json
[
  [50, 2, 0.20],
  [50, 2, 0.23],
  [50, 2, 0.26],
  [50, 2, 0.29],
  [50, 2, 0.32],
  [50, 2, 0.35],
  [50, 2, 0.3875],
  [50, 2, 0.425],
  [50, 2, 0.4625],
  [50, 2, 0.50],
  [50, 2, 0.53],
  [50, 2, 0.56],
  [50, 2, 0.59],
  [50, 2, 0.62],
  [50, 2, 0.65]
]
```

For each row:

- index 0: Energy restored (`50`)
- index 1: duration (`2` turns)
- index 2: DMG increase ratio

## Normalized table

```json
[
  {"normalized_trace_level": 1, "dmg_increase_percent": 20},
  {"normalized_trace_level": 2, "dmg_increase_percent": 23},
  {"normalized_trace_level": 3, "dmg_increase_percent": 26},
  {"normalized_trace_level": 4, "dmg_increase_percent": 29},
  {"normalized_trace_level": 5, "dmg_increase_percent": 32},
  {"normalized_trace_level": 6, "dmg_increase_percent": 35},
  {"normalized_trace_level": 7, "dmg_increase_percent": 38.75},
  {"normalized_trace_level": 8, "dmg_increase_percent": 42.5},
  {"normalized_trace_level": 9, "dmg_increase_percent": 46.25},
  {"normalized_trace_level": 10, "dmg_increase_percent": 50},
  {"normalized_trace_level": 11, "dmg_increase_percent": 53},
  {"normalized_trace_level": 12, "dmg_increase_percent": 56},
  {"normalized_trace_level": 13, "dmg_increase_percent": 59},
  {"normalized_trace_level": 14, "dmg_increase_percent": 62},
  {"normalized_trace_level": 15, "dmg_increase_percent": 65}
]
```

## Qualification warning

Do not claim either snapshot is byte-identical to game version 3.4. The first source is explicitly a version 4.3 repository snapshot. The second is a pinned community repository snapshot. The table can be recorded as source-backed at those snapshots while the accepted video's trace level remains unknown.
