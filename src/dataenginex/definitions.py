"""Core definition models for the data layer.

Definitions are data-shaped Pydantic v2 models (ADR-003): they can be
written as Python, serialized to JSON, and exported to other formats
(ODCS, YAML) without change. Engines and runtimes consume these
models; they never redefine them.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

LOGICAL_TYPES = (
    "string",
    "integer",
    "long",
    "double",
    "decimal",
    "boolean",
    "date",
    "timestamp",
)


class Column(BaseModel):
    """One column of a Structure."""

    name: str
    dtype: str
    nullable: bool = True
    description: str = ""

    @field_validator("dtype")
    @classmethod
    def dtype_is_known(cls, value: str) -> str:
        if value not in LOGICAL_TYPES:
            raise ValueError(
                "unknown dtype " + repr(value) + "; expected one of "
                + ", ".join(LOGICAL_TYPES)
            )
        return value


class Structure(BaseModel):
    """A named set of columns: the shape of a dataset at a layer."""

    name: str
    columns: list[Column]
    primary_key: list[str] = Field(default_factory=list)
    description: str = ""

    @model_validator(mode="after")
    def columns_are_consistent(self) -> "Structure":
        names = [c.name for c in self.columns]
        if len(names) != len(set(names)):
            raise ValueError(
                "duplicate column names in structure " + self.name
            )
        missing = [k for k in self.primary_key if k not in names]
        if missing:
            raise ValueError(
                "primary key columns not in structure " + self.name
                + ": " + ", ".join(missing)
            )
        return self

    def column(self, name: str) -> Column | None:
        for c in self.columns:
            if c.name == name:
                return c
        return None


class Contract(BaseModel):
    """Quality and compatibility expectations for one Structure.

    This slice covers structural rules (not-null and unique columns).
    Freshness SLAs, sensitivity, and value rules arrive with the
    contracts milestone. Compatibility uses the ADR-004 vocabulary.
    """

    structure: str
    not_null: list[str] = Field(default_factory=list)
    unique: list[str] = Field(default_factory=list)
    compatibility: str = "backward"

    @field_validator("compatibility")
    @classmethod
    def compatibility_is_known(cls, value: str) -> str:
        allowed = ("backward", "full", "none")
        if value not in allowed:
            raise ValueError(
                "unknown compatibility " + repr(value)
                + "; expected one of " + ", ".join(allowed)
            )
        return value


class Project(BaseModel):
    """A set of definitions that `dataenginex check` validates as a whole."""

    name: str
    structures: list[Structure] = Field(default_factory=list)
    contracts: list[Contract] = Field(default_factory=list)


def validate_project(project: Project) -> list[str]:
    """Cross-reference checks that single models cannot do alone.

    Returns human-readable problems; an empty list means valid.
    This is the check the dataenginex check command runs (M0).
    """
    problems: list[str] = []
    by_name: dict[str, Structure] = {}
    for structure in project.structures:
        if structure.name in by_name:
            problems.append("duplicate structure name: " + structure.name)
        by_name[structure.name] = structure
    for contract in project.contracts:
        structure = by_name.get(contract.structure)
        if structure is None:
            problems.append(
                "contract references unknown structure: "
                + contract.structure
            )
            continue
        for col in contract.not_null:
            if structure.column(col) is None:
                problems.append(
                    "contract for " + contract.structure
                    + " requires not-null on unknown column: " + col
                )
        for col in contract.unique:
            if structure.column(col) is None:
                problems.append(
                    "contract for " + contract.structure
                    + " requires unique on unknown column: " + col
                )
    return problems
