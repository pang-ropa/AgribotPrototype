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
# PATHS
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
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# LOGIN SYSTEM
# ============================================
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "user":  {"password": "user123",  "role": "user"}
}

.main .block-container > div:first-child {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

[data-testid="stVerticalBlock"] {
    gap: 5px !important;
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
    overflow: hidden !important;
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
    gap: 20px !important;
    width: 100% !important;
    flex-direction: column !important;
    margin-bottom: 8px !important;
}

section[data-testid="stSidebar"] .stRadio label {
    font-size: 16px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    background: rgba(46,125,50,0.12) !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 6px 8px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    min-height: 44px !important;
    display: flex !important;
    align-items: center !important;
    margin-top: -15px !important;
    padding-top: 0 !important;
}

/* Hide radio circle */
section[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:first-child {
    display: none !important;
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

section[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
    color: #ffffff !important;
}

/* ── 7. LOGOUT BUTTON ──────────────────────────────────────── */
[data-testid="stSidebar"] .stButton > button {
    font-size: 16px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    background: rgba(46,125,50,0.12) !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 6px 8px !important;
    width: 100% !important;
    min-height: 44px !important;
    transition: all 0.2s !important;
    margin-top: 8px !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
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
# HELPERS
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
# SESSION STATE — always start at landing page
# ============================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

def login():
    st.title("🔐 AgriBot-AI Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = users[username]["role"]
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

if not st.session_state.logged_in:
    login()
    st.stop()

# ============================================
# CSS (WHITE UI + FORCE DARK TEXT)
# ============================================
css_code = """
<style>

/* MAIN BACKGROUND */
[data-testid="stAppViewContainer"]{
    background-color:#F6F7FB;
}

/* REMOVE HEADER */
[data-testid="stHeader"]{
    background:transparent;
}

/* FORCE TEXT COLORS */
[data-testid="stAppViewContainer"] * {
    color: #111827 !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"]{
    background:white;
    border-right:1px solid #E5E7EB;
    padding-top:20px;
}

/* SIDEBAR LOGO */
[data-testid="stSidebar"] img{
    width:60px;
    margin:auto;
    display:block;
}

/* SIDEBAR TITLE */
.sidebar-title{
    text-align:center;
    font-size:20px;
    font-weight:700;
    color:#2E7D32 !important;
    margin-top:5px;
    margin-bottom:20px;
}

/* NAVIGATION */
.stRadio label{
    font-size:16px;
    font-weight:500;
    padding:8px;
    border-radius:6px;
}
.stRadio label:hover{
    background:#F3F4F6;
}

/* METRIC CARDS */
div[data-testid="stMetric"]{
    background:white;
    border-radius:10px;
    padding:15px;
    border:1px solid #E5E7EB;
    box-shadow:0px 2px 6px rgba(0,0,0,0.05);
}

/* METRIC TEXT */
div[data-testid="stMetricLabel"]{
    color:#6B7280 !important;
    font-weight:600;
}
div[data-testid="stMetricValue"]{
    font-size:28px;
    font-weight:700;
    color:#111827 !important;
}

/* INPUTS */
input, textarea {
    color:#111827 !important;
    background:white !important;
}

/* BUTTON */
.stButton button{
    border-radius:8px;
    background:#2E7D32;
    color:white !important;
    border:none;
}

/* REMOVE STREAMLIT BRANDING */
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}

</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# ============================================
# DATA LOADING
# ============================================
@st.cache_resource
def load_assets():
    try:
        model  = joblib.load(os.path.join(SCRIPT_DIR, 'anomaly_model.pkl'))
        scaler = joblib.load(os.path.join(SCRIPT_DIR, 'anomaly_scaler.pkl'))
        return model, scaler
    except Exception:
        return None, None

def get_data():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                dict(st.secrets["gcp_service_account"]), scope)
        elif os.path.exists(CREDENTIALS_FILE):
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                CREDENTIALS_FILE, scope)
        else:
            return pd.DataFrame()

        client = gspread.authorize(creds)
        sheet = client.open("Agribot-Live-Data").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def find_column(df, possible_names):
    for name in possible_names:
        for col in df.columns:
            if name.lower() in col.lower():
                return col
    return None

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=60)

    st.markdown('<div class="sidebar-title">AgriBot-AI</div>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        page = st.radio("Navigation", ["Dashboard", "Analysis", "System Logs", "Users"])
    else:
        page = st.radio("Navigation", ["Dashboard", "Analysis"])

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# ============================================
# LOAD DATA
# ============================================
model, scaler = load_assets()
df = get_data()

if not df.empty:
    temp_col = find_column(df, ['temp'])
    hum_col  = find_column(df, ['humid'])
    ph_col   = find_column(df, ['ph'])
    soil_col = find_column(df, ['soil'])

    val_temp = df[temp_col].iloc[-1] if temp_col else 0
    val_hum  = df[hum_col].iloc[-1] if hum_col else 0
    val_ph   = df[ph_col].iloc[-1] if ph_col else 0
    val_soil = df[soil_col].iloc[-1] if soil_col else 0
else:
    val_temp = val_hum = val_ph = val_soil = 0

# ============================================
# DASHBOARD
# ============================================
if page == "Dashboard":
    st.markdown("## Dashboard")
    st.caption("Smart Hydroponics Monitoring System")

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("🌡 Temperature", f"{val_temp}°C")
    with m2: st.metric("💧 Humidity", f"{val_hum}%")
    with m3: st.metric("🧪 pH", f"{val_ph}")
    with m4: st.metric("🌱 Soil", f"{val_soil}%")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Sensor Trends")
        if not df.empty:
            st.line_chart(df)

    with col2:
        st.subheader("AI Status")
        if model and scaler:
            st.success("System Running Normally")
        else:
            st.warning("AI Model not loaded")

# ============================================
# ANALYSIS
# ============================================
elif page == "Analysis":
    st.title("Analysis")
    if not df.empty:
        st.line_chart(df)

# ============================================
# LOGS
# ============================================
elif page == "System Logs":
    st.title("Logs")
    if not df.empty:
        st.dataframe(df.tail(20))

# ============================================
# USERS
# ============================================
elif page == "Users":
    st.title("Users")
    st.table(pd.DataFrame({
        "Username": ["admin", "user"],
        "Role": ["Admin", "User"]
    }))

# AUTO REFRESH
time.sleep(10)
st.rerun()
