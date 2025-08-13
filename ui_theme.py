import streamlit as st


def apply_global_theme():
    """
    Inject a modern dark theme with deep coloring and refined UI styles.
    This function is idempotent and safe to call multiple times.
    """
    custom_css = """
    <style>
      /* Base */
      html, body, [data-testid="stAppViewContainer"] {
        background: #0B1020 !important;
        color: #E6E6F0 !important;
      }

      /* Typography */
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
      :root {
        --brand: #7C4DFF;
        --brand-600: #6A3BFF;
        --surface: #121A2B;
        --surface-2: #151F34;
        --muted: #9AA4B2;
        --ok: #22C55E;
        --warn: #F59E0B;
        --err: #EF4444;
        --ring: rgba(124, 77, 255, 0.45);
        --shadow: 0 10px 30px rgba(0,0,0,0.35);
      }

      * { font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Apple Color Emoji', 'Segoe UI Emoji', sans-serif; }

      /* Headers */
      h1, h2, h3, h4, h5, h6 { color: #F1F5FF; letter-spacing: 0.2px; }
      h1 { font-weight: 700; }
      h2, h3 { font-weight: 600; }

      /* Sidebar */
      [data-testid="stSidebar"] {
        background: var(--surface) !important;
        border-right: 1px solid rgba(255,255,255,0.06);
      }
      [data-testid="stSidebar"] .stButton>button,
      [data-testid="stSidebar"] .stDownloadButton>button,
      [data-testid="stSidebar"] [data-baseweb="select"] div,
      [data-testid="stSidebar"] .stTextInput>div>div>input,
      [data-testid="stSidebar"] .stTextArea textarea {
        background: var(--surface-2) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        color: #E6E6F0 !important;
      }

      /* Cards / containers */
      .block-container { padding-top: 2rem; }
      .stApp header { background: transparent; }
      .stAlert { background: var(--surface-2) !important; border: 1px solid rgba(255,255,255,0.06) !important; }
      .stMetric { background: var(--surface) !important; border-radius: 12px; padding: 16px; box-shadow: var(--shadow); }

      /* Inputs */
      .stTextInput>div>div>input,
      .stTextArea textarea,
      [data-baseweb="select"] div,
      .stNumberInput input,
      .stDateInput input {
        background: var(--surface) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        color: #E6E6F0 !important;
        box-shadow: 0 0 0 0 transparent;
      }
      .stTextInput>div>div>input:focus,
      .stTextArea textarea:focus,
      [data-baseweb="select"]:focus-within div {
        border-color: var(--brand) !important;
        box-shadow: 0 0 0 3px var(--ring) !important;
      }

      /* Buttons */
      .stButton>button, .stDownloadButton>button {
        background: linear-gradient(180deg, var(--brand), var(--brand-600));
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1rem !important;
        font-weight: 600;
        box-shadow: var(--shadow);
        transition: transform .06s ease, filter .2s ease;
      }
      .stButton>button:hover, .stDownloadButton>button:hover { filter: brightness(1.05); transform: translateY(-1px); }
      .stButton>button:active, .stDownloadButton>button:active { transform: translateY(0); filter: brightness(0.98); }

      /* Chat */
      [data-testid="stChatInput"]>div>div {
        background: var(--surface) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
      }
      [data-testid="stChatMessage"] {
        background: var(--surface) !important;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 12px 14px;
        box-shadow: var(--shadow);
      }

      /* Tables */
      .stDataFrame [data-testid="stTable"] {
        background: var(--surface) !important;
        color: #E6E6F0 !important;
      }
      .stDataFrame thead tr th { background: #0F1527 !important; }

      /* Plotly */
      .js-plotly-plot .plotly .modebar { background: rgba(12, 18, 36, 0.85) !important; border-radius: 8px; }

      /* Dividers */
      hr { border-top: 1px solid rgba(255,255,255,0.08) !important; }
    </style>
    """

    st.markdown(custom_css, unsafe_allow_html=True)


