import streamlit as st

from src.frontend.api_client import (
    APIClientError,
    get_risk_distribution,
)

from src.frontend.components.ui import (
    render_kpi_card,
    render_section_header,
    render_api_error,
)

from src.frontend.components.charts import (
    create_risk_donut,
    create_default_rate_chart,
)

from src.frontend.components.risk_segment_reports import (
    render_risk_segment_reports,
)

def render_risk_analysis():

    render_section_header(
        "Risk Classification Overview",
        "Rule-based credit risk assessment and "
        "historical default outcomes."
    )

    try:
        with st.spinner("Loading risk analysis..."):
            distribution = get_risk_distribution()

    except APIClientError as error:
        render_api_error(error)
        return

    # Validate API response
    try:
        if not isinstance(distribution, list):
            raise ValueError(
                "Risk distribution must be a list."
            )

        risk_lookup = {
            row["risk_band"]: row
            for row in distribution
        }

        if set(risk_lookup) != {
            "LOW", "MEDIUM", "HIGH"
        } or len(distribution) != 3:
            raise ValueError(
                "Expected LOW, MEDIUM and HIGH risk bands."
            )

        total_customers = sum(
            row["total_customers"]
            for row in distribution
        )

        if total_customers <= 0:
            raise ValueError(
                "No customers found in risk distribution."
            )

        high = risk_lookup["HIGH"]
        medium = risk_lookup["MEDIUM"]
        low = risk_lookup["LOW"]

        high_share = (
            high["total_customers"]
            / total_customers
        ) * 100

    except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        st.error(
            f"Invalid risk distribution data: {error}"
        )
        return

    # ---------------------------------------
    # Risk KPIs
    # ---------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        render_kpi_card(
            "HIGH-Risk Customers",
            f"{high['total_customers']:,}",
            f"{high_share:.2f}% of the portfolio",
            "red"
        )

    with col2:
        render_kpi_card(
            "HIGH-Risk Historical Default Rate",
            f"{high['historical_default_rate_pct']:.2f}%",
            f"{high['historical_defaults']:,} observed defaults",
            "amber"
        )

    with col3:
        render_kpi_card(
            "Average HIGH Risk Score",
            f"{high['average_risk_score']:.2f}",
            "Rule-based score (0–11)",
            "navy"
        )

    st.markdown(
        '<div style="height:12px;"></div>',
        unsafe_allow_html=True
    )

    # ---------------------------------------
    # Risk Visualizations
    # ---------------------------------------

    st.divider()

    render_section_header(
        "Risk Distribution",
        "Customer concentration and historical "
        "default rates across risk categories."
    )

    left, right = st.columns(2, gap="medium")

    with left:
        st.markdown(
            "**Customers by Risk Category**"
        )

        st.plotly_chart(
            create_risk_donut(distribution),
            width="stretch",
            config={"displayModeBar": False}
        )

    with right:
        st.markdown(
            "**Historical Default Rate Comparison**"
        )

        st.plotly_chart(
            create_default_rate_chart(distribution),
            width="stretch",
            config={"displayModeBar": False}
        )

    # ---------------------------------------
    # Risk Band Comparison
    # ---------------------------------------

    st.divider()

    render_section_header(
        "Risk Band Comparison",
        "Detailed comparison of risk categories."
    )

    rows = []

    for band in ("LOW", "MEDIUM", "HIGH"):

        row = risk_lookup[band]

        rows.append({
            "Risk Band": band,
            "Customers": row["total_customers"],
            "Portfolio Share (%)": round(
                row["total_customers"]
                / total_customers * 100,
                2
            ),
            "Historical Defaults": row[
                "historical_defaults"
            ],
            "Default Rate (%)": row[
                "historical_default_rate_pct"
            ],
            "Average Risk Score": row[
                "average_risk_score"
            ],
        })

    st.dataframe(
        rows,
        width="stretch",
        hide_index=True
    )

    # ---------------------------------------
    # Transparent Scoring Framework
    # ---------------------------------------

    st.divider()

    render_section_header(
        "Risk Scoring Methodology",
        "Transparent, deterministic business rules."
    )

    with st.expander(
        "View scoring components and thresholds",
        expanded=True
    ):

        st.markdown(
            """
            **1. Repayment Delay Frequency (0–3 points)**

            - No delayed months: 0
            - One delayed month: 1
            - Two delayed months: 2
            - Three or more delayed months: 3

            **2. Maximum Repayment Delay (0–3 points)**

            - No delay: 0
            - Maximum delay status 1: 1
            - Maximum delay status 2: 2
            - Maximum delay status 3 or higher: 3

            **3. Latest Credit Utilization (0–3 points)**

            - Below 50%: 0
            - 50% to below 70%: 1
            - 70% to 100%: 2
            - Above 100%: 3

            **4. Payment-to-Bill Ratio (0–2 points)**

            - Non-positive total bill amount: 0
            - Ratio below 20%: 2
            - 20% to below 50%: 1
            - 50% or higher: 0
            """
        )

        st.markdown("**Final Risk Classification**")

        st.dataframe(
            [
                {
                    "Risk Band": "LOW",
                    "Score Range": "0–2"
                },
                {
                    "Risk Band": "MEDIUM",
                    "Score Range": "3–5"
                },
                {
                    "Risk Band": "HIGH",
                    "Score Range": "6–11"
                }
            ],
            width="stretch",
            hide_index=True
        )

    st.caption(
        "Risk scores are generated using fixed "
        "business rules, not machine learning. "
        "Historical default rates represent observed "
        "outcomes and should not be interpreted as "
        "individual default probabilities."
    )

 


  

    