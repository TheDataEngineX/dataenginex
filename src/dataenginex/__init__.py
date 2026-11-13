"""dataenginex - Layer 0 foundation package.

Definitions as code, engines as plugins. This package holds the data
layer abstractions (Source, Structure, Contract, Layer, Transform,
Pipeline, Serving, Run) and one local engine (DuckDB). It must never
import from the runtime or any app.
"""

from dataenginex.definitions import (
    Column,
    Contract,
    Project,
    Structure,
    validate_project,
)

__version__ = "0.0.1"

__all__ = [
    "Column",
    "Contract",
    "Project",
    "Structure",
    "__version__",
    "validate_project",
]
