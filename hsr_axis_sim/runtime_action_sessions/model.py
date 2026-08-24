"""Immutable contracts for explicit multi-action capture sessions."""

from __future__ import annotations

from dataclasses import dataclass

from hsr_axis_sim.runtime_action_captures import SingleActionEventCaptureResult
from hsr_axis_sim.runtime_adapters import LegacyEventAdapterConfig
from hsr_axis_sim.runtime_capture_cursors import PendingEventCaptureCursor
from hsr_axis_sim.runtime_exports import TraceExportConfig
from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.turn_context import TurnContext


class RuntimeActionSessionError(RuntimeError):
    """Base class for controlled multi-action session failures."""


class RuntimeActionSessionInputError(RuntimeActionSessionError):
    """Raised when session input or result provenance is invalid."""


class MultiActionCaptureSessionFailure(RuntimeActionSessionError):
    """Raised when one state-mutating action/capture step fails.

    The completed results and last_successful_cursor describe only confirmed
    completed boundaries before the failed step. They do not imply that retry
    from that cursor is safe because the failed step may have mutated state or
    appended uncaptured events.
    """

    def __init__(
        self,
        *,
        failed_action_index: int,
        failed_action_id: str,
        completed_results: tuple[SingleActionEventCaptureResult, ...],
        last_successful_cursor: PendingEventCaptureCursor,
    ) -> None:
        if not isinstance(failed_action_index, int) or isinstance(failed_action_index, bool) or failed_action_index < 0:
            raise RuntimeActionSessionInputError(
                "failed_action_index must be a non-negative integer"
            )
        if not isinstance(failed_action_id, str) or not failed_action_id.strip():
            raise RuntimeActionSessionInputError(
                "failed_action_id must be a non-empty string"
            )
        if not isinstance(completed_results, tuple) or any(
            not isinstance(item, SingleActionEventCaptureResult)
            for item in completed_results
        ):
            raise RuntimeActionSessionInputError(
                "completed_results must be a tuple of SingleActionEventCaptureResult values"
            )
        if len(completed_results) != failed_action_index:
            raise RuntimeActionSessionInputError(
                "completed_results length must equal failed_action_index"
            )
        if not isinstance(last_successful_cursor, PendingEventCaptureCursor):
            raise RuntimeActionSessionInputError(
                "last_successful_cursor has an invalid type"
            )
        if completed_results and completed_results[-1].next_cursor != last_successful_cursor:
            raise RuntimeActionSessionInputError(
                "last_successful_cursor must equal the final completed result next_cursor"
            )
        self.failed_action_index = failed_action_index
        self.failed_action_id = failed_action_id
        self.completed_results = completed_results
        self.last_successful_cursor = last_successful_cursor
        super().__init__(
            f"multi-action capture session failed at action index "
            f"{failed_action_index} ({failed_action_id!r})"
        )


@dataclass(frozen=True)
class ExplicitActionCaptureStep:
    action: Action
    turn_context: TurnContext | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.action, Action):
            raise RuntimeActionSessionInputError("action has an invalid type")
        if self.turn_context is not None and not isinstance(self.turn_context, TurnContext):
            raise RuntimeActionSessionInputError(
                "turn_context must be TurnContext or None"
            )


@dataclass(frozen=True)
class MultiActionCaptureSessionConfig:
    initial_cursor: PendingEventCaptureCursor
    adapter_config: LegacyEventAdapterConfig
    segment_export_configs: tuple[TraceExportConfig, ...]
    pretty: bool

    def __post_init__(self) -> None:
        if not isinstance(self.initial_cursor, PendingEventCaptureCursor):
            raise RuntimeActionSessionInputError("initial_cursor has an invalid type")
        if not isinstance(self.adapter_config, LegacyEventAdapterConfig):
            raise RuntimeActionSessionInputError("adapter_config has an invalid type")
        if not isinstance(self.segment_export_configs, tuple):
            raise RuntimeActionSessionInputError(
                "segment_export_configs must be a tuple"
            )
        if any(
            not isinstance(item, TraceExportConfig)
            for item in self.segment_export_configs
        ):
            raise RuntimeActionSessionInputError(
                "segment_export_configs must contain only TraceExportConfig values"
            )
        if not isinstance(self.pretty, bool):
            raise RuntimeActionSessionInputError("pretty must be a bool")


@dataclass(frozen=True)
class MultiActionCaptureSessionResult:
    config: MultiActionCaptureSessionConfig
    steps: tuple[ExplicitActionCaptureStep, ...]
    results: tuple[SingleActionEventCaptureResult, ...]
    final_cursor: PendingEventCaptureCursor

    def __post_init__(self) -> None:
        if not isinstance(self.config, MultiActionCaptureSessionConfig):
            raise RuntimeActionSessionInputError("config has an invalid type")
        if not isinstance(self.steps, tuple) or not self.steps:
            raise RuntimeActionSessionInputError("steps must be a non-empty tuple")
        if any(not isinstance(item, ExplicitActionCaptureStep) for item in self.steps):
            raise RuntimeActionSessionInputError(
                "steps must contain only ExplicitActionCaptureStep values"
            )
        if not isinstance(self.results, tuple) or any(
            not isinstance(item, SingleActionEventCaptureResult)
            for item in self.results
        ):
            raise RuntimeActionSessionInputError(
                "results must be a tuple of SingleActionEventCaptureResult values"
            )
        if len(self.results) != len(self.steps):
            raise RuntimeActionSessionInputError(
                "results length must equal steps length"
            )
        if len(self.config.segment_export_configs) != len(self.steps):
            raise RuntimeActionSessionInputError(
                "segment_export_configs length must equal steps length"
            )
        if not isinstance(self.final_cursor, PendingEventCaptureCursor):
            raise RuntimeActionSessionInputError("final_cursor has an invalid type")

        cursor = self.config.initial_cursor
        for index, (step, export_config, result) in enumerate(
            zip(self.steps, self.config.segment_export_configs, self.results)
        ):
            if result.action_id != step.action.id or result.actor_id != step.action.actor_id:
                raise RuntimeActionSessionInputError(
                    f"results[{index}] action identity must match steps[{index}]"
                )
            request = result.request
            if request.cursor != cursor:
                raise RuntimeActionSessionInputError(
                    f"results[{index}] cursor must equal the previous accepted cursor"
                )
            bridge = request.bridge_config
            if bridge.adapter_config != self.config.adapter_config:
                raise RuntimeActionSessionInputError(
                    f"results[{index}] adapter_config must match session config"
                )
            if bridge.start_sequence != cursor.next_runtime_sequence:
                raise RuntimeActionSessionInputError(
                    f"results[{index}] start_sequence must match current cursor"
                )
            if bridge.export_config != export_config:
                raise RuntimeActionSessionInputError(
                    f"results[{index}] export_config must match declared segment config"
                )
            if bridge.pretty is not self.config.pretty:
                raise RuntimeActionSessionInputError(
                    f"results[{index}] pretty flag must match session config"
                )
            if step.turn_context is not None and result.turn_context is not step.turn_context:
                raise RuntimeActionSessionInputError(
                    f"results[{index}] must preserve caller TurnContext identity"
                )
            cursor = result.next_cursor

        if self.final_cursor != cursor:
            raise RuntimeActionSessionInputError(
                "final_cursor must equal the final accepted result next_cursor"
            )

    @property
    def action_count(self) -> int:
        return len(self.steps)
