"""The canonical retail example (decision 0022): the M0 golden dataset.

Source paths are relative to this folder. Run it with:

    from dataenginex import run_pipeline
    run_pipeline(project, "retail_pipeline", "examples/retail")
"""

from dataenginex import (
    Column,
    Contract,
    Pipeline,
    Project,
    Source,
    Structure,
    Transform,
)

project = Project(
    name="retail",
    structures=[
        Structure(
            name="orders",
            columns=[
                Column(name="order_id", dtype="string", nullable=False),
                Column(name="customer_id", dtype="string", nullable=False),
                Column(name="ordered_at", dtype="timestamp", nullable=False),
                Column(name="status", dtype="string"),
            ],
            primary_key=["order_id"],
        ),
        Structure(
            name="gold_daily_sales",
            columns=[
                Column(name="order_date", dtype="date", nullable=False),
                Column(name="revenue", dtype="double", nullable=False),
                Column(name="units", dtype="long", nullable=False),
            ],
            primary_key=["order_date"],
        ),
    ],
    contracts=[
        Contract(
            structure="orders",
            not_null=["order_id", "customer_id", "ordered_at"],
            unique=["order_id"],
        ),
        Contract(
            structure="gold_daily_sales",
            not_null=["order_date", "revenue", "units"],
            unique=["order_date"],
        ),
    ],
    pipelines=[
        Pipeline(
            name="retail_pipeline",
            sources=[
                Source(name="orders", path="orders.csv"),
                Source(name="order_lines", path="order_lines.csv"),
                Source(name="products", path="products.csv"),
                Source(name="customers", path="customers.csv"),
            ],
            silver=[
                Transform(
                    name="orders_joined",
                    sql="""
                        SELECT o.order_id, o.customer_id, o.ordered_at, o.status,
                               c.name AS customer_name, c.city
                        FROM orders o
                        LEFT JOIN customers c USING (customer_id)
                    """,
                ),
            ],
            gold=[
                Transform(
                    name="gold_daily_sales",
                    sql="""
                        SELECT CAST(o.ordered_at AS DATE) AS order_date,
                               SUM(CAST(l.quantity AS INTEGER)
                                   * CAST(l.unit_price AS DOUBLE)) AS revenue,
                               SUM(CAST(l.quantity AS INTEGER)) AS units
                        FROM orders o
                        JOIN order_lines l USING (order_id)
                        GROUP BY 1
                    """,
                ),
            ],
        ),
    ],
)
