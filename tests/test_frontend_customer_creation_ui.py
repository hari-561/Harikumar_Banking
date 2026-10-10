
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.frontend.pages import customer_management as management


@pytest.fixture
def ui():
    def columns(sizes, **kwargs):
        count = sizes if isinstance(sizes, int) else len(sizes)
        return tuple(nullcontext() for _ in range(count))

    def number_input(label, **kwargs):
        return kwargs.get("value")

    def selectbox(label, options, **kwargs):
        return options[kwargs.get("index", 0)]

    response = {
        "message": "Customer created successfully.",
        "customer_id": 30001,
        "risk_score": 0,
        "risk_band": "LOW",
    }

    with (
        patch.object(
            management.st, "form",
            return_value=nullcontext(),
        ),
        patch.object(
            management.st, "columns",
            side_effect=columns,
        ),
        patch.object(
            management.st, "number_input",
            side_effect=number_input,
        ),
        patch.object(
            management.st, "selectbox",
            side_effect=selectbox,
        ),
        patch.object(
            management.st, "data_editor",
            side_effect=lambda data, **kwargs: data,
        ) as editor,
        patch.object(
            management.st, "form_submit_button",
            return_value=False,
        ) as submit,
        patch.object(
            management, "render_section_header"
        ),
        patch.object(
            management, "create_customer",
            return_value=response,
        ) as create,
        patch.object(
            management, "render_api_error"
        ) as show_api_error,
        patch(
            "src.frontend.components.customer_update."
            "render_update_customer"
        ),
        patch(
            "src.frontend.components.customer_delete."
            "render_delete_customer"
        ),
        patch.object(management.st, "success") as success,
        patch.object(management.st, "error") as error,
        patch.object(management.st, "metric") as metric,
    ):
        yield SimpleNamespace(
            response=response,
            editor=editor,
            submit=submit,
            create=create,
            show_api_error=show_api_error,
            success=success,
            error=error,
            metric=metric,
        )


def test_form_not_submitted_does_not_create_customer(ui):
    management.render_customer_management()

    ui.create.assert_not_called()


def test_form_displays_six_month_activity_editor(ui):
    management.render_customer_management()

    data = ui.editor.call_args.args[0]
    options = ui.editor.call_args.kwargs

    assert len(data) == 6
    assert list(data["activity_month"]) == management.MONTHS
    assert options["num_rows"] == "fixed"
    assert "activity_month" in options["disabled"]


def test_submitted_form_creates_customer(ui):
    with patch.object(
        management.st,
        "form_submit_button",
        return_value=True,
    ):
        management.render_customer_management()

    ui.create.assert_called_once()

    payload = ui.create.call_args.args[0]

    assert payload["customer_id"] == 30001
    assert payload["gender_code"] == 1
    assert payload["education_code"] == 1
    assert payload["marital_status_code"] == 1
    assert payload["age"] == 30
    assert payload["credit_limit"] == 100000.0
    assert payload["default_next_month"] == 0
    assert len(payload["monthly_activity"]) == 6


def test_customer_creation_uses_selected_values(ui):
    selections = {
        "Gender": "Female",
        "Education": "University",
        "Marital Status": "Single",
        "Historical Default Outcome": 1,
    }

    numbers = {
        "Customer ID": 30050,
        "Age": 45,
        "Credit Limit": 250000.0,
    }

    def selectbox(label, options, **kwargs):
        return selections.get(label, options[0])

    def number_input(label, **kwargs):
        return numbers.get(label, kwargs.get("value"))

    with (
        patch.object(
            management.st,
            "form_submit_button",
            return_value=True,
        ),
        patch.object(
            management.st,
            "selectbox",
            side_effect=selectbox,
        ),
        patch.object(
            management.st,
            "number_input",
            side_effect=number_input,
        ),
    ):
        management.render_customer_management()

    payload = ui.create.call_args.args[0]

    assert payload["customer_id"] == 30050
    assert payload["gender_code"] == 2
    assert payload["education_code"] == 2
    assert payload["marital_status_code"] == 2
    assert payload["age"] == 45
    assert payload["credit_limit"] == 250000.0
    assert payload["default_next_month"] == 1


def test_successful_creation_displays_feedback(ui):
    with patch.object(
        management.st,
        "form_submit_button",
        return_value=True,
    ):
        management.render_customer_management()

    ui.success.assert_called_once_with(
        "Customer created successfully."
    )

    labels = [
        call.args[0]
        for call in ui.metric.call_args_list
    ]

    assert labels == [
        "Customer ID",
        "Risk Score",
        "Risk Band",
    ]


def test_validation_error_blocks_creation(ui):
    invalid = management.default_monthly_activity()
    invalid.loc[0, "payment_amount"] = -100.0

    with (
        patch.object(
            management.st,
            "form_submit_button",
            return_value=True,
        ),
        patch.object(
            management.st,
            "data_editor",
            return_value=invalid,
        ),
    ):
        management.render_customer_management()

    ui.create.assert_not_called()
    ui.error.assert_called_once()

    assert "Payment amounts cannot be negative" in (
        ui.error.call_args.args[0]
    )


def test_api_failure_displays_error(ui):
    ui.create.side_effect = management.APIClientError(
        "Customer creation failed"
    )

    with patch.object(
        management.st,
        "form_submit_button",
        return_value=True,
    ):
        management.render_customer_management()

    ui.show_api_error.assert_called_once()
    ui.success.assert_not_called()


def test_payload_monthly_activity_schema(ui):
    with patch.object(
        management.st,
        "form_submit_button",
        return_value=True,
    ):
        management.render_customer_management()

    payload = ui.create.call_args.args[0]

    for row in payload["monthly_activity"]:
        assert set(row) == {
            "activity_month",
            "repayment_status",
            "bill_amount",
            "payment_amount",
        }


def test_form_uses_expected_default_credit_limit(ui):
    with patch.object(
        management.st,
        "form_submit_button",
        return_value=True,
    ):
        management.render_customer_management()

    payload = ui.create.call_args.args[0]

    assert payload["credit_limit"] == 100000.0
    assert payload["age"] == 30


def test_api_failure_does_not_show_success_metrics(ui):
    ui.create.side_effect = management.APIClientError(
        "Duplicate customer",
        status_code=409,
    )

    with patch.object(
        management.st,
        "form_submit_button",
        return_value=True,
    ):
        management.render_customer_management()

    ui.show_api_error.assert_called_once()
    ui.metric.assert_not_called()
