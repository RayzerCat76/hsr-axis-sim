"""Read-only first-divergence selection and deterministic text reporting."""

from .model import (
    RuntimeTraceDivergenceError,
    RuntimeTraceDivergenceInputError,
    RuntimeTraceFirstDivergence,
    RuntimeTraceFirstDivergenceReport,
)
from .report import build_first_divergence_report, render_first_divergence_text

__all__ = [
    "RuntimeTraceDivergenceError",
    "RuntimeTraceDivergenceInputError",
    "RuntimeTraceFirstDivergence",
    "RuntimeTraceFirstDivergenceReport",
    "build_first_divergence_report",
    "render_first_divergence_text",
]
