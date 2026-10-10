import streamlit as st

from src.frontend.api_client import (
    APIClientError,
    get_portfolio_summary,
    get_customer_segments,
)
from src.frontend.components.segment_drilldown import (
    render_segment_drilldown,
)
from src.frontend.components.ui import (
    render_kpi_card,
    render_section_header,
    render_api_error,
)

from src.frontend.components.charts import (
    create_segment_count_chart,
    create_segment_default_chart,
)

from src.frontend.components.segment_drilldown import (
    render_segment_drilldown,
)


SEGMENT_OPTIONS = {
    "Education": "education",
    "Gender": "gender",
    "Marital Status": "marital_status",
    "Age": "age",
}


def validate_segment_data(data):
    if not isinstance(data, list) or not data:
        raise ValueError(
            "Segment API returned no usable records."
        )

    required = {
        "segment",
        "total_customers",
        "average_credit_limit",
        "historical_defaults",
        "historical_default_rate_pct",
        "customers_with_payment_delay",
        "average_latest_utilization_pct",
    }

    for row in data:
        if not isinstance(row, dict):
            raise ValueError(
                "Invalid segment record."
            )

        missing = required - row.keys()
        if missing:
            raise ValueError(
                f"Missing segment fields: {sorted(missing)}"
            )

        if not str(row["segment"]).strip():
            raise ValueError("Empty segment label.")

        count = row["total_customers"]
        defaults = row["historical_defaults"]

        if not (
            isinstance(count, int)
            and not isinstance(count, bool)
            and count >= 0
            and isinstance(defaults, int)
            and not isinstance(defaults, bool)
            and 0 <= defaults <= count
        ):
            raise ValueError(
                "Invalid customer or default counts."
            )

        if not (
            0 <= row["historical_default_rate_pct"] <= 100
        ):
            raise ValueError(
                "Invalid historical default rate."
            )

    labels = [row["segment"] for row in data]
    if len(labels) != len(set(labels)):
        raise ValueError("Duplicate segment labels.")

    return data


def render_portfolio_analytics():

    render_section_header(
        "Portfolio Exposure",
        "Credit exposure and utilization indicators "
        "from the curated banking warehouse."
    )

    try:
        with st.spinner("Loading portfolio summary..."):
            summary = get_portfolio_summary()

    except APIClientError as error:
        render_api_error(error)
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        render_kpi_card(
            "Total Credit Exposure",
            f"{summary['total_credit_exposure'] / 1_000_000_000:.2f}B",
            "Source dataset monetary units",
            "navy",
        )

    with col2:
        render_kpi_card(
            "Over-Limit Customers",
            f"{summary['over_limit_customers']:,}",
            "Latest utilization above 100%",
            "red",
        )

    with col3:
        render_kpi_card(
            "Average Credit Limit",
            f"{summary['average_credit_limit']:,.2f}",
            "Source dataset monetary units",
            "blue",
        )

    st.divider()

    render_section_header(
        "Customer Segment Analysis",
        "Compare customer composition and "
        "historical credit outcomes."
    )

    selected_label = st.selectbox(
        "Segment customers by",
        options=list(SEGMENT_OPTIONS),
        index=0,
        key="portfolio_segment_type",
    )

    selected_segment = SEGMENT_OPTIONS[
        selected_label
    ]

    try:
        with st.spinner("Loading segment analytics..."):
            segment_data = validate_segment_data(
                get_customer_segments(
                    selected_segment
                )
            )

        # A complete segmentation should reconcile
        # with the portfolio-level totals.
        total_segment_customers = sum(
            row["total_customers"]
            for row in segment_data
        )

        total_segment_defaults = sum(
            row["historical_defaults"]
            for row in segment_data
        )

        if (
            total_segment_customers
            != summary["total_customers"]
            or total_segment_defaults
            != summary["historical_defaults"]
        ):
            st.warning(
                "Segment totals do not reconcile "
                "with the portfolio summary. "
                "Check the API data before interpreting "
                "these comparisons."
            )
            return

        left, right = st.columns(
            2,
            gap="medium",
        )

        with left:
            st.markdown(
                "**Customers by Segment**"
            )
            st.plotly_chart(
                create_segment_count_chart(
                    segment_data
                ),
                width="stretch",
                config={
                    "displayModeBar": False
                },
            )

        with right:
            st.markdown(
                "**Historical Default Rate by Segment**"
            )
            st.plotly_chart(
                create_segment_default_chart(
                    segment_data
                ),
                width="stretch",
                config={
                    "displayModeBar": False
                },
            )

        st.divider()

        render_section_header(
            "Segment Comparison",
            "Detailed credit exposure and "
            "repayment indicators."
        )

        table_rows = []

        for row in segment_data:
            table_rows.append({
                "Segment": row["segment"],
                "Customers": row[
                    "total_customers"
                ],
                "Historical Defaults": row[
                    "historical_defaults"
                ],
                "Default Rate (%)": row[
                    "historical_default_rate_pct"
                ],
                "Avg. Credit Limit": row[
                    "average_credit_limit"
                ],
                "Delayed Customers": row[
                    "customers_with_payment_delay"
                ],
                "Avg. Utilization (%)": row[
                    "average_latest_utilization_pct"
                ],
            })

        st.dataframe(
            table_rows,
            width="stretch",
            hide_index=True,
        )

        st.caption(
            "Segments reflect historical customer "
            "attributes and observed repayment "
            "outcomes. Differences between groups "
            "are descriptive and do not establish "
            "causation or individual creditworthiness."
        )


                # ---------------------------------------
        # Interactive Segment Drill-Down
        # ---------------------------------------

        st.divider()

        render_section_header(
            "Segment Drill-Down",
            "Inspect a selected customer segment "
            "against the overall portfolio."
        )

        segment_names = [
            row["segment"]
            for row in segment_data
        ]

        selected_name = st.selectbox(
            "Select a segment to analyze",
            options=segment_names,
            key=f"drilldown_{selected_segment}",
        )

        selected_record = next(
            row for row in segment_data
            if row["segment"] == selected_name
        )

        render_segment_drilldown(
            selected_record,
            summary,
        )




    except APIClientError as error:
        render_api_error(error)

    except (
        ValueError,
        KeyError,
        TypeError,
        ZeroDivisionError,
    ) as error:
        st.error(
            f"Unable to display segment analytics: "
            f"{error}"
        )