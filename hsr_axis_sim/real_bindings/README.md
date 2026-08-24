# Reviewed Real Bindings

This namespace contains narrowly reviewed executable shells backed by accepted atomic facts. A shell is not a complete character skill or kit and must keep unresolved damage, toughness, trace-level, build, and real-video target fields outside execution.

The reviewed public execution path is `real_bindings.registry`. It returns immutable validated handles and dispatches only through static handler specifications that pair an in-code executor, validator, and pinned atomic-fact digest. Registry JSON never selects Python modules or callables. Raw binding dictionaries and low-level shell helpers remain implementation details and are not a reviewed execution contract.

The Pela Skill v0.1 shell validates one selected enemy, consumes one SP, grants 30 Energy to the actor, and removes the lexically first buff whose data explicitly marks it `removable: true`. It performs no damage or toughness operation.

The Tingyun Ultimate v0.1 shell validates one selected ally, consumes 130 Energy from Tingyun, restores 50 Energy to the selected ally with the generic clamp, and executes as an Ultimate interrupt. It does not implement the Ultimate's damage buff, damage, toughness, or real-video target.
