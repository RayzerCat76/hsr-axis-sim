# LUMEN REVIEW CHECKLIST — HSR-AXIS-001H Data Schema

Use this checklist after Codex returns 001H.

## 1. Scope control

- [ ] Did Codex avoid scraping Huroka/Yatta/HoneyHunter/Bilibili?
- [ ] Did Codex avoid AI axis search?
- [ ] Did Codex avoid implementing a large set of real characters?
- [ ] Did Codex avoid rewriting the simulator core unnecessarily?
- [ ] Did all previous tests still pass?
- [ ] Did all previous golden replay CLIs still pass?

## 2. Schema quality

- [ ] Is there a clear CharacterSpec?
- [ ] Is there a clear BaseStatsSpec?
- [ ] Is there a clear SkillSpec?
- [ ] Is there a clear TeamSpec / UnitInstanceSpec?
- [ ] Are triggers represented through the existing Trigger model rather than special character code?
- [ ] Are effects represented as existing effect primitives?
- [ ] Are skills data-driven and executable?
- [ ] Is the schema internal/normalized rather than Huroka-specific?

## 3. Loader quality

- [ ] Can CharacterSpec load from JSON?
- [ ] Can Unit be instantiated from CharacterSpec + instance overrides?
- [ ] Can BattleState be built from a team spec?
- [ ] Can SkillSpec become an Action?
- [ ] Do character-owned trigger templates get the correct instantiated owner_id?
- [ ] Do stat overrides apply only to known fields?
- [ ] Are duplicate unit ids rejected?
- [ ] Are duplicate skill ids rejected?
- [ ] Are unknown character ids rejected?
- [ ] Are unknown effect types rejected?

## 4. Sample data quality

- [ ] Is `seele_like.json` simplified and generic?
- [ ] Is `bronya_like.json` simplified and generic?
- [ ] Is `generic_enemy.json` simplified and generic?
- [ ] Is `bronya_seele_team.json` readable and minimal?
- [ ] Does the sample avoid full official skill text?

## 5. Replay / validation quality

- [ ] Is there a data-loaded replay or equivalent test?
- [ ] Does it demonstrate on-kill extra turn through data-loaded triggers?
- [ ] Does it demonstrate at least one data-loaded support skill or action construction?
- [ ] Does it check HP, extra_turn_stack, and actor order?
- [ ] If ReplayValidator was extended, is the change minimal and backward-compatible?

## 6. Tests

- [ ] Are schema failures tested?
- [ ] Are loader failures tested?
- [ ] Are skill/action construction tests included?
- [ ] Is character-owned trigger attachment tested?
- [ ] Is the data-loaded Bronya-like + Seele-like flow tested?
- [ ] Are tests meaningful rather than superficial?

## 7. Red flags

Fail or request fix if:

- [ ] Character data is only natural language and not executable.
- [ ] Huroka-specific raw schema leaks into core simulator.
- [ ] Real character kits are hard-coded in Python instead of data.
- [ ] ReplayValidator backward compatibility is broken.
- [ ] Old golden replays no longer pass.
- [ ] Unknown/invalid data silently defaults instead of raising clear errors.
- [ ] The project jumps into scraping or AI search prematurely.

## Gate decision

- [ ] PASS — 001H accepted.
- [ ] PASS WITH FIX — small 001H-FIX needed before next task.
- [ ] FAIL — return to Codex with specific corrections.

Recommended next after 001H if passed:

- **HSR-AXIS-001I — Enemy Action Pattern / Basic Enemy AI MVP**, if the simulator still needs enemy turns for video replay matching.
- Or **HSR-AXIS-002A — External Data Adapter Planning**, if the data layer is clean and stable.
