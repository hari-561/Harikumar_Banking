import html
from textwrap import dedent

import streamlit as st

from src.frontend.styles import COLORS


def render_kpi_card(
    label,
    value,
    subtitle="",
    accent="blue"
):
    """
    Render a compact enterprise-style KPI card.
    """

    accent_color = COLORS.get(
        accent,
        COLORS["blue"]
    )

    safe_label = html.escape(str(label))
    safe_value = html.escape(str(value))
    safe_subtitle = html.escape(str(subtitle))

    # Keep the HTML on one line to prevent
    # Streamlit from interpreting it as code.
    markup = (
        '<div class="cr-kpi-card">'
        f'<div class="cr-kpi-label">{safe_label}</div>'
        f'<div class="cr-kpi-value" '
        f'style="color: {accent_color};">'
        f'{safe_value}</div>'
        f'<div class="cr-kpi-subtitle">{safe_subtitle}</div>'
        '</div>'
    )

    st.markdown(
        markup,
        unsafe_allow_html=True
    )


def render_risk_badge(risk_band):
    """
    Render a risk classification badge.
    """

    band = str(risk_band).upper()

    if band not in ("LOW", "MEDIUM", "HIGH"):
        band = "UNKNOWN"

    markup = f"""
    <span class="cr-risk-badge cr-risk-{band.lower()}">
        {band} RISK
    </span>
    """

    st.markdown(
        dedent(markup).strip(),
        unsafe_allow_html=True
    )


def render_section_header(
    title,
    description=""
):
    markup = f"""
    <div class="cr-section-header">
        <h3>{html.escape(str(title))}</h3>
        <p>{html.escape(str(description))}</p>
    </div>
    """

    st.markdown(
        dedent(markup).strip(),
        unsafe_allow_html=True
    )


def render_empty_state(
    title="No records found",
    message="Try adjusting your filters."
):
    markup = f"""
    <div class="cr-empty-state">
        <div class="cr-empty-icon">⌕</div>
        <h3>{html.escape(str(title))}</h3>
        <p>{html.escape(str(message))}</p>
    </div>
    """

    st.markdown(
        dedent(markup).strip(),
        unsafe_allow_html=True
    )


def render_api_error(error):
    """
    Display a safe, consistent API error.
    """

    st.error(
        f"Unable to load data: {error}",
        icon="⚠️"
    )