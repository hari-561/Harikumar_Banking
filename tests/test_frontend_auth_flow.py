
from contextlib import nullcontext
from unittest.mock import patch

import pytest

from src.frontend.components import auth


class Session(dict):
    """Dict with Streamlit-style attribute access."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        self[name] = value


@pytest.fixture
def login_ui():
    state = Session()

    with (
        patch.object(auth.st, "session_state", state),
        patch.object(
            auth.st, "columns",
            return_value=(
                nullcontext(),
                nullcontext(),
                nullcontext(),
            ),
        ),
        patch.object(
            auth.st, "form",
            return_value=nullcontext(),
        ),
        patch.object(
            auth.st, "form_submit_button",
            return_value=True,
        ),
        patch.object(auth.st, "rerun") as rerun,
        patch.object(auth.st, "error") as show_error,
        patch.object(auth, "api_request") as request,
    ):
        yield state, request, rerun, show_error


@pytest.mark.parametrize(
    "role", ["ADMIN", "ANALYST", "VIEWER"]
)
def test_successful_login(login_ui, role):
    state, request, rerun, show_error = login_ui

    request.return_value = {
        "access_token": "jwt-token",
        "user_id": 10,
        "username": "tester",
        "role": role,
    }

    with patch.object(
        auth.st,
        "text_input",
        side_effect=["  tester  ", "password123"],
    ):
        auth.render_login()

    request.assert_called_once_with(
        method="POST",
        endpoint="/auth/login",
        json_data={
            "username": "tester",
            "password": "password123",
        },
    )

    assert state["authenticated"] is True
    assert state["access_token"] == "jwt-token"
    assert state["user_id"] == 10
    assert state["role"] == role
    assert state["active_page"] == "Overview"
    rerun.assert_called_once()
    show_error.assert_not_called()


def test_invalid_credentials(login_ui):
    state, request, rerun, show_error = login_ui

    request.side_effect = auth.APIClientError(
        "Unauthorized", status_code=401
    )

    with patch.object(
        auth.st,
        "text_input",
        side_effect=["tester", "wrong-password"],
    ):
        auth.render_login()

    assert state.get("authenticated") is not True
    show_error.assert_called_once_with(
        "Invalid username or password."
    )
    rerun.assert_not_called()


def test_login_server_error(login_ui):
    state, request, rerun, show_error = login_ui

    request.side_effect = auth.APIClientError(
        "Backend unavailable", status_code=503
    )

    with patch.object(
        auth.st,
        "text_input",
        side_effect=["tester", "password123"],
    ):
        auth.render_login()

    assert state.get("authenticated") is not True
    show_error.assert_called_once_with(
        "Backend unavailable"
    )
    rerun.assert_not_called()


@pytest.fixture
def app_module():
    # Import separately because app.py configures Streamlit
    # when the module is first loaded.
    from src.frontend import app
    return app


def test_unauthenticated_user_sees_login(app_module):
    state = Session({"authenticated": False})

    with (
        patch.object(
            app_module.st, "session_state", state
        ),
        patch.object(
            app_module, "apply_global_styles"
        ),
        patch.object(
            app_module, "initialize_auth_session"
        ),
        patch.object(
            app_module, "render_login"
        ) as login,
        patch.object(
            app_module, "api_request"
        ) as request,
    ):
        app_module.main()

    login.assert_called_once()
    request.assert_not_called()


def test_authenticated_user_session_verified(app_module):
    state = Session({
        "authenticated": True,
        "user_id": 10,
        "username": "tester",
        "role": "VIEWER",
    })

    with (
        patch.object(
            app_module.st, "session_state", state
        ),
        patch.object(
            app_module, "apply_global_styles"
        ),
        patch.object(
            app_module, "initialize_auth_session"
        ),
        patch.object(
            app_module, "api_request",
            return_value={
                "user_id": 10,
                "username": "tester",
                "role": "VIEWER",
            },
        ) as request,
        patch.object(
            app_module, "render_sidebar",
            return_value="Overview",
        ),
        patch.object(
            app_module, "render_page_header"
        ),
        patch.object(
            app_module, "render_overview"
        ) as overview,
    ):
        app_module.main()

    request.assert_called_once_with(
        method="GET",
        endpoint="/auth/me",
    )
    overview.assert_called_once()


def test_unauthorized_page_is_blocked(app_module):
    state = Session({
        "authenticated": True,
        "user_id": 10,
        "role": "VIEWER",
    })

    with (
        patch.object(
            app_module.st, "session_state", state
        ),
        patch.object(
            app_module, "apply_global_styles"
        ),
        patch.object(
            app_module, "initialize_auth_session"
        ),
        patch.object(
            app_module, "api_request",
            return_value={
                "user_id": 10,
                "username": "tester",
                "role": "VIEWER",
            },
        ),
        patch.object(
            app_module, "render_sidebar",
            return_value="Customer Management",
        ),
        patch.object(
            app_module.st, "error"
        ) as show_error,
        patch.object(
            app_module.st, "stop",
            side_effect=RuntimeError("stopped"),
        ),
        patch.object(
            app_module, "render_customer_management"
        ) as management,
    ):
        with pytest.raises(
            RuntimeError, match="stopped"
        ):
            app_module.main()

    show_error.assert_called_once_with(
        "You are not authorized to access this page."
    )
    management.assert_not_called()


@pytest.mark.parametrize("status_code", [401, 403])
def test_expired_session_triggers_logout(
    app_module, status_code
):
    state = Session({
        "authenticated": True,
        "user_id": 10,
        "role": "VIEWER",
    })

    with (
        patch.object(
            app_module.st, "session_state", state
        ),
        patch.object(
            app_module, "apply_global_styles"
        ),
        patch.object(
            app_module, "initialize_auth_session"
        ),
        patch.object(
            app_module, "api_request",
            side_effect=app_module.APIClientError(
                "Invalid session",
                status_code=status_code,
            ),
        ),
        patch.object(
            app_module.st, "warning"
        ) as warning,
        patch.object(
            app_module, "logout_user",
            side_effect=RuntimeError("logout"),
        ) as logout,
    ):
        with pytest.raises(
            RuntimeError, match="logout"
        ):
            app_module.main()

    warning.assert_called_once()
    logout.assert_called_once()
