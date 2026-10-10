import streamlit as st
import plotly.graph_objects as go

def calculate_segment_comparison(segment, summary):
    """Compare selected segment with portfolio baselines."""

    total_customers = segment["total_customers"]
    portfolio_customers = summary["total_customers"]

    if total_customers <= 0 or portfolio_customers <= 0:
        raise ValueError("Customer counts must be positive.")

    segment_delay_rate = (
        segment["customers_with_payment_delay"]
        / total_customers * 100
    )

    portfolio_delay_rate = (
        summary["customers_with_payment_delay"]
        / portfolio_customers * 100
    )

    return {
        "default_rate": {
            "value": segment["historical_default_rate_pct"],
            "baseline": summary["historical_default_rate_pct"],
            "difference": (
                segment["historical_default_rate_pct"]
                - summary["historical_default_rate_pct"]
            ),
        },
        "credit_limit": {
            "value": segment["average_credit_limit"],
            "baseline": summary["average_credit_limit"],
            "difference": (
                segment["average_credit_limit"]
                - summary["average_credit_limit"]
            ),
        },
        "utilization": {
            "value": segment["average_latest_utilization_pct"],
            "baseline": summary["average_latest_utilization_pct"],
            "difference": (
                segment["average_latest_utilization_pct"]
                - summary["average_latest_utilization_pct"]
            ),
        },
        "payment_delay": {
            "count": segment["customers_with_payment_delay"],
            "value": segment_delay_rate,
            "baseline": portfolio_delay_rate,
            "difference": (
                segment_delay_rate - portfolio_delay_rate
            ),
        },
    }


def render_segment_drilldown(segment, summary):

    comparison = calculate_segment_comparison(
        segment, summary
    )

    st.markdown(
        f"### Selected Segment: {segment['segment']}"
    )

    st.caption(
        f"{segment['total_customers']:,} customers | "
        "Comparison with overall portfolio"
    )

    col1, col2 = st.columns(2)

    with col1:
        item = comparison["default_rate"]

        st.metric(
            "Historical Default Rate",
            f"{item['value']:.2f}%",
            f"{item['difference']:+.2f} pp",
            delta_color="inverse",
        )

        st.caption(
            f"Portfolio baseline: "
            f"{item['baseline']:.2f}%"
        )

    with col2:
        item = comparison["credit_limit"]

        st.metric(
            "Average Credit Limit",
            f"{item['value']:,.2f}",
            f"{item['difference']:+,.2f}",
            delta_color="off",
        )

        st.caption(
            f"Portfolio baseline: "
            f"{item['baseline']:,.2f}"
        )

    col3, col4 = st.columns(2)

    with col3:
        item = comparison["utilization"]

        st.metric(
            "Average Latest Utilization",
            f"{item['value']:.2f}%",
            f"{item['difference']:+.2f} pp",
            delta_color="off",
        )

        st.caption(
            f"Portfolio baseline: "
            f"{item['baseline']:.2f}%"
        )

    with col4:
        item = comparison["payment_delay"]

        st.metric(
            "Customers With Payment Delay",
            f"{item['count']:,}",
            f"{item['value']:.2f}% of segment",
            delta_color="off",
        )

        st.caption(
            f"Portfolio delay rate: "
            f"{item['baseline']:.2f}% | "
            f"Difference: {item['difference']:+.2f} pp"
        )

    st.caption(
        "Differences in percentage points (pp) are "
        "calculated against the overall portfolio. "
        "These are descriptive historical comparisons, "
        "not individual credit decisions."
    )


    st.markdown("**Selected Segment vs Overall Portfolio**")

    render_comparison_chart(comparison)



def render_comparison_chart(comparison):

    labels = [
        "Historical Default Rate",
        "Average Utilization",
        "Payment Delay Rate",
    ]

    segment_values = [
        comparison["default_rate"]["value"],
        comparison["utilization"]["value"],
        comparison["payment_delay"]["value"],
    ]

    portfolio_values = [
        comparison["default_rate"]["baseline"],
        comparison["utilization"]["baseline"],
        comparison["payment_delay"]["baseline"],
    ]

    fig = go.Figure()

    fig.add_bar(
        name="Selected Segment",
        x=labels,
        y=segment_values,
        marker_color="#2563EB",
    )

    fig.add_bar(
        name="Overall Portfolio",
        x=labels,
        y=portfolio_values,
        marker_color="#94A3B8",
    )

    fig.update_layout(
        barmode="group",
        height=360,
        margin=dict(l=30, r=20, t=25, b=55),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(
            title="Percentage (%)",
            ticksuffix="%",
            gridcolor="#E2E8F0",
        ),
        legend=dict(
            orientation="h",
            y=1.15,
            x=0,
        ),
        font=dict(color="#172B4D"),
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )