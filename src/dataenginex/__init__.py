"""dataenginex - Layer 0 foundation package.

Definitions as code, engines as plugins. This package holds the data
layer abstractions (Source, Structure, Contract, Layer, Transform,
Pipeline, Serving, Run) and one local engine (DuckDB). It must never
import from the runtime or any app.
"""

from dataenginex.definitions import (
    Column,
    Contract,
    Pipeline,
    Project,
    Source,
    Structure,
    Transform,
    validate_project,
)
from dataenginex.engine import run_pipeline
from dataenginex.receipt import Receipt
from dataenginex.state import StateStore

__version__ = "0.0.1"

__all__ = [
    "Column",
    "Contract",
    "Pipeline",
    "Project",
    "Receipt",
    "Source",
    "StateStore",
    "Structure",
    "Transform",
    "__version__",
    "run_pipeline",
    "validate_project",
]
