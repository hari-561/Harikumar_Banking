
from io import BytesIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.frontend.api_client import (
    APIClientError,
    get_risk_distribution,
    get_segment_analytics,
)


RISK_ORDER = ["LOW", "MEDIUM", "HIGH"]

RISK_COLORS = {
    "LOW": "#0F766E",
    "MEDIUM": "#D97706",
    "HIGH": "#DC2626",
}

SEGMENT_OPTIONS = {
    "Gender": "gender",
    "Education": "education",
    "Marital Status": "marital_status",
    "Age": "age",
}

SEGMENT_COLUMNS = {
    "segment": "Segment",
    "total_customers": "Customers",
    "average_credit_limit": "Average Credit Limit",
    "historical_defaults": "Historical Defaults",
    "historical_default_rate_pct": "Default Rate (%)",
    "customers_with_payment_delay": "Customers With Delay",
    "average_latest_utilization_pct": "Average Utilization (%)",
}


def make_chart(labels, values, title, suffix=""):
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=labels,
            y=values,
            marker_color="#2563EB",
            text=[
                f"{value:,.2f}{suffix}"
                if suffix
                else f"{value:,.0f}"
                for value in values
            ],
            textposition="outside",
        )
    )

    fig.update_layout(
        title=title,
        height=380,
        margin=dict(l=20, r=20, t=55, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title=None,
        yaxis_title=None,
        yaxis=dict(
            gridcolor="#E2E8F0",
            rangemode="tozero",
        ),
        showlegend=False,
    )

    return fig


def render_risk_concentration():
    st.markdown("### Risk Concentration Report")

    try:
        risk_data = get_risk_distribution()
    except APIClientError as exc:
        st.error(f"Unable to load risk data: {exc}")
        return

    df = pd.DataFrame(risk_data)

    if df.empty:
        st.info("No risk data available.")
        return

    df["risk_band"] = pd.Categorical(
        df["risk_band"],
        categories=RISK_ORDER,
        ordered=True,
    )

    df = df.sort_values("risk_band").copy()

    total_customers = df["total_customers"].sum()
    total_defaults = df["historical_defaults"].sum()

    df["customer_share_pct"] = (
        df["total_customers"] / total_customers * 100
        if total_customers
        else 0
    )

    df["default_share_pct"] = (
        df["historical_defaults"] / total_defaults * 100
        if total_defaults
        else 0
    )

    high = df[
        df["risk_band"] == "HIGH"
    ]

    if not high.empty:
        high_row = high.iloc[0]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "HIGH-Risk Customers",
                f"{int(high_row['total_customers']):,}",
            )

        with col2:
            st.metric(
                "Share of Portfolio",
                f"{high_row['customer_share_pct']:.2f}%",
            )

        with col3:
            st.metric(
                "Share of Historical Defaults",
                f"{high_row['default_share_pct']:.2f}%",
            )

    st.markdown("#### Portfolio Share vs Default Share")

    fig = go.Figure()

    fig.add_bar(
        name="Customer Share",
        x=df["risk_band"].astype(str),
        y=df["customer_share_pct"],
        marker_color="#64748B",
        text=df["customer_share_pct"].map(
            lambda x: f"{x:.2f}%"
        ),
        textposition="outside",
    )

    fig.add_bar(
        name="Historical Default Share",
        x=df["risk_band"].astype(str),
        y=df["default_share_pct"],
        marker_color="#DC2626",
        text=df["default_share_pct"].map(
            lambda x: f"{x:.2f}%"
        ),
        textposition="outside",
    )

    fig.update_layout(
        barmode="group",
        height=400,
        margin=dict(l=20, r=20, t=35, b=35),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Share (%)",
        yaxis=dict(
            gridcolor="#E2E8F0",
            rangemode="tozero",
        ),
        legend=dict(orientation="h", y=1.12),
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    report_df = df[
        [
            "risk_band",
            "total_customers",
            "historical_defaults",
            "historical_default_rate_pct",
            "average_risk_score",
            "customer_share_pct",
            "default_share_pct",
        ]
    ].copy()

    report_df["risk_band"] = (
        report_df["risk_band"].astype(str)
    )

    report_df.columns = [
        "Risk Band",
        "Customers",
        "Historical Defaults",
        "Default Rate (%)",
        "Average Risk Score",
        "Customer Share (%)",
        "Default Share (%)",
    ]

    st.markdown("#### Risk Concentration Details")

    st.dataframe(
        report_df,
        width="stretch",
        hide_index=True,
    )

    st.download_button(
        "Download Risk Concentration CSV",
        data=report_df.to_csv(index=False).encode("utf-8"),
        file_name="risk_concentration_report.csv",
        mime="text/csv",
        key="risk_concentration_download",
    )

    st.caption(
        "Historical defaults describe outcomes recorded "
        "in the dataset, not predictions of future defaults."
    )


def render_segment_report():
    st.markdown("### Customer Segment Analysis")

    selected_label = st.selectbox(
        "Select Customer Segment",
        list(SEGMENT_OPTIONS.keys()),
        key="report_segment_selection",
    )

    segment_type = SEGMENT_OPTIONS[selected_label]

    try:
        segment_data = get_segment_analytics(segment_type)
    except (APIClientError, ValueError) as exc:
        st.error(f"Unable to load segment data: {exc}")
        return

    df = pd.DataFrame(segment_data)

    if df.empty:
        st.info("No segment data available.")
        return

    df = df.sort_values(
        "total_customers",
        ascending=False,
    ).reset_index(drop=True)

    total_customers = int(df["total_customers"].sum())
    total_defaults = int(df["historical_defaults"].sum())
    total_delayed = int(
        df["customers_with_payment_delay"].sum()
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Customers",
            f"{total_customers:,}",
        )

    with col2:
        st.metric(
            "Historical Defaults",
            f"{total_defaults:,}",
        )

    with col3:
        st.metric(
            "Customers With Delay",
            f"{total_delayed:,}",
        )

    st.markdown("#### Segment Distribution")

    fig_customers = make_chart(
        labels=df["segment"],
        values=df["total_customers"],
        title=f"Customers by {selected_label}",
    )

    st.plotly_chart(
        fig_customers,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.markdown("#### Historical Default Rate")

    fig_defaults = make_chart(
        labels=df["segment"],
        values=df["historical_default_rate_pct"],
        title=f"Default Rate by {selected_label}",
        suffix="%",
    )

    st.plotly_chart(
        fig_defaults,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.markdown("#### Segment Comparison")

    report_df = df.rename(
        columns=SEGMENT_COLUMNS
    )

    st.dataframe(
        report_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Average Credit Limit":
                st.column_config.NumberColumn(
                    "Average Credit Limit",
                    format="%.2f",
                ),
            "Default Rate (%)":
                st.column_config.NumberColumn(
                    "Default Rate (%)",
                    format="%.2f%%",
                ),
            "Average Utilization (%)":
                st.column_config.NumberColumn(
                    "Average Utilization (%)",
                    format="%.2f%%",
                ),
        },
    )

    st.download_button(
        f"Download {selected_label} Segment CSV",
        data=report_df.to_csv(index=False).encode("utf-8"),
        file_name=f"{segment_type}_segment_report.csv",
        mime="text/csv",
        key=f"segment_download_{segment_type}",
    )

    st.caption(
        "Segment statistics are descriptive summaries "
        "of historical customer records."
    )


def render_risk_segment_reports():
    st.divider()

    st.markdown("## Advanced Risk & Segment Reports")

    risk_tab, segment_tab = st.tabs(
        [
            "Risk Concentration",
            "Customer Segments",
        ]
    )

    with risk_tab:
        render_risk_concentration()

    with segment_tab:
        render_segment_report()

