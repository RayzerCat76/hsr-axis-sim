# LUMEN REVIEW CHECKLIST — HSR-AXIS-001I

## Must pass

- `python -m pytest -q` passes.
- All existing golden replay CLI checks pass.
- New target resolver tests are present and meaningful.
- Existing `target_ids` behavior remains backward compatible.

## Core checks

1. `targets.py` exists and has a clear resolver.
2. `UnitEffect` accepts `target_ref` while preserving `target_ids`.
3. Resolution precedence is correct:
   - `target_ref`
   - `target_ids`
   - `action.target_ids`
   - actor fallback
4. `actor` / `self` resolves to the instantiated unit id, not the character id.
5. `action_targets` resolves to the action's selected targets.
6. `all_allies`, `alive_allies`, `all_enemies`, and `alive_enemies` behave correctly.
7. Unknown target refs fail clearly.
8. Non-unit effects do not receive invalid `target_ref` kwargs.

## Data checks

- `seele_like.json` should not need `target_ids: ["seele_like"]` for self energy gain.
- `bronya_like.json` should not need `target_ids: ["bronya_like"]` for self energy gain.
- Bronya-like immediate action should target selected action targets semantically, not rely on accidental fallback behavior.
- Existing data-loaded replay still passes.

## Important edge cases

- Same character instantiated twice with different unit ids.
- Dead allies/enemies excluded from alive selectors only.
- Old replay JSON using `target_ids` still works.
- Trigger effects still work after target resolver changes.

## Scope guard

Reject or ask for revision if Codex adds any of these in 001I:

- Huroka scraping
- Yatta/HoneyHunter import adapter
- Bilibili video processing
- real official character kits
- AI search / beam search
- full HSR damage formula
- large UI rewrite

## Likely next task after pass

If 001I passes, the likely next task is:

**HSR-AXIS-001J — Enemy AI / Scripted Enemy Action Pattern MVP**

Reason: before Huroka import or AI axis search, the simulator needs deterministic enemy actions so Bilibili golden replays can include enemy turns.
