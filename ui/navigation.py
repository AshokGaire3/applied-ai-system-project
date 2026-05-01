import streamlit as st


NAV_ITEMS: tuple[tuple[str, str], ...] = (
    ("Profile", "👤"),
    ("Pets", "🐾"),
    ("Tasks", "✅"),
    ("Schedule", "🗓️"),
    ("Wellness", "💚"),
    ("Care handoff", "📄"),
    ("AI Coach", "🤖"),
)
DEFAULT_SERVICE = NAV_ITEMS[0][0]
_SERVICE_TO_SLUG = {label: label.lower().replace(" ", "-") for label, _ in NAV_ITEMS}
_SLUG_TO_SERVICE = {slug: label for label, slug in _SERVICE_TO_SLUG.items()}


def normalize_service(service: str | None) -> str:
    if not service:
        return DEFAULT_SERVICE
    return service if service in _SERVICE_TO_SLUG else DEFAULT_SERVICE


def service_from_query_params() -> str:
    raw = st.query_params.get("page")
    if not raw:
        return DEFAULT_SERVICE
    slug = str(raw).strip().lower()
    return _SLUG_TO_SERVICE.get(slug, DEFAULT_SERVICE)


def sync_service_query_param(service: str) -> None:
    st.query_params["page"] = _SERVICE_TO_SLUG[service]


def render_sidebar_nav(current_service: str) -> str:
    selected_service = normalize_service(current_service)
    if "sidebar_collapsed" not in st.session_state:
        st.session_state.sidebar_collapsed = False

    with st.sidebar:
        st.markdown('<div class="pawpal-brand">🐾 <strong>PawPal+</strong></div>', unsafe_allow_html=True)
        collapse_label = "Expand" if st.session_state.sidebar_collapsed else "Collapse"
        if st.button(f"{collapse_label} sidebar", use_container_width=True):
            st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed

        labels = [label for label, _ in NAV_ITEMS]
        icon_map = {label: icon for label, icon in NAV_ITEMS}
        nav_options = labels

        selected = st.radio(
            "Navigate",
            options=nav_options,
            index=nav_options.index(selected_service),
            label_visibility="collapsed",
            format_func=(
                (lambda label: icon_map[label])
                if st.session_state.sidebar_collapsed
                else (lambda label: f"{icon_map[label]}  {label}")
            ),
            key="pawpal_sidebar_nav",
        )

    sync_service_query_param(selected)
    return selected
