
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.frontend.pages import customer_explorer as explorer


class Session(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        self[name] = value


@pytest.fixture
def ui():
    state = Session()

    response = {
        "items": [],
        "total_records": 0,
        "total_pages": 0,
        "page": 1,
    }

    def selectbox(label, options, **kwargs):
        return options[kwargs.get("index", 0)]

    with (
        patch.object(explorer.st, "session_state", state),
        patch.object(
            explorer.st, "form",
            return_value=nullcontext(),
        ),
        patch.object(
            explorer.st, "columns",
            side_effect=lambda sizes, **kwargs: tuple(
                nullcontext()
                for _ in range(
                    sizes if isinstance(sizes, int)
                    else len(sizes)
                )
            ),
        ),
        patch.object(
            explorer.st, "number_input",
            side_effect=lambda label, **kwargs:
                kwargs.get("value", 0),
        ) as number_input,
        patch.object(
            explorer.st, "selectbox",
            side_effect=selectbox,
        ) as select,
        patch.object(
            explorer.st, "form_submit_button",
            return_value=False,
        ) as submit,
        patch.object(
            explorer, "render_section_header"
        ),
        patch.object(
            explorer, "get_customers",
            return_value=response,
        ) as get_customers,
        patch.object(
            explorer, "get_customer_detail"
        ) as get_detail,
        patch.object(
            explorer, "get_customer_activity"
        ) as get_activity,
        patch.object(
            explorer, "render_customer_profile"
        ) as render_profile,
        patch.object(
            explorer, "render_customer_activity"
        ) as render_activity,
        patch.object(
            explorer, "render_api_error"
        ) as show_error,
    ):
        yield SimpleNamespace(
            state=state,
            number_input=number_input,
            select=select,
            submit=submit,
            get_customers=get_customers,
            get_detail=get_detail,
            get_activity=get_activity,
            render_profile=render_profile,
            render_activity=render_activity,
            show_error=show_error,
        )


def test_default_filters_are_initialized(ui):
    explorer.render_customer_explorer()

    assert ui.state["explorer_page"] == 1
    assert ui.state["explorer_filters"] == {
        "risk_band": None,
        "has_payment_delay": None,
        "page_size": 20,
        "min_credit_limit": None,
        "max_credit_limit": None,
        "sort_by": "customer_id",
        "sort_order": "asc",
    }

    ui.get_customers.assert_called_once_with(
        page=1,
        **ui.state["explorer_filters"],
    )


def test_existing_filters_are_preserved(ui):
    saved_filters = {
        "risk_band": "HIGH",
        "has_payment_delay": True,
        "page_size": 50,
        "min_credit_limit": 100000.0,
        "max_credit_limit": None,
        "sort_by": "risk_score",
        "sort_order": "desc",
    }

    ui.state["explorer_filters"] = saved_filters.copy()
    ui.state["explorer_page"] = 3

    explorer.render_customer_explorer()

    assert ui.state["explorer_filters"] == saved_filters
    assert ui.state["explorer_page"] == 3

    ui.get_customers.assert_called_once_with(
        page=3,
        **saved_filters,
    )


def test_applying_filters_resets_pagination(ui):
    ui.state["explorer_filters"] = {
        "risk_band": None,
        "page_size": 20,
    }
    ui.state["explorer_page"] = 5

    def submit(label, **kwargs):
        return label == "Apply Filters"

    def select(label, options, **kwargs):
        if label == "Risk Band":
            return "HIGH"
        if label == "Payment Delay":
            return "Yes"
        if label == "Records Per Page":
            return 50
        if label == "Sort By":
            return "Risk Score"
        if label == "Sort Order":
            return "desc"
        return options[0]

    with (
        patch.object(
            explorer.st,
            "form_submit_button",
            side_effect=submit,
        ),
        patch.object(
            explorer.st,
            "selectbox",
            side_effect=select,
        ),
    ):
        explorer.render_customer_explorer()

    filters = ui.state["explorer_filters"]

    assert ui.state["explorer_page"] == 1
    assert filters["risk_band"] == "HIGH"
    assert filters["has_payment_delay"] is True
    assert filters["page_size"] == 50
    assert filters["sort_by"] == "risk_score"
    assert filters["sort_order"] == "desc"

    assert ui.get_customers.call_args.kwargs["page"] == 1


def test_invalid_credit_limit_range_blocks_request(ui):
    def number_input(label, **kwargs):
        if label == "Minimum Credit Limit":
            return 200000.0
        if label.startswith("Maximum Credit Limit"):
            return 100000.0
        return kwargs.get("value", 0)

    with (
        patch.object(
            explorer.st,
            "number_input",
            side_effect=number_input,
        ),
        patch.object(
            explorer.st,
            "error",
        ) as show_error,
    ):
        explorer.render_customer_explorer()

    show_error.assert_called_once()
    assert "Maximum credit limit" in (
        show_error.call_args.args[0]
    )
    ui.get_customers.assert_not_called()


def test_customer_lookup_stores_selected_id(ui):
    ui.get_detail.return_value = {
        "customer_id": 42
    }

    def submit(label, **kwargs):
        return label == "Find Customer"

    def number_input(label, **kwargs):
        if label == "Find Customer by ID":
            return 42
        return kwargs.get("value", 0)

    with (
        patch.object(
            explorer.st,
            "form_submit_button",
            side_effect=submit,
        ),
        patch.object(
            explorer.st,
            "number_input",
            side_effect=number_input,
        ),
    ):
        explorer.render_customer_explorer()

    assert ui.state["explorer_selected_customer"] == 42
    assert ui.get_detail.call_count == 2
    ui.get_activity.assert_called_once_with(42)
    ui.render_profile.assert_called_once_with(
        {"customer_id": 42}
    )


def test_customer_listing_api_failure(ui):
    ui.get_customers.side_effect = explorer.APIClientError(
        "Customer service unavailable"
    )

    explorer.render_customer_explorer()

    ui.show_error.assert_called_once()
    ui.get_detail.assert_not_called()


def test_customer_lookup_api_failure(ui):
    ui.get_detail.side_effect = explorer.APIClientError(
        "Customer not found",
        status_code=404,
    )

    with patch.object(
        explorer.st,
        "form_submit_button",
        side_effect=lambda label, **kwargs:
            label == "Find Customer",
    ):
        explorer.render_customer_explorer()

    ui.show_error.assert_called_once()
    assert "explorer_selected_customer" not in ui.state
