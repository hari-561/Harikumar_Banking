
import pandas as pd
import streamlit as st

from src.frontend.api_client import (
    APIClientError,
    get_customer_detail,
    get_customer_activity,
    update_customer,
)

from src.frontend.components.ui import render_api_error

from src.frontend.pages.customer_management import (
    GENDER_OPTIONS,
    EDUCATION_OPTIONS,
    MARITAL_OPTIONS,
    MONTHS,
    validate_monthly_activity,
)


def option_from_code(options, code):
    for label, value in options.items():
        if value == code:
            return label
    return None


def get_existing_codes(customer):
    """
    The customer detail API exposes demographic labels,
    not necessarily the original numeric codes.

    Resolve the codes from the existing customer data
    when they are unambiguous.
    """

    demographics = customer["demographics"]

    gender_map = {
        "Male": 1,
        "Female": 2,
    }

    education_map = {
        "Graduate School": 1,
        "University": 2,
        "High School": 3,
        "Others": None,
    }

    marital_map = {
        "Married": 1,
        "Single": 2,
        "Others": None,
    }

    return {
        "gender_code": gender_map.get(
            demographics["gender"]
        ),
        "education_code": education_map.get(
            demographics["education"]
        ),
        "marital_status_code": marital_map.get(
            demographics["marital_status"]
        ),
    }


def load_customer_for_edit(customer_id):

    customer = get_customer_detail(customer_id)

    activity_response = get_customer_activity(
        customer_id
    )

    activity = activity_response["activity"]

    if len(activity) != 6:
        raise ValueError(
            "The customer does not have exactly "
            "six monthly activity records."
        )

    activity_df = pd.DataFrame(activity)

    activity_df = activity_df.sort_values(
        "activity_month"
    ).reset_index(drop=True)

    codes = get_existing_codes(customer)

    return {
        "customer": customer,
        "codes": codes,
        "activity": activity_df,
    }


def render_update_customer():

    st.markdown("### Update Customer")

    st.caption(
        "Load an existing customer before editing. "
        "The customer ID cannot be changed."
    )

    with st.form("update_customer_lookup"):

        customer_id = st.number_input(
            "Customer ID to Update",
            min_value=1,
            value=30001,
            step=1,
        )

        load_clicked = st.form_submit_button(
            "Load Customer",
            width="stretch",
        )

    if load_clicked:

        try:
            record = load_customer_for_edit(
                int(customer_id)
            )

            st.session_state[
                "management_edit_record"
            ] = record

            st.session_state[
                "management_edit_customer_id"
            ] = int(customer_id)

            st.success(
                f"Customer {customer_id} loaded."
            )

        except (APIClientError, ValueError) as exc:
            st.session_state.pop(
                "management_edit_record",
                None,
            )
            st.session_state.pop(
                "management_edit_customer_id",
                None,
            )

            if isinstance(exc, APIClientError):
                render_api_error(exc)
            else:
                st.error(str(exc))

    record = st.session_state.get(
        "management_edit_record"
    )

    if record is None:
        st.info(
            "Enter a customer ID and select "
            "Load Customer to begin editing."
        )
        return

    loaded_id = st.session_state[
        "management_edit_customer_id"
    ]

    customer = record["customer"]
    demographics = customer["demographics"]
    profile = customer["credit_profile"]
    codes = record["codes"]

    st.info(f"Editing Customer #{loaded_id}")

    # Avoid silently replacing undocumented
    # education or marital status codes.
    if (
        codes["gender_code"] is None
        or codes["education_code"] is None
        or codes["marital_status_code"] is None
    ):
        st.error(
            "One or more original demographic codes "
            "cannot be reconstructed safely from "
            "the customer detail API. Update is "
            "disabled for this customer until "
            "the original codes are available."
        )
        return

    gender_label = option_from_code(
        GENDER_OPTIONS,
        codes["gender_code"],
    )

    education_label = option_from_code(
        EDUCATION_OPTIONS,
        codes["education_code"],
    )

    marital_label = option_from_code(
        MARITAL_OPTIONS,
        codes["marital_status_code"],
    )

    if None in (
        gender_label,
        education_label,
        marital_label,
    ):
        st.error(
            "The customer's demographic codes "
            "are not supported by this form."
        )
        return

    with st.form(
        f"update_customer_form_{loaded_id}"
    ):

        st.markdown("#### Customer Information")

        col1, col2, col3 = st.columns(3)

        with col1:
            gender = st.selectbox(
                "Gender",
                list(GENDER_OPTIONS.keys()),
                index=list(
                    GENDER_OPTIONS.keys()
                ).index(gender_label),
            )

        with col2:
            education = st.selectbox(
                "Education",
                list(EDUCATION_OPTIONS.keys()),
                index=list(
                    EDUCATION_OPTIONS.keys()
                ).index(education_label),
            )

        with col3:
            marital_status = st.selectbox(
                "Marital Status",
                list(MARITAL_OPTIONS.keys()),
                index=list(
                    MARITAL_OPTIONS.keys()
                ).index(marital_label),
            )

        age = st.number_input(
            "Age",
            min_value=1,
            max_value=120,
            value=int(demographics["age"]),
            step=1,
        )

        st.divider()

        st.markdown("#### Credit Information")

        credit_limit = st.number_input(
            "Credit Limit",
            min_value=1.0,
            value=float(profile["credit_limit"]),
            step=10000.0,
            format="%.2f",
        )

        default_next_month = st.selectbox(
            "Historical Default Outcome",
            [0, 1],
            index=int(profile["default_next_month"]),
            format_func=lambda value: (
                "No Default (0)"
                if value == 0
                else "Default Recorded (1)"
            ),
        )

        st.divider()

        st.markdown("#### Monthly Credit Activity")

        activity_df = st.data_editor(
            record["activity"],
            width="stretch",
            hide_index=True,
            num_rows="fixed",
            disabled=["activity_month"],
            column_config={
                "activity_month":
                    st.column_config.TextColumn(
                        "Month"
                    ),
                "repayment_status":
                    st.column_config.NumberColumn(
                        "Repayment Status",
                        min_value=-2,
                        max_value=9,
                        step=1,
                        format="%d",
                    ),
                "bill_amount":
                    st.column_config.NumberColumn(
                        "Bill Amount",
                        format="%.2f",
                    ),
                "payment_amount":
                    st.column_config.NumberColumn(
                        "Payment Amount",
                        min_value=0,
                        format="%.2f",
                    ),
            },
        )

        confirm = st.checkbox(
            "I confirm that I want to update "
            f"Customer #{loaded_id}."
        )

        submitted = st.form_submit_button(
            "Save Customer Changes",
            type="primary",
            width="stretch",
        )

    if submitted:

        if not confirm:
            st.warning(
                "Please confirm the update "
                "before saving."
            )
            return

        try:
            monthly_activity = (
                validate_monthly_activity(
                    activity_df
                )
            )

            payload = {
                "gender_code": GENDER_OPTIONS[
                    gender
                ],
                "education_code": EDUCATION_OPTIONS[
                    education
                ],
                "marital_status_code": MARITAL_OPTIONS[
                    marital_status
                ],
                "age": int(age),
                "credit_limit": float(
                    credit_limit
                ),
                "default_next_month": int(
                    default_next_month
                ),
                "monthly_activity": monthly_activity,
            }

            response = update_customer(
                loaded_id,
                payload,
            )

            st.success(
                response.get(
                    "message",
                    "Customer updated successfully.",
                )
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Customer ID",
                    response["customer_id"],
                )

            with col2:
                st.metric(
                    "Updated Risk Score",
                    response["risk_score"],
                )

            with col3:
                st.metric(
                    "Updated Risk Band",
                    response["risk_band"],
                )

            # Clear cached edit data so the next
            # edit loads fresh values from the API.
            st.session_state.pop(
                "management_edit_record",
                None,
            )

            st.info(
                "Update completed. Select "
                "Load Customer again to view "
                "the latest saved values."
            )

        except ValueError as exc:
            st.error(str(exc))

        except APIClientError as exc:
            render_api_error(exc)
