# HSR Universal Combat Runtime Framework Baseline v1.0

**Research date:** 2026-07-12  
**Target live version:** 4.3  
**Policy:** Evidence First; Unknown > Guess  
**Registry total:** 200 rules  
**Status counts:** {"CONFIRMED": 107, "PARTIAL": 81, "UNKNOWN": 12}

## 1. Milestone decision

The broad mechanic-inventory phase is complete enough to begin architecture implementation.

This does **not** mean every hidden game rule is solved.

Binding policy:

```text
CONFIRMED
→ may implement with evidence-linked deterministic tests

PARTIAL
→ may reserve interfaces and policy fields
→ may not choose guessed global defaults

UNKNOWN
→ must block or require explicit unresolved/content-defined policy
```

## 2. Four distinct defensive primitives

### 2.1 Normal independent Shield

```text
Shield Value
= (Scaling Stat × Coefficient + Flat Shield)
× (1 + Shield Bonus)
```

Independent Shields:

```text
do not add into one pool
effective displayed Shield = highest remaining Shield
all active Shields absorb the full incoming damage simultaneously
weaker Shields can break in the background
```

When a background Shield breaks, its attached status effects also end.

### 2.2 Stackable Shield family

Some explicitly named Shield families override normal behavior:

```text
repeated grant adds to one family pool
pool has a cap based on a reference Skill Shield
```

Examples use 200% or 300% caps.

This must be effect data:

```text
family_id
reference_value
cap_multiplier
grant_policy
```

### 2.3 Collective Shield

A Collective Shield is one shared pool protecting multiple linked entities:

```text
all protected entities use one shared remaining value
HP does not decrease while eligible damage is covered
```

Exact simultaneous AoE deduction order remains `PARTIAL`.

### 2.4 Barrier

```text
if damage comes from an attack:
    nullify damage
except:
    DoT trigger damage
after being attacked:
    Barrier ends
```

Barrier is not a Shield value and should not generate ordinary Shield overflow.

## 3. Defense resolution architecture

Candidate order:

```text
ATTACK_CONTACT
→ BARRIER / SCRIPTED NULLIFICATION
→ DAMAGE DISTRIBUTION
→ PER-TARGET DAMAGE CALCULATION
→ COLLECTIVE POOL / LOCAL SHIELD ABSORPTION
→ HP CHANGE
→ ACTION-BATCH LETHAL RESOLUTION
```

Some content can override individual phases, but the phases must remain distinct.

## 4. Toughness Reduction formula

```text
Toughness Reduction
=
(Base Toughness Reduction + Additive Toughness Reduction)
× (1 + Toughness Reduction Increase)
× (1 + Weakness Break Efficiency + Toughness Vulnerability)
× Ability Multiplier
```

Current cap:

```text
Weakness Break Efficiency <= 300%
```

## 5. Toughness Lock / Protection

Toughness Lock is not ordinary zero-valued reduction.

```text
if target toughness is locked:
    block ordinary Toughness-reduction application
    preserve attempted reduction in trace
    evaluate explicit bypass/override effects
```

HP damage, mitigation, Shield state, and Toughness permission are separate axes.

## 6. Multiple Toughness gauges

The Runtime must support:

```text
Primary Toughness
Exo-Toughness
phase armor / special secondary gauges
```

Exo-Toughness:

```text
becomes reducible after the primary break condition
can trigger another Weakness Break
restores when the enemy recovers from Weakness Break
```

Use:

```text
ToughnessGauge[]
```

rather than one `current_toughness` field.

## 7. Current Super Break pipeline

```text
Super Break DMG
=
(Toughness Reduction / 10)
× Level Multiplier
× Ability Multiplier
× (1 + Break Effect)
× (1 + Break DMG Increase)
× (1 + Super Break DMG Increase)
× DEF Multiplier
× RES Multiplier
× Vulnerability Multiplier
× Mitigation Multiplier
× Broken Multiplier
```

Super Break:

```text
is Break DMG
cannot CRIT
does not use ordinary DMG Boost
```

Some explicit content can permit Super Break against targets that are not broken or are under Toughness Protection.

## 8. Precision and rounding

Current mechanics uses fractional Toughness values such as:

```text
1.666...
3.333...
6.666...
```

Therefore:

```text
integer-only internal Toughness storage is invalid
```

Framework rule:

```text
preserve full internal precision
never feed displayed rounded values back into state
```

Every result family needs a quantization policy:

```text
NONE
FLOOR
CEIL
ROUND_HALF_UP
ROUND_HALF_EVEN
TRUNCATE
DISPLAY_ONLY
CONTENT_DEFINED
```

The exact hidden rounding stage for:

```text
damage
healing
Shield
HP
overflow
```

remains `UNKNOWN`.

## 9. Linked defensive resources

Shared Shield pools, owner-linked Shield families, matrices, summons, and phase protections need:

```text
pool_id
owner_id
protected_entities
eligible_damage_families
deduction_order
expiration_policy
cleanup_events
```

Possible cleanup events:

```text
owner Downed
linked entity removed
Shield depleted
phase changed
countdown expired
wave ended
```

## 10. Counter remains evidence-gated

Barrier confirms:

```text
attack contact can occur
while final damage equals zero
```

Normal Shields confirm:

```text
HP damage can equal zero
while Shield damage occurs
```

This does not prove every Counter uses the same event.

Counter definitions must subscribe explicitly to:

```text
TARGET_ATTACKED
HIT_RESOLVED
DAMAGE_RESOLVED
SHIELD_DAMAGED
HP_LOST
```

until each effect is verified.

## 11. v1.0 implementation tracks

```text
1. Event / Action / Attack / Hit contexts
2. Timeline and inserted-action queue
3. Effect / Duration / Stack / Refresh
4. Modifier and Damage resolver
5. Toughness / Break / Super Break
6. Shield / Barrier / Distribution / linked defense
7. Entity / Summon / Memosprite / Lifecycle
8. Targeting / deterministic RNG / Enemy AI
9. Trace / Replay / first-divergence validator
```

## 12. Production blockers

```text
Extra Turn FIFO/LIFO frame evidence
Counter eligibility matrix
DoT snapshot/dynamic
single-effect cleanse/dispel priority
damage/heal/shield/HP rounding
generic multi-hit continuation
Bounce replacement policy
true revive AV/status re-entry
```

The framework can now be implemented around explicit policies without pretending these blockers are solved.
