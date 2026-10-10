
from contextlib import nullcontext
from unittest.mock import patch

import pytest

from src.frontend.components import (
    customer_update as update,
    customer_delete as delete,
)
from src.frontend.pages.customer_management import (
    default_monthly_activity,
)


class Session(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        self[name] = value


@pytest.fixture
def customer():
    return {
        "customer_id": 30001,
        "demographics": {
            "gender": "Male",
            "education": "University",
            "marital_status": "Single",
            "age": 30,
        },
        "credit_profile": {
            "credit_limit": 100000.0,
            "default_next_month": 0,
        },
        "risk": {
            "risk_score": 3,
            "risk_band": "MEDIUM",
        },
    }


@pytest.fixture
def ui(customer):
    state = Session()

    def columns(sizes, **kwargs):
        count = sizes if isinstance(sizes, int) else len(sizes)
        return tuple(nullcontext() for _ in range(count))

    with (
        patch.object(update.st, "session_state", state),
        patch.object(
            update.st, "form",
            return_value=nullcontext(),
        ),
        patch.object(
            update.st, "columns",
            side_effect=columns,
        ),
        patch.object(
            update.st, "number_input",
            side_effect=lambda label, **kwargs:
                kwargs.get("value"),
        ),
        patch.object(
            update.st, "selectbox",
            side_effect=lambda label, options, **kwargs:
                options[kwargs.get("index", 0)],
        ),
        patch.object(
            update.st, "data_editor",
            side_effect=lambda data, **kwargs: data,
        ),
        patch.object(
            update.st, "form_submit_button",
            return_value=False,
        ),
        patch.object(
            update.st, "checkbox",
            return_value=False,
        ),
        patch.object(
            update.st, "text_input",
            return_value="",
        ),
        patch.object(
            update.st, "success"
        ) as success,
        patch.object(
            update.st, "error"
        ) as error,
        patch.object(
            update.st, "warning"
        ) as warning,
        patch.object(
            update, "render_api_error"
        ) as update_api_error,
        patch.object(
            delete, "render_api_error"
        ) as delete_api_error,
        patch.object(
            update, "update_customer"
        ) as update_api,
        patch.object(
            delete, "delete_customer"
        ) as delete_api,
        patch.object(
            update, "load_customer_for_edit"
        ) as load_edit,
        patch.object(
            delete, "get_customer_detail",
            return_value=customer,
        ) as get_detail,
        patch.object(
            delete, "get_customer_activity",
            return_value={"activity": [{}] * 6},
        ),
    ):
        yield {
            "state": state,
            "customer": customer,
            "success": success,
            "error": error,
            "warning": warning,
            "update_api_error": update_api_error,
            "delete_api_error": delete_api_error,
            "update_api": update_api,
            "delete_api": delete_api,
            "load_edit": load_edit,
            "get_detail": get_detail,
        }


def edit_record(customer):
    return {
        "customer": customer,
        "codes": {
            "gender_code": 1,
            "education_code": 2,
            "marital_status_code": 2,
        },
        "activity": default_monthly_activity(),
    }


def test_update_requires_customer_load(ui):
    update.render_update_customer()

    ui["update_api"].assert_not_called()


def test_update_loads_customer_into_session(ui):
    ui["load_edit"].return_value = edit_record(
        ui["customer"]
    )

    with patch.object(
        update.st,
        "form_submit_button",
        side_effect=lambda label, **kwargs:
            label == "Load Customer",
    ):
        update.render_update_customer()

    assert ui["state"]["management_edit_customer_id"] == 30001
    assert "management_edit_record" in ui["state"]


def test_update_requires_confirmation(ui):
    ui["state"]["management_edit_record"] = edit_record(
        ui["customer"]
    )
    ui["state"]["management_edit_customer_id"] = 30001

    with patch.object(
        update.st,
        "form_submit_button",
        side_effect=lambda label, **kwargs:
            label == "Save Customer Changes",
    ):
        update.render_update_customer()

    ui["update_api"].assert_not_called()
    assert any(
        "Please confirm the update" in str(call)
        for call in ui["warning"].call_args_list
    )


def test_confirmed_update_sends_payload(ui):
    ui["state"]["management_edit_record"] = edit_record(
        ui["customer"]
    )
    ui["state"]["management_edit_customer_id"] = 30001

    ui["update_api"].return_value = {
        "message": "Customer updated successfully.",
        "customer_id": 30001,
        "risk_score": 3,
        "risk_band": "MEDIUM",
    }

    with (
        patch.object(
            update.st,
            "form_submit_button",
            side_effect=lambda label, **kwargs:
                label == "Save Customer Changes",
        ),
        patch.object(
            update.st, "checkbox",
            return_value=True,
        ),
    ):
        update.render_update_customer()

    ui["update_api"].assert_called_once()

    customer_id, payload = (
        ui["update_api"].call_args.args
    )

    assert customer_id == 30001
    assert payload["gender_code"] == 1
    assert payload["education_code"] == 2
    assert payload["marital_status_code"] == 2
    assert payload["age"] == 30
    assert payload["credit_limit"] == 100000.0
    assert len(payload["monthly_activity"]) == 6

    assert "management_edit_record" not in ui["state"]


def test_update_blocks_ambiguous_codes(ui):
    record = edit_record(ui["customer"])
    record["codes"]["education_code"] = None

    ui["state"]["management_edit_record"] = record
    ui["state"]["management_edit_customer_id"] = 30001

    update.render_update_customer()

    ui["update_api"].assert_not_called()
    assert any(
        "cannot be reconstructed safely" in str(call)
        for call in ui["error"].call_args_list
    )


def test_update_api_failure(ui):
    ui["state"]["management_edit_record"] = edit_record(
        ui["customer"]
    )
    ui["state"]["management_edit_customer_id"] = 30001

    ui["update_api"].side_effect = update.APIClientError(
        "Update failed"
    )

    with (
        patch.object(
            update.st,
            "form_submit_button",
            side_effect=lambda label, **kwargs:
                label == "Save Customer Changes",
        ),
        patch.object(
            update.st, "checkbox",
            return_value=True,
        ),
    ):
        update.render_update_customer()

    ui["update_api_error"].assert_called_once()


def test_delete_requires_customer_lookup(ui):
    delete.render_delete_customer()

    ui["delete_api"].assert_not_called()


def test_delete_lookup_stores_customer(ui):
    with patch.object(
        delete.st,
        "form_submit_button",
        side_effect=lambda label, **kwargs:
            label == "Find Customer",
    ):
        delete.render_delete_customer()

    assert (
        ui["state"]["management_delete_customer"]
        ["customer_id"] == 30001
    )
    assert (
        ui["state"]["management_delete_activity_count"]
        == 6
    )


def test_delete_requires_exact_id(ui):
    ui["state"]["management_delete_customer"] = (
        ui["customer"]
    )

    with (
        patch.object(
            delete.st,
            "form_submit_button",
            side_effect=lambda label, **kwargs:
                label == "Permanently Delete Customer",
        ),
        patch.object(
            delete.st,
            "text_input",
            return_value="99999",
        ),
        patch.object(
            delete.st,
            "checkbox",
            return_value=True,
        ),
    ):
        delete.render_delete_customer()

    ui["delete_api"].assert_not_called()
    assert any(
        "confirmation does not match" in str(call)
        for call in ui["error"].call_args_list
    )


def test_delete_requires_acknowledgment(ui):
    ui["state"]["management_delete_customer"] = (
        ui["customer"]
    )

    with (
        patch.object(
            delete.st,
            "form_submit_button",
            side_effect=lambda label, **kwargs:
                label == "Permanently Delete Customer",
        ),
        patch.object(
            delete.st,
            "text_input",
            return_value="30001",
        ),
    ):
        delete.render_delete_customer()

    ui["delete_api"].assert_not_called()
    assert any(
        "Please acknowledge permanent deletion" in str(call)
        for call in ui["error"].call_args_list
    )


def test_delete_verifies_customer_before_request(ui):
    ui["state"]["management_delete_customer"] = (
        ui["customer"]
    )

    ui["get_detail"].return_value = {
        "customer_id": 99999
    }

    with (
        patch.object(
            delete.st,
            "form_submit_button",
            side_effect=lambda label, **kwargs:
                label == "Permanently Delete Customer",
        ),
        patch.object(
            delete.st,
            "text_input",
            return_value="30001",
        ),
        patch.object(
            delete.st,
            "checkbox",
            return_value=True,
        ),
    ):
        delete.render_delete_customer()

    ui["delete_api"].assert_not_called()
    assert any(
        "Customer verification failed" in str(call)
        for call in ui["error"].call_args_list
    )


def test_successful_delete_requires_404_verification(ui):
    ui["state"]["management_delete_customer"] = (
        ui["customer"]
    )

    ui["delete_api"].return_value = {
        "customer_id": 30001
    }

    ui["get_detail"].side_effect = [
        ui["customer"],
        delete.APIClientError(
            "Not found",
            status_code=404,
        ),
    ]

    with (
        patch.object(
            delete.st,
            "form_submit_button",
            side_effect=lambda label, **kwargs:
                label == "Permanently Delete Customer",
        ),
        patch.object(
            delete.st,
            "text_input",
            return_value="30001",
        ),
        patch.object(
            delete.st,
            "checkbox",
            return_value=True,
        ),
    ):
        delete.render_delete_customer()

    ui["delete_api"].assert_called_once_with(30001)

    assert any(
        "was deleted successfully" in str(call)
        for call in ui["success"].call_args_list
    )

    assert "management_delete_customer" not in (
        ui["state"]
    )


def test_delete_response_id_mismatch(ui):
    ui["state"]["management_delete_customer"] = (
        ui["customer"]
    )

    ui["delete_api"].return_value = {
        "customer_id": 99999
    }

    with (
        patch.object(
            delete.st,
            "form_submit_button",
            side_effect=lambda label, **kwargs:
                label == "Permanently Delete Customer",
        ),
        patch.object(
            delete.st,
            "text_input",
            return_value="30001",
        ),
        patch.object(
            delete.st,
            "checkbox",
            return_value=True,
        ),
    ):
        delete.render_delete_customer()

    assert any(
        "Delete response ID does not match" in str(call)
        for call in ui["error"].call_args_list
    )


def test_delete_api_failure(ui):
    ui["state"]["management_delete_customer"] = (
        ui["customer"]
    )

    ui["get_detail"].side_effect = (
        delete.APIClientError(
            "Backend unavailable"
        )
    )

    with (
        patch.object(
            delete.st,
            "form_submit_button",
            side_effect=lambda label, **kwargs:
                label == "Permanently Delete Customer",
        ),
        patch.object(
            delete.st,
            "text_input",
            return_value="30001",
        ),
        patch.object(
            delete.st,
            "checkbox",
            return_value=True,
        ),
    ):
        delete.render_delete_customer()

    ui["delete_api_error"].assert_called_once()
    ui["delete_api"].assert_not_called()
