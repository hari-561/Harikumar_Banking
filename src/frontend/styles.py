import streamlit as st


COLORS = {
    "navy": "#142B49",
    "blue": "#2563EB",
    "canvas": "#F4F7FB",
    "white": "#FFFFFF",
    "teal": "#0D9488",
    "red": "#DC3545",
    "amber": "#F59E0B",
    "text": "#172B4D",
    "muted": "#64748B",
    "border": "#E2E8F0",
}

RISK_COLORS = {
    "LOW": COLORS["teal"],
    "MEDIUM": COLORS["amber"],
    "HIGH": COLORS["red"],
}


def apply_global_styles():
    st.markdown(
        """
        <style>
        /* Application canvas */
        .stApp {
            background-color: #F4F7FB;
            color: #172B4D;
        }

        /* Main content area */
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 100%;
        }

        /* Typography */
        h1, h2, h3 {
            color: #142B49;
            font-weight: 650;
            letter-spacing: -0.025em;
        }

        h1 {
            font-size: 1.85rem;
        }

        h2 {
            font-size: 1.35rem;
        }

        h3 {
            font-size: 1.1rem;
        }

        /* Compact content spacing */
        div[data-testid="stVerticalBlock"] {
            gap: 0.8rem;
        }

        /* Buttons */
        .stButton > button,
        .stDownloadButton > button {
            border-radius: 9px;
            font-weight: 600;
            min-height: 2.4rem;
            transition: all 0.15s ease;
        }

        .stButton > button[kind="primary"] {
            background-color: #2563EB;
            border-color: #2563EB;
            color: white;
        }

        .stButton > button[kind="primary"]:hover {
            background-color: #1D4ED8;
            border-color: #1D4ED8;
        }

        /* Inputs */
        div[data-baseweb="input"] {
            border-radius: 9px;
        }

        /* Data tables */
        div[data-testid="stDataFrame"] {
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            overflow: hidden;
        }

        /* Horizontal dividers */
        hr {
            border-color: #E2E8F0;
            margin: 0.8rem 0;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #142B49;
        }

        section[data-testid="stSidebar"] * {
            color: #F8FAFC;
        }

        /* Sidebar navigation will be styled
           more precisely in Phase 7B-4. */

        /* Compact metric cards */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 11px;
            padding: 0.9rem 1rem;
            box-shadow: 0 2px 8px rgba(20, 43, 73, 0.035);
        }

        div[data-testid="stMetricLabel"] {
            color: #64748B;
        }

        div[data-testid="stMetricValue"] {
            color: #142B49;
            font-weight: 700;
        }

        /* Responsive content padding */
        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1rem;
            }
        }
        /* Brand */
        .app-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 2px 18px;
        }

        .brand-symbol {
            width: 42px;
            height: 42px;
            border-radius: 11px;
            background: #294869;
            color: #6EE7D2 !important;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 25px;
        }

        .brand-title {
            font-size: 21px;
            font-weight: 750;
            color: #FFFFFF !important;
            letter-spacing: -0.04em;
        }

        .brand-subtitle {
            font-size: 10px;
            font-weight: 650;
            letter-spacing: 0.16em;
            color: #AFC3D9 !important;
        }

        /* Sidebar navigation */
        section[data-testid="stSidebar"] div[role="radiogroup"] {
            gap: 6px;
        }

        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            padding: 10px 12px;
            border-radius: 9px;
            transition: background 0.15s ease;
        }

        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background: #243E5C;
        }

        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
            background: #294869;
            border-left: 3px solid #6EE7D2;
        }

        /* Connection status */
        .connection-status {
            display: flex;
            align-items: center;
            gap: 9px;
            padding: 11px 12px;
            border-radius: 9px;
            font-size: 12px;
            font-weight: 650;
        }

        .connection-status.connected {
            background: #123D42;
            color: #8CF1D7 !important;
        }

        .connection-status.disconnected {
            background: #542C35;
            color: #FFB4BE !important;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
        }

        /* Main page header */
        .page-header {
            padding: 4px 0 20px;
            border-bottom: 1px solid #E2E8F0;
            margin-bottom: 18px;
        }

        .page-eyebrow {
            font-size: 10px;
            font-weight: 750;
            color: #2563EB;
            letter-spacing: 0.14em;
            margin-bottom: 7px;
        }

        .page-header h1 {
            font-size: 29px;
            margin: 0 0 5px;
            color: #142B49;
            font-weight: 750;
        }

        .page-header p {
            margin: 0;
            font-size: 13px;
            color: #64748B;
        }

        /* Placeholder */
        .workspace-placeholder {
            min-height: 260px;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            background: #FFFFFF;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 30px;
        }

        .placeholder-icon {
            font-size: 34px;
            color: #2563EB;
            margin-bottom: 10px;
        }

        .workspace-placeholder h3 {
            color: #142B49;
            margin: 5px 0;
        }

        .workspace-placeholder p {
            color: #64748B;
            max-width: 380px;
            font-size: 13px;
            line-height: 1.7;
        }


        /* Compact sidebar */
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem;
        }

        /* Navigation items */
        section[data-testid="stSidebar"]
        div[role="radiogroup"] label {
            display: flex;
            align-items: center;
            min-height: 42px;
            padding: 9px 12px;
            border-radius: 9px;
            cursor: pointer;
            margin-bottom: 3px;
        }

        /* Hide native radio circles */
        section[data-testid="stSidebar"]
        div[role="radiogroup"] label > div:first-child {
            display: none;
        }

        /* Selected navigation */
        section[data-testid="stSidebar"]
        div[role="radiogroup"] label:has(input:checked) {
            background-color: #294869;
            border-left: 3px solid #6EE7D2;
        }

        /* Hover */
        section[data-testid="stSidebar"]
        div[role="radiogroup"] label:hover {
            background-color: #243E5C;
        }

        /* Navigation text */
        section[data-testid="stSidebar"]
        div[role="radiogroup"] label p {
            font-size: 13px;
            font-weight: 500;
            color: #D0DCE9;
        }




        /* Dense application layout */
        .block-container {
            padding-top: 1rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }

        /* Page header */
        .page-header {
            padding: 0 0 14px;
            margin-bottom: 16px;
        }

        .page-header h1 {
            font-size: 25px !important;
            line-height: 1.3;
            font-weight: 700;
            margin: 0 0 5px;
        }

        .page-header p {
            font-size: 13px;
            margin: 0;
        }

        /* Sidebar spacing */
        section[data-testid="stSidebar"]
        div[data-testid="stVerticalBlock"] {
            gap: 0.5rem;
        }


        /* Hide radio control graphics while preserving labels */
        section[data-testid="stSidebar"]
        div[role="radiogroup"] label
        div[data-testid="stMarkdownContainer"] {
            margin: 0;
        }

        section[data-testid="stSidebar"]
        div[role="radiogroup"] label > div:first-child {
            display: none !important;
        }

        /* Compact navigation spacing */
        section[data-testid="stSidebar"]
        div[role="radiogroup"] {
            gap: 2px !important;
        }

        section[data-testid="stSidebar"]
        div[role="radiogroup"] label {
            min-height: 40px !important;
            padding: 8px 12px !important;
            margin: 0 !important;
            width: 100%;
        }

        /* Navigation text */
        section[data-testid="stSidebar"]
        div[role="radiogroup"] label p {
            font-size: 13px !important;
            line-height: 1.3 !important;
        }

        /* Compact sidebar widget spacing */
        section[data-testid="stSidebar"]
        div[data-testid="stVerticalBlock"] {
            gap: 0.4rem !important;
        }



        /* =========================================
   REUSABLE COMPONENTS
   ========================================= */

        /* KPI Cards */
        .cr-kpi-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 11px;
            padding: 16px 18px;
            min-height: 122px;
            box-shadow: 0 2px 8px rgba(20, 43, 73, 0.035);
        }

        .cr-kpi-label {
            color: #64748B;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 10px;
        }

        .cr-kpi-value {
            font-size: 27px;
            font-weight: 750;
            letter-spacing: -0.035em;
            line-height: 1.2;
            font-variant-numeric: tabular-nums;
        }

        .cr-kpi-subtitle {
            color: #64748B;
            font-size: 11px;
            margin-top: 8px;
        }

        /* Risk Badges */
        .cr-risk-badge {
            display: inline-flex;
            align-items: center;
            border-radius: 7px;
            padding: 5px 11px;
            font-size: 11px;
            font-weight: 750;
            letter-spacing: 0.035em;
        }

        .cr-risk-low {
            background: #DDF7F0;
            color: #087F72;
        }

        .cr-risk-medium {
            background: #FFF2CF;
            color: #9A6700;
        }

        .cr-risk-high {
            background: #FDE5E7;
            color: #B42332;
        }

        .cr-risk-unknown {
            background: #E2E8F0;
            color: #475569;
        }

        /* Section Headers */
        .cr-section-header {
            margin: 8px 0 14px;
        }

        .cr-section-header h3 {
            font-size: 17px;
            font-weight: 700;
            color: #142B49;
            margin: 0 0 4px;
        }

        .cr-section-header p {
            font-size: 12px;
            color: #64748B;
            margin: 0;
        }

        /* Empty State */
        .cr-empty-state {
            background: #FFFFFF;
            border: 1px dashed #CBD5E1;
            border-radius: 12px;
            padding: 40px 24px;
            text-align: center;
        }

        .cr-empty-icon {
            font-size: 32px;
            color: #94A3B8;
            margin-bottom: 10px;
        }

        .cr-empty-state h3 {
            font-size: 17px;
            color: #142B49;
            margin: 0 0 8px;
        }

        .cr-empty-state p {
            font-size: 13px;
            color: #64748B;
            margin: 0;
        }


        /* Executive Insights */

        .cr-insights-heading {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            margin: 8px 0 14px;
            gap: 12px;
        }

        .cr-insights-heading span {
            color: #142B49;
            font-size: 17px;
            font-weight: 700;
        }

        .cr-insights-heading small {
            color: #64748B;
            font-size: 12px;
        }

        .cr-insight-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-left: 4px solid #2563EB;
            border-radius: 10px;
            padding: 16px 18px;
            min-height: 138px;
            height: 100%;
            box-shadow: 0 2px 8px rgba(20,43,73,0.035);
        }

        .cr-insight-red {
            border-left-color: #DC3545;
        }

        .cr-insight-amber {
            border-left-color: #F59E0B;
        }

        .cr-insight-blue {
            border-left-color: #2563EB;
        }

        .cr-insight-teal {
            border-left-color: #0D9488;
        }

        .cr-insight-title {
            color: #142B49;
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 9px;
        }

        .cr-insight-description {
            color: #64748B;
            font-size: 12px;
            line-height: 1.6;
        }

        /* Compact chart spacing */

        div[data-testid="stPlotlyChart"] {
            border: 1px solid #E2E8F0;
            border-radius: 11px;
            background: #FFFFFF;
            padding: 8px;
        }

        /* Responsive insight cards */

        @media (max-width: 900px) {
            .cr-insight-card {
                min-height: auto;
            }
        }


        /* Logout button styling */
.st-key-logout_button button {
    background-color: #B91C1C !important;
    color: #FFFFFF !important;
    border: 1px solid #B91C1C !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}

.st-key-logout_button button:hover {
    background-color: #991B1B !important;
    color: #FFFFFF !important;
    border-color: #991B1B !important;
}

.st-key-logout_button button p {
    color: #FFFFFF !important;
}


/* Compact API connection status */
.connection-status {
    padding: 8px 12px !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    min-height: auto !important;
}

.connection-status .status-dot {
    width: 7px !important;
    height: 7px !important;
}




        </style>
        """,
        unsafe_allow_html=True
    )