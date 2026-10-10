
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.frontend import api_client as api


@pytest.fixture
def session():
    """Provide isolated Streamlit session state."""
    with patch.object(
        api.st,
        "session_state",
        {"access_token": "test-jwt-token"},
    ):
        yield


@pytest.fixture
def response():
    result = MagicMock()
    result.raise_for_status.return_value = None
    result.json.return_value = {"status": "ok"}
    return result


def test_api_request_success(session, response):
    with patch.object(
        api.requests, "request", return_value=response
    ) as mock_request:
        result = api.api_request("GET", "/health")

    assert result == {"status": "ok"}

    kwargs = mock_request.call_args.kwargs
    assert kwargs["method"] == "GET"
    assert kwargs["url"] == f"{api.API_BASE_URL}/health"
    assert kwargs["headers"]["Authorization"] == (
        "Bearer test-jwt-token"
    )
    assert kwargs["timeout"] == 15


def test_api_request_without_token(response):
    with (
        patch.object(api.st, "session_state", {}),
        patch.object(
            api.requests, "request", return_value=response
        ) as mock_request,
    ):
        api.api_request("GET", "/health")

    assert "Authorization" not in (
        mock_request.call_args.kwargs["headers"]
    )


def test_api_request_custom_timeout(session, response):
    with patch.object(
        api.requests, "request", return_value=response
    ) as mock_request:
        api.api_request("GET", "/health", timeout=30)

    assert mock_request.call_args.kwargs["timeout"] == 30


def test_api_request_post_payload(session, response):
    payload = {"customer_id": 100}

    with patch.object(
        api.requests, "request", return_value=response
    ) as mock_request:
        api.api_request(
            "POST",
            "/customers",
            json_data=payload,
        )

    assert mock_request.call_args.kwargs["json"] == payload


def test_api_request_query_parameters(session, response):
    params = {"page": 2, "page_size": 10}

    with patch.object(
        api.requests, "request", return_value=response
    ) as mock_request:
        api.api_request(
            "GET",
            "/customers",
            params=params,
        )

    assert mock_request.call_args.kwargs["params"] == params


def test_api_request_timeout(session):
    with patch.object(
        api.requests,
        "request",
        side_effect=requests.exceptions.Timeout(),
    ):
        with pytest.raises(
            api.APIClientError, match="timed out"
        ):
            api.api_request("GET", "/health")


def test_api_request_connection_failure(session):
    with patch.object(
        api.requests,
        "request",
        side_effect=requests.exceptions.ConnectionError(),
    ):
        with pytest.raises(
            api.APIClientError, match="Cannot connect"
        ):
            api.api_request("GET", "/health")


@pytest.mark.parametrize(
    "status_code, detail",
    [
        (400, "Invalid customer data"),
        (401, "Not authenticated"),
        (403, "Permission denied"),
        (404, "Customer not found"),
        (500, "Internal server error"),
    ],
)
def test_api_request_http_errors(
    session, status_code, detail
):
    error_response = requests.Response()
    error_response.status_code = status_code
    error_response._content = (
        '{"detail": "' + detail + '"}'
    ).encode("utf-8")

    with patch.object(
        api.requests,
        "request",
        return_value=error_response,
    ):
        with pytest.raises(api.APIClientError) as exc:
            api.api_request("GET", "/customers/999")

    assert exc.value.status_code == status_code
    assert detail in str(exc.value)


def test_api_request_invalid_json(session, response):
    response.json.side_effect = ValueError("Invalid JSON")

    with patch.object(
        api.requests, "request", return_value=response
    ):
        with pytest.raises(
            api.APIClientError, match="invalid JSON"
        ):
            api.api_request("GET", "/health")


def test_api_request_unexpected_request_error(session):
    with patch.object(
        api.requests,
        "request",
        side_effect=requests.exceptions.RequestException(
            "Mock network error"
        ),
    ):
        with pytest.raises(
            api.APIClientError,
            match="Unexpected API communication error",
        ):
            api.api_request("GET", "/health")


def test_get_customers_default_parameters():
    with patch.object(
        api, "api_request", return_value={}
    ) as mock_request:
        api.get_customers()

    kwargs = mock_request.call_args.kwargs

    assert kwargs["endpoint"] == "/customers"
    assert kwargs["params"] == {
        "page": 1,
        "page_size": 20,
        "sort_by": "customer_id",
        "sort_order": "asc",
    }


def test_get_customers_filters():
    with patch.object(
        api, "api_request", return_value={}
    ) as mock_request:
        api.get_customers(
            page=2,
            page_size=50,
            risk_band="HIGH",
            has_payment_delay=False,
            min_credit_limit=100000,
            max_credit_limit=500000,
        )

    params = mock_request.call_args.kwargs["params"]

    assert params["page"] == 2
    assert params["page_size"] == 50
    assert params["risk_band"] == "HIGH"
    assert params["has_payment_delay"] is False
    assert params["min_credit_limit"] == 100000
    assert params["max_credit_limit"] == 500000


@pytest.mark.parametrize(
    "segment",
    ["gender", "education", "marital_status", "age"],
)
def test_valid_customer_segments(segment):
    with patch.object(
        api, "api_request", return_value=[]
    ) as mock_request:
        result = api.get_customer_segments(segment)

    assert result == []
    assert mock_request.call_args.kwargs["params"] == {
        "segment": segment
    }


def test_invalid_customer_segment():
    with pytest.raises(ValueError, match="Unsupported"):
        api.get_customer_segments("invalid_segment")


def test_customer_crud_endpoints():
    with patch.object(
        api, "api_request", return_value={}
    ) as mock_request:
        api.get_customer_detail(10)
        api.get_customer_activity(10)
        api.create_customer({"customer_id": 10})
        api.update_customer(10, {"age": 35})
        api.delete_customer(10)

    calls = mock_request.call_args_list

    assert calls[0].kwargs["endpoint"] == "/customers/10"
    assert calls[1].kwargs["endpoint"] == (
        "/customers/10/activity"
    )
    assert calls[2].kwargs["method"] == "POST"
    assert calls[3].kwargs["method"] == "PUT"
    assert calls[4].kwargs["method"] == "DELETE"


def test_csv_export_success(session):
    result = MagicMock()
    result.headers = {"content-type": "text/csv"}
    result.content = b"customer_id,risk_band\n1,HIGH\n"

    with patch.object(
        api.requests, "get", return_value=result
    ) as mock_get:
        content = api.export_customers_csv(
            risk_band="HIGH"
        )

    assert content.startswith(b"customer_id")
    kwargs = mock_get.call_args.kwargs

    assert kwargs["headers"]["Authorization"] == (
        "Bearer test-jwt-token"
    )
    assert kwargs["headers"]["Accept"] == "text/csv"
    assert kwargs["params"]["risk_band"] == "HIGH"
    assert kwargs["timeout"] == 120


def test_csv_export_invalid_content_type(session):
    result = MagicMock()
    result.headers = {"content-type": "application/json"}

    with patch.object(
        api.requests, "get", return_value=result
    ):
        with pytest.raises(
            ValueError, match="did not return CSV"
        ):
            api.export_customers_csv()


def test_csv_export_network_failure(session):
    with patch.object(
        api.requests,
        "get",
        side_effect=requests.exceptions.ConnectionError(
            "Mock export failure"
        ),
    ):
        with pytest.raises(
            RuntimeError, match="Customer CSV export failed"
        ):
            api.export_customers_csv()
