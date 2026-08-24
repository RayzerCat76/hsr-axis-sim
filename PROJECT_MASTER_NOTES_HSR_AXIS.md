# PROJECT_MASTER_NOTES_HSR_AXIS

## Working title
HSR Axis Simulator

## Project goal
Create a deterministic Honkai: Star Rail inspired combat simulator that can help players find high-score action axes through replay validation and later AI search.

This is not just a damage calculator. The core goal is:

```text
Action-value timeline simulator + replay validator + score optimizer / beam-search axis finder
```

---

## Development workflow

Use the same style as Ray's previous technical projects:

1. Lumen defines architecture and task boundaries.
2. Codex executes one small task at a time.
3. Every task has a Task ID.
4. Every Codex task uses High reasoning when mechanics are involved.
5. Every task has clear deliverables.
6. Codex must produce `LUMEN_RESULT.md`.
7. Lumen reviews before the next task starts.
8. No phase jump: simulator core first, AI later.

---

## Planned task sequence

### HSR-AXIS-001A
Action-value core engine.

### HSR-AXIS-001B
Replay validator using manually recorded golden replay JSON.

### HSR-AXIS-001C
Simplified Bronya + Seele style sample replay.

### HSR-AXIS-001D
Buff/debuff duration and turn-context audit.

### HSR-AXIS-002A
Character / skill / effect JSON schema.

### HSR-AXIS-002B
Manual sample characters using effect primitives.

### HSR-AXIS-002C
External data adapter planning for Huroka/Yatta/HoneyHunter-like sources.

### HSR-AXIS-003A
Damage formula MVP.

### HSR-AXIS-004A
Enemy AI and deterministic enemy action scripts.

### HSR-AXIS-005A
Beam search axis finder.

### HSR-AXIS-006A
UI / visualization.

---

## Key design rule

External databases provide raw text and numbers.
The simulator needs executable mechanics.

So the data layers should be:

```text
Raw external data -> normalized character data -> executable effect primitives
```

Do not directly simulate natural-language skill descriptions.

---

## Important mechanics to preserve

- Action value
- Speed
- Action advance
- Action delay
- Speed change AV recalculation
- Immediate action
- Extra turn
- Does not end current turn
- Buff/debuff duration
- Skill points
- Energy
- Ultimate insertion
- Follow-up attacks
- Summons / extra units
- Enemy target selection / taunt
- Forced RNG for replay validation

---

## Validation philosophy

The simulator should be checked against public gameplay video traces.

Best first validation source:
- a low-randomness no-reset / no-RNG-heavy axis video
- character builds shown at the end
- manually recorded action order
- manually recorded SP, energy, AV, buff, toughness, and HP checkpoints

The replay validator should support forced RNG:

```json
{
  "forced_rng": {
    "crit": true,
    "effect_hit": true,
    "enemy_target": "ally_1"
  }
}
```

This lets the simulator answer:

```text
If the same random outcomes happen, does the simulator reproduce the video?
```

That is the correct validation goal.
