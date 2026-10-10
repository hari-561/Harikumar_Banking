
from unittest.mock import MagicMock, patch

import pytest

from src.frontend.components import auth


@pytest.fixture
def mock_session():
    state = {}

    with patch.object(auth.st, "session_state", state):
        yield state


def test_initialize_auth_session(mock_session):
    auth.initialize_auth_session()

    assert mock_session == {
        "authenticated": False,
        "access_token": None,
        "user_id": None,
        "username": None,
        "role": None,
    }


def test_initialize_auth_preserves_existing_values(mock_session):
    mock_session.update({
        "authenticated": True,
        "access_token": "existing-token",
        "user_id": 5,
        "username": "admin",
        "role": "ADMIN",
    })

    auth.initialize_auth_session()

    assert mock_session["authenticated"] is True
    assert mock_session["access_token"] == "existing-token"
    assert mock_session["role"] == "ADMIN"


def test_initialize_auth_adds_missing_keys(mock_session):
    mock_session["authenticated"] = True

    auth.initialize_auth_session()

    assert mock_session["authenticated"] is True
    assert mock_session["access_token"] is None
    assert mock_session["role"] is None


def test_logout_clears_authentication(mock_session):
    mock_session.update({
        "authenticated": True,
        "access_token": "secret-token",
        "user_id": 10,
        "username": "admin",
        "role": "ADMIN",
        "active_page": "Overview",
        "sidebar_navigation": "Overview",
    })

    with patch.object(auth.st, "rerun") as rerun:
        auth.logout_user()

    assert mock_session == {}
    rerun.assert_called_once()


def test_logout_preserves_unrelated_state(mock_session):
    mock_session.update({
        "authenticated": True,
        "access_token": "secret-token",
        "role": "ADMIN",
        "theme_preference": "dark",
    })

    with patch.object(auth.st, "rerun"):
        auth.logout_user()

    assert mock_session == {"theme_preference": "dark"}


def test_logout_without_existing_session(mock_session):
    with patch.object(auth.st, "rerun") as rerun:
        auth.logout_user()

    assert mock_session == {}
    rerun.assert_called_once()


@pytest.mark.parametrize(
    "role",
    ["ADMIN", "ANALYST", "VIEWER"],
)
def test_auth_session_supports_roles(mock_session, role):
    mock_session.update({
        "authenticated": True,
        "role": role,
    })

    auth.initialize_auth_session()

    assert mock_session["authenticated"] is True
    assert mock_session["role"] == role


def test_login_rejects_empty_credentials():
    """
    Verify the login form rejects blank credentials
    without contacting the backend.
    """
    with (
        patch.object(auth.st, "columns") as columns,
        patch.object(auth.st, "form") as form,
        patch.object(auth.st, "text_input") as text_input,
        patch.object(
            auth.st, "form_submit_button", return_value=True
        ),
        patch.object(auth.st, "error") as show_error,
        patch.object(auth, "api_request") as request,
    ):
        context = MagicMock()
        context.__enter__.return_value = context

        columns.return_value = (
            context, context, context
        )
        form.return_value = context

        text_input.side_effect = ["", ""]

        auth.render_login()

    show_error.assert_called_once_with(
        "Please enter your username and password."
    )
    request.assert_not_called()
