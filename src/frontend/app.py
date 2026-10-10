import streamlit as st

from src.frontend.styles import apply_global_styles
from src.frontend.pages.overview import render_overview
from src.frontend.components.shell import (
    render_sidebar,
    render_page_header,
    render_placeholder,
)
from src.frontend.pages.portfolio_analytics import (
    render_portfolio_analytics,
)

from src.frontend.pages.customer_explorer import (
    render_customer_explorer,
)

from src.frontend.pages.reports_export import (
    render_reports_export,
)

from src.frontend.components.ui import (
    render_kpi_card,
    render_risk_badge,
    render_section_header,
    render_api_error,
)
from src.frontend.pages.customer_management import (
    render_customer_management,
)
from src.frontend.api_client import api_request, APIClientError
from src.frontend.pages.overview import render_overview
from src.frontend.pages.risk_analysis import (
    render_risk_analysis,
)
st.set_page_config(
    page_title="CreditRisk Intelligence",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():

    apply_global_styles()

    selected_page = render_sidebar()

    render_page_header(
        selected_page
    )

    if selected_page == "Overview":
        render_overview()

    elif selected_page == "Risk Analysis":
        render_risk_analysis()
    
    elif selected_page == "Portfolio Analytics":
        render_portfolio_analytics()

    elif selected_page == "Customer Explorer":
     render_customer_explorer()

    elif selected_page == "Customer Management":
        render_customer_management()

    elif selected_page == "Reports & Export":
        render_reports_export()

    else:
        render_placeholder(selected_page)


if __name__ == "__main__":
    main()