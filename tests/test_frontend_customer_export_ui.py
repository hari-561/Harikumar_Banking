
from contextlib import nullcontext
from unittest.mock import patch

import pytest

from src.frontend.components import customer_export as export


CSV = (
    b"customer_id,risk_band,credit_limit\n"
    b"1,LOW,100000\n"
    b"2,HIGH,200000\n"
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
def ui():
    state = Session()

    def columns(sizes, **kwargs):
        count = sizes if isinstance(sizes, int) else len(sizes)
        return tuple(nullcontext() for _ in range(count))

    with (
        patch.object(export.st, "session_state", state),
        patch.object(
            export.st, "form",
            return_value=nullcontext(),
        ),
        patch.object(
            export.st, "spinner",
            return_value=nullcontext(),
        ),
        patch.object(
            export.st, "columns",
            side_effect=columns,
        ),
        patch.object(
            export.st, "selectbox",
            side_effect=lambda label, options, **kwargs:
                options[kwargs.get("index", 0)],
        ),
        patch.object(
            export.st, "number_input",
            side_effect=lambda label, **kwargs:
                kwargs.get("value", 0),
        ),
        patch.object(
            export.st, "form_submit_button",
            return_value=False,
        ),
        patch.object(
            export, "export_customers_csv",
            return_value=CSV,
        ) as api,
        patch.object(
            export.st, "download_button"
        ) as download,
        patch.object(
            export.st, "dataframe"
        ) as dataframe,
        patch.object(
            export.st, "error"
        ) as error,
        patch.object(
            export.st, "warning"
        ) as warning,
        patch.object(
            export.st, "info"
        ) as info,
    ):
        yield {
            "state": state,
            "api": api,
            "download": download,
            "dataframe": dataframe,
            "error": error,
            "warning": warning,
            "info": info,
        }


def generate():
    return patch.object(
        export.st,
        "form_submit_button",
        return_value=True,
    )


def test_no_export_before_submission(ui):
    export.render_customer_export()

    ui["api"].assert_not_called()
    ui["download"].assert_not_called()


def test_export_uses_default_filters(ui):
    with generate():
        export.render_customer_export()

    ui["api"].assert_called_once_with(
        risk_band=None,
        has_payment_delay=None,
        min_credit_limit=None,
        max_credit_limit=None,
        sort_by="customer_id",
        sort_order="asc",
    )


def test_export_stores_csv_and_metadata(ui):
    with generate():
        export.render_customer_export()

    assert ui["state"]["customer_export_bytes"] == CSV

    info = ui["state"]["customer_export_info"]

    assert info["rows"] == 2
    assert info["columns"] == 3
    assert len(info["preview"]) == 2


def test_download_has_correct_file_properties(ui):
    with generate():
        export.render_customer_export()

    kwargs = ui["download"].call_args.kwargs

    assert kwargs["data"] == CSV
    assert kwargs["file_name"] == "customers_export.csv"
    assert kwargs["mime"] == "text/csv"
    assert kwargs["disabled"] is False


def test_selected_filters_are_sent_to_api(ui):
    selections = {
        "Risk Band": "HIGH",
        "Payment Delay": "Yes",
        "Sort By": "Risk Score",
        "Sort Order": "desc",
    }

    limits = {
        "Minimum Credit Limit": 100000.0,
        "Maximum Credit Limit (0 = No Limit)": 500000.0,
    }

    with (
        generate(),
        patch.object(
            export.st,
            "selectbox",
            side_effect=lambda label, options, **kwargs:
                selections.get(label, options[0]),
        ),
        patch.object(
            export.st,
            "number_input",
            side_effect=lambda label, **kwargs:
                limits.get(label, kwargs.get("value", 0)),
        ),
    ):
        export.render_customer_export()

    ui["api"].assert_called_once_with(
        risk_band="HIGH",
        has_payment_delay=True,
        min_credit_limit=100000.0,
        max_credit_limit=500000.0,
        sort_by="risk_score",
        sort_order="desc",
    )


def test_invalid_credit_range_blocks_export(ui):
    with (
        generate(),
        patch.object(
            export.st,
            "number_input",
            side_effect=lambda label, **kwargs:
                200000.0
                if label == "Minimum Credit Limit"
                else (
                    100000.0
                    if label.startswith("Maximum Credit Limit")
                    else kwargs.get("value", 0)
                ),
        ),
    ):
        export.render_customer_export()

    ui["api"].assert_not_called()
    assert any(
        "Maximum credit limit" in str(call)
        for call in ui["error"].call_args_list
    )


def test_new_generation_clears_previous_export(ui):
    ui["state"]["customer_export_bytes"] = b"old"
    ui["state"]["customer_export_info"] = {"rows": 1}

    ui["api"].side_effect = RuntimeError(
        "Export failed"
    )

    with generate():
        export.render_customer_export()

    assert "customer_export_bytes" not in ui["state"]
    assert "customer_export_info" not in ui["state"]


def test_api_failure_displays_error(ui):
    ui["api"].side_effect = RuntimeError(
        "Backend unavailable"
    )

    with generate():
        export.render_customer_export()

    ui["download"].assert_not_called()

    assert any(
        "Unable to generate CSV export" in str(call)
        for call in ui["error"].call_args_list
    )


def test_invalid_csv_displays_error(ui):
    ui["api"].return_value = b""

    with generate():
        export.render_customer_export()

    ui["download"].assert_not_called()
    ui["error"].assert_called_once()


def test_empty_csv_disables_download(ui):
    ui["api"].return_value = (
        b"customer_id,risk_band\n"
    )

    with generate():
        export.render_customer_export()

    assert (
        ui["state"]["customer_export_info"]["rows"]
        == 0
    )

    kwargs = ui["download"].call_args.kwargs

    assert kwargs["disabled"] is True

    assert any(
        "No customers match" in str(call)
        for call in ui["warning"].call_args_list
    )


def test_saved_export_survives_rerun(ui):
    with generate():
        export.render_customer_export()

    ui["api"].reset_mock()
    ui["download"].reset_mock()

    export.render_customer_export()

    ui["api"].assert_not_called()
    ui["download"].assert_called_once()
    assert ui["download"].call_args.kwargs["data"] == CSV


def test_export_preview_uses_dataframe(ui):
    with generate():
        export.render_customer_export()

    ui["dataframe"].assert_called_once()

    preview = ui["dataframe"].call_args.args[0]

    assert list(preview["customer_id"]) == [1, 2]
