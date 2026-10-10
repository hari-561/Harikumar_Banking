import streamlit as st
import pandas as pd
def format_amount(value):
    if value is None:
        return "N/A"

    return f"{float(value):,.2f}"


def format_percentage(ratio):
    if ratio is None:
        return "N/A"

    return f"{float(ratio) * 100:.2f}%"

def render_customer_profile(customer):

    customer_id = customer["customer_id"]
    demographics = customer["demographics"]
    profile = customer["credit_profile"]
    risk = customer["risk"]

    risk_band = risk["risk_band"]
    risk_score = risk["risk_score"]

    # ------------------------------------
    # Profile heading
    # ------------------------------------

    st.subheader(f"Customer #{customer_id}")

    st.caption(
        "Individual customer credit profile "
        "and rule-based risk assessment."
    )

    if risk_band == "HIGH":
        st.error("Risk Classification: HIGH")
    elif risk_band == "MEDIUM":
        st.warning("Risk Classification: MEDIUM")
    else:
        st.success("Risk Classification: LOW")

    # ------------------------------------
    # Summary metrics
    # ------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Credit Limit",
            format_amount(profile["credit_limit"]),
        )

    with col2:
        st.metric(
            "Risk Score",
            f"{risk_score} / 11",
        )

    with col3:
        st.metric(
            "Latest Utilization",
            format_percentage(
                profile["latest_utilization_ratio"]
            ),
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(
            "Delayed Months",
            f"{profile['delay_month_count']} / 6",
        )

    with col5:
        st.metric(
            "Total Bills (6 Months)",
            format_amount(
                profile["total_bill_amount_6m"]
            ),
        )

    with col6:
        st.metric(
            "Total Payments (6 Months)",
            format_amount(
                profile["total_payment_amount_6m"]
            ),
        )

    st.divider()

    # ------------------------------------
    # Demographics
    # ------------------------------------

    st.markdown("#### Customer Information")

    col1, col2 = st.columns(2)

    with col1:
        st.write(
            "**Gender:**",
            demographics["gender"],
        )

        st.write(
            "**Age:**",
            demographics["age"],
        )

    with col2:
        st.write(
            "**Education:**",
            demographics["education"],
        )

        st.write(
            "**Marital Status:**",
            demographics["marital_status"],
        )

    st.divider()

    # ------------------------------------
    # Credit profile
    # ------------------------------------

    st.markdown("#### Credit Profile")

    credit_details = [
        {
            "Metric": "Maximum Delay Status",
            "Value": profile["max_delay_status"],
        },
        {
            "Metric": "Payment Delay",
            "Value": (
                "Yes"
                if profile["has_payment_delay"]
                else "No"
            ),
        },
        {
            "Metric": "Average Bill Amount (6M)",
            "Value": format_amount(
                profile["average_bill_amount_6m"]
            ),
        },
        {
            "Metric": "Average Payment Amount (6M)",
            "Value": format_amount(
                profile["average_payment_amount_6m"]
            ),
        },
        {
            "Metric": "Payment-to-Bill Ratio",
            "Value": format_percentage(
                risk["payment_to_bill_ratio"]
            ),
        },
    ]

  

    credit_df = pd.DataFrame(credit_details)

    credit_df["Value"] = credit_df["Value"].apply(
        lambda value: "N/A" if value is None else str(value)
    )

    st.dataframe(
        credit_df,
        width="stretch",
        hide_index=True,
    )

    st.divider()

    # ------------------------------------
    # Risk scoring breakdown
    # ------------------------------------

    st.markdown("#### Risk Assessment Breakdown")

    scoring_rows = [
        {
            "Component": "Delay Frequency",
            "Score": risk["delay_frequency_score"],
            "Maximum": 3,
        },
        {
            "Component": "Delay Severity",
            "Score": risk["delay_severity_score"],
            "Maximum": 3,
        },
        {
            "Component": "Credit Utilization",
            "Score": risk["utilization_score"],
            "Maximum": 3,
        },
        {
            "Component": "Payment Behavior",
            "Score": risk["payment_behavior_score"],
            "Maximum": 2,
        },
    ]

    st.dataframe(
        scoring_rows,
        width="stretch",
        hide_index=True,
    )

    calculated_score = sum(
        row["Score"] for row in scoring_rows
    )

    if calculated_score != risk_score:
        st.error(
            "Risk score reconciliation failed: "
            "component scores do not match "
            "the reported total."
        )
    else:
        st.caption(
            f"Total Risk Score: {risk_score}/11 "
            f"| Rule Version: {risk['rule_version']}"
        )

    # ------------------------------------
    # Historical outcome
    # ------------------------------------

    st.markdown("#### Historical Default Outcome")

    default_status = profile["default_next_month"]

    if default_status == 1:
        st.warning(
            "Historical Outcome: Default Recorded"
        )
    else:
        st.info(
            "Historical Outcome: No Default Recorded"
        )

    st.caption(
        "The historical default outcome is an observed "
        "dataset label. The risk classification is "
        "generated independently using fixed business "
        "rules, not machine learning."
    )