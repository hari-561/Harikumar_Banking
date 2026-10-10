import csv
import io

from typing import Literal

from fastapi import (
    APIRouter,
    HTTPException,
    Query
)

from fastapi.responses import StreamingResponse

from src.api.services.export_service import (
    get_customers_for_export
)


router = APIRouter(
    prefix="/export",
    tags=["Export"]
)


@router.get("/customers")
def export_customers(

    risk_band: Literal[
        "LOW",
        "MEDIUM",
        "HIGH"
    ] | None = None,

    has_payment_delay: bool | None = None,

    min_credit_limit: float | None = Query(
        default=None,
        ge=0
    ),

    max_credit_limit: float | None = Query(
        default=None,
        ge=0
    ),

    sort_by: Literal[
        "customer_id",
        "credit_limit",
        "latest_utilization_ratio",
        "delay_month_count",
        "risk_score"
    ] = "customer_id",

    sort_order: Literal[
        "asc",
        "desc"
    ] = "asc"
):

    if (
        min_credit_limit is not None
        and max_credit_limit is not None
        and min_credit_limit > max_credit_limit
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "min_credit_limit cannot be greater "
                "than max_credit_limit"
            )
        )

    rows = get_customers_for_export(
        risk_band=risk_band,
        has_payment_delay=has_payment_delay,
        min_credit_limit=min_credit_limit,
        max_credit_limit=max_credit_limit,
        sort_by=sort_by,
        sort_order=sort_order
    )

    output = io.StringIO()

    writer = csv.writer(output)

    headers = [
        "customer_id",
        "gender",
        "education",
        "marital_status",
        "age",
        "credit_limit",
        "delay_month_count",
        "max_delay_status",
        "has_payment_delay",
        "total_bill_amount_6m",
        "average_bill_amount_6m",
        "total_payment_amount_6m",
        "average_payment_amount_6m",
        "latest_utilization_ratio",
        "payment_to_bill_ratio",
        "risk_score",
        "risk_band",
        "rule_version"
    ]

    writer.writerow(headers)

    for row in rows:

        writer.writerow([
            row["customer_id"],
            row["gender"],
            row["education"],
            row["marital_status"],
            row["age"],
            row["credit_limit"],
            row["delay_month_count"],
            row["max_delay_status"],
            bool(row["has_payment_delay"]),
            row["total_bill_amount_6m"],
            row["average_bill_amount_6m"],
            row["total_payment_amount_6m"],
            row["average_payment_amount_6m"],
            row["latest_utilization_ratio"],
            row["payment_to_bill_ratio"],
            row["risk_score"],
            row["risk_band"],
            row["rule_version"]
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                'attachment; filename="customers_export.csv"'
        }
    )