from typing import List, Literal

from fastapi import APIRouter, Query
from src.api.schemas import (
    PortfolioSummaryResponse,
    RiskDistributionItem,
    MonthlyTrendItem,
    SegmentAnalyticsItem
)

from src.api.services.analytics_service import (
    get_portfolio_summary,
    get_risk_distribution,
    get_monthly_trends,
    get_segment_analytics
)


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get(
    "/summary",
    response_model=PortfolioSummaryResponse
)
def portfolio_summary():
    return get_portfolio_summary()


@router.get(
    "/risk-distribution",
    response_model=List[RiskDistributionItem]
)
def risk_distribution():
    return get_risk_distribution()


@router.get(
    "/monthly-trends",
    response_model=List[MonthlyTrendItem]
)
def monthly_trends():
    return get_monthly_trends()



@router.get(
    "/segments",
    response_model=List[SegmentAnalyticsItem]
)
def segment_analytics(
    segment: Literal[
        "gender",
        "education",
        "marital_status",
        "age"
    ] = Query(...)
):

    return get_segment_analytics(segment)