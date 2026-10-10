
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.frontend.api_client import (
    APIClientError,
    get_portfolio_summary,
    get_risk_distribution,
)

from src.frontend.components.ui import (
    render_section_header,
    render_api_error,
)
from src.frontend.components.risk_segment_reports import (
    render_risk_segment_reports,
)

from src.frontend.components.customer_export import (
        render_customer_export,
    )

RISK_ORDER = ["LOW", "MEDIUM", "HIGH"]

RISK_COLORS = {
    "LOW": "#0F766E",
    "MEDIUM": "#D97706",
    "HIGH": "#DC2626",
}


def format_number(value):
    return f"{int(value):,}"


def format_amount(value):
    return f"{float(value):,.2f}"


def render_portfolio_metrics(summary):

    st.markdown("#### Portfolio Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Customers",
            format_number(summary["total_customers"]),
        )

    with col2:
        st.metric(
            "Total Credit Exposure",
            format_amount(summary["total_credit_exposure"]),
        )

    with col3:
        st.metric(
            "Average Credit Limit",
            format_amount(summary["average_credit_limit"]),
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(
            "Historical Defaults",
            format_number(summary["historical_defaults"]),
        )

    with col5:
        st.metric(
            "Historical Default Rate",
            f"{summary['historical_default_rate_pct']:.2f}%",
        )

    with col6:
        st.metric(
            "Average Latest Utilization",
            f"{summary['average_latest_utilization_pct']:.2f}%",
        )

    st.divider()

    st.markdown("#### Payment Behavior")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Customers With Payment Delay",
            format_number(
                summary["customers_with_payment_delay"]
            ),
        )

    with col2:
        st.metric(
            "Repeated Payment Delays",
            format_number(
                summary["customers_with_repeated_delay"]
            ),
        )

    with col3:
        st.metric(
            "Over-Limit Customers",
            format_number(
                summary["over_limit_customers"]
            ),
        )

    col4, col5 = st.columns(2)

    with col4:
        st.metric(
            "Total Bills (6 Months)",
            format_amount(
                summary["total_bill_amount_6m"]
            ),
        )

    with col5:
        st.metric(
            "Total Payments (6 Months)",
            format_amount(
                summary["total_payment_amount_6m"]
            ),
        )


def render_risk_distribution(risk_data):

    st.markdown("### Risk Distribution Report")

    df = pd.DataFrame(risk_data)

    if df.empty:
        st.info("No risk distribution data available.")
        return

    df["risk_band"] = pd.Categorical(
        df["risk_band"],
        categories=RISK_ORDER,
        ordered=True,
    )

    df = df.sort_values("risk_band")

    colors = [
        RISK_COLORS[str(band)]
        for band in df["risk_band"]
    ]

    # ----------------------------------
    # Customer distribution chart
    # ----------------------------------

    st.markdown("#### Customers by Risk Band")

    fig = go.Figure()

    fig.add_bar(
        x=df["risk_band"].astype(str),
        y=df["total_customers"],
        marker_color=colors,
        text=df["total_customers"].map(
            lambda value: f"{value:,}"
        ),
        textposition="outside",
    )

    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=20, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title=None,
        yaxis_title="Customers",
        yaxis=dict(gridcolor="#E2E8F0"),
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.divider()

    # ----------------------------------
    # Historical default rate chart
    # ----------------------------------

    st.markdown(
        "#### Historical Default Rate by Risk Band"
    )

    default_fig = go.Figure()

    default_fig.add_bar(
        x=df["risk_band"].astype(str),
        y=df["historical_default_rate_pct"],
        marker_color=colors,
        text=df["historical_default_rate_pct"].map(
            lambda value: f"{value:.2f}%"
        ),
        textposition="outside",
    )

    default_fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=20, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title=None,
        yaxis_title="Default Rate (%)",
        yaxis=dict(
            gridcolor="#E2E8F0",
            rangemode="tozero",
        ),
        showlegend=False,
    )

    st.plotly_chart(
        default_fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.divider()

    # ----------------------------------
    # Risk comparison table
    # ----------------------------------

    st.markdown("#### Risk Band Comparison")

    report_df = df[
        [
            "risk_band",
            "total_customers",
            "historical_defaults",
            "historical_default_rate_pct",
            "average_risk_score",
        ]
    ].copy()

    report_df.columns = [
        "Risk Band",
        "Customers",
        "Historical Defaults",
        "Default Rate (%)",
        "Average Risk Score",
    ]

    report_df["Risk Band"] = (
        report_df["Risk Band"].astype(str)
    )

    st.dataframe(
        report_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Customers":
                st.column_config.NumberColumn(
                    "Customers",
                    format="%d",
                ),
            "Historical Defaults":
                st.column_config.NumberColumn(
                    "Historical Defaults",
                    format="%d",
                ),
            "Default Rate (%)":
                st.column_config.NumberColumn(
                    "Default Rate (%)",
                    format="%.2f%%",
                ),
            "Average Risk Score":
                st.column_config.NumberColumn(
                    "Average Risk Score",
                    format="%.2f",
                ),
        },
    )

    total_customers = int(
        df["total_customers"].sum()
    )

    st.caption(
        f"Total customers across all risk bands: "
        f"{total_customers:,}"
    )


def render_reports_export():

    render_section_header(
        "Reports & Export",
        "Portfolio reporting and downloadable banking risk data.",
    )

    try:
        summary = get_portfolio_summary()
        risk_data = get_risk_distribution()

    except APIClientError as exc:
        render_api_error(exc)
        return

    render_portfolio_metrics(summary)

    st.divider()

    render_risk_distribution(risk_data)

    st.divider()

  

    render_customer_export()

    st.divider()

    st.markdown("#### Reporting Information")

    st.info(
        "Reports are generated from the existing "
        "MySQL warehouse through FastAPI. "
        "Customer risk scores use deterministic "
        "business rules rather than machine learning."
    )

    st.caption(
        "CSV export functionality will be added "
        "in Phase 7G-3."
    )

    st.divider()

    render_risk_segment_reports()
