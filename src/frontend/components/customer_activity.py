
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_customer_activity(activity_response):

    activity = activity_response.get("activity", [])

    if not activity:
        st.info(
            "No monthly credit activity is available "
            "for this customer."
        )
        return

    # ---------------------------------------
    # Prepare and validate data
    # ---------------------------------------

    df = pd.DataFrame(activity)

    required_columns = {
        "activity_month",
        "repayment_status",
        "bill_amount",
        "payment_amount",
    }

    if not required_columns.issubset(df.columns):
        st.error(
            "Customer activity response is missing "
            "required fields."
        )
        return

    df["activity_month"] = pd.to_datetime(
        df["activity_month"],
        errors="coerce",
    )

    if df["activity_month"].isna().any():
        st.error("Invalid activity month detected.")
        return

    df = df.sort_values(
        "activity_month"
    ).reset_index(drop=True)

    for column in [
        "repayment_status",
        "bill_amount",
        "payment_amount",
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    if df[
        [
            "repayment_status",
            "bill_amount",
            "payment_amount",
        ]
    ].isna().any().any():
        st.error(
            "Invalid or missing numeric activity data."
        )
        return

    df["month_label"] = (
        df["activity_month"].dt.strftime("%b %Y")
    )

    # ---------------------------------------
    # Summary metrics
    # ---------------------------------------

    st.markdown("### Six-Month Credit Activity")

    total_bills = df["bill_amount"].sum()
    total_payments = df["payment_amount"].sum()

    delayed_months = int(
        (df["repayment_status"] > 0).sum()
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Bills",
            f"{total_bills:,.2f}",
        )

    with col2:
        st.metric(
            "Total Payments",
            f"{total_payments:,.2f}",
        )

    with col3:
        st.metric(
            "Delayed Months",
            f"{delayed_months} / {len(df)}",
        )

    st.divider()

    # ---------------------------------------
    # Monthly billing and payment chart
    # ---------------------------------------

    st.markdown("#### Monthly Billing vs Payments")

    billing_chart = go.Figure()

    billing_chart.add_bar(
        x=df["month_label"],
        y=df["bill_amount"],
        name="Bill Amount",
        marker_color="#2563EB",
    )

    billing_chart.add_bar(
        x=df["month_label"],
        y=df["payment_amount"],
        name="Payment Amount",
        marker_color="#0F766E",
    )

    billing_chart.update_layout(
        barmode="group",
        height=380,
        margin=dict(l=20, r=20, t=20, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title=None,
        yaxis_title="Amount",
        yaxis=dict(gridcolor="#E2E8F0"),
        legend=dict(
            orientation="h",
            y=1.15,
            x=0,
        ),
    )

    st.plotly_chart(
        billing_chart,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.divider()

    # ---------------------------------------
    # Repayment status chart
    # ---------------------------------------

    st.markdown("#### Monthly Repayment Status")

    status_chart = go.Figure()

    status_chart.add_trace(
        go.Scatter(
            x=df["month_label"],
            y=df["repayment_status"],
            mode="lines+markers",
            name="Repayment Status",
            line=dict(
                color="#2563EB",
                width=3,
            ),
            marker=dict(size=9),
        )
    )

    status_chart.add_hline(
        y=0,
        line_dash="dash",
        line_color="#94A3B8",
    )

    status_chart.update_layout(
        height=340,
        margin=dict(l=20, r=20, t=20, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title=None,
        yaxis_title="Repayment Status Code",
        yaxis=dict(
            dtick=1,
            gridcolor="#E2E8F0",
        ),
        showlegend=False,
    )

    st.plotly_chart(
        status_chart,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.caption(
        "Repayment status codes are sourced from "
        "the historical dataset. Positive values "
        "indicate repayment delays. Negative values "
        "represent separate repayment states."
    )

    st.divider()

    # ---------------------------------------
    # Monthly activity table
    # ---------------------------------------

    st.markdown("#### Detailed Monthly Activity")

    table_df = pd.DataFrame({
        "Month": df["month_label"],
        "Repayment Status": df["repayment_status"].astype(int),
        "Bill Amount": df["bill_amount"],
        "Payment Amount": df["payment_amount"],
    })

    st.dataframe(
        table_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Bill Amount": st.column_config.NumberColumn(
                "Bill Amount",
                format="%.2f",
            ),
            "Payment Amount": st.column_config.NumberColumn(
                "Payment Amount",
                format="%.2f",
            ),
        },
    )

    st.caption(
        f"Showing {len(df)} monthly records. "
        "Amounts and repayment statuses are "
        "historical observations."
    )
