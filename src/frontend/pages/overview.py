import streamlit as st

from src.frontend.api_client import (
    APIClientError,
    get_portfolio_summary,
    get_risk_distribution,
    get_monthly_trends
)

from src.frontend.components.ui import (
    render_kpi_card,
    render_section_header,
    render_api_error,
)

from src.frontend.components.charts import (
    create_risk_donut,
    create_default_rate_chart,
    create_monthly_delinquency_chart,
    create_monthly_delay_count_chart,
)

from src.frontend.components.insights import (
    generate_executive_insights,
    render_executive_insights,
)

def load_overview_data():
    """
    Fetch all datasets required by the
    Executive Overview Dashboard.
    """

    summary = get_portfolio_summary()
    distribution = get_risk_distribution()
    monthly_data = get_monthly_trends()

    return summary, distribution, monthly_data

def render_overview():

    render_section_header(
        "Portfolio Performance",
        "Historical credit portfolio indicators "
        "from FastAPI."
    )

    refresh_col, info_col = st.columns(
        [1, 5],
        vertical_alignment="center"
    )

    with refresh_col:
        if st.button(
            "↻ Refresh Data",
            key="refresh_overview",
            width="stretch"
        ):
            st.rerun()

    with info_col:
        st.caption(
            "Historical dataset: April–September 2005"
        )

    try:
        with st.spinner("Loading portfolio dashboard..."):
            summary, distribution, monthly_data = (
                load_overview_data()
            )

    except APIClientError as error:
        render_api_error(error)
        return

    # -----------------------------------------
    # KPI Row 1
    # -----------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        render_kpi_card(
            label="Total Customers",
            value=f"{summary['total_customers']:,}",
            subtitle="Total credit customers",
            accent="blue"
        )

    with col2:
        render_kpi_card(
            label="Historical Default Rate",
            value=(
                f"{summary['historical_default_rate_pct']:.2f}%"
            ),
            subtitle=(
                f"{summary['historical_defaults']:,} "
                "observed defaults"
            ),
            accent="red"
        )

    with col3:
        render_kpi_card(
            label="Customers With Payment Delay",
            value=(
                f"{summary['customers_with_payment_delay']:,}"
            ),
            subtitle="At least one delayed month",
            accent="amber"
        )

    st.markdown(
    '<div style="height: 12px;"></div>',
    unsafe_allow_html=True
)

    # -----------------------------------------
    # KPI Row 2
    # -----------------------------------------

    col4, col5, col6 = st.columns(3)

    with col4:
        render_kpi_card(
            label="Average Credit Limit",
            value=(
                f"{summary['average_credit_limit']:,.2f}"
            ),
            subtitle="Source dataset monetary units",
            accent="navy"
        )

    with col5:
        render_kpi_card(
            label="Average Latest Utilization",
            value=(
                f"{summary['average_latest_utilization_pct']:.2f}%"
            ),
            subtitle="Latest billing period",
            accent="teal"
        )

    with col6:
        render_kpi_card(
            label="Repeated Payment Delays",
            value=(
                f"{summary['customers_with_repeated_delay']:,}"
            ),
            subtitle="Two or more delayed months",
            accent="red"
        )


        st.divider()

    render_section_header(
        "Credit Risk Distribution",
        "Customer risk classification and observed "
        "historical default outcomes."
    )

    try:
        with st.spinner("Loading risk distribution..."):
            distribution = distribution

        if not isinstance(distribution, list):
            st.warning(
                "Risk distribution response has an "
                "unexpected format."
            )
            return

        if not distribution:
            st.info("No risk distribution data available.")
            return

        # Validate risk bands and avoid silently
        # displaying incomplete portfolio results.
        bands = [row["risk_band"] for row in distribution]

        if sorted(bands) != sorted(["LOW", "MEDIUM", "HIGH"]):
            st.warning(
                "Risk distribution data is incomplete "
                "or contains unexpected risk bands."
            )
            return

        left, right = st.columns(2, gap="medium")

        with left:
            st.markdown("**Customers by Risk Band**")

            st.plotly_chart(
                create_risk_donut(distribution),
                width="stretch",
                config={"displayModeBar": False},
            )

        with right:
            st.markdown(
                "**Historical Default Rate by Risk Band**"
            )

            st.plotly_chart(
                create_default_rate_chart(distribution),
                width="stretch",
                config={"displayModeBar": False},
            )

        st.caption(
            "Risk bands are assigned using transparent "
            "business rules. Historical default rates "
            "describe observed outcomes and are not "
            "machine-learning predictions."
        )

    except APIClientError as error:
        render_api_error(error)


        # -----------------------------------------
    # Monthly Delinquency Trend
    # -----------------------------------------

    st.divider()

    render_section_header(
        "Repayment Behaviour — Six-Month Trend",
        "Historical monthly credit activity "
        "from April to September 2005."
    )

    try:
        with st.spinner("Loading monthly trends..."):
            monthly_data = monthly_data

        left, right = st.columns(
            2,
            gap="medium"
        )

        with left:
            st.markdown(
                "**Monthly Delinquency Rate**"
            )

            st.plotly_chart(
                create_monthly_delinquency_chart(
                    monthly_data
                ),
                width="stretch",
                config={
                    "displayModeBar": False
                }
            )

        with right:
            st.markdown(
                "**Monthly Delayed Customers**"
            )

            st.plotly_chart(
                create_monthly_delay_count_chart(
                    monthly_data
                ),
                width="stretch",
                config={
                    "displayModeBar": False
                }
            )

        st.caption(
            "Delinquency is defined here as a positive "
            "repayment-delay status for the corresponding "
            "month. These figures represent historical "
            "observations, not real-time banking activity."
        )

    except APIClientError as error:
        render_api_error(error)

    except (ValueError, KeyError, TypeError) as error:
        st.error(
            f"Unable to display monthly trends: {error}"
        )

        # -----------------------------------------
    # Executive Insights
    # -----------------------------------------
    # -----------------------------------------
    # Executive Insights
    # -----------------------------------------

    st.divider()

    try:
        insights = generate_executive_insights(
            summary,
            distribution,
            monthly_data
        )

        render_executive_insights(insights)

    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        st.error(
            "Unable to generate executive insights "
            "from the returned portfolio data."
        )

    st.divider()

    

    st.caption(
        "Historical default outcomes and rule-based "
        "risk classifications are different measures. "
        "All values are retrieved from FastAPI."
    )