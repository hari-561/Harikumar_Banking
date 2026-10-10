import streamlit as st

from src.frontend.api_client import (
    APIClientError,
    api_request,
)


def initialize_auth_session():
    """
    Initialize authentication session variables.
    """
    defaults = {
        "authenticated": False,
        "access_token": None,
        "user_id": None,
        "username": None,
        "role": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_login():
    """
    Display the login screen.
    """

    st.markdown(
        "<h1 style='text-align:center;'>"
        "🏦 CreditRisk Intelligence"
        "</h1>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<p style='text-align:center;'>"
        "Banking Loan Risk Analysis Application"
        "</p>",
        unsafe_allow_html=True,
    )

    st.divider()

    left, center, right = st.columns([1, 1.5, 1])

    with center:
        st.subheader("Sign in")

        with st.form("login_form"):
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
            )

            submitted = st.form_submit_button(
                "Login",
                use_container_width=True,
            )

        if submitted:
            if not username.strip() or not password:
                st.error(
                    "Please enter your username and password."
                )
                return

            try:
                response = api_request(
                    method="POST",
                    endpoint="/auth/login",
                    json_data={
                        "username": username.strip(),
                        "password": password,
                    },
                )

                st.session_state.authenticated = True
                st.session_state.access_token = (
                    response["access_token"]
                )
                st.session_state.user_id = (
                    response["user_id"]
                )
                st.session_state.username = (
                    response["username"]
                )
                st.session_state.role = (
                    response["role"]
                )

                st.session_state.active_page = "Overview"

                st.rerun()

            except APIClientError as error:
                if error.status_code == 401:
                    st.error("Invalid username or password.")
                else:
                    st.error(str(error))




def logout_user():
    """
    Clear authentication information and return to login.
    """
    auth_keys = [
        "authenticated",
        "access_token",
        "user_id",
        "username",
        "role",
        "active_page",
        "sidebar_navigation",
    ]

    for key in auth_keys:
        st.session_state.pop(key, None)

    st.rerun()