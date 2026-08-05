"""
Shared CSS and styling helpers for Streamlit pages.

Premium design system with navy blue theme, visible inputs, and polished elements.
"""

import html as _html

import streamlit as st
import pandas as pd

# ── Common CSS applied to every page ────────────────────────────
_COMMON_CSS = """\
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body { font-family: 'Inter', sans-serif; }
html { scroll-behavior: smooth; }

/* Remove Streamlit default top padding */
.stMainBlockContainer {
    padding-top: 0rem !important;
}
.stAppHeader {
    background: transparent !important;
}
/* Hide the sidebar top decoration / header gap */
[data-testid="stSidebar"] > div:first-child {
    padding-top: 0rem !important;
}
[data-testid="stSidebarHeader"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}
[data-testid="stSidebarNav"] {
    padding-top: 0 !important;
    margin-top: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] {
    padding-top: 0.5rem !important;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #050d1a 0%, #0f1d32 100%) !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    overflow-x: hidden !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdown"],
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown h3,
[data-testid="stSidebar"] .stMarkdown li,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stCaption {
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #ffffff !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] a {
    color: #60a5fa !important;
}
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small {
    color: #cbd5e1 !important;
}
[data-testid="stSidebar"] .stSpinner > div > span {
    color: #e2e8f0 !important;
}

/* PASSWORD / TEXT INPUT */
[data-testid="stSidebar"] input[type="password"],
[data-testid="stSidebar"] input[type="text"] {
    background-color: #0f1d32 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: 1.5px solid #1e3a5f !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    font-size: 16px !important;
    caret-color: #60a5fa !important;
}
[data-testid="stSidebar"] input[type="password"] {
    font-size: 20px !important;
    letter-spacing: 4px !important;
}
[data-testid="stSidebar"] input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.35) !important;
    outline: none !important;
}
[data-testid="stSidebar"] input::placeholder {
    color: #4b6a8f !important;
    -webkit-text-fill-color: #4b6a8f !important;
    font-size: 14px !important;
    letter-spacing: normal !important;
}
/* Eye toggle icon for password fields */
[data-testid="stSidebar"] button[kind="icon"] svg,
[data-testid="stSidebar"] [data-testid="stTextInput"] button svg {
    fill: #cbd5e1 !important;
    stroke: #cbd5e1 !important;
}

/* Sidebar divider */
[data-testid="stSidebar"] hr {
    border-color: #1e3a5f !important;
}

/* BUTTONS */
.stButton > button {
    background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 1.3rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 15px rgba(29,78,216,0.35) !important;
    letter-spacing: 0.02em !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(29,78,216,0.5) !important;
    background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* Download button */
.stDownloadButton > button {
    background: linear-gradient(135deg, #0369a1 0%, #0284c7 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(3,105,161,0.3) !important;
}
.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(3,105,161,0.45) !important;
}

/* FORM SUBMIT BUTTON */
.stFormSubmitButton > button {
    background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1.5rem !important;
    box-shadow: 0 4px 15px rgba(29,78,216,0.35) !important;
    transition: all 0.3s ease !important;
}
.stFormSubmitButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(29,78,216,0.5) !important;
}

/* METRICS */
[data-testid="stMetric"] {
    background: linear-gradient(145deg, #ffffff, #eff6ff) !important;
    border: 1px solid #dbeafe !important;
    border-radius: 14px !important;
    padding: 1.1rem !important;
    box-shadow: 0 2px 10px rgba(29,78,216,0.06) !important;
    transition: transform 0.2s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
}
[data-testid="stMetric"] label {
    color: #1e40af !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #1e293b !important;
    font-weight: 800 !important;
}

/* FILE UPLOADER */
[data-testid="stFileUploader"] {
    border-radius: 14px !important;
}
[data-testid="stFileUploader"] section {
    border: 2px dashed #93c5fd !important;
    border-radius: 14px !important;
    background: linear-gradient(145deg, #eff6ff, #dbeafe) !important;
    padding: 1.5rem !important;
    transition: all 0.3s ease;
}
[data-testid="stFileUploader"] section:hover {
    border-color: #3b82f6 !important;
    background: linear-gradient(145deg, #dbeafe, #bfdbfe) !important;
}
[data-testid="stFileUploader"] button {
    color: #1e293b !important; /* Forces dark text on the light button */ 
}
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] small {
    color: #1e293b !important; /* Forces dark text for uploader labels and instructions */
}



/* MAIN CONTENT TEXT INPUT */
.stTextInput > div > div {
    border-radius: 10px !important;
    border: 1.5px solid #93c5fd !important;
    transition: border-color 0.2s ease;
}
.stTextInput > div > div:focus-within {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.15) !important;
}

/* EXPANDER */
.streamlit-expanderHeader {
    background: linear-gradient(145deg, #eff6ff, #dbeafe) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}

/* Fix: Hide Material Icon text that overlaps expander header when font fails to load */
[data-testid="stExpander"] details summary svg {
    overflow: hidden !important;
    width: 1rem !important;
    height: 1rem !important;
    flex-shrink: 0 !important;
}
[data-testid="stExpander"] details summary span[data-testid="stMarkdownContainer"] {
    position: relative !important;
    z-index: 2 !important;
    background: inherit !important;
}
/* Ensure the expander toggle icon renders correctly and does not overlap */
[data-testid="stExpander"] details summary > div {
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] details summary > div > div:first-child {
    flex-shrink: 0 !important;
    max-width: 1.5rem !important;
    width: 1.5rem !important;
    overflow: hidden !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
/* Hide fallback Material Icon text like "arrow_down" */
[data-testid="stExpander"] details summary > div > div:first-child span {
    font-size: 0 !important;
    width: 0 !important;
    overflow: hidden !important;
    display: none !important;
}
/* Make sure the SVG icon is visible */
[data-testid="stExpander"] details summary > div > div:first-child svg {
    display: block !important;
    font-size: 1rem !important;
}

/* ALERTS */
.stAlert {
    border-radius: 12px !important;
}

/* DATAFRAME */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 2px 8px rgba(29,78,216,0.08) !important;
}

/* SLIDER */
.stSlider > div > div > div {
    color: #2563eb !important;
}

/* PAGE HEADER */
.page-header {
    text-align: center;
    padding: 2rem 1rem 1.5rem;
    margin-bottom: 1rem;
}
.page-header h1 {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #1d4ed8, #2563eb, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
}
.page-header p {
    color: #475569;
    font-size: 0.95rem;
    margin: 0;
}

/* GLOBAL TEXT VISIBILITY */
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
    color: #0f172a !important;
    font-weight: 700 !important;
}
.stMarkdown p, .stMarkdown li, .stMarkdown span {
    color: #0f172a !important; /* Darker, high-contrast text */
}
.stCaption, .stMarkdown small {
    color: #334155 !important; /* Darker slate gray for small text and captions */
}

[data-testid="stHeader"] h1,
[data-testid="stHeader"] h2 {
    color: #0f172a !important;
}
/* Subheader visibility */
.stSubheader, [data-testid="stSubheader"] {
    color: #0f172a !important;
}
/* Form labels and text */
label {
    color: #1e293b !important;
    font-weight: 600 !important;
}
/* Spinner text */
.stSpinner > div > span {
    color: #1e293b !important;
}
/* Selectbox and other widget text */
[data-testid="stSelectbox"] label,
[data-testid="stSlider"] label,
[data-testid="stFileUploader"] label {
    color: #0f172a !important;
    font-weight: 600 !important;
}
/* Main area text inputs */
.stTextInput input {
    color: #0f172a !important;
}
/* Metric text override for main area */
[data-testid="stMetric"] label {
    color: #1e40af !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #0f172a !important;
}

/* Sidebar text color overrides (restores white text visibility on dark sidebar background) */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption {
    color: #ffffff !important;
}
</style>
"""

# ── Chat bubble CSS (for pages with conversation UI) ────────────
_CHAT_CSS = """\
<style>
/* CHAT MESSAGES */
.chat-message {
    display: flex;
    align-items: flex-start;
    margin-bottom: 20px;
    animation: chatFadeIn 0.4s ease-out;
}
@keyframes chatFadeIn {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}

.chat-message .avatar {
    font-size: 1.4rem;
    margin-right: 14px;
    min-width: 42px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    flex-shrink: 0;
}

.chat-message.user .avatar {
    background: linear-gradient(135deg, #eff6ff, #dbeafe);
    border: 2px solid #93c5fd;
}

.chat-message.bot .avatar {
    background: linear-gradient(135deg, #1d4ed8, #2563eb);
    border: 2px solid #60a5fa;
    color: white;
    box-shadow: 0 3px 10px rgba(29,78,216,0.3);
}

.chat-message .message {
    padding: 16px 20px;
    border-radius: 18px;
    max-width: 82%;
    font-size: 14px;
    line-height: 1.7;
    word-wrap: break-word;
    overflow-wrap: break-word;
    min-width: 0;
}

.chat-message.user .message {
    background: linear-gradient(145deg, #ffffff, #eff6ff);
    border: 1px solid #dbeafe;
    border-top-left-radius: 4px;
    box-shadow: 0 2px 8px rgba(29,78,216,0.06);
    color: #1e293b;
}

.chat-message.bot .message {
    background: linear-gradient(145deg, #eff6ff, #dbeafe);
    border: 1px solid #93c5fd;
    border-top-left-radius: 4px;
    box-shadow: 0 2px 12px rgba(29,78,216,0.1);
    color: #1e293b;
}

.chat-message .message b {
    color: #0f172a;
    font-weight: 700;
}
</style>
"""


def inject_common_css() -> None:
    """Inject the shared premium CSS into a Streamlit page."""
    st.markdown(_COMMON_CSS, unsafe_allow_html=True)


def inject_chat_css() -> None:
    """Inject common CSS + chat bubble CSS (use on pages with conversation UI)."""
    st.markdown(_COMMON_CSS + _CHAT_CSS, unsafe_allow_html=True)


# ── Shared Streamlit helpers ────────────────────────────────────


def render_chat_message(question: str, answer: str) -> None:
    """
    Render a chat message pair with XSS-safe HTML escaping.

    User input is escaped before injection into the HTML template.
    """
    safe_q = _html.escape(question)
    safe_a = _html.escape(answer)
    st.markdown(
        f"""
        <div class="chat-message user">
            <div class="avatar">👤</div>
            <div class="message"><b>You:</b><br>{safe_q}</div>
        </div>
        <div class="chat-message bot">
            <div class="avatar">🤖</div>
            <div class="message"><b>Bot:</b><br>{safe_a}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def init_api_key_state(settings) -> None:
    """
    Synchronize the API key from settings into Streamlit session state.

    Call once at the top of each page to avoid repeating the same
    init block across every Streamlit page.
    """
    env_key = settings.google_api_key

    if "env_api_key" not in st.session_state:
        st.session_state.env_api_key = env_key
    if st.session_state.env_api_key != env_key:
        st.session_state.api_key = env_key
        st.session_state.env_api_key = env_key

    if "api_key" not in st.session_state:
        st.session_state.api_key = env_key


def render_sidebar_history(
    history_key: str,
    file_name_prefix: str,
    *,
    rerun_key: str = "",
    reset_key: str = "",
) -> None:
    """
    Render the shared sidebar history controls: Rerun, Reset, and Download.

    Args:
        history_key:      Session state key for the history list.
        file_name_prefix: Prefix for the download CSV filename.
        rerun_key:        Unique Streamlit widget key for the Rerun button.
        reset_key:        Unique Streamlit widget key for the Reset button.
    """
    st.subheader("📜 History")
    col1, col2 = st.columns(2)

    if col1.button("Rerun", key=rerun_key or f"{history_key}_rerun"):
        st.rerun()
    if col2.button("Reset", key=reset_key or f"{history_key}_reset"):
        st.session_state[history_key] = []
        st.rerun()

    history = st.session_state.get(history_key, [])
    if history:
        hist_df = pd.DataFrame(
            history,
            columns=["Question", "Answer", "Model", "Timestamp", "File"],
        )
        st.download_button(
            label="⬇️ Download History CSV",
            data=hist_df.to_csv(index=False),
            file_name=f"{file_name_prefix}_history.csv",
            mime="text/csv",
            use_container_width=True,
        )
