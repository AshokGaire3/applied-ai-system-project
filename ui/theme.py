import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --pp-bg: #f5f7fb;
            --pp-surface: #ffffff;
            --pp-text: #111827;
            --pp-muted: #64748b;
            --pp-border: #e5e7eb;
            --pp-primary: #5b5ce2;
            --pp-primary-soft: #ede9fe;
            --pp-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
            --pp-radius: 14px;
        }

        .stApp {
            background: var(--pp-bg);
            color: var(--pp-text);
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 5rem;
            max-width: 1320px;
        }

        .pawpal-section-title {
            margin-top: 0.15rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
            font-size: 1.05rem;
        }

        .pawpal-card {
            border: 1px solid var(--pp-border);
            border-radius: var(--pp-radius);
            padding: 1rem;
            background: var(--pp-surface);
            margin-bottom: 0.75rem;
            box-shadow: var(--pp-shadow);
            transition: transform 160ms ease, box-shadow 160ms ease;
        }

        .pawpal-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.1);
        }

        .pawpal-muted {
            color: var(--pp-muted);
            font-size: 0.93rem;
        }

        section[data-testid="stSidebar"] {
            border-right: 1px solid var(--pp-border);
            background: linear-gradient(180deg, #f8f9ff 0%, #ffffff 100%);
        }

        .pawpal-brand {
            margin-bottom: 0.8rem;
            border-radius: 12px;
            border: 1px solid #dbe2ff;
            background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%);
            padding: 0.8rem 0.9rem;
        }

        div[data-testid="stSidebar"] div[data-testid="stRadio"] label {
            border-radius: 12px;
            padding: 0.45rem 0.6rem;
            border: 1px solid transparent;
            transition: all 140ms ease;
        }

        div[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
            background: #f5f3ff;
            border-color: #ddd6fe;
        }

        div[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {
            background: var(--pp-primary-soft);
            border-color: #c4b5fd;
            box-shadow: inset 0 0 0 1px #c4b5fd;
        }

        .pawpal-topbar {
            position: sticky;
            top: 0;
            z-index: 10;
            border-radius: 14px;
            border: 1px solid var(--pp-border);
            margin-bottom: 1rem;
            background: rgba(255, 255, 255, 0.88);
            backdrop-filter: blur(7px);
            padding: 0.8rem 1rem;
        }

        .pawpal-topbar-title {
            font-size: 1.35rem;
            font-weight: 700;
            color: #111827;
        }

        .pawpal-topbar-subtitle {
            font-size: 0.9rem;
            color: var(--pp-muted);
        }

        div[data-testid="stMetric"] {
            border: 1px solid var(--pp-border);
            border-radius: 12px;
            padding: 0.7rem;
            background: white;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.35rem;
        }

        /* floating quick actions container */
        div[data-testid="stVerticalBlock"]:has(
            > div[data-testid="element-container"]
            > div[data-testid="stMarkdownContainer"]
            > .pawpal-fab-marker
        ) {
            position: fixed;
            right: 1.4rem;
            bottom: 1.2rem;
            z-index: 90;
            background: transparent;
        }

        .pawpal-fab-marker {
            display: none;
        }

        div[data-testid="stPopover"] > button {
            border-radius: 999px !important;
            border: none !important;
            background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%) !important;
            color: white !important;
            box-shadow: 0 10px 25px rgba(99, 102, 241, 0.35);
            min-height: 2.8rem;
            transition: transform 140ms ease;
        }

        div[data-testid="stPopover"] > button:hover {
            transform: translateY(-1px);
        }

        @media (max-width: 1024px) {
            .block-container {
                padding-bottom: 6rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
