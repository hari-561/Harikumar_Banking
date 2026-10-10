import html
import streamlit as st


def generate_executive_insights(
    summary,
    risk_distribution,
    monthly_data
):
    """
    Generate deterministic observations
    from FastAPI portfolio analytics.
    """

    insights = []

    # ---------------------------------
    # 1. Risk concentration
    # ---------------------------------

    risk_lookup = {
        row["risk_band"]: row
        for row in risk_distribution
    }

    if "HIGH" in risk_lookup and "LOW" in risk_lookup:

        high = risk_lookup["HIGH"]
        low = risk_lookup["LOW"]

        high_rate = high["historical_default_rate_pct"]
        low_rate = low["historical_default_rate_pct"]

        if low_rate > 0:
            ratio = high_rate / low_rate

            insights.append({
                "title": "Higher Historical Default Rate",
                "description": (
                    f"HIGH-risk customers have a "
                    f"{ratio:.2f}× historical default "
                    f"rate compared with LOW-risk "
                    f"customers ({high_rate:.2f}% "
                    f"versus {low_rate:.2f}%)."
                ),
                "tone": "red"
            })

    # ---------------------------------
    # 2. Monthly delinquency peak
    # ---------------------------------

    if monthly_data:

        peak = max(
            monthly_data,
            key=lambda row: row[
                "delayed_customer_rate_pct"
            ]
        )

        month = peak["activity_month"][:7]

        insights.append({
            "title": "Highest Monthly Delinquency",
            "description": (
                f"{month} recorded the highest "
                f"monthly delinquency rate at "
                f"{peak['delayed_customer_rate_pct']:.2f}%, "
                f"affecting "
                f"{peak['delayed_customers']:,} customers."
            ),
            "tone": "amber"
        })

    # ---------------------------------
    # 3. Repeated repayment delays
    # ---------------------------------

    total = summary["total_customers"]
    repeated = summary[
        "customers_with_repeated_delay"
    ]

    if total > 0:
        repeated_pct = (
            repeated / total
        ) * 100

        insights.append({
            "title": "Repeated Payment Delays",
            "description": (
                f"{repeated:,} customers "
                f"({repeated_pct:.2f}% of the portfolio) "
                f"experienced delays in at least "
                f"two of the six observed months."
            ),
            "tone": "blue"
        })

    return insights


def render_executive_insights(insights):

    st.markdown(
        '<div class="cr-insights-heading">'
        '<span>Executive Insights</span>'
        '<small>Derived from portfolio analytics</small>'
        '</div>',
        unsafe_allow_html=True
    )

    if not insights:
        st.info(
            "Insufficient data to generate "
            "executive insights."
        )
        return

    columns = st.columns(
        len(insights),
        gap="medium"
    )

    for column, insight in zip(
        columns,
        insights
    ):
        with column:

            tone = insight.get("tone", "blue")

            if tone not in (
                "blue", "red", "amber", "teal"
            ):
                tone = "blue"

            title = html.escape(
                str(insight["title"])
            )

            description = html.escape(
                str(insight["description"])
            )

            markup = (
                f'<div class="cr-insight-card '
                f'cr-insight-{tone}">'
                f'<div class="cr-insight-title">'
                f'{title}</div>'
                f'<div class="cr-insight-description">'
                f'{description}</div>'
                '</div>'
            )

            st.markdown(
                markup,
                unsafe_allow_html=True
            )