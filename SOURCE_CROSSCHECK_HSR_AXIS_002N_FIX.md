# Source Cross-Check — HSR-AXIS-002N-FIX

## Source A

- Repository: `Mar-7th/StarRailRes`
- Commit: `7b349e39ee0f6f3bf814567995829b99c95e7a93`
- Path: `index_new/en/character_skills.json`
- Skill ID: `120203`
- Description field states that the Ultimate restores Energy and increases target DMG for two turns.
- `params[*][2]` contains the 15 DMG-increase ratios.

## Source B

- Repository: `KQM-git/SRL`
- Commit: `de0e5c09c8dbba9577367ad86e991fe91c4f0e36`
- Path: `src/data/characters/Tingyun.json`
- Skill name: `Amidst the Rejoicing Clouds`
- `params[*][2]` contains the same 15 DMG-increase ratios.

## Qualification

These are separate pinned repository snapshots corroborating the rows. This review does not claim that they are independent upstream extractions, nor that either snapshot is byte-identical to the accepted version-3.4 video environment.

## Exact table

| Trace level | Ratio | Percent |
|---:|---:|---:|
| 1 | 0.20 | 20% |
| 2 | 0.23 | 23% |
| 3 | 0.26 | 26% |
| 4 | 0.29 | 29% |
| 5 | 0.32 | 32% |
| 6 | 0.35 | 35% |
| 7 | 0.3875 | 38.75% |
| 8 | 0.425 | 42.5% |
| 9 | 0.4625 | 46.25% |
| 10 | 0.50 | 50% |
| 11 | 0.53 | 53% |
| 12 | 0.56 | 56% |
| 13 | 0.59 | 59% |
| 14 | 0.62 | 62% |
| 15 | 0.65 | 65% |
