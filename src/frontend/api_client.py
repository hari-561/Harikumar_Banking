import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# Load .env from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
).rstrip("/")


class APIClientError(Exception):
    """Raised when a FastAPI request fails."""

    def __init__(self, message, status_code=None):
        self.status_code = status_code
        super().__init__(message)


def api_request(
    method,
    endpoint,
    params=None,
    json_data=None,
    timeout=15
):
    """
    Send an HTTP request to the FastAPI backend.

    Returns:
        Parsed JSON response.

    Raises:
        APIClientError on connection,
        timeout, HTTP, or response errors.
    """

    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"

    try:
        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            timeout=timeout
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:
        raise APIClientError(
            "The API request timed out. Please try again."
        )

    except requests.exceptions.ConnectionError:
        raise APIClientError(
            "Cannot connect to FastAPI. "
            "Check whether the backend server is running."
        )

    except requests.exceptions.HTTPError as error:
        status_code = error.response.status_code

        try:
            detail = error.response.json().get(
                "detail",
                "API request failed"
            )
        except ValueError:
            detail = "API request failed"

        if isinstance(detail, (dict, list)):
            detail = str(detail)

        raise APIClientError(
            str(detail),
            status_code=status_code
        )

    except ValueError:
        raise APIClientError(
            "The API returned an invalid JSON response."
        )

    except requests.exceptions.RequestException as error:
        raise APIClientError(
            f"Unexpected API communication error: {error}"
        )


def get_health():
    return api_request(
        method="GET",
        endpoint="/health"
    )

def get_portfolio_summary():
    return api_request(
        method="GET",
        endpoint="/analytics/summary"
    )

def get_risk_distribution():
    return api_request(
        method="GET",
        endpoint="/analytics/risk-distribution"
    )

def get_monthly_trends():
    return api_request(
        method="GET",
        endpoint="/analytics/monthly-trends"
    )

def get_customer_segments(segment):
    allowed_segments = {
        "gender",
        "education",
        "marital_status",
        "age",
    }

    if segment not in allowed_segments:
        raise ValueError(
            f"Unsupported segment type: {segment}"
        )

    return api_request(
        method="GET",
        endpoint="/analytics/segments",
        params={"segment": segment},
    )



def get_customers(
    page=1,
    page_size=20,
    risk_band=None,
    has_payment_delay=None,
    min_credit_limit=None,
    max_credit_limit=None,
    sort_by="customer_id",
    sort_order="asc",
):
    params = {
        "page": page,
        "page_size": page_size,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }

    optional_params = {
        "risk_band": risk_band,
        "has_payment_delay": has_payment_delay,
        "min_credit_limit": min_credit_limit,
        "max_credit_limit": max_credit_limit,
    }

    params.update({
        key: value
        for key, value in optional_params.items()
        if value is not None
    })

    return api_request(
        method="GET",
        endpoint="/customers",
        params=params,
    )


def get_customer_detail(customer_id):
    return api_request(
        method="GET",
        endpoint=f"/customers/{customer_id}",
    )


def get_customer_activity(customer_id):
    return api_request(
        method="GET",
        endpoint=f"/customers/{customer_id}/activity",
    )


def create_customer(payload):
    return api_request(
        method="POST",
        endpoint="/customers",
        json_data=payload,
    )

def update_customer(customer_id, payload):
    return api_request(
        method="PUT",
        endpoint=f"/customers/{customer_id}",
        json_data=payload,
    )

def delete_customer(customer_id):
    return api_request(
        method="DELETE",
        endpoint=f"/customers/{customer_id}",
    )


def export_customers_csv(
    risk_band=None,
    has_payment_delay=None,
    min_credit_limit=None,
    max_credit_limit=None,
    sort_by="customer_id",
    sort_order="asc",
):
    import requests

    params = {
        "sort_by": sort_by,
        "sort_order": sort_order,
    }

    optional_filters = {
        "risk_band": risk_band,
        "has_payment_delay": has_payment_delay,
        "min_credit_limit": min_credit_limit,
        "max_credit_limit": max_credit_limit,
    }

    params.update({
        key: value
        for key, value in optional_filters.items()
        if value is not None
    })

    # Use the same API base URL configured for
    # the existing api_request() function.
    # Replace this fallback if your API client
    # uses a different configuration.
    base_url = "http://127.0.0.1:8000"

    try:
        response = requests.get(
            f"{base_url}/export/customers",
            params=params,
            timeout=120,
            headers={"Accept": "text/csv"},
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "content-type", ""
        ).lower()

        if "text/csv" not in content_type:
            raise ValueError(
                "The export API did not return CSV data."
            )

        return response.content

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Customer CSV export failed: {exc}"
        ) from exc



def get_segment_analytics(segment):
    allowed_segments = {
        "gender",
        "education",
        "marital_status",
        "age",
    }

    if segment not in allowed_segments:
        raise ValueError(f"Unsupported segment: {segment}")

    return api_request(
        "GET",
        "/analytics/segments",
        params={"segment": segment},
    )