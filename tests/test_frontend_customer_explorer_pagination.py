
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


def sample_customer(customer_id):
    return {
        "customer_id": customer_id,
        "age": 30,
        "gender": "Male",
        "education": "University",
        "credit_limit": 100000,
        "delay_month_count": 1,
        "latest_utilization_ratio": 0.45,
        "risk_score": 3,
        "risk_band": "MEDIUM",
    }


@pytest.fixture
def ui():
    state = Session({
        "explorer_page": 1,
        "explorer_filters": {
            "risk_band": None,
            "has_payment_delay": None,
            "page_size": 20,
            "min_credit_limit": None,
            "max_credit_limit": None,
            "sort_by": "customer_id",
            "sort_order": "asc",
        },
    })

    response = {
        "items": [
            sample_customer(101),
            sample_customer(102),
        ],
        "total_records": 42,
        "total_pages": 3,
        "page": 1,
    }

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
        ),
        patch.object(
            explorer.st, "selectbox",
            side_effect=lambda label, options, **kwargs:
                options[kwargs.get("index", 0)],
        ),
        patch.object(
            explorer.st, "form_submit_button",
            return_value=False,
        ),
        patch.object(
            explorer.st, "dataframe",
            return_value=SimpleNamespace(
                selection=SimpleNamespace(rows=[])
            ),
        ) as dataframe,
        patch.object(
            explorer.st, "button",
            return_value=False,
        ) as button,
        patch.object(
            explorer.st, "rerun"
        ) as rerun,
        patch.object(
            explorer, "render_section_header"
        ),
        patch.object(
            explorer, "get_customers",
            return_value=response,
        ) as get_customers,
        patch.object(
            explorer, "get_customer_detail",
            return_value={"customer_id": 102},
        ) as get_detail,
        patch.object(
            explorer, "get_customer_activity",
            return_value={"activity": []},
        ) as get_activity,
        patch.object(
            explorer, "render_customer_profile"
        ) as render_profile,
        patch.object(
            explorer, "render_customer_activity"
        ) as render_activity,
    ):
        yield SimpleNamespace(
            state=state,
            response=response,
            dataframe=dataframe,
            button=button,
            rerun=rerun,
            get_customers=get_customers,
            get_detail=get_detail,
            get_activity=get_activity,
            render_profile=render_profile,
            render_activity=render_activity,
        )


def test_customer_table_displays_records(ui):
    explorer.render_customer_explorer()

    rows = ui.dataframe.call_args.args[0]

    assert len(rows) == 2
    assert rows[0]["Customer ID"] == 101
    assert rows[1]["Customer ID"] == 102
    assert rows[0]["Utilization (%)"] == 45.0


def test_customer_table_enables_row_selection(ui):
    explorer.render_customer_explorer()

    kwargs = ui.dataframe.call_args.kwargs

    assert kwargs["on_select"] == "rerun"
    assert kwargs["selection_mode"] == "single-row"
    assert kwargs["key"] == "customer_explorer_table"


def test_selecting_customer_row_loads_profile(ui):
    ui.dataframe.return_value = SimpleNamespace(
        selection=SimpleNamespace(rows=[1])
    )

    explorer.render_customer_explorer()

    assert ui.state["explorer_selected_customer"] == 102
    ui.get_detail.assert_called_once_with(102)
    ui.get_activity.assert_called_once_with(102)
    ui.render_profile.assert_called_once()
    ui.render_activity.assert_called_once()


def test_no_row_selection_preserves_customer(ui):
    ui.state["explorer_selected_customer"] = 102

    explorer.render_customer_explorer()

    assert ui.state["explorer_selected_customer"] == 102
    ui.get_detail.assert_called_once_with(102)


def test_previous_button_disabled_on_first_page(ui):
    explorer.render_customer_explorer()

    calls = {
        call.args[0]: call.kwargs
        for call in ui.button.call_args_list
    }

    assert calls["← Previous"]["disabled"] is True
    assert calls["Next →"]["disabled"] is False


def test_next_button_advances_page(ui):
    with patch.object(
        explorer.st,
        "button",
        side_effect=lambda label, **kwargs:
            label == "Next →",
    ):
        explorer.render_customer_explorer()

    assert ui.state["explorer_page"] == 2
    ui.rerun.assert_called_once()


def test_previous_button_decrements_page(ui):
    ui.state["explorer_page"] = 2
    ui.response["page"] = 2

    with patch.object(
        explorer.st,
        "button",
        side_effect=lambda label, **kwargs:
            label == "← Previous",
    ):
        explorer.render_customer_explorer()

    assert ui.state["explorer_page"] == 1
    ui.rerun.assert_called_once()


def test_next_button_disabled_on_last_page(ui):
    ui.state["explorer_page"] = 3
    ui.response["page"] = 3

    explorer.render_customer_explorer()

    calls = {
        call.args[0]: call.kwargs
        for call in ui.button.call_args_list
    }

    assert calls["Next →"]["disabled"] is True
    assert calls["← Previous"]["disabled"] is False


def test_current_page_is_sent_to_api(ui):
    ui.state["explorer_page"] = 2
    ui.response["page"] = 2

    explorer.render_customer_explorer()

    ui.get_customers.assert_called_once_with(
        page=2,
        **ui.state["explorer_filters"],
    )
