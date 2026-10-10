
from contextlib import nullcontext
from unittest.mock import patch

import pytest

from src.frontend.components import shell


class Session(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        self[name] = value


@pytest.fixture
def sidebar():
    state = Session({
        "username": "tester",
        "role": "VIEWER",
    })

    with (
        patch.object(shell.st, "session_state", state),
        patch.object(
            shell.st, "sidebar", nullcontext()
        ),
        patch.object(
            shell.st, "radio",
            side_effect=lambda *args, **kwargs:
                kwargs["options"][kwargs["index"]],
        ) as radio,
        patch.object(
            shell.st, "button", return_value=False
        ) as button,
        patch.object(
            shell.st, "markdown"
        ) as markdown,
        patch.object(
            shell, "get_health", return_value={}
        ),
    ):
        yield state, radio, button, markdown


@pytest.mark.parametrize(
    "role,expected_count",
    [
        ("ADMIN", 6),
        ("ANALYST", 5),
        ("VIEWER", 4),
    ],
)
def test_sidebar_role_page_visibility(
    sidebar, role, expected_count
):
    state, radio, _, _ = sidebar
    state["role"] = role

    selected = shell.render_sidebar()

    options = radio.call_args.kwargs["options"]

    assert len(options) == expected_count
    assert selected == "Overview"
    assert "Overview" in options

    if role != "ADMIN":
        assert "Customer Management" not in options

    if role == "VIEWER":
        assert "Reports & Export" not in options


def test_invalid_active_page_resets_to_overview(sidebar):
    state, radio, _, _ = sidebar
    state["active_page"] = "Customer Management"
    state["sidebar_navigation"] = "Customer Management"

    shell.render_sidebar()

    assert state["active_page"] == "Overview"
    assert "sidebar_navigation" not in state
    assert radio.call_args.kwargs["index"] == 0


def test_valid_active_page_is_preserved(sidebar):
    state, radio, _, _ = sidebar
    state["active_page"] = "Risk Analysis"

    selected = shell.render_sidebar()

    assert selected == "Risk Analysis"
    assert radio.call_args.kwargs["index"] == 1


def test_sidebar_connected_status(sidebar):
    _, _, _, markdown = sidebar

    shell.render_sidebar()

    assert any(
        "API Connected" in str(call)
        for call in markdown.call_args_list
    )


def test_sidebar_disconnected_status(sidebar):
    _, _, _, markdown = sidebar

    with patch.object(
        shell,
        "get_health",
        side_effect=shell.APIClientError(
            "Connection failed"
        ),
    ):
        shell.render_sidebar()

    assert any(
        "API Disconnected" in str(call)
        for call in markdown.call_args_list
    )


def test_sidebar_logout_button(sidebar):
    _, _, button, _ = sidebar

    with (
        patch.object(
            shell.st, "button", return_value=True
        ),
        patch.object(shell, "logout_user") as logout,
    ):
        shell.render_sidebar()

    logout.assert_called_once()


def test_sidebar_rejects_unknown_role(sidebar):
    state, radio, _, _ = sidebar
    state["role"] = "UNKNOWN"

    with (
        patch.object(shell.st, "error") as error,
        patch.object(
            shell.st,
            "stop",
            side_effect=RuntimeError("stopped"),
        ),
    ):
        with pytest.raises(
            RuntimeError, match="stopped"
        ):
            shell.render_sidebar()

    error.assert_called_once_with(
        "Your account has no assigned dashboard access."
    )
    radio.assert_not_called()
