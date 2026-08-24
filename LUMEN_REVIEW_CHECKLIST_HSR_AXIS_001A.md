# LUMEN_REVIEW_CHECKLIST_HSR_AXIS_001A

When Codex finishes HSR-AXIS-001A, paste or upload these back to Lumen:

1. `LUMEN_RESULT.md`
2. Project tree / file structure
3. All files in `hsr_axis_sim/sim/`
4. All files in `tests/`
5. Pytest output

---

## Lumen review checklist

### Scope control
- Did Codex stay inside 001A scope?
- Did Codex avoid scraping Huroka/Yatta/HoneyHunter?
- Did Codex avoid implementing AI search too early?
- Did Codex avoid hard-coding real characters?

### Timeline correctness
- Does `base_av = 10000 / speed` work?
- Does lowest `current_av` act first?
- Does global AV advance by the minimum current AV?
- Are all alive normal timeline units reduced by elapsed AV?
- Does the normal actor reset by adding base AV after turn end?

### Speed-change correctness
- Does speed increase reduce remaining AV by `old_av * old_speed / new_speed`?
- Does speed decrease increase remaining AV by the same formula?
- Is base AV recalculated after speed changes?

### Action manipulation correctness
- Does action advance subtract `base_av * percent`?
- Does action delay add `base_av * percent`?
- Is 100% advance clamped at 0?
- Is immediate action implemented as setting current AV to 0?
- Is immediate action correctly different from 100% action advance when current AV > base AV?

### Extra turn correctness
- Are extra turns resolved before normal timeline actors?
- Do extra turns avoid advancing global AV?
- Do extra turns avoid changing the unit's original normal timeline position?
- Does normal timeline resume correctly after extra turns?

### Does-not-end-turn correctness
- Does it keep the same TurnContext open?
- Does it avoid creating an extra turn?
- Does it avoid resetting AV prematurely?

### Test quality
- Are tests real mechanism tests rather than shallow import tests?
- Do tests use `pytest.approx` for float tolerance?
- Can tests be run with a simple `pytest` command?

### Code quality
- Is the engine modular?
- Are state mutations explicit?
- Is the package easy to extend to replay validation, damage, and character data?

---

## Gate decision

After review, Lumen should decide one of:

- PASS: proceed to HSR-AXIS-001B Replay Validator
- REVISE: Codex must fix 001A issues
- REBUILD: architecture is too wrong; redo 001A
