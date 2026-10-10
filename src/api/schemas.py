from typing import List, Literal

from pydantic import BaseModel


class CustomerListItem(BaseModel):
    customer_id: int
    age: int
    gender: str
    education: str
    marital_status: str
    credit_limit: float
    has_payment_delay: bool
    delay_month_count: int
    latest_utilization_ratio: float
    risk_score: int
    risk_band: str


class CustomerListResponse(BaseModel):
    page: int
    page_size: int
    total_records: int
    total_pages: int
    items: List[CustomerListItem]




class CustomerDemographics(BaseModel):
    gender: str
    education: str
    marital_status: str
    age: int


class CustomerCreditProfile(BaseModel):
    credit_limit: float

    delay_month_count: int
    max_delay_status: int
    has_payment_delay: bool

    total_bill_amount_6m: float
    average_bill_amount_6m: float

    total_payment_amount_6m: float
    average_payment_amount_6m: float

    latest_utilization_ratio: float

    default_next_month: int


class CustomerRiskAssessment(BaseModel):
    payment_to_bill_ratio: float | None

    delay_frequency_score: int
    delay_severity_score: int
    utilization_score: int
    payment_behavior_score: int

    risk_score: int
    risk_band: str

    rule_version: str


class CustomerDetailResponse(BaseModel):
    customer_id: int

    demographics: CustomerDemographics

    credit_profile: CustomerCreditProfile

    risk: CustomerRiskAssessment



from datetime import date


class MonthlyActivityItem(BaseModel):
    activity_month: date
    repayment_status: int
    bill_amount: float
    payment_amount: float


class CustomerActivityResponse(BaseModel):
    customer_id: int
    activity: List[MonthlyActivityItem]


class CustomerRiskResponse(BaseModel):
    customer_id: int
    payment_to_bill_ratio: float | None
    delay_frequency_score: int
    delay_severity_score: int
    utilization_score: int
    payment_behavior_score: int
    risk_score: int
    risk_band: str
    rule_version: str


class PortfolioSummaryResponse(BaseModel):
    total_customers: int
    total_credit_exposure: float
    average_credit_limit: float
    historical_defaults: int
    historical_default_rate_pct: float
    customers_with_payment_delay: int
    customers_with_repeated_delay: int
    average_latest_utilization_pct: float
    over_limit_customers: int
    total_bill_amount_6m: float
    total_payment_amount_6m: float


class RiskDistributionItem(BaseModel):
    risk_band: str
    total_customers: int
    historical_defaults: int
    historical_default_rate_pct: float
    average_risk_score: float


class MonthlyTrendItem(BaseModel):
    activity_month: date
    customer_records: int
    total_bill_amount: float
    average_bill_amount: float
    total_payment_amount: float
    average_payment_amount: float
    delayed_customers: int
    delayed_customer_rate_pct: float


class SegmentAnalyticsItem(BaseModel):
    segment: str
    total_customers: int
    average_credit_limit: float
    historical_defaults: int
    historical_default_rate_pct: float
    customers_with_payment_delay: int
    average_latest_utilization_pct: float


from pydantic import BaseModel, Field


class MonthlyActivityCreate(BaseModel):
    activity_month: date

    repayment_status: int = Field(
        ...,
        ge=-2,
        le=8
    )

    bill_amount: float

    payment_amount: float = Field(
        ...,
        ge=0
    )



class CustomerCreateRequest(BaseModel):

    customer_id: int = Field(
        ...,
        ge=1
    )

    gender_code: int

    education_code: int

    marital_status_code: int

    age: int = Field(
        ...,
        gt=0
    )

    credit_limit: float = Field(
        ...,
        gt=0
    )

    default_next_month: int = Field(
        ...,
        ge=0,
        le=1
    )

    monthly_activity: List[
        MonthlyActivityCreate
    ]



class CustomerCreateRequest(BaseModel):

    customer_id: int = Field(..., ge=1)

    gender_code: Literal[1, 2]

    education_code: Literal[
        0, 1, 2, 3, 4, 5, 6
    ]

    marital_status_code: Literal[
        0, 1, 2, 3
    ]

    age: int = Field(..., gt=0)

    credit_limit: float = Field(..., gt=0)

    default_next_month: Literal[0, 1]

    monthly_activity: List[
        MonthlyActivityCreate
    ]



class CustomerUpdateRequest(BaseModel):

    gender_code: Literal[1, 2]

    education_code: Literal[
        0, 1, 2, 3, 4, 5, 6
    ]

    marital_status_code: Literal[
        0, 1, 2, 3
    ]

    age: int = Field(..., gt=0)

    credit_limit: float = Field(..., gt=0)

    default_next_month: Literal[0, 1]

    monthly_activity: List[
        MonthlyActivityCreate
    ] = Field(
        ...,
        min_length=6,
        max_length=6
    )




class CustomerMutationResponse(BaseModel):
    message: str
    customer_id: int
    risk_score: int
    risk_band: str


class CustomerDeleteResponse(BaseModel):
    message: str
    customer_id: int


class MonthlyActivityCreate(BaseModel):
    activity_month: date

    repayment_status: int = Field(
        ...,
        ge=-2,
        le=8
    )

    bill_amount: float

    payment_amount: float = Field(
        ...,
        ge=0
    )


class CustomerCreateRequest(BaseModel):
    customer_id: int = Field(..., ge=1)

    gender_code: Literal[1, 2]

    education_code: Literal[
        0, 1, 2, 3, 4, 5, 6
    ]

    marital_status_code: Literal[
        0, 1, 2, 3
    ]

    age: int = Field(..., gt=0)

    credit_limit: float = Field(..., gt=0)

    default_next_month: Literal[0, 1]

    monthly_activity: List[
        MonthlyActivityCreate
    ] = Field(
        ...,
        min_length=6,
        max_length=6
    )


class CustomerUpdateRequest(BaseModel):
    gender_code: Literal[1, 2]

    education_code: Literal[
        0, 1, 2, 3, 4, 5, 6
    ]

    marital_status_code: Literal[
        0, 1, 2, 3
    ]

    age: int = Field(..., gt=0)

    credit_limit: float = Field(..., gt=0)

    default_next_month: Literal[0, 1]

    monthly_activity: List[
        MonthlyActivityCreate
    ] = Field(
        ...,
        min_length=6,
        max_length=6
    )


class CustomerMutationResponse(BaseModel):
    message: str
    customer_id: int
    risk_score: int
    risk_band: str


class CustomerDeleteResponse(BaseModel):
    message: str
    customer_id: int