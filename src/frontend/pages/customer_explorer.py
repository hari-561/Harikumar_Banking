
import streamlit as st

from src.frontend.api_client import (
    APIClientError,
    get_customers,
    get_customer_detail,
)
from src.frontend.components.ui import (
    render_section_header,
    render_api_error,
)
from src.frontend.components.customer_profile import (
    render_customer_profile,
)

from src.frontend.api_client import get_customer_activity

from src.frontend.components.customer_activity import (
    render_customer_activity,
)


SORT_OPTIONS = {
    "Customer ID": "customer_id",
    "Credit Limit": "credit_limit",
    "Credit Utilization": "latest_utilization_ratio",
    "Delayed Months": "delay_month_count",
    "Risk Score": "risk_score",
}


def render_customer_explorer():

    # ==========================================
    # PAGE HEADER
    # ==========================================

    render_section_header(
        "Customer Directory",
        "Search, filter, and investigate individual "
        "customer credit profiles.",
    )

    # ==========================================
    # CUSTOMER ID LOOKUP
    # ==========================================

    with st.form("customer_lookup_form"):

        lookup_col, button_col = st.columns([4, 1])

        with lookup_col:
            customer_id = st.number_input(
                "Find Customer by ID",
                min_value=1,
                value=1,
                step=1,
            )

        with button_col:
            st.write("")
            st.write("")

            lookup_submitted = st.form_submit_button(
                "Find Customer",
                width="stretch",
            )

    if lookup_submitted:

        try:
            customer = get_customer_detail(
                int(customer_id)
            )

            st.session_state[
                "explorer_selected_customer"
            ] = customer["customer_id"]

            st.success(
                f"Customer {customer['customer_id']} found."
            )

        except APIClientError as exc:
            render_api_error(exc)

    st.divider()

    # ==========================================
    # CUSTOMER FILTERS
    # ==========================================

    render_section_header(
        "Customer Filters",
        "Refine customer records using "
        "server-side filters.",
    )

    with st.form("customer_filter_form"):

        col1, col2, col3 = st.columns(3)

        with col1:
            risk_selection = st.selectbox(
                "Risk Band",
                ["All", "LOW", "MEDIUM", "HIGH"],
            )

        with col2:
            delay_selection = st.selectbox(
                "Payment Delay",
                ["All", "Yes", "No"],
            )

        with col3:
            page_size = st.selectbox(
                "Records Per Page",
                [10, 20, 50, 100],
                index=1,
            )

        col4, col5 = st.columns(2)

        with col4:
            min_limit = st.number_input(
                "Minimum Credit Limit",
                min_value=0.0,
                value=0.0,
                step=10000.0,
            )

        with col5:
            max_limit = st.number_input(
                "Maximum Credit Limit (0 = No Limit)",
                min_value=0.0,
                value=0.0,
                step=10000.0,
            )

        col6, col7 = st.columns(2)

        with col6:
            sort_label = st.selectbox(
                "Sort By",
                list(SORT_OPTIONS.keys()),
            )

        with col7:
            sort_order = st.selectbox(
                "Sort Order",
                ["asc", "desc"],
                format_func=lambda x: (
                    "Ascending"
                    if x == "asc"
                    else "Descending"
                ),
            )

        apply_filters = st.form_submit_button(
            "Apply Filters",
            type="primary",
        )

    # ==========================================
    # STORE FILTERS
    # ==========================================

    if (
        "explorer_filters" not in st.session_state
        or apply_filters
    ):

        if (
            max_limit > 0
            and max_limit < min_limit
        ):
            st.error(
                "Maximum credit limit must be greater "
                "than or equal to minimum credit limit."
            )
            return

        st.session_state["explorer_filters"] = {
            "risk_band": (
                None
                if risk_selection == "All"
                else risk_selection
            ),
            "has_payment_delay": (
                None
                if delay_selection == "All"
                else delay_selection == "Yes"
            ),
            "page_size": page_size,
            "min_credit_limit": (
                min_limit
                if min_limit > 0
                else None
            ),
            "max_credit_limit": (
                max_limit
                if max_limit > 0
                else None
            ),
            "sort_by": SORT_OPTIONS[sort_label],
            "sort_order": sort_order,
        }

        st.session_state["explorer_page"] = 1

    filters = st.session_state["explorer_filters"]

    page = st.session_state.get(
        "explorer_page",
        1,
    )

    # ==========================================
    # FETCH CUSTOMER RECORDS
    # ==========================================

    try:
        response = get_customers(
            page=page,
            **filters,
        )

    except APIClientError as exc:
        render_api_error(exc)
        return

    records = response["items"]
    total_records = response["total_records"]
    total_pages = response["total_pages"]
    current_page = response["page"]

    st.divider()

    render_section_header(
        "Customer Records",
        f"{total_records:,} matching customers",
    )

    # ==========================================
    # CUSTOMER TABLE
    # ==========================================

    if records:

        table_rows = []

        for customer in records:

            table_rows.append({
                "Customer ID": customer["customer_id"],
                "Age": customer["age"],
                "Gender": customer["gender"],
                "Education": customer["education"],
                "Credit Limit": customer["credit_limit"],
                "Delayed Months": customer["delay_month_count"],
                "Utilization (%)": round(
                    customer["latest_utilization_ratio"] * 100,
                    2,
                ),
                "Risk Score": customer["risk_score"],
                "Risk Band": customer["risk_band"],
            })

        selection = st.dataframe(
            table_rows,
            width="stretch",
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="customer_explorer_table",
            column_config={
                "Credit Limit": (
                    st.column_config.NumberColumn(
                        "Credit Limit",
                        format="%.2f",
                    )
                ),
                "Utilization (%)": (
                    st.column_config.NumberColumn(
                        "Utilization (%)",
                        format="%.2f%%",
                    )
                ),
            },
        )

        # --------------------------------------
        # HANDLE ROW SELECTION
        # --------------------------------------

        selected_rows = selection.selection.rows

        if selected_rows:

            selected_index = selected_rows[0]

            selected_customer_id = (
                table_rows[selected_index]["Customer ID"]
            )

            st.session_state[
                "explorer_selected_customer"
            ] = selected_customer_id

        # ======================================
        # PAGINATION
        # ======================================

        st.caption(
            f"Page {current_page:,} of {total_pages:,} "
            f"| {total_records:,} matching customers"
        )

        prev_col, page_col, next_col = st.columns(
            [1, 2, 1]
        )

        with prev_col:

            if st.button(
                "← Previous",
                disabled=current_page <= 1,
                width="stretch",
            ):
                st.session_state[
                    "explorer_page"
                ] = current_page - 1

                st.rerun()

        with page_col:

            st.markdown(
                f"<div style='text-align:center;"
                f"padding:9px;'>"
                f"Page {current_page} / {total_pages}"
                f"</div>",
                unsafe_allow_html=True,
            )

        with next_col:

            if st.button(
                "Next →",
                disabled=current_page >= total_pages,
                width="stretch",
            ):
                st.session_state[
                    "explorer_page"
                ] = current_page + 1

                st.rerun()

    else:

        st.info(
            "No customers match the selected filters."
        )

    # ==========================================
    # INDIVIDUAL CUSTOMER PROFILE
    # ==========================================

    selected_customer_id = st.session_state.get(
        "explorer_selected_customer"
    )

    st.divider()

    render_section_header(
        "Customer Profile",
        "View detailed customer information, "
        "credit metrics, and risk assessment.",
    )

    if selected_customer_id is not None:

        try:
            customer_detail = get_customer_detail(
                selected_customer_id
            )

            render_customer_profile(
                customer_detail
            )

            st.divider()

            activity_response = get_customer_activity(
                selected_customer_id
            )

            render_customer_activity(
                activity_response
            )

        except APIClientError as exc:
            render_api_error(exc)

    else:

        st.info(
            "Select a customer from the table "
            "or use Find Customer by ID to view "
            "their detailed profile."
        )
