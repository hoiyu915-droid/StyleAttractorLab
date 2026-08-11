"""StyleAttractorLab public package surface."""

from .core import (
    LabValidationError,
    assemble_recipe,
    catalog_records,
    create_run,
    summarize_scores,
    validate_repository,
)

__all__ = [
    "LabValidationError",
    "assemble_recipe",
    "catalog_records",
    "create_run",
    "summarize_scores",
    "validate_repository",
]

__version__ = "0.2.0"
