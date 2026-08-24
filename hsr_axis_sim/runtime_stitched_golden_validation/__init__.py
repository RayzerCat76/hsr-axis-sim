"""Explicit stitched-actual handoff into accepted Golden Replay validation."""

from .model import (
    StitchedActualGoldenValidationResult,
    StitchedGoldenValidationError,
    StitchedGoldenValidationInputError,
)
from .validate import (
    render_stitched_actual_golden_validation_text,
    validate_stitched_actual_against_golden,
)

__all__ = [
    "StitchedActualGoldenValidationResult",
    "StitchedGoldenValidationError",
    "StitchedGoldenValidationInputError",
    "render_stitched_actual_golden_validation_text",
    "validate_stitched_actual_against_golden",
]
