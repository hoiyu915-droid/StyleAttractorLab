"""StyleAttractorLab public package surface."""

from .core import (
    LabValidationError,
    assemble_recipe,
    create_run,
    summarize_scores,
    validate_repository,
)

__all__ = [
    "LabValidationError",
    "assemble_recipe",
    "create_run",
    "summarize_scores",
    "validate_repository",
]

__version__ = "0.1.0"

