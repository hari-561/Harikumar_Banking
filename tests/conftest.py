
import os

import pytest
import requests
import streamlit as st


BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
).rstrip("/")


@pytest.fixture(scope="session")
def integration_token():
    username = os.getenv("TEST_API_USERNAME")
    password = os.getenv("TEST_API_PASSWORD")

    if not username or not password:
        pytest.fail(
            "Set TEST_API_USERNAME and TEST_API_PASSWORD "
            "before running integration tests."
        )

    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": username,
            "password": password,
        },
        timeout=30,
    )

    assert response.status_code == 200, (
        f"Integration test login failed: HTTP {response.status_code}"
    )

    return response.json()["access_token"]


@pytest.fixture(autouse=True)
def authenticated_frontend(request):
    frontend_modules = {
        "test_customer_explorer.py",
        "test_customer_management.py",
        "test_frontend_analytics.py",
    }

    if request.node.path.name not in frontend_modules:
        yield
        return

    token = request.getfixturevalue("integration_token")

    st.session_state["access_token"] = token

    try:
        yield
    finally:
        st.session_state.pop("access_token", None)
