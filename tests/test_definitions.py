import pytest
from pydantic import ValidationError

from dataenginex import (
    Column,
    Contract,
    Project,
    Structure,
    validate_project,
)


def retail_orders() -> Structure:
    return Structure(
        name="orders",
        columns=[
            Column(name="order_id", dtype="long", nullable=False),
            Column(name="store_id", dtype="string", nullable=False),
            Column(name="total", dtype="decimal"),
            Column(name="ordered_at", dtype="timestamp", nullable=False),
        ],
        primary_key=["order_id"],
    )


def test_valid_project_has_no_problems():
    project = Project(
        name="retail",
        structures=[retail_orders()],
        contracts=[
            Contract(
                structure="orders",
                not_null=["order_id", "store_id"],
                unique=["order_id"],
            )
        ],
    )
    assert validate_project(project) == []


def test_unknown_dtype_rejected():
    with pytest.raises(ValidationError):
        Column(name="x", dtype="json")


def test_duplicate_columns_rejected():
    with pytest.raises(ValidationError):
        Structure(
            name="bad",
            columns=[
                Column(name="a", dtype="string"),
                Column(name="a", dtype="string"),
            ],
        )


def test_primary_key_must_exist():
    with pytest.raises(ValidationError):
        Structure(
            name="bad",
            columns=[Column(name="a", dtype="string")],
            primary_key=["missing"],
        )


def test_contract_unknown_structure_reported():
    project = Project(
        name="retail",
        structures=[retail_orders()],
        contracts=[Contract(structure="nope")],
    )
    problems = validate_project(project)
    assert len(problems) == 1
    assert "nope" in problems[0]


def test_contract_unknown_columns_reported():
    project = Project(
        name="retail",
        structures=[retail_orders()],
        contracts=[
            Contract(
                structure="orders",
                not_null=["ghost"],
                unique=["phantom"],
            )
        ],
    )
    problems = validate_project(project)
    assert len(problems) == 2


def test_definitions_round_trip_json():
    project = Project(
        name="retail",
        structures=[retail_orders()],
        contracts=[Contract(structure="orders", unique=["order_id"])],
    )
    restored = Project.model_validate_json(project.model_dump_json())
    assert restored == project
