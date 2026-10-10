
import streamlit as st
import pandas as pd

from src.frontend.api_client import (
    APIClientError,
    create_customer,
)
from src.frontend.components.ui import (
    render_section_header,
    render_api_error,
)


MONTHS = [
    "2005-04-01",
    "2005-05-01",
    "2005-06-01",
    "2005-07-01",
    "2005-08-01",
    "2005-09-01",
]

GENDER_OPTIONS = {
    "Male": 1,
    "Female": 2,
}

EDUCATION_OPTIONS = {
    "Graduate School": 1,
    "University": 2,
    "High School": 3,
    "Others (4)": 4,
    "Other Code (0)": 0,
    "Other Code (5)": 5,
    "Other Code (6)": 6,
}

MARITAL_OPTIONS = {
    "Married": 1,
    "Single": 2,
    "Others (3)": 3,
    "Other Code (0)": 0,
}


def default_monthly_activity():
    return pd.DataFrame({
        "activity_month": MONTHS,
        "repayment_status": [0] * 6,
        "bill_amount": [0.0] * 6,
        "payment_amount": [0.0] * 6,
    })


def validate_monthly_activity(df):

    required_columns = [
        "activity_month",
        "repayment_status",
        "bill_amount",
        "payment_amount",
    ]

    if not all(
        column in df.columns
        for column in required_columns
    ):
        raise ValueError(
            "Monthly activity columns are missing."
        )

    if len(df) != 6:
        raise ValueError(
            "Exactly six monthly activity records are required."
        )

    if df[required_columns].isna().any().any():
        raise ValueError(
            "Monthly activity cannot contain empty values."
        )

    actual_months = [
        str(value)[:10]
        for value in df["activity_month"]
    ]

    if actual_months != MONTHS:
        raise ValueError(
            "Monthly activity must contain April through "
            "September 2005 in chronological order."
        )

    activity = []

    for _, row in df.iterrows():

        status = float(row["repayment_status"])

        if not status.is_integer():
            raise ValueError(
                "Repayment status must be an integer."
            )

        if not -2 <= status <= 9:
            raise ValueError(
                "Repayment status must be between -2 and 9."
            )

        bill_amount = float(row["bill_amount"])
        payment_amount = float(row["payment_amount"])

        if payment_amount < 0:
            raise ValueError(
                "Payment amounts cannot be negative."
            )

        activity.append({
            "activity_month": str(row["activity_month"])[:10],
            "repayment_status": int(status),
            "bill_amount": bill_amount,
            "payment_amount": payment_amount,
        })

    return activity


def render_customer_management():

    render_section_header(
        "Customer Management",
        "Create and maintain customer credit records.",
    )

    st.caption(
        "Customer creation is a database-changing operation. "
        "Use a test customer ID and verify the information "
        "before submitting."
    )

    st.markdown("### Create Customer")

    with st.form("create_customer_form"):

        st.markdown("#### Customer Information")

        col1, col2, col3 = st.columns(3)

        with col1:
            customer_id = st.number_input(
                "Customer ID",
                min_value=1,
                value=30001,
                step=1,
            )

            gender = st.selectbox(
                "Gender",
                list(GENDER_OPTIONS.keys()),
            )

        with col2:
            age = st.number_input(
                "Age",
                min_value=1,
                max_value=120,
                value=30,
                step=1,
            )

            education = st.selectbox(
                "Education",
                list(EDUCATION_OPTIONS.keys()),
            )

        with col3:
            marital_status = st.selectbox(
                "Marital Status",
                list(MARITAL_OPTIONS.keys()),
            )

        st.divider()

        st.markdown("#### Credit Information")

        credit_col1, credit_col2 = st.columns(2)

        with credit_col1:
            credit_limit = st.number_input(
                "Credit Limit",
                min_value=1.0,
                value=100000.0,
                step=10000.0,
                format="%.2f",
            )

        with credit_col2:
            default_next_month = st.selectbox(
                "Historical Default Outcome",
                options=[0, 1],
                format_func=lambda value: (
                    "No Default (0)"
                    if value == 0
                    else "Default Recorded (1)"
                ),
            )

        st.divider()

        st.markdown("#### Monthly Credit Activity")

        st.caption(
            "Enter six months of billing, payments, "
            "and repayment statuses. Negative bill "
            "amounts are permitted because they occur "
            "in the source dataset."
        )

        activity_df = st.data_editor(
            default_monthly_activity(),
            width="stretch",
            hide_index=True,
            num_rows="fixed",
            disabled=["activity_month"],
            column_config={
                "activity_month": st.column_config.TextColumn(
                    "Month",
                ),
                "repayment_status": st.column_config.NumberColumn(
                    "Repayment Status",
                    min_value=-2,
                    max_value=9,
                    step=1,
                    format="%d",
                ),
                "bill_amount": st.column_config.NumberColumn(
                    "Bill Amount",
                    format="%.2f",
                ),
                "payment_amount": st.column_config.NumberColumn(
                    "Payment Amount",
                    min_value=0,
                    format="%.2f",
                ),
            },
        )

        st.divider()

        submitted = st.form_submit_button(
            "Create Customer",
            type="primary",
            width="stretch",
        )

    if submitted:

        try:
            monthly_activity = validate_monthly_activity(
                activity_df
            )

            payload = {
                "customer_id": int(customer_id),
                "gender_code": GENDER_OPTIONS[gender],
                "education_code": EDUCATION_OPTIONS[education],
                "marital_status_code": MARITAL_OPTIONS[
                    marital_status
                ],
                "age": int(age),
                "credit_limit": float(credit_limit),
                "default_next_month": int(
                    default_next_month
                ),
                "monthly_activity": monthly_activity,
            }

            response = create_customer(payload)

            st.success(
                response.get(
                    "message",
                    "Customer created successfully.",
                )
            )

            result_col1, result_col2, result_col3 = (
                st.columns(3)
            )

            with result_col1:
                st.metric(
                    "Customer ID",
                    response["customer_id"],
                )

            with result_col2:
                st.metric(
                    "Risk Score",
                    response["risk_score"],
                )

            with result_col3:
                st.metric(
                    "Risk Band",
                    response["risk_band"],
                )

            st.info(
                "Customer created. Verify the new record "
                "in Customer Explorer."
            )

        except ValueError as exc:
            st.error(str(exc))

        except APIClientError as exc:
            render_api_error(exc)


    st.divider()

    from src.frontend.components.customer_update import (
        render_update_customer,
    )

    render_update_customer()


    st.divider()

    from src.frontend.components.customer_delete import (
        render_delete_customer,
    )

    render_delete_customer()


