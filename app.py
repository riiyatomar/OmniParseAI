"""
📚 Document Chat Hub – Home Page

This is the main entry point for the multi-page Streamlit app.
Run with:  streamlit run app.py
"""

import streamlit as st

# ── Page config (must be first Streamlit call) ──────────────────
st.set_page_config(
    page_title="Document Chat Hub",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Global ────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }

    /* ── Kill ALL Streamlit top whitespace ──────────────── */
    .stMainBlockContainer {
        padding-top: 0 !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    .stAppHeader {
        background: transparent !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    #MainMenu { visibility: hidden !important; }

    /* ── Sidebar ───────────────────────────────────────── */
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
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
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #050d1a 0%, #0f1d32 100%) !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdown"],
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] small,
    [data-testid="stSidebar"] a {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] a {
        color: #60a5fa !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #1e3a5f !important;
    }

    /* ── Hero banner ───────────────────────────────────── */
    .hero-banner {
        background: linear-gradient(135deg, #050d1a 0%, #0a1f3d 40%, #112d5e 70%, #0a1f3d 100%);
        border-radius: 24px;
        padding: 3rem 2.5rem 2.5rem;
        margin: 0.5rem 0 2rem;
        position: relative;
        overflow: hidden;
        text-align: center;
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: -80px; right: -80px;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(37,99,235,0.35), transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero-banner::after {
        content: '';
        position: absolute;
        bottom: -60px; left: -60px;
        width: 250px; height: 250px;
        background: radial-gradient(circle, rgba(59,130,246,0.25), transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(37,99,235,0.2);
        color: #93c5fd;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 0.35rem 1rem;
        border-radius: 50px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 1rem;
        border: 1px solid rgba(37,99,235,0.3);
        position: relative;
        z-index: 1;
    }
    .hero-banner h1 {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #dbeafe 0%, #93c5fd 30%, #60a5fa 60%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 0.8rem;
        line-height: 1.15;
        position: relative;
        z-index: 1;
    }
    .hero-banner p {
        color: #7da3c9;
        font-size: 1.05rem;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.6;
        position: relative;
        z-index: 1;
    }

    /* ── Section headers ───────────────────────────────── */
    .section-header {
        text-align: center;
        margin: 1.5rem 0 1rem;
    }
    .section-header h2 {
        font-size: 1.5rem;
        font-weight: 800;
        color: #1e293b;
        margin: 0;
    }
    .section-header p {
        color: #64748b;
        font-size: 0.9rem;
        margin: 0.3rem 0 0;
    }

    /* ── Feature cards ────────────────────────────────── */
    .card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1.2rem;
        padding: 0.5rem 0 1.5rem;
    }
    @media (max-width: 600px) {
        .card-grid { grid-template-columns: 1fr; }
    }
    .feature-card {
        border-radius: 18px;
        padding: 1.6rem;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        border: 1px solid transparent;
        min-width: 0;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .feature-card:nth-child(1) {
        background: linear-gradient(145deg, #dbeafe, #bfdbfe);
        border-color: #93c5fd;
    }
    .feature-card:nth-child(2) {
        background: linear-gradient(145deg, #e0f2fe, #bae6fd);
        border-color: #7dd3fc;
    }
    .feature-card:nth-child(3) {
        background: linear-gradient(145deg, #eff6ff, #dbeafe);
        border-color: #93c5fd;
    }
    .feature-card:nth-child(4) {
        background: linear-gradient(145deg, #e0e7ff, #c7d2fe);
        border-color: #a5b4fc;
    }
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 4px;
        border-radius: 18px 18px 0 0;
    }
    .feature-card:nth-child(1)::before {
        background: linear-gradient(90deg, #1d4ed8, #3b82f6);
    }
    .feature-card:nth-child(2)::before {
        background: linear-gradient(90deg, #0369a1, #0ea5e9);
    }
    .feature-card:nth-child(3)::before {
        background: linear-gradient(90deg, #1e40af, #60a5fa);
    }
    .feature-card:nth-child(4)::before {
        background: linear-gradient(90deg, #3730a3, #6366f1);
    }
    .feature-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 20px 40px rgba(29,78,216,0.15);
    }
    .feature-card .icon {
        font-size: 2.2rem;
        margin-bottom: 0.6rem;
        display: inline-block;
    }
    .feature-card h3 {
        margin: 0 0 0.4rem;
        font-size: 1.1rem;
        font-weight: 700;
        color: #1e293b;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .feature-card p {
        margin: 0;
        font-size: 0.85rem;
        color: #475569;
        line-height: 1.55;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .feature-card .tag {
        display: inline-block;
        margin-top: 0.7rem;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 0.25rem 0.7rem;
        border-radius: 50px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .feature-card:nth-child(1) .tag {
        background: rgba(29,78,216,0.15);
        color: #1e40af;
    }
    .feature-card:nth-child(2) .tag {
        background: rgba(3,105,161,0.15);
        color: #075985;
    }
    .feature-card:nth-child(3) .tag {
        background: rgba(30,64,175,0.15);
        color: #1e3a8a;
    }
    .feature-card:nth-child(4) .tag {
        background: rgba(55,48,163,0.15);
        color: #312e81;
    }

    /* ── Steps section ─────────────────────────────────── */
    .steps-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1rem;
        padding: 0.5rem 0 1rem;
    }
    @media (max-width: 500px) {
        .steps-grid { grid-template-columns: 1fr 1fr; }
    }
    .step-card {
        text-align: center;
        padding: 1.5rem 1rem;
        border-radius: 16px;
        background: #ffffff;
        border: 1px solid #dbeafe;
        position: relative;
        transition: all 0.2s ease;
        min-width: 0;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .step-card:hover {
        border-color: #93c5fd;
        box-shadow: 0 8px 24px rgba(29,78,216,0.1);
    }
    .step-num {
        width: 36px; height: 36px;
        background: linear-gradient(135deg, #1d4ed8, #2563eb);
        color: white;
        font-weight: 700;
        font-size: 0.9rem;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 0.7rem;
        box-shadow: 0 4px 12px rgba(29,78,216,0.35);
    }
    .step-card h4 {
        margin: 0 0 0.3rem;
        font-size: 0.95rem;
        font-weight: 700;
        color: #1e293b;
        white-space: normal;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .step-card p {
        margin: 0;
        font-size: 0.8rem;
        color: #64748b;
        line-height: 1.45;
        white-space: normal;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }

    /* ── Divider ───────────────────────────────────────── */
    .section-divider {
        border: none;
        border-top: 1px solid #dbeafe;
        margin: 1.5rem 0;
    }

    /* ── Tech stack badges ─────────────────────────────── */
    .tech-stack {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        justify-content: center;
        align-items: center;
        padding: 0.5rem 0 1rem;
    }
    .tech-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background: #ffffff;
        border: 1px solid #dbeafe;
        border-radius: 50px;
        padding: 0.45rem 1rem;
        font-size: 0.8rem;
        font-weight: 600;
        color: #475569;
        transition: all 0.25s ease;
        white-space: nowrap;
    }
    .tech-badge:hover {
        border-color: #60a5fa;
        background: linear-gradient(135deg, #eff6ff, #dbeafe);
        color: #1e40af;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(29,78,216,0.12);
    }

    /* ── Footer ────────────────────────────────────────── */
    .footer {
        text-align: center;
        padding: 2rem 0 1rem;
        color: #94a3b8;
        font-size: 0.8rem;
        border-top: 1px solid #dbeafe;
        margin-top: 1.5rem;
    }
    .footer a {
        color: #2563eb;
        text-decoration: none;
        font-weight: 600;
    }
    .footer a:hover {
        color: #1d4ed8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Hero Banner ─────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero-banner">
        <div class="hero-badge">✨ Powered by Google Gemini AI</div>
        <h1>Document Chat Hub</h1>
        <p>Upload PDFs, CSVs, Excel, or ODF files and have intelligent conversations
        with your documents — powered by RAG, OCR, and vector search.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Feature cards ───────────────────────────────────────────────
st.markdown(
    """
    <div class="section-header">
        <h2>📂 Choose Your Document Type</h2>
        <p>Select a format from the sidebar to start chatting</p>
    </div>
    <div class="card-grid">
        <div class="feature-card">
            <div class="icon">📄</div>
            <h3>PDF Chat</h3>
            <p>Upload multiple PDFs, extract text with OCR fallback,
            build a vector index, and ask questions with full
            conversation history.</p>
            <span class="tag">RAG · FAISS · OCR</span>
        </div>
        <div class="feature-card">
            <div class="icon">📊</div>
            <h3>CSV Chat</h3>
            <p>Upload a CSV file and query its contents in plain
            English. Gemini analyses schema &amp; data to return
            structured answers.</p>
            <span class="tag">Data Analysis</span>
        </div>
        <div class="feature-card">
            <div class="icon">📝</div>
            <h3>ODF Chat</h3>
            <p>Open and chat with LibreOffice / OpenDocument (.odt)
            files. Text is extracted automatically so you can
            focus on asking questions.</p>
            <span class="tag">Document Q&amp;A</span>
        </div>
        <div class="feature-card">
            <div class="icon">📈</div>
            <h3>Excel Chat</h3>
            <p>Upload Excel workbooks (.xlsx) with multiple sheets
            and query your data in plain English. Gemini analyses
            all sheets to give you precise answers.</p>
            <span class="tag">Multi-Sheet Analysis</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── How it works ────────────────────────────────────────────────
st.markdown(
    """
    <hr class="section-divider">
    <div class="section-header">
        <h2>🚀 How It Works</h2>
        <p>Get started in four simple steps</p>
    </div>
    <div class="steps-grid">
        <div class="step-card">
            <div class="step-num">1</div>
            <h4>Set Up .env</h4>
            <p>Add your Google Gemini API key to the .env file</p>
        </div>
        <div class="step-card">
            <div class="step-num">2</div>
            <h4>Choose Page</h4>
            <p>Pick PDF, CSV, ODF, or Excel from the sidebar</p>
        </div>
        <div class="step-card">
            <div class="step-num">3</div>
            <h4>Upload File</h4>
            <p>Drag &amp; drop your document</p>
        </div>
        <div class="step-card">
            <div class="step-num">4</div>
            <h4>Ask Questions</h4>
            <p>Chat with your document using AI</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Tech stack ──────────────────────────────────────────────────
st.markdown(
    """
    <hr class="section-divider">
    <div class="section-header">
        <h2>🛠️ Built With</h2>
    </div>
    <div class="tech-stack">
        <span class="tech-badge">🤖 Google Gemini</span>
        <span class="tech-badge">🦜 LangChain</span>
        <span class="tech-badge">🔍 FAISS</span>
        <span class="tech-badge">🎈 Streamlit</span>
        <span class="tech-badge">⚡ FastAPI</span>
        <span class="tech-badge">📑 PyPDF2</span>
        <span class="tech-badge">👁️ Tesseract OCR</span>
        <span class="tech-badge">📊 OpenPyXL</span>
        <span class="tech-badge">🐼 Pandas</span>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("---")
    st.markdown(
        """
        **Select a page** from the navigation above to start chatting
        with your documents.

        🔗 [API Docs (Swagger)](http://localhost:8000/docs)
        """
    )

# ── Footer ──────────────────────────────────────────────────────
st.markdown(
    """
    <div class="footer">
        Built with 💙 using Streamlit · Google Gemini · LangChain ·
        <a href="http://localhost:8000/docs" target="_blank">API Docs</a>
    </div>
    """,
    unsafe_allow_html=True,
)
