import streamlit as st

from src.frontend.styles import apply_global_styles

from src.frontend.components.ui import (
    render_kpi_card,
    render_risk_badge,
    render_section_header,
    render_empty_state,
    render_api_error,
)


st.set_page_config(
    page_title="CreditRisk UI Components",
    page_icon="🏦",
    layout="wide",
)

apply_global_styles()

st.title("UI Component Preview")

render_section_header(
    "Portfolio Metrics",
    "Reusable banking dashboard components."
)

# KPI cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    render_kpi_card(
        "Total Customers",
        "30,000",
        "Portfolio size",
        "blue"
    )

with col2:
    render_kpi_card(
        "Historical Default Rate",
        "22.12%",
        "Observed default percentage",
        "red"
    )

with col3:
    render_kpi_card(
        "High Risk Customers",
        "6,361",
        "Rule-based HIGH classification",
        "red"
    )

with col4:
    render_kpi_card(
        "Delayed Customers",
        "10,069",
        "At least one delayed month",
        "amber"
    )

st.divider()

render_section_header(
    "Risk Classification",
    "Standardized risk indicators."
)

risk_cols = st.columns(3)

for column, band in zip(
    risk_cols,
    ["LOW", "MEDIUM", "HIGH"]
):
    with column:
        render_risk_badge(band)

st.divider()

render_section_header(
    "Empty State",
    "Displayed when filters return no results."
)

render_empty_state(
    "No matching customers",
    "Try changing the selected risk band."
)

st.divider()

render_section_header(
    "Error Handling",
    "Standardized backend error presentation."
)

render_api_error(
    "The FastAPI service is unavailable."
)