
from io import BytesIO

import pandas as pd
import streamlit as st

from src.frontend.api_client import (
    export_customers_csv,
)


SORT_OPTIONS = {
    "Customer ID": "customer_id",
    "Credit Limit": "credit_limit",
    "Credit Utilization": "latest_utilization_ratio",
    "Delayed Months": "delay_month_count",
    "Risk Score": "risk_score",
}


def render_customer_export():

    st.markdown("### Customer Data Export")

    st.caption(
        "Download customer credit and risk data "
        "using filters supported by FastAPI."
    )

    with st.form("customer_csv_export_form"):

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
            sort_label = st.selectbox(
                "Sort By",
                list(SORT_OPTIONS.keys()),
            )

        col4, col5, col6 = st.columns(3)

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

        with col6:
            sort_order = st.selectbox(
                "Sort Order",
                ["asc", "desc"],
                format_func=lambda value: (
                    "Ascending"
                    if value == "asc"
                    else "Descending"
                ),
            )

        generate_clicked = st.form_submit_button(
            "Generate Customer CSV",
            type="primary",
            width="stretch",
        )

    if generate_clicked:

        # Invalidate any previously generated file
        # before applying new filters.
        st.session_state.pop(
            "customer_export_bytes",
            None,
        )

        st.session_state.pop(
            "customer_export_info",
            None,
        )

        if (
            max_limit > 0
            and max_limit < min_limit
        ):
            st.error(
                "Maximum credit limit must be greater "
                "than or equal to minimum credit limit."
            )
            return

        filters = {
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
            "min_credit_limit": (
                min_limit if min_limit > 0 else None
            ),
            "max_credit_limit": (
                max_limit if max_limit > 0 else None
            ),
            "sort_by": SORT_OPTIONS[sort_label],
            "sort_order": sort_order,
        }

        try:
            with st.spinner(
                "Generating customer export..."
            ):
                csv_bytes = export_customers_csv(
                    **filters
                )

                df = pd.read_csv(
                    BytesIO(csv_bytes)
                )

            st.session_state[
                "customer_export_bytes"
            ] = csv_bytes

            st.session_state[
                "customer_export_info"
            ] = {
                "rows": len(df),
                "columns": len(df.columns),
                "filters": filters,
                "preview": df.head(10),
            }

        except (
            RuntimeError,
            ValueError,
            pd.errors.ParserError,
            pd.errors.EmptyDataError,
        ) as exc:
            st.error(
                f"Unable to generate CSV export: {exc}"
            )
            return

    csv_bytes = st.session_state.get(
        "customer_export_bytes"
    )

    export_info = st.session_state.get(
        "customer_export_info"
    )

    if csv_bytes is None or export_info is None:
        st.info(
            "Select filters and generate a CSV "
            "to preview and download the data."
        )
        return

    st.divider()

    st.markdown("#### Export Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Matching Customers",
            f"{export_info['rows']:,}",
        )

    with col2:
        st.metric(
            "Export Columns",
            export_info["columns"],
        )

    with col3:
        st.metric(
            "File Size",
            f"{len(csv_bytes) / 1024:.1f} KB",
        )

    st.markdown("#### CSV Preview")

    if export_info["rows"] == 0:
        st.warning(
            "No customers match the selected filters."
        )

    else:
        st.dataframe(
            export_info["preview"],
            width="stretch",
            hide_index=True,
        )

    st.caption(
        "Preview shows up to 10 records. "
        "The downloaded CSV includes every "
        "matching customer."
    )

    st.download_button(
        label="Download Customer CSV",
        data=csv_bytes,
        file_name="customers_export.csv",
        mime="text/csv",
        type="primary",
        width="stretch",
        disabled=export_info["rows"] == 0,
    )
