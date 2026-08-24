# Trace Evidence Reports

These reports are deterministic, human-readable merges of an action-sequence trace, a non-executable semantic map, and approximate media frame anchors. They are evidence-only: media timestamps are not simulator time or AV, and unknown combat values remain unknown.

The committed reports are reproducible with `python3 -m hsr_axis_sim.tools.trace_evidence_report` using the three accepted Botu Dilemma source artifacts. They do not make the trace executable or infer combat state.
