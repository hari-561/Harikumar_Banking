import streamlit as st
from textwrap import dedent

from src.frontend.api_client import (
    APIClientError,
    get_health,
)

from src.frontend.navigation import NAVIGATION

def render_sidebar():

    # Initialize selected page
    if "active_page" not in st.session_state:
        st.session_state.active_page = "Overview"

    with st.sidebar:

        # -----------------------------------
        # 1. Application branding
        # -----------------------------------

        brand_html = """
        <div class="app-brand">
            <div class="brand-symbol">▦</div>
            <div>
                <div class="brand-title">
                    CreditRisk
                </div>
                <div class="brand-subtitle">
                    INTELLIGENCE
                </div>
            </div>
        </div>
        """

        st.markdown(
            dedent(brand_html).strip(),
            unsafe_allow_html=True
        )

        st.divider()

        # -----------------------------------
        # 2. Sidebar navigation
        # -----------------------------------

        page_names = list(NAVIGATION.keys())

        selected_page = st.radio(
            "Navigation",
            options=page_names,
            index=page_names.index(
                st.session_state.active_page
            ),
            format_func=lambda page: (
                f"{NAVIGATION[page]['icon']}  {page}"
            ),
            label_visibility="collapsed",
            key="sidebar_navigation"
        )

        st.session_state.active_page = selected_page

        st.divider()

        # -----------------------------------
        # 3. FastAPI connection status
        # -----------------------------------

        try:

            # Real API health check
            get_health()

            status_html = """
            <div class="connection-status connected">
                <span class="status-dot"></span>
                <span>API Connected</span>
            </div>
            """

        except APIClientError:

            status_html = """
            <div class="connection-status disconnected">
                <span class="status-dot"></span>
                <span>API Disconnected</span>
            </div>
            """

        # Render connection indicator
        st.markdown(
            dedent(status_html).strip(),
            unsafe_allow_html=True
        )

        # -----------------------------------
        # 4. Sidebar footer
        # -----------------------------------

        st.caption(
            "Banking Credit Risk Analytics"
        )

    # Return selected page to app.py
    return selected_page



def render_page_header(page_name):
    config = NAVIGATION[page_name]

    html = f"""
    <div class="page-header">
        <div class="page-eyebrow">
            BANKING ANALYTICS
        </div>
        <h1>{config['title']}</h1>
        <p>{config['description']}</p>
    </div>
    """

    st.markdown(
        dedent(html).strip(),
        unsafe_allow_html=True
    )


def render_placeholder(page_name):
    config = NAVIGATION[page_name]

    html = f"""
    <div class="workspace-placeholder">
        <div class="placeholder-icon">
            {config['icon']}
        </div>
        <h3>{page_name} Workspace</h3>
        <p>
            This page is ready for implementation.
            Its features will be added in the
            corresponding Phase 7 step.
        </p>
    </div>
    """

    st.markdown(
        dedent(html).strip(),
        unsafe_allow_html=True
    )