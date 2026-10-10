
import streamlit as st

from src.frontend.api_client import (
    APIClientError,
    get_customer_detail,
    get_customer_activity,
    delete_customer,
)

from src.frontend.components.ui import render_api_error


def clear_delete_selection():
    st.session_state.pop(
        "management_delete_customer",
        None,
    )
    st.session_state.pop(
        "management_delete_activity_count",
        None,
    )


def render_delete_customer():

    st.markdown("### Delete Customer")

    st.warning(
        "Deleting a customer is permanent. "
        "The operation may remove related credit "
        "profiles, monthly activity records, "
        "and risk assessments."
    )

    # -------------------------------------
    # Step 1: Find customer
    # -------------------------------------

    with st.form("delete_customer_lookup_form"):

        customer_id = st.number_input(
            "Customer ID to Delete",
            min_value=1,
            value=30001,
            step=1,
        )

        lookup_clicked = st.form_submit_button(
            "Find Customer",
            width="stretch",
        )

    if lookup_clicked:

        clear_delete_selection()

        try:
            customer = get_customer_detail(
                int(customer_id)
            )

            activity_response = get_customer_activity(
                int(customer_id)
            )

            st.session_state[
                "management_delete_customer"
            ] = customer

            st.session_state[
                "management_delete_activity_count"
            ] = len(
                activity_response.get("activity", [])
            )

            st.success(
                f"Customer {customer_id} found."
            )

        except APIClientError as exc:
            render_api_error(exc)

    # -------------------------------------
    # Step 2: Review selected customer
    # -------------------------------------

    customer = st.session_state.get(
        "management_delete_customer"
    )

    if customer is None:
        st.info(
            "Find a customer to review their "
            "details before deletion."
        )
        return

    selected_id = int(customer["customer_id"])

    demographics = customer["demographics"]
    profile = customer["credit_profile"]
    risk = customer["risk"]

    activity_count = st.session_state.get(
        "management_delete_activity_count",
        0,
    )

    st.divider()

    st.markdown(
        f"#### Customer #{selected_id}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Credit Limit",
            f"{float(profile['credit_limit']):,.2f}",
        )

    with col2:
        st.metric(
            "Risk Score",
            risk["risk_score"],
        )

    with col3:
        st.metric(
            "Risk Band",
            risk["risk_band"],
        )

    st.write(
        "**Gender:**",
        demographics["gender"],
    )

    st.write(
        "**Age:**",
        demographics["age"],
    )

    st.write(
        "**Education:**",
        demographics["education"],
    )

    st.write(
        "**Marital Status:**",
        demographics["marital_status"],
    )

    st.write(
        "**Monthly Activity Records:**",
        activity_count,
    )

    st.divider()

    # -------------------------------------
    # Step 3: Confirmation
    # -------------------------------------

    st.markdown(
        "#### Confirm Permanent Deletion"
    )

    st.error(
        f"You are about to permanently delete "
        f"Customer #{selected_id}. "
        "This action cannot be undone through "
        "the Customer Management interface."
    )

    with st.form(
        f"delete_customer_confirm_{selected_id}"
    ):

        typed_id = st.text_input(
            f"Type {selected_id} to confirm deletion",
            placeholder="Enter exact Customer ID",
        )

        acknowledged = st.checkbox(
            "I understand that this deletion "
            "is permanent and may remove "
            "related customer records."
        )

        delete_clicked = st.form_submit_button(
            "Permanently Delete Customer",
            type="primary",
            width="stretch",
        )

    if not delete_clicked:
        return

    if typed_id.strip() != str(selected_id):
        st.error(
            "Customer ID confirmation does not match."
        )
        return

    if not acknowledged:
        st.error(
            "Please acknowledge permanent deletion."
        )
        return

    # -------------------------------------
    # Step 4: Delete customer
    # -------------------------------------

    try:
        # Recheck the customer immediately before
        # sending the destructive request.
        current_customer = get_customer_detail(
            selected_id
        )

        if int(current_customer["customer_id"]) != selected_id:
            st.error(
                "Customer verification failed. "
                "Deletion was cancelled."
            )
            return

        response = delete_customer(
            selected_id
        )

        if int(response["customer_id"]) != selected_id:
            st.error(
                "Delete response ID does not match. "
                "Check backend state before retrying."
            )
            clear_delete_selection()
            return

        clear_delete_selection()

        # Do not claim complete deletion until
        # the customer detail API is checked.
        try:
            get_customer_detail(selected_id)

        except APIClientError as exc:

            if getattr(exc, "status_code", None) == 404:
                st.success(
                    f"Customer #{selected_id} "
                    "was deleted successfully."
                )

                st.info(
                    "The customer detail API now "
                    "returns 404. Related table "
                    "counts will be verified "
                    "during final validation."
                )
            else:
                st.warning(
                    "The DELETE request succeeded, "
                    "but verification failed. "
                    "Check the backend before retrying."
                )
                render_api_error(exc)

        else:
            st.error(
                "The customer is still accessible "
                "after deletion. Investigate the "
                "backend before trying again."
            )

    except APIClientError as exc:
        render_api_error(exc)
