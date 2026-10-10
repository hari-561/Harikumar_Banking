import plotly.graph_objects as go

from src.frontend.styles import COLORS
from datetime import date
import plotly.graph_objects as go

RISK_PALETTE = {
    "LOW": COLORS["teal"],
    "MEDIUM": COLORS["amber"],
    "HIGH": COLORS["red"],
}

RISK_ORDER = ["LOW", "MEDIUM", "HIGH"]


def create_risk_donut(distribution):
    records = {
        row["risk_band"]: row
        for row in distribution
    }

    bands = [
        band for band in RISK_ORDER
        if band in records
    ]

    counts = [
        records[band]["total_customers"]
        for band in bands
    ]

    total = sum(counts)

    fig = go.Figure(
        data=[
            go.Pie(
                labels=bands,
                values=counts,
                hole=0.68,
                sort=False,
                marker=dict(
                    colors=[
                        RISK_PALETTE[band]
                        for band in bands
                    ]
                ),
                textinfo="percent",
                textposition="outside",
                hovertemplate=(
                    "<b>%{label} Risk</b><br>"
                    "Customers: %{value:,}<br>"
                    "Share: %{percent}"
                    "<extra></extra>"
                ),
            )
        ]
    )

    fig.add_annotation(
        text=f"<b>{total:,}</b><br>Customers",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(
            size=19,
            color=COLORS["navy"]
        ),
        align="center"
    )

    fig.update_layout(
        height=340,
        margin=dict(l=20, r=20, t=15, b=15),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        showlegend=True,
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.08,
        ),
    )

    return fig


def create_default_rate_chart(distribution):
    records = {
        row["risk_band"]: row
        for row in distribution
    }

    bands = [
        band for band in RISK_ORDER
        if band in records
    ]

    rates = [
        records[band]["historical_default_rate_pct"]
        for band in bands
    ]

    counts = [
        records[band]["total_customers"]
        for band in bands
    ]

    defaults = [
        records[band]["historical_defaults"]
        for band in bands
    ]

    fig = go.Figure(
        go.Bar(
            x=bands,
            y=rates,
            marker_color=[
                RISK_PALETTE[band]
                for band in bands
            ],
            text=[
                f"{rate:.2f}%"
                for rate in rates
            ],
            textposition="outside",
            customdata=list(zip(counts, defaults)),
            hovertemplate=(
                "<b>%{x} Risk</b><br>"
                "Historical default rate: %{y:.2f}%<br>"
                "Customers: %{customdata[0]:,}<br>"
                "Observed defaults: %{customdata[1]:,}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=340,
        margin=dict(l=35, r=20, t=30, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        yaxis=dict(
            title="Historical Default Rate (%)",
            range=[0, max(60, max(rates, default=0) * 1.2)],
            gridcolor=COLORS["border"],
            zeroline=False,
        ),
        xaxis=dict(
            title=None,
            showgrid=False,
        ),
        bargap=0.45,
        showlegend=False,
    )

    return fig


def prepare_monthly_trends(monthly_data):
    """
    Validate and normalize the monthly API response.
    """

    if not isinstance(monthly_data, list):
        raise ValueError(
            "Monthly trends response must be a list."
        )

    if len(monthly_data) != 6:
        raise ValueError(
            "Expected exactly six monthly records."
        )

    records = sorted(
        monthly_data,
        key=lambda row: row["activity_month"]
    )

    expected_months = [
        "2005-04-01",
        "2005-05-01",
        "2005-06-01",
        "2005-07-01",
        "2005-08-01",
        "2005-09-01",
    ]

    actual_months = [
        row["activity_month"]
        for row in records
    ]

    if actual_months != expected_months:
        raise ValueError(
            "Monthly trend records do not match "
            "the expected April–September 2005 period."
        )

    for row in records:
        if row["customer_records"] <= 0:
            raise ValueError(
                "Invalid customer count in monthly trends."
            )

        if not (
            0 <= row["delayed_customers"]
            <= row["customer_records"]
        ):
            raise ValueError(
                "Invalid delayed customer count."
            )

        if not (
            0 <= row["delayed_customer_rate_pct"]
            <= 100
        ):
            raise ValueError(
                "Invalid monthly delinquency rate."
            )

    return records


def create_monthly_delinquency_chart(monthly_data):
    """
    Line chart showing monthly delinquency percentage.
    """

    records = prepare_monthly_trends(monthly_data)

    months = [
        date.fromisoformat(
            row["activity_month"]
        ).strftime("%b")
        for row in records
    ]

    rates = [
        row["delayed_customer_rate_pct"]
        for row in records
    ]

    delayed_counts = [
        row["delayed_customers"]
        for row in records
    ]

    total_counts = [
        row["customer_records"]
        for row in records
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=months,
            y=rates,
            mode="lines+markers+text",
            name="Delinquency Rate",
            line=dict(
                color=COLORS["blue"],
                width=3
            ),
            marker=dict(
                size=9,
                color=COLORS["blue"],
                line=dict(
                    color="white",
                    width=2
                )
            ),
            text=[
                f"{rate:.2f}%"
                for rate in rates
            ],
            textposition="top center",
            textfont=dict(size=11),
            customdata=list(
                zip(delayed_counts, total_counts)
            ),
            hovertemplate=(
                "<b>%{x} 2005</b><br>"
                "Delinquency Rate: %{y:.2f}%<br>"
                "Delayed Customers: %{customdata[0]:,}<br>"
                "Total Customers: %{customdata[1]:,}"
                "<extra></extra>"
            )
        )
    )

    fig.update_layout(
        height=340,
        margin=dict(
            l=45,
            r=20,
            t=35,
            b=35
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color=COLORS["text"]
        ),
        xaxis=dict(
            title=None,
            showgrid=False
        ),
        yaxis=dict(
            title="Delinquency Rate (%)",
            range=[0, max(rates) * 1.25],
            gridcolor=COLORS["border"],
            zeroline=False,
            ticksuffix="%"
        ),
        showlegend=False,
        hovermode="x unified"
    )

    return fig


def create_monthly_delay_count_chart(monthly_data):
    """
    Bar chart showing delayed customer counts.
    """

    records = prepare_monthly_trends(monthly_data)

    months = [
        date.fromisoformat(
            row["activity_month"]
        ).strftime("%b")
        for row in records
    ]

    counts = [
        row["delayed_customers"]
        for row in records
    ]

    rates = [
        row["delayed_customer_rate_pct"]
        for row in records
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=months,
            y=counts,
            name="Delayed Customers",
            marker=dict(
                color=[
                    COLORS["red"]
                    if month == "Sep"
                    else COLORS["blue"]
                    for month in months
                ],
                cornerradius=5
            ),
            text=[
                f"{count:,}"
                for count in counts
            ],
            textposition="outside",
            textfont=dict(size=11),
            customdata=rates,
            hovertemplate=(
                "<b>%{x} 2005</b><br>"
                "Delayed Customers: %{y:,}<br>"
                "Delinquency Rate: %{customdata:.2f}%"
                "<extra></extra>"
            )
        )
    )

    fig.update_layout(
        height=340,
        margin=dict(
            l=45,
            r=20,
            t=35,
            b=35
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color=COLORS["text"]
        ),
        xaxis=dict(
            title=None,
            showgrid=False
        ),
        yaxis=dict(
            title="Delayed Customers",
            range=[0, max(counts) * 1.25],
            gridcolor=COLORS["border"],
            zeroline=False
        ),
        bargap=0.35,
        showlegend=False
    )

    return fig



def create_segment_count_chart(segment_data):
    labels = [
        row["segment"] for row in segment_data
    ]
    counts = [
        row["total_customers"]
        for row in segment_data
    ]

    fig = go.Figure(
        go.Bar(
            x=counts,
            y=labels,
            orientation="h",
            marker_color=COLORS["blue"],
            text=[f"{n:,}" for n in counts],
            textposition="auto",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Customers: %{x:,}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=max(320, 62 * len(labels)),
        margin=dict(l=20, r=25, t=15, b=35),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        xaxis=dict(
            title="Customers",
            gridcolor=COLORS["border"],
        ),
        yaxis=dict(
            title=None,
            autorange="reversed",
            automargin=True,
        ),
        showlegend=False,
    )

    return fig


def create_segment_default_chart(segment_data):
    labels = [
        row["segment"] for row in segment_data
    ]
    rates = [
        row["historical_default_rate_pct"]
        for row in segment_data
    ]
    defaults = [
        row["historical_defaults"]
        for row in segment_data
    ]

    fig = go.Figure(
        go.Bar(
            x=rates,
            y=labels,
            orientation="h",
            marker_color=COLORS["amber"],
            text=[f"{r:.2f}%" for r in rates],
            textposition="auto",
            customdata=defaults,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Historical default rate: %{x:.2f}%<br>"
                "Observed defaults: %{customdata:,}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=max(320, 62 * len(labels)),
        margin=dict(l=20, r=35, t=15, b=35),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        xaxis=dict(
            title="Historical Default Rate (%)",
            ticksuffix="%",
            range=[0, max(10, max(rates, default=0) * 1.2)],
            gridcolor=COLORS["border"],
        ),
        yaxis=dict(
            title=None,
            autorange="reversed",
            automargin=True,
        ),
        showlegend=False,
    )

    return fig