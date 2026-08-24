"""Explicit one-way bridge from caller-supplied legacy Events to a runtime trace artifact."""

from __future__ import annotations

from collections.abc import Iterable

from hsr_axis_sim.runtime_adapters import adapt_legacy_event_stream
from hsr_axis_sim.runtime_exports import (
    build_runtime_trace_artifact,
    build_runtime_trace_document,
)
from hsr_axis_sim.sim.events import Event

from .model import (
    LegacyEventTraceBridgeConfig,
    LegacyEventTraceBridgeResult,
    RuntimeTraceBridgeInputError,
)


def build_legacy_event_trace_artifact(
    events: Iterable[Event],
    *,
    config: LegacyEventTraceBridgeConfig,
) -> LegacyEventTraceBridgeResult:
    """Adapt one explicit legacy event iterable once, then export it unchanged."""

    if not isinstance(config, LegacyEventTraceBridgeConfig):
        raise RuntimeTraceBridgeInputError(
            "config must be LegacyEventTraceBridgeConfig"
        )

    runtime_events = adapt_legacy_event_stream(
        events,
        start_sequence=config.start_sequence,
        config=config.adapter_config,
    )
    document = build_runtime_trace_document(
        runtime_events,
        config=config.export_config,
    )
    artifact = build_runtime_trace_artifact(
        document,
        pretty=config.pretty,
    )
    return LegacyEventTraceBridgeResult(config=config, artifact=artifact)
