import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
import base64
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ============================================================
# PATHS (unchanged)
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH  = os.path.join(SCRIPT_DIR, "agribotailogo.png")
BG_PATH    = os.path.join(SCRIPT_DIR, "background.jpg")
PI_LOGO    = os.path.expanduser("~/env/Thesis code/backend/agribotailogo.png")
PI_BG      = os.path.expanduser("~/env/Thesis code/backend/background.jpg")
WIN_LOGO   = r"C:\Users\admin\Downloads\AgribotPrototype\backend\agribotailogo.png"
WIN_BG     = r"C:\Users\admin\Downloads\AgribotPrototype\backend\background.jpg"

LANDING_BG_PATH = os.path.join(SCRIPT_DIR, "landpage.png")
PI_LANDING_BG   = os.path.expanduser("~/env/Thesis code/backend/landpage.png")
WIN_LANDING_BG  = r"C:\Users\admin\Downloads\AgribotPrototype\backend\landpage.png"

ACTUAL_LOGO       = next((p for p in [LOGO_PATH, PI_LOGO, WIN_LOGO]                   if os.path.exists(p)), "")
ACTUAL_BG         = next((p for p in [BG_PATH,   PI_BG,   WIN_BG]                    if os.path.exists(p)), "")
ACTUAL_LANDING_BG = next((p for p in [LANDING_BG_PATH, PI_LANDING_BG, WIN_LANDING_BG] if os.path.exists(p)), "")

CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "..", "credentials.json")
if not os.path.exists(CREDENTIALS_FILE):
    CREDENTIALS_FILE = os.path.expanduser("~/env/Thesis code/credentials.json")

SPREADSHEET_ID = "1mYScsUkoZn84FIoO_QMaku3gZT3Z9df72kPE3ray9-A"

# ── Tab favicon ───────────────────────────────────────────────
_page_icon = "🌱"
if ACTUAL_LOGO:
    try:
        from PIL import Image as _PILImage
        _page_icon = _PILImage.open(ACTUAL_LOGO)
    except Exception:
        pass

st.set_page_config(
    page_title="AgriBot-AI | Dashboard",
    page_icon=_page_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# OPTIMIZED CSS FOR 7-INCH DISPLAY
# Includes adjustable margin variables at the top
# ============================================================
OPTIMIZED_CSS = """
<style>
/* ── GLOBAL MARGIN VARIABLES ────────────────────────────── */
:root {
    --page-margin-top: 0px;      /* Adjust top spacing for all pages */
    --page-margin-bottom: 0px;   /* Adjust bottom spacing */
    --page-margin-left: 0px;     /* Adjust left spacing */
    --page-margin-right: 0px;    /* Adjust right spacing */

    /* Login page fine‑tuning (on top of global margins) */
    --login-margin-top: -20px;   /* negative moves up, positive down */
}

/* ── 1. BASE ───────────────────────────────────────────────── */
html, body {
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    height: 100% !important;
    width: 100% !important;
    font-size: 14px !important;
}

/* ── 2. ROOT APP ──────────────────────────────────────────── */
.stApp {
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    height: 100vh !important;
    width: 100vw !important;
    max-height: 100vh !important;
}

/* ── 3. REMOVE ALL STREAMLIT OFFSETS ──────────────────────── */
[data-testid="stAppViewContainer"] {
    overflow: hidden !important;
    padding: 0 !important;
    margin: 0 !important;
    height: 100vh !important;
}

[data-testid="stAppViewBlockContainer"] {
    overflow: hidden !important;
    padding: 0 !important;
    margin: 0 !important;
    padding-top: 0 !important;
    height: 100vh !important;
    max-height: 100vh !important;
}

.main {
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    height: 100vh !important;
}

section.main > div {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    margin-top: 0 !important;
}

/* ── MAIN CONTAINER WITH ADJUSTABLE MARGINS ───────────────── */
.main .block-container {
    padding: var(--page-margin-top) var(--page-margin-right) var(--page-margin-bottom) var(--page-margin-left) !important;
    margin: 0 !important;
    max-width: 100% !important;
    width: 100% !important;
    overflow: hidden !important;
    height: 100vh !important;
    max-height: 100vh !important;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;  /* ensures padding does not increase height */
}

.main .block-container > div:first-child {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

[data-testid="stVerticalBlock"] {
    gap: 0px !important;
}

/* ── 4. HIDE STREAMLIT CHROME ─────────────────────────────── */
#MainMenu,
footer,
header,
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="collapsedControl"],
.stDeployButton,
button[title="View App"],
button[title="Manage app"],
button[kind="headerNoSpacing"],
a[href*="streamlit.io"],
.viewerBadge_container__1QSob,
.styles_viewerBadge__CvC9N,
#GithubIcon,
.css-1dp5vir {
    display: none !important;
    visibility: hidden !important;
}

/* ── 5. SIDEBAR ────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    width: 230px !important;
    min-width: 230px !important;
    background: #023f23 !important;
    border-right: 1px solid rgba(46,125,50,0.5) !important;
    overflow: remove !important;
    height: 100vh !important;
    padding-top: 0 !important;
}

[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    padding: 0 4px 4px !important;
}

[data-testid="stSidebar"] [data-testid="stElementToolbar"] {
    display: none !important;
}

/* ── 6. SIDEBAR NAVIGATION RADIO ───────────────────────────── */
.stRadio > div {
    gap: 2px !important;
    width: 100% !important;
    flex-direction: column !important;
}
./* More specific selector to override any default */
section[data-testid="stSidebar"] .stRadio label {
    font-size: 13px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    background: transparent !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 6px 8px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    min-height: 44px !important;
    display: flex !important;
    align-items: center !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(76,175,80,0.12) !important;
    color: #ffffff !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {
    background: rgba(46,125,50,0.22) !important;
    border-left: 3px solid #4CAF50 !important;
    color: #ffffff !important;
    padding-left: 9px !important;
}
section[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:first-child {
    display: none !important;
}
section[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
}
/* If the text inside the label is wrapped in a <p>, force its color too */
section[data-testid="stSidebar"] .stRadio label p {
    color: #ffffff !important;
}

/* ── 7. LOGOUT BUTTON ──────────────────────────────────────── */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(46,125,50,0.12) !important;
    border: 1px solid rgba(76,175,80,0.3) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    width: 100% !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    padding: 10px !important;
    min-height: 48px !important;
    transition: all 0.2s !important;
    margin-top: 20px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(198,40,40,0.15) !important;
    border-color: rgba(198,40,40,0.5) !important;
    color: #ffffff !important;
}

/* ── 8. METRIC CARDS ───────────────────────────────────────── */
div[data-testid="stMetric"] {
    background: #023f23 !important;
    border: 1px solid rgba(76,175,80,0.3) !important;
    border-radius: 10px !important;
    padding: 8px 6px !important;
    text-align: center !important;
}
div[data-testid="stMetricLabel"] {
    font-weight: 700 !important;
    font-size: 11px !important;
    color: #66bb6a !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    justify-content: center !important;
}
div[data-testid="stMetricValue"] {
    font-size: 24px !important;
    font-weight: 900 !important;
    color: #fff !important;
    margin-top: 1px !important;
}

/* ── 9. DASHBOARD CUSTOM CARDS ─────────────────────────────── */
.cam-card {
    background: rgba(13,17,23,0.9);
    border: 1px solid rgba(46,125,50,0.4);
    border-radius: 12px;
    padding: 10px;
    height: 100%;
}
.section-title {
    font-size: 12px !important;
    font-weight: 700 !important;
    color: #66bb6a !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    margin-bottom: 15px !important;
    margin-top: 0 !important;
    border-left: 3px solid #4CAF50;
    padding-left: 7px;
}
.alert-item {
    padding: 6px 10px;
    background: rgba(183,28,28,0.12);
    border: 1px solid rgba(183,28,28,0.3);
    color: #ef9a9a;
    border-radius: 8px;
    margin: 10px 0;
    font-size: 13px !important;
}
.sched-badge {
    display: inline-block;
    background: rgba(21,101,192,0.2);
    border: 1px solid rgba(21,101,192,0.5);
    border-radius: 5px;
    padding: 2px 6px;
    font-size: 10px !important;
    color: #90CAF9;
    font-weight: 700;
    margin: 0 2px;
}
.cam-meta {
    font-size: 10px !important;
    color: #66bb6a;
    margin-top: 15px;
    line-height: 1.5;
}
.drive-link {
    display: inline-block;
    margin-top: 5px;
    background: rgba(46,125,50,0.15);
    border: 1px solid rgba(76,175,80,0.3);
    border-radius: 7px;
    padding: 4px 10px;
    color: #81c784;
    font-size: 11px !important;
    text-decoration: none;
}
.cam-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 200px;
    background: rgba(46,125,50,0.04);
    border: 2px dashed rgba(46,125,50,0.3);
    border-radius: 10px;
    text-align: center;
    padding: 20px;
}

/* ── 10. PLOTLY CHART HEIGHT ───────────────────────────────── */
.js-plotly-plot, .plotly, .plot-container {
    max-height: 210px !important;
}
[data-testid="stPlotlyChart"] {
    height: 210px !important;
    overflow: hidden !important;
}

/* ── 11. DATAFRAME ─────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    max-height: 300px !important;
    overflow-y: auto !important;
    font-size: 13px !important;
}

/* ── 12. STREAMLIT ALERTS ──────────────────────────────────── */
[data-testid="stAlert"] {
    padding: 8px 12px !important;
    font-size: 13px !important;
    border-radius: 8px !important;
    margin: 4px 0 !important;
}

/* ── 13. SELECTBOX & INPUTS ────────────────────────────────── */
[data-testid="stSelectbox"] {
    margin-bottom: 4px !important;
}
[data-baseweb="select"] {
    min-height: 42px !important;
}
.stSelectbox label {
    font-size: 12px !important;
    color: #66bb6a !important;
    margin-bottom: 2px !important;
}
.stTextInput label {
    color: #c8e6c9 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}

/* ── 14. LANDING PAGE BUTTON ───────────────────────────────── */
.landing-btn-wrapper button {
    background: linear-gradient(135deg, #2e7d32, #66bb6a) !important;
    border: 2px solid rgba(255,255,255,0.3) !important;
    border-radius: 50px !important;
    color: white !important;
    font-size: 24px !important;
    font-weight: 700 !important;
    padding: 14px 48px !important;
    cursor: pointer !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    min-height: 64px !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.5) !important;
    width: auto !important;
}
.landing-btn-wrapper button:hover {
    transform: scale(1.05) !important;
    box-shadow: 0 12px 32px rgba(76,175,80,0.7) !important;
}
/* Hide sidebar on landing page */
.landing-page section[data-testid="stSidebar"] {
    display: none !important;
}

/* ── 15. LOGIN FORM ────────────────────────────────────────── */
[data-testid="stForm"] {
    background: linear-gradient(160deg,
        rgba(27,94,32,0.65) 0%, rgba(46,125,50,0.55) 100%) !important;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 18px;
    border: 1px solid rgba(165,214,167,0.35);
    box-shadow: 0 12px 40px rgba(0,0,0,0.35);
    padding: 26px 36px 34px !important;
}
[data-testid="stForm"] input {
    background: rgba(255,255,255,0.1) !important;
    color: #fff !important;
    border: 1px solid rgba(165,214,167,0.45) !important;
    border-radius: 10px !important;
    font-size: 16px !important;
    min-height: 48px !important;
}
[data-testid="stForm"] input::placeholder {
    color: rgba(200,230,200,0.6) !important;
}
[data-testid="stForm"] button[kind="primaryFormSubmit"] {
    background: linear-gradient(90deg, #2e7d32, #66bb6a) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    letter-spacing: 1.5px;
    font-size: 16px !important;
    padding: 12px !important;
    min-height: 52px !important;
    margin-top: 4px !important;
}

/* ── 16. PULSE ANIMATION ───────────────────────────────────── */
@keyframes pulse {
    0%,100% { box-shadow: 0 0 5px #4CAF50; }
    50%      { box-shadow: 0 0 14px #4CAF50; opacity: 0.7; }
}

/* ── 17. COLUMNS FILL HEIGHT ───────────────────────────────── */
[data-testid="column"] {
    height: 100%;
    padding: 0 4px !important;
}

/* ── 18. MAIN DASHBOARD FLEX LAYOUT ────────────────────────── */
.main .block-container {
    display: flex;
    flex-direction: column;
    overflow: hidden;
}
.main .block-container > [data-testid="stVerticalBlock"] {
    flex: 1;
    overflow: hidden;
}
</style>
"""
st.markdown(OPTIMIZED_CSS, unsafe_allow_html=True)

# ============================================================
# HELPERS (unchanged)
# ============================================================
def file_to_b64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

def gdrive_thumbnail(url: str, size: str = "w1200") -> str:
    if not url:
        return ""
    try:
        if "id=" in url:
            fid = url.split("id=")[1].split("&")[0]
            return f"https://drive.google.com/thumbnail?id={fid}&sz={size}"
    except Exception:
        pass
    return url

def set_background(path: str):
    b64 = file_to_b64(path)
    if not b64:
        return
    mime = "image/png" if path.endswith(".png") else "image/jpeg"
    st.markdown(f"""<style>
    .stApp {{
        background-image: url("data:{mime};base64,{b64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    .stApp::before {{
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.52);
        z-index: 0;
        pointer-events: none;
    }}
    </style>""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE — always start at landing page after reboot
# No persistent file – session survives browser refresh only.
# ============================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if "page" not in st.session_state:
    st.session_state.page = "landing"   # always start at landing

USERS = {
    "admin@agribot.ai": {"password": "admin123", "role": "admin"},
    "user@agribot.ai":  {"password": "user123",  "role": "user"},
}

st_autorefresh(interval=30_000, limit=None, key="dashboard_autorefresh")

# ============================================================
# PAGE: LANDING (clean left-aligned button, no negative margins)
# ============================================================
def show_landing():
    if ACTUAL_LANDING_BG:
        set_background(ACTUAL_LANDING_BG)
    else:
        st.markdown("""<style>.stApp { background: #0a0d12 !important; }</style>""",
                    unsafe_allow_html=True)

    # Remove the dark overlay for the landing page
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] { display: none !important; }
    /* Disable the semi-transparent overlay added by set_background */
    .stApp::before {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Center the button with a top margin to appear below the existing text on the background
    col1, col2, col3 = st.columns([3, 2, 9])
    with col2:
        # Adjust margin-top if needed (try 55vh–65vh)
        st.markdown("<div style='margin-top: 30vh;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-left: -45vh;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="landing-btn-wrapper">', unsafe_allow_html=True)
        if st.button("Let's Start", use_container_width=True, key="landing_btn"):
            st.session_state.page = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

# ============================================================
# PAGE: LOGIN
# ============================================================
def show_login():
    set_background(ACTUAL_BG)

     # --- LOCK SCROLLING CSS ---
    st.markdown("""
        <style>
        /* Force the app container to never exceed screen height */
        html, body, [data-testid="stAppViewContainer"] {
            overflow: hidden !important;
            height: 100vh !important;
            position: fixed;
            width: 100vw;
        }
        /* Hide the Streamlit header and padding */
        header {visibility: hidden;}
        .main .block-container {
            padding-top: 2rem !important;
            padding-bottom: 0rem !important;
        }
        /* Completely hide scrollbars */
        ::-webkit-scrollbar {display: none;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""<style>
    section[data-testid="stSidebar"] { display: none !important; }
    </style>""", unsafe_allow_html=True)

    logo_b64  = file_to_b64(ACTUAL_LOGO)
    logo_html = (
        f'<div style="display:flex;justify-content:center;margin-bottom:16px;">'
        f'<img src="data:image/png;base64,{logo_b64}" '
        f'style="width:100px;height:100px;border-radius:50%;'
        f'border:3px solid #4CAF50;object-fit:cover;'
        f'box-shadow:0 0 28px rgba(76,175,80,0.5);"/></div>'
    ) if logo_b64 else ""

    st.markdown(
        f'<div style="display:flex;flex-direction:column;align-items:center;margin-top:-90px;">'
        f'{logo_html}'
        f'<div style="text-align:center;font-size:34px;font-weight:900;color:#fff;'
        f'letter-spacing:1px;text-shadow:0 2px 12px rgba(0,0,0,0.6);margin-bottom:4px;">'
        f'AgriBot-AI</div>'
        f'<div style="text-align:center;color:#81c784;font-size:12px;'
        f'letter-spacing:3px;text-transform:uppercase;margin-bottom:20px;">'
        f'Smart Farming &middot; Intelligent Monitoring</div>'
        f'</div>',
        unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.6, 1])
    with mid:
        with st.form("login_form"):
            email    = st.text_input("Email",    placeholder="admin@agribot.ai")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            if st.form_submit_button("LOGIN", use_container_width=True):
                if email in USERS and USERS[email]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.role      = USERS[email]["role"]
                    st.session_state.page      = "dashboard"
                    session_save(USERS[email]["role"])
                    st.rerun()
                else:
                    st.error("Invalid email or password")

        st.markdown(
            '<div style="text-align:center;margin-top:10px;">'
            '<span style="font-size:11px;color:#388e3c;">← </span>'
            '</div>', unsafe_allow_html=True)
        if st.button("← Back to Landing", use_container_width=True, key="back_btn"):
            st.session_state.page = "landing"
            st.rerun()

    st.stop()

# ============================================================
# MAIN FLOW: route by st.session_state.page
# ============================================================
if st.session_state.page == "landing":
    show_landing()

if st.session_state.page == "login":
    show_login()

# If not logged in but somehow page is dashboard, redirect to login
if not st.session_state.logged_in and st.session_state.page == "dashboard":
    st.session_state.page = "login"
    st.rerun()

# ============================================================
# DATA FUNCTIONS (unchanged)
# ============================================================
@st.cache_resource
def load_assets():
    try:
        model  = joblib.load(os.path.join(SCRIPT_DIR, 'anomaly_model.pkl'))
        scaler = joblib.load(os.path.join(SCRIPT_DIR, 'anomaly_scaler.pkl'))
        return model, scaler
    except Exception:
        return None, None

@st.cache_resource
def get_sheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                dict(st.secrets["gcp_service_account"]), scope)
        elif os.path.exists(CREDENTIALS_FILE):
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                CREDENTIALS_FILE, scope)
        else:
            st.error("credentials.json not found.")
            return None
        return gspread.authorize(creds).open_by_key(SPREADSHEET_ID).sheet1
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

@st.cache_data(ttl=30)
def get_latest_readings():
    if sheet is None:
        return pd.DataFrame()
    try:
        df = pd.DataFrame(sheet.get_all_records())
        if df.empty:
            return df
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df.sort_values('timestamp').groupby('plant_id').last().reset_index()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_historical_data(plant_id=None, hours=24):
    if sheet is None:
        return pd.DataFrame()
    try:
        df = pd.DataFrame(sheet.get_all_records())
        if df.empty:
            return df
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df[df['timestamp'] >= datetime.now() - timedelta(hours=hours)]
        if plant_id is not None:
            df = df[df['plant_id'] == plant_id]
        return df.sort_values('timestamp')
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=30)
def get_latest_image() -> dict:
    if sheet is None:
        return {}
    try:
        df = pd.DataFrame(sheet.get_all_records())
        if df.empty or 'image_url' not in df.columns:
            return {}
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp', ascending=False)
        for _, row in df.iterrows():
            raw = str(row.get('image_url', '')).strip()
            if raw.startswith("http"):
                return {
                    "url":       gdrive_thumbnail(raw, "w1200"),
                    "plant_id":  int(row.get('plant_id', 0)),
                    "timestamp": pd.to_datetime(row['timestamp']).strftime("%b %d, %Y · %I:%M %p"),
                }
        return {}
    except Exception:
        return {}

# ============================================================
# SIDEBAR (dashboard only)
# ============================================================
sheet    = get_sheet()
logo_b64 = file_to_b64(ACTUAL_LOGO)

with st.sidebar:
    st.markdown(
        f'<div style="display:flex; flex-direction:column; align-items:center; '
        f'padding-top:5px; width:100%;">'  
        f'<div style="padding:2px; border-radius:50%; '
        f'background:linear-gradient(145deg,#388e3c,#1b5e20); '
        f'box-shadow:0 0 12px rgba(76,175,80,0.3); margin-bottom:2px;">'
        f'<img src="data:image/png;base64,{logo_b64}" '
        f'style="border-radius:50%; width:80px; height:80px; ' 
        f'display:block; object-fit:cover; background:#0a0d12;"/>'
        f'</div>'
        f'<div style="font-size:15px; font-weight:900; color:#ffffff; '
        f'letter-spacing:0.5px; margin-bottom:3px;">AgriBot-AI</div>'
        f'<div style="font-size:9px; font-weight:700; letter-spacing:1px; '
        f'text-transform:uppercase; padding:1px 8px; border-radius:20px; '
        f'background:rgba(46,125,50,0.15); border:1px solid rgba(76,175,80,0.25); '
        f'color:#ffffff; margin-bottom:7px;">' 
        f'{"👑 Admin" if st.session_state.role == "admin" else "🌿 Field User"}'
        f'</div>'
        f'<div style="font-size:9px; font-weight:700; color:#ffffff; '
        f'letter-spacing:2px; text-transform:uppercase; width:100%; '
        f'text-align:center; padding:0 2px; margin-bottom:4px;">Navigation</div>',
        unsafe_allow_html=True)

    nav_opts = (
        ["📡  Live Dashboard", "📈  Analysis",
         "📜  System Logs",    "👥  Users"]
        if st.session_state.role == "admin"
        else ["📡  Live Dashboard", "📈  Analysis"]
    )
    raw_page = st.radio("", nav_opts, label_visibility="collapsed")
    page_map = {
        "📡  Live Dashboard": "DASHBOARD",
        "📈  Analysis":       "ANALYSIS",
        "📜  System Logs":    "LOGS",
        "👥  Users":          "USERS",
    }
    page = page_map.get(raw_page, "DASHBOARD")

    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;
                background:rgba(46,125,50,0.1);border:1px solid rgba(46,125,50,0.3);
                border-radius:8px;padding:4px 8px;width:100%;
                margin:4px 0 2px;box-sizing:border-box;">
        <div style="width:7px;height:7px;background:#4CAF50;border-radius:50%;
                    animation:pulse 2s infinite;flex-shrink:0;"></div>
        <span style="font-size:10px;font-weight:700;color:#ffffff;
                     letter-spacing:1.5px;text-transform:uppercase;">System Online</span>
    </div>""", unsafe_allow_html=True)

    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.role      = None
        st.session_state.page      = "landing"
        st.rerun()

# ============================================================
# SHARED DATA + THRESHOLDS
# ============================================================
model,  scaler = load_assets()
latest         = get_latest_readings()

PH_LOW,   PH_HIGH   = 5.5, 6.5
SOIL_DRY, SOIL_WET  = 30,  80
TEMP_LOW, TEMP_HIGH = 15,  30
HUM_LOW,  HUM_HIGH  = 50,  85

# ============================================================
# PAGE: LIVE DASHBOARD (unchanged)
# ============================================================
if page == "DASHBOARD":
    st.markdown(
        '<div style="padding:6px 12px 2px;">'
        '<div style="font-size:20px;font-weight:900;color:#fff;line-height:1.2;">'
        'Real-Time Monitoring</div>'
        '<div style="font-size:20px;color:#66bb6a;letter-spacing:1px;margin-top:-75px;">'
        'Greenhouse Overview — AgriBot-AI</div>'
        '</div>',
        unsafe_allow_html=True)

    if latest.empty:
        st.warning("No sensor data yet — waiting for the Pi...")
        st.stop()

    avg_temp = float(latest['temp_c'].mean())
    avg_hum  = float(latest['humidity'].mean())
    avg_ph   = float(latest['ph'].mean())
    avg_soil = float(latest['soil_moisture'].mean())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TEMP",     f"{avg_temp:.1f} °C")
    m2.metric("HUMIDITY", f"{avg_hum:.0f} %")
    m3.metric("PH",       f"{avg_ph:.2f}")
    m4.metric("SOIL",     f"{avg_soil:.0f} %")

    img_data = get_latest_image()

    cam_col, right_col = st.columns([3, 2], gap="small")

    with cam_col:
        st.markdown('<div style="margin-top: 10px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📷 Plant Health Feed</div>',
                    unsafe_allow_html=True)
        if img_data.get("url"):
            st.markdown(
                f'<img src="{img_data["url"]}" '
                f'style="width:100%;max-height:230px;object-fit:cover;'
                f'border-radius:8px;"/>',
                unsafe_allow_html=True)
            pid_txt = f"🥬 Plant {img_data['plant_id']}" if img_data.get("plant_id") else ""
            ts_txt  = f"🕒 {img_data['timestamp']}"       if img_data.get("timestamp") else ""
            st.markdown(
                f'<div class="cam-meta">{pid_txt}&nbsp;&nbsp;{ts_txt}<br>'
                f'Captured at '
                f'<span class="sched-badge">7:00 AM</span>'
                f'<span class="sched-badge">12:00 NN</span>'
                f'<span class="sched-badge">12:30 PM</span></div>'
                f'<a href="{img_data["url"]}" target="_blank" class="drive-link">'
                f'☁️ View in Drive ↗</a>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="cam-placeholder">'
                '<div style="font-size:36px;margin-bottom:8px;">📷</div>'
                '<div style="font-size:12px;font-weight:700;color:#4CAF50;">No image yet</div>'
                '<div style="font-size:10px;color:#2e7d32;margin-top:100px;">'
                'Captures at '
                '<span class="sched-badge">7:00 AM</span>'
                '<span class="sched-badge">12:00 NN</span>'
                '<span class="sched-badge">12:30 PM</span></div>'
                '</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        if not latest.empty:
            last_ts = pd.to_datetime(latest['timestamp']).max()
            st.markdown(
                f'<div style="text-align:right;font-size:9px;color:#388e3c;'
                f'margin-bottom:6px;">🔄 {last_ts.strftime("%H:%M:%S")}</div>',
                unsafe_allow_html=True)

        st.markdown('<div class="section-title">🤖 AI Health Status</div>',
                    unsafe_allow_html=True)
        p1 = latest[latest['plant_id'] == 1]
        if not p1.empty and model and scaler:
            try:
                feat = np.array([[float(p1.iloc[0]['temp_c']),
                                  float(p1.iloc[0]['humidity']),
                                  float(p1.iloc[0]['ph'])]])
                pred = model.predict(scaler.transform(feat))[0]
                if pred == -1:
                    st.error("🚨 **ALERT** — Anomaly detected.")
                else:
                    st.success("✅ **HEALTHY** — Optimal conditions.")
            except Exception as e:
                st.info(f"Processing... ({e})")
        else:
            st.warning("Awaiting data / AI model...")

        st.markdown("<div style='margin:6px 0 2px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">🔔 Alerts</div>',
                    unsafe_allow_html=True)
        alerts = []
        for _, plant in latest.iterrows():
            pid  = int(plant['plant_id'])
            soil = float(plant['soil_moisture'])
            ph   = float(plant['ph'])
            if soil < SOIL_DRY:
                alerts.append(f"🌱 P{pid}: soil dry ({soil:.0f}%)")
            elif soil > SOIL_WET:
                alerts.append(f"🌱 P{pid}: soil wet ({soil:.0f}%)")
            if ph < PH_LOW or ph > PH_HIGH:
                alerts.append(f"🧪 P{pid}: pH {ph:.2f}")
        if avg_temp < TEMP_LOW or avg_temp > TEMP_HIGH:
            alerts.append(f"🌡️ Temp: {avg_temp:.1f}°C")
        if avg_hum < HUM_LOW or avg_hum > HUM_HIGH:
            alerts.append(f"💧 Hum: {avg_hum:.0f}%")
        if alerts:
            for a in alerts[:5]:
                st.markdown(f'<div class="alert-item">{a}</div>', unsafe_allow_html=True)
        else:
            st.success("✅ All parameters in range.")

# ============================================================
# PAGE: ANALYSIS (unchanged)
# ============================================================
elif page == "ANALYSIS":
    st.markdown(
        '<div style="padding:6px 12px 4px;">'
        '<div style="font-size:18px;font-weight:900;color:#fff;">Historical Trends</div>'
        '<div style="font-size:10px;color:#66bb6a;letter-spacing:1px;margin-top:1px;">'
        'Sensor data over time</div></div>',
        unsafe_allow_html=True)

    if not latest.empty:
        sc1, sc2, sc3 = st.columns([1, 1, 1])
        with sc1:
            sensor_choice = st.selectbox("Sensor", [
                "Temperature (°C)", "Humidity (%)", "pH", "Soil Moisture (%)"])
        with sc2:
            plant_sel = st.selectbox("Plant", list(range(1, 11)))
        with sc3:
            time_range = st.selectbox("Range", ["24 hours", "7 days", "30 days"])
            hours = {"24 hours": 24, "7 days": 168, "30 days": 720}[time_range]

        hist_df = get_historical_data(plant_id=plant_sel, hours=hours)
        if not hist_df.empty:
            col_map = {
                "Temperature (°C)": ("temp_c",        "°C"),
                "Humidity (%)":     ("humidity",       "%"),
                "pH":               ("ph",             "pH"),
                "Soil Moisture (%)":("soil_moisture",  "%"),
            }
            y_col, y_label = col_map[sensor_choice]
            fig = px.line(hist_df, x='timestamp', y=y_col,
                          title=f"{sensor_choice} — Plant {plant_sel}")
            fig.update_layout(
                height=210,
                margin=dict(t=32, b=20, l=30, r=10),
                yaxis_title=y_label,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(13,17,23,0.85)',
                font_color='#a5d6a7',
                title_font_color='#fff',
                title_font_size=12,
            )
            st.plotly_chart(fig, use_container_width=True)

            if sensor_choice == "Soil Moisture (%)":
                st.markdown('<div class="section-title">🌱 All Plants — Current Soil</div>',
                            unsafe_allow_html=True)
                bar = px.bar(latest.sort_values('plant_id'),
                             x='plant_id', y='soil_moisture',
                             color='soil_moisture', color_continuous_scale='Greens',
                             labels={'plant_id': 'Plant', 'soil_moisture': 'Soil %'})
                bar.update_layout(
                    height=180,
                    margin=dict(t=10, b=20, l=30, r=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(13,17,23,0.85)',
                    font_color='#a5d6a7',
                )
                st.plotly_chart(bar, use_container_width=True)
        else:
            st.warning("No data for this plant in the selected time range.")
    else:
        st.warning("No data available yet.")

# ============================================================
# PAGE: SYSTEM LOGS (unchanged)
# ============================================================
elif page == "LOGS":
    st.markdown(
        '<div style="padding:6px 12px 4px;">'
        '<div style="font-size:18px;font-weight:900;color:#fff;">System Logs</div>'
        '<div style="font-size:10px;color:#66bb6a;letter-spacing:1px;margin-top:1px;">'
        'Last 24 hours</div></div>',
        unsafe_allow_html=True)

    logs = get_historical_data(plant_id=None, hours=24)
    if not logs.empty:
        def classify(r):
            if r['temp_c'] < TEMP_LOW or r['temp_c'] > TEMP_HIGH:
                return "🌡️ Temp"
            if r['humidity'] < HUM_LOW or r['humidity'] > HUM_HIGH:
                return "💧 Humidity"
            if r['ph'] < PH_LOW or r['ph'] > PH_HIGH:
                return "🧪 pH"
            if r['soil_moisture'] < SOIL_DRY or r['soil_moisture'] > SOIL_WET:
                return "🌱 Soil"
            return "Normal"

        logs['event'] = logs.apply(classify, axis=1)
        cols = ['timestamp', 'plant_id', 'temp_c', 'humidity', 'soil_moisture', 'ph', 'event']
        cfg  = {
            "timestamp":    "Time",
            "plant_id":     "Plant",
            "temp_c":       "Temp (°C)",
            "humidity":     "Hum (%)",
            "soil_moisture":"Soil %",
            "ph":           "pH",
            "event":        "Event",
        }
        if 'image_url' in logs.columns:
            cols.insert(-1, 'image_url')
            cfg['image_url'] = st.column_config.LinkColumn("📸 Image")

        st.dataframe(logs[cols].tail(50), use_container_width=True,
                     hide_index=True, height=300, column_config=cfg)
    else:
        st.info("No logs available.")

# ============================================================
# PAGE: USER MANAGEMENT (unchanged)
# ============================================================
elif page == "USERS":
    st.markdown(
        '<div style="padding:6px 12px 4px;">'
        '<div style="font-size:18px;font-weight:900;color:#fff;">Admin Panel</div>'
        '<div style="font-size:10px;color:#66bb6a;letter-spacing:1px;margin-top:1px;">'
        'Registered accounts</div></div>',
        unsafe_allow_html=True)

    st.table(pd.DataFrame({
        "Username": ["admin@agribot.ai", "user@agribot.ai"],
        "Role":     ["Administrator",    "Standard User"]
    }))
    st.info("Future feature: add / remove users via database.")