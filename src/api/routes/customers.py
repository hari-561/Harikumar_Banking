from typing import Literal
from src.utils.logger import setup_logger
from fastapi import APIRouter, Query, HTTPException
from fastapi import Path
from src.api.schemas import CustomerListResponse
from src.api.schemas import (
    CustomerListResponse,
    CustomerDetailResponse,
    CustomerActivityResponse,
    CustomerRiskResponse,
    CustomerDeleteResponse
)

from src.api.services.customer_service import (
    get_customers,
    get_customer_by_id,
    get_customer_activity,
    get_customer_risk
)

from src.api.schemas import (
    CustomerCreateRequest,
    CustomerMutationResponse
)

from src.api.services.customer_crud_service import (
    create_customer
)

from src.api.schemas import (
    CustomerUpdateRequest,
    CustomerMutationResponse
)

from src.api.services.customer_crud_service import (
    create_customer,
    update_customer,
    delete_customer
)

from fastapi import Depends

from src.api.security.rbac import require_roles



router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)
logger = setup_logger("banking.customer")




@router.get(
    "",
    response_model=CustomerListResponse,
    dependencies=[
        Depends(require_roles("ADMIN", "ANALYST", "VIEWER"))
    ]
)
def list_customers(

    page: int = Query(
        default=1,
        ge=1
    ),

    page_size: int = Query(
        default=20,
        ge=1,
        le=100
    ),

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

    return get_customers(
        page=page,
        page_size=page_size,
        risk_band=risk_band,
        has_payment_delay=has_payment_delay,
        min_credit_limit=min_credit_limit,
        max_credit_limit=max_credit_limit,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get(
    "/{customer_id}",
    response_model=CustomerDetailResponse,
    dependencies=[
        Depends(require_roles("ADMIN", "ANALYST", "VIEWER"))
    ]
)
def customer_detail(
    customer_id: int = Path(
        ...,
        ge=1
    )
):

    customer = get_customer_by_id(
        customer_id
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return customer



@router.get(
    "/{customer_id}/activity",
    response_model=CustomerActivityResponse,
    dependencies=[
        Depends(require_roles("ADMIN", "ANALYST", "VIEWER"))
    ]
)
def customer_activity(
    customer_id: int = Path(..., ge=1)
):

    activity = get_customer_activity(
        customer_id
    )

    if activity is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return activity


@router.get(
    "/{customer_id}/risk",
    response_model=CustomerRiskResponse,
    dependencies=[
        Depends(require_roles("ADMIN", "ANALYST", "VIEWER"))
    ]
)
def customer_risk(
    customer_id: int = Path(..., ge=1)
):

    risk = get_customer_risk(
        customer_id
    )

    if risk is None:
        raise HTTPException(
            status_code=404,
            detail="Customer risk assessment not found"
        )

    return risk


@router.post(
    "",
    response_model=CustomerMutationResponse,
    status_code=201,
    dependencies=[
        Depends(require_roles("ADMIN"))
    ]
)
def create_new_customer(
    request: CustomerCreateRequest
):

    try:
        result = create_customer(
            request
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error)
        )

    if result["status"] == "duplicate":
        raise HTTPException(
            status_code=409,
            detail="Customer already exists"
        )

    logger.info(
    "Customer created | customer_id=%s | outcome=success",
    result["customer_id"]
)

    return {
        "message":
            "Customer created successfully",

        "customer_id":
            result["customer_id"],

        "risk_score":
            result["risk_score"],

        "risk_band":
            result["risk_band"]
    }



@router.put(
    "/{customer_id}",
    response_model=CustomerMutationResponse,
    dependencies=[
        Depends(require_roles("ADMIN"))
    ]
)
def update_existing_customer(
    request: CustomerUpdateRequest,
    customer_id: int = Path(..., ge=1)
):

    try:
        result = update_customer(
            customer_id,
            request
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error)
        )

    if result["status"] == "not_found":
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    logger.info(
    "Customer updated | customer_id=%s | outcome=success",
    result["customer_id"]
)

    return {
        "message":
            "Customer updated successfully",

        "customer_id":
            result["customer_id"],

        "risk_score":
            result["risk_score"],

        "risk_band":
            result["risk_band"]
    }



@router.delete(
    "/{customer_id}",
    response_model=CustomerDeleteResponse,
    dependencies=[
        Depends(require_roles("ADMIN"))
    ]
)
def delete_existing_customer(
    customer_id: int = Path(..., ge=1)
):

    result = delete_customer(
        customer_id
    )

    if result["status"] == "not_found":
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    logger.info(
    "Customer deleted | customer_id=%s | outcome=success",
    result["customer_id"]
)

    return {
        "message":
            "Customer deleted successfully",

        "customer_id":
            result["customer_id"]
    }