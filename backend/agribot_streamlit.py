import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
import base64
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import plotly.express as px
from streamlit_autorefresh import st_autorefresh   # requires streamlit-autorefresh in requirements.txt

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

ACTUAL_LOGO = next((p for p in [LOGO_PATH, PI_LOGO, WIN_LOGO] if os.path.exists(p)), "")
ACTUAL_BG   = next((p for p in [BG_PATH,   PI_BG,   WIN_BG]   if os.path.exists(p)), "")

CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "..", "credentials.json")
if not os.path.exists(CREDENTIALS_FILE):
    CREDENTIALS_FILE = os.path.expanduser("~/env/Thesis code/credentials.json")

SPREADSHEET_ID = "1mYScsUkoZn84FIoO_QMaku3gZT3Z9df72kPE3ray9-A"

# Tab favicon
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
    .stApp{{background-image:url("data:{mime};base64,{b64}");
            background-size:cover;background-position:center;
            background-repeat:no-repeat;background-attachment:fixed;}}
    .stApp::before{{content:"";position:fixed;inset:0;
            background:rgba(0,0,0,0.52);z-index:0;pointer-events:none;}}
    </style>""", unsafe_allow_html=True)

# ============================================================
# LOGIN
# ============================================================
USERS = {
    "admin@agribot.ai": {"password": "admin123", "role": "admin"},
    "user@agribot.ai":  {"password": "user123",  "role": "user"},
}
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role      = None

def login():
    set_background(ACTUAL_BG)
    logo_b64  = file_to_b64(ACTUAL_LOGO)
    logo_html = (
        f'<div style="display:flex;justify-content:center;margin-bottom:20px;">'
        f'<img src="data:image/png;base64,{logo_b64}" style="width:120px;height:120px;'
        f'border-radius:50%;border:3px solid #4CAF50;object-fit:cover;'
        f'box-shadow:0 0 28px rgba(76,175,80,0.5);"/></div>'
    ) if logo_b64 else ""

    st.markdown("""<style>
    #MainMenu{visibility:hidden;}footer{visibility:hidden;}
    [data-testid="stForm"]{
        background:linear-gradient(160deg,rgba(27,94,32,0.65) 0%,rgba(46,125,50,0.55) 100%)!important;
        backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
        border-radius:20px;border:1px solid rgba(165,214,167,0.35);
        box-shadow:0 12px 40px rgba(0,0,0,0.35);padding:34px 44px 44px;
    }
    [data-testid="stForm"] input{
        background:rgba(255,255,255,0.1)!important;color:#fff!important;
        border:1px solid rgba(165,214,167,0.45)!important;border-radius:10px!important;
        font-size:14px!important;
    }
    [data-testid="stForm"] input::placeholder{color:rgba(200,230,200,0.6)!important;}
    [data-testid="stForm"] button[kind="primaryFormSubmit"]{
        background:linear-gradient(90deg,#2e7d32,#66bb6a)!important;
        border:none!important;color:#fff!important;font-weight:700!important;
        border-radius:10px!important;letter-spacing:1.5px;font-size:14px!important;
        padding:12px!important;margin-top:4px!important;
    }
    .stTextInput label{color:#c8e6c9!important;font-weight:600!important;font-size:13px!important;}
    </style>""", unsafe_allow_html=True)

    st.markdown(
        f'<div style="display:flex;flex-direction:column;align-items:center;margin-top:52px;">'
        f'{logo_html}'
        f'<div style="text-align:center;font-size:38px;font-weight:900;color:#fff;'
        f'letter-spacing:1px;text-shadow:0 2px 12px rgba(0,0,0,0.6);margin-bottom:6px;">'
        f'AgriBot-AI</div>'
        f'<div style="text-align:center;color:#81c784;font-size:13px;letter-spacing:3px;'
        f'text-transform:uppercase;margin-bottom:24px;">'
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
                    st.rerun()
                else:
                    st.error("Invalid email or password")

if not st.session_state.logged_in:
    login()
    st.stop()

# ============================================================
# GLOBAL CSS – ULTRA CLEAN, HIDE ALL STREAMLIT BRANDING
# ============================================================
st.markdown("""<style>
/* ===== LIGHT / DARK MODE VARIABLES ===== */
:root {
    --bg-color: #ffffff;
    --text-color: #000000;
    --card-bg: rgba(46, 125, 50, 0.15);
    --border-color: #4CAF50;
    --sidebar-bg: #0a0d12;
    --sidebar-text: #81c784;
}
@media (prefers-color-scheme: dark) {
    :root {
        --bg-color: #0E1117;
        --text-color: #f0f0f0;
        --card-bg: rgba(76, 175, 80, 0.2);
        --border-color: #66bb6a;
        --sidebar-bg: #0a0d12;
        --sidebar-text: #66bb6a;
    }
}
body { background-color: var(--bg-color); color: var(--text-color); }

/* ===== HIDE ALL STREAMLIT UI ELEMENTS ===== */
#MainMenu,
footer,
header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stSidebarUserContent"] + div,
[data-testid="collapsedControl"],
.stApp > header,
.stApp > footer,
div[data-testid="stBottomBlock"] > div:first-child,
div[data-testid="stBottom"] > div:first-child,
a[href*="streamlit"],
button[kind="headerNoSpacing"],
button[title="View All Apps"],
button[title="Manage app"],
[data-testid="stAppViewContainer"] > section > div:first-child > div:first-child {
    display: none !important;
}

/* ===== MAIN CONTAINER – FULL SCREEN, NO PADDING, NO SCROLL ===== */
.main .block-container {
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    height: 100vh !important;
    overflow: hidden !important;
    display: flex;
    flex-direction: column;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    width: 260px !important;
    background: linear-gradient(180deg,#0a0d12 0%,#0d1117 100%) !important;
    border-right: 1px solid rgba(46,125,50,0.5) !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    padding: 0 16px 28px !important;
}
[data-testid="stSidebar"] [data-testid="stElementToolbar"] {
    display: none !important;
}

/* ===== METRIC CARDS ===== */
div[data-testid="stMetric"] {
    background: var(--card-bg) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 16px !important;
    padding: 20px 16px !important;
    text-align: center !important;
}
div[data-testid="stMetricLabel"] {
    font-weight: 700 !important;
    font-size: 11px !important;
    color: #66bb6a !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    justify-content: center !important;
}
div[data-testid="stMetricValue"] {
    font-size: 34px !important;
    font-weight: 900 !important;
    color: #ffffff !important;
    margin-top: 4px !important;
}

/* ===== CUSTOM CARDS ===== */
.cam-card {
    background: rgba(13,17,23,0.9);
    border: 1px solid rgba(46,125,50,0.4);
    border-radius: 18px;
    padding: 20px;
}
.sensor-row {
    background: rgba(13,17,23,0.85);
    border: 1px solid rgba(46,125,50,0.25);
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.s-label {
    font-size: 11px;
    font-weight: 700;
    color: #66bb6a;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 3px;
}
.s-val {
    font-size: 26px;
    font-weight: 900;
    color: #fff;
    line-height: 1;
}
.s-unit {
    font-size: 13px;
    color: #a5d6a7;
    margin-left: 2px;
}
.s-ok { font-size: 11px; color: #4CAF50; margin-top: 3px; }
.s-warn { font-size: 11px; color: #FF9800; margin-top: 3px; }
.s-bad { font-size: 11px; color: #f44336; margin-top: 3px; }
.s-icon { font-size: 26px; opacity: 0.6; }

.section-title {
    font-size: 13px;
    font-weight: 700;
    color: #66bb6a;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 14px;
    margin-top: 2px;
    border-left: 3px solid #4CAF50;
    padding-left: 10px;
}
.alert-item {
    padding: 9px 14px;
    background: rgba(183,28,28,0.12);
    border: 1px solid rgba(183,28,28,0.3);
    color: #ef9a9a;
    border-radius: 10px;
    margin: 5px 0;
    font-size: 13px;
}
.sched-badge {
    display: inline-block;
    background: rgba(21,101,192,0.2);
    border: 1px solid rgba(21,101,192,0.5);
    border-radius: 6px;
    padding: 2px 9px;
    font-size: 11px;
    color: #90CAF9;
    font-weight: 700;
    margin: 0 2px;
}
.cam-meta {
    font-size: 11px;
    color: #66bb6a;
    margin-top: 8px;
    line-height: 1.7;
}
.drive-link {
    display: inline-block;
    margin-top: 10px;
    background: rgba(46,125,50,0.15);
    border: 1px solid rgba(76,175,80,0.3);
    border-radius: 8px;
    padding: 6px 12px;
    color: #81c784;
    font-size: 12px;
    text-decoration: none;
}
.cam-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 340px;
    background: rgba(46,125,50,0.04);
    border: 2px dashed rgba(46,125,50,0.3);
    border-radius: 14px;
    text-align: center;
    padding: 40px;
}
</style>""", unsafe_allow_html=True)

# ============================================================
# CLIENT‑SIDE AUTO‑REFRESH (every 30 seconds)
# ============================================================
st_autorefresh(interval=30000, key="auto_refresh")

# ============================================================
# DATA FUNCTIONS (unchanged – keep your existing functions here)
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
    """Returns {url, plant_id, timestamp} for the single most recent captured image."""
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
# SIDEBAR (unchanged – keep your existing sidebar code)
# ============================================================
sheet    = get_sheet()
logo_b64 = file_to_b64(ACTUAL_LOGO)

with st.sidebar:
    st.markdown(f"""
    <div style="display:flex;flex-direction:column;align-items:center;
                padding-top:32px;width:100%;margin-bottom:8px;">
        <div style="padding:4px;border-radius:50%;
                    background:linear-gradient(145deg,#388e3c,#1b5e20);
                    box-shadow:0 0 20px rgba(76,175,80,0.3);margin-bottom:14px;">
            <img src="data:image/png;base64,{logo_b64}"
                 style="border-radius:50%;width:110px;height:110px;
                        display:block;object-fit:cover;background:#0a0d12;"/>
        </div>
        <div style="font-size:19px;font-weight:900;color:#4CAF50;
                    letter-spacing:0.5px;margin-bottom:2px;">AgriBot-AI</div>
        <div style="font-size:9px;color:#388e3c;letter-spacing:3px;
                    text-transform:uppercase;margin-bottom:10px;">
            Crop Monitoring System</div>
        <div style="font-size:9px;font-weight:700;letter-spacing:1.5px;
                    text-transform:uppercase;padding:4px 14px;border-radius:20px;
                    background:rgba(46,125,50,0.15);border:1px solid rgba(76,175,80,0.25);
                    color:#66bb6a;">
            {'👑 Administrator' if st.session_state.role == 'admin' else '🌿 Field User'}
        </div>
    </div>
    <div style="width:55%;height:1px;background:linear-gradient(90deg,transparent,
                rgba(76,175,80,0.4),transparent);margin:14px auto 18px;"></div>
    <div style="font-size:9px;font-weight:700;color:#2e7d32;letter-spacing:3px;
                text-transform:uppercase;width:100%;padding:0 4px;
                margin-bottom:8px;">Navigation</div>
    """, unsafe_allow_html=True)

    nav_opts = (
        ["📡  Live Dashboard", "📈  Analysis",
         "📜  System Logs",    "👥  User Management"]
        if st.session_state.role == "admin"
        else ["📡  Live Dashboard", "📈  Analysis"]
    )
    raw_page = st.radio("", nav_opts, label_visibility="collapsed")
    page_map = {
        "📡  Live Dashboard":  "DASHBOARD",
        "📈  Analysis":        "ANALYSIS",
        "📜  System Logs":     "LOGS",
        "👥  User Management": "USERS",
    }
    page = page_map.get(raw_page, "DASHBOARD")

    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;
                background:rgba(46,125,50,0.1);border:1px solid rgba(46,125,50,0.3);
                border-radius:10px;padding:10px 14px;width:100%;
                margin:16px 0 10px;box-sizing:border-box;">
        <div style="width:8px;height:8px;background:#4CAF50;border-radius:50%;
                    box-shadow:0 0 8px #4CAF50;animation:pulse 2s infinite;
                    flex-shrink:0;"></div>
        <span style="font-size:11px;font-weight:700;color:#66bb6a;
                     letter-spacing:2px;text-transform:uppercase;">System Online</span>
    </div>
    <style>
    @keyframes pulse{0%,100%{box-shadow:0 0 5px #4CAF50;}
                     50%{box-shadow:0 0 14px #4CAF50;opacity:0.7;}}
    </style>""", unsafe_allow_html=True)

    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.role      = None
        st.rerun()

# ============================================================
# SHARED DATA + THRESHOLDS
# ============================================================
model,  scaler = load_assets()
latest         = get_latest_readings()

PH_LOW,   PH_HIGH   = 5.5,  6.5
SOIL_DRY, SOIL_WET  = 30,   80
TEMP_LOW, TEMP_HIGH = 15,   30
HUM_LOW,  HUM_HIGH  = 50,   85

def sensor_cls(val, lo, hi):
    return "s-ok" if lo <= val <= hi else ("s-bad" if val < lo * 0.7 or val > hi * 1.3 else "s-warn")

def health_of(soil, ph):
    if ph < PH_LOW or ph > PH_HIGH:  return "🔴 pH Alert",  "#f44336"
    if soil < SOIL_DRY:               return "⚠️ Too Dry",   "#FF9800"
    if soil > SOIL_WET:               return "⚠️ Too Wet",   "#FF9800"
    return                                   "✅ Healthy",    "#4CAF50"

# ==============================================================
# PAGE: LIVE DASHBOARD
# ==============================================================
if page == "DASHBOARD":
    st.markdown("""
    <div style="margin-bottom:6px;">
        <div style="font-size:26px;font-weight:900;900;color:#color:#ffffff;
                    letterffffff;
-spacing                    letter-spacing:0.3:0px;.3px;line-height:1line-height:1.2.2;">
           ;">
            Real-Time Monitoring Real-Time Monitoring</div>
       </div>
        <div style="font-size: <div style="font-size:13px13px;color;color:#:#66bb666bb6a;a;letter-spacing:letter-spacing:1px1px;margin-top:4px;margin-top:4px;">
            Greenhouse Overview;">
            Greenhouse Overview — Agri — AgriBot-AI CropBot-AI Crop System System</div>
    </</div>
    </div>""",div>""", unsafe_ unsafe_allow_html=True)

    ifallow_html=True)

    if latest.empty latest.empty:
        st.warning("No sensor data yet:
        st.warning("No sensor data yet — waiting for the — waiting for the Pi...")
        Pi... st.stop")
        st.stop()

    # Aggregate()

    # Aggregate across all plants ( across all plants (greenhousegreenhouse-level view)
    avg_temp = float-level view)
    avg_temp = float(latest(latest['temp['temp_c'].mean())
_c'].mean())
    avg_hum  =    avg_hum  = float(latest[' float(latest['humidityhumidity'].mean())
    avg_ph   = float(latest['ph'].mean())
   '].mean())
    avg_ph   = float(latest['ph'].mean())
    avg_ avg_soil =soil = float(latest[' float(latest['soil_moistsoil_moisture'].ure'].mean())

mean())

    m    m1,1, m2, m m2, m3,3, m4 m4 = st.columns( = st.columns(4)
4)
    m1    m1.metric("TEMP",    .metric("TEMP",     f"{ f"{avg_tempavg_temp:.1f}:.1f} °C °C")
   ")
    m2.metric m2.metric("H("HUMIDITY", f"{avg_hum:.0f} %")
    m3.metricUMIDITY", f"{avg_hum:.0f} %")
    m3.metric("PH("PH",       f"{",       f"{avg_avg_ph:.2fph:.2f}")
    m4}")
    m4.metric("SO.metric("SOIL",IL",     f     f"{avg_soil"{avg_soil:.0:.0f}f} %")

    st %")

    st.markdown.markdown("<div("<div style=' style='margin:margin:18px 0 6px;18px 0 6px;'></div>", unsafe_allow_html=True)

    with st.spinner("Loading latest capture..."'></div>", unsafe_allow_html=True)

    with st.spinner("Loading latest capture..."):
        img_data):
        img_data = get = get_latest_image()

    cam_latest_image()

    cam_col, sensor_col_col, sensor_col = st.columns = st.columns([3,([3, 2 2], gap="large], gap="large")

   ")

    with cam_col:
 with cam_col:
        st.markdown('<div        st.markdown('<div class="cam-card class="cam-card">', unsafe_allow_html=True)
        st.markdown('<div class="">', unsafe_allow_html=True)
        st.markdown('<div class="section-titlesection-title">">📷 Plant📷 Plant Health Feed</div>', Health Feed</div>', unsafe_allow_html unsafe_allow_html=True)

=True)

        if        if img_data.get("url"):
            st.image(img_data[" img_data.get("url"):
            st.image(img_data["url"],url"], use_container use_container_width=True)
           _width=True)
            pid_txt = pid_t f"xt = f"🥬🥬 Plant {img_data Plant {img_data['plant['plant_id']_id']}" if}" if img_data img_data.get(".get("plant_id") else ""
           plant_id") else ""
            ts_txt  = f" ts_txt  = f"🕒 {img🕒 {img_data['_data['timestamp']timestamp']}"      }"       if img_data.get if img_data.get("timestamp") else ""
            st.mark("timestamp") else ""
            st.markdown(
down(
                f                f''<div class<div class="cam="cam-meta-meta">'
">'
                f'{pid                f'{pid_txt}&nbsp_txt}&nbsp;&nbsp;{;&nbsp;{ts_tts_txtxt}<br>'
               }<br>'
                f' f'Captured at '
Captured at '
                f'                f'<span class="s<span class="sched-bched-badge">7:adge">7:00 AM</span00 AM</span>'
>'
                f                f'<span class="sched-badge">'<span class="sched-badge">12:12:0000 NN</ NN</span>'
span>'
                f                f''<span class="sched-badge"><span class="sched-badge">12:30 PM</span12:30 PM</span>'
>'
                f'</                f'</div>'
                f'<a href="{div>'
                f'<a href="{img_dataimg_data["url"]}"["url"]}" target="_blank" class=" target="_blank" class="drive-link">'
drive-link">'
                f                f'☁️'☁️ View in Google Drive ↗</ View in Google Drive ↗</a>a>',
                unsafe_',
                unsafe_allow_html=True)
        elseallow_html=True)
        else:
           :
            st.mark st.markdown(
               down(
                '<div class '<div class="cam="cam-placeholder">'
-placeholder">'
                '<div style="font                '<div style="font-size:54px;margin-bottom:16px;">📷</div>'
                '<div-size:54px;margin-bottom:16px;">📷</div>'
                '<div style=" style="font-size:15px;font-weight:700;color:#4CAF50;">No image yet</font-size:15px;font-weight:700;color:#4CAF50;">No image yet</div>'
               div>'
                '<div style=" '<div style="font-sizefont-size:12:12px;px;color:#color:#2e2e7d7d32;32;margin-top:8px;">margin-top:8px;">'
                'Pi captures at '
               '
                'Pi captures at '
                '<span '<span class="sched class="sched-badge">7:00-badge">7:00 AM</span>'
                '<span class="sched-badge">12:00 NN</span>'
                '<span AM</span>'
                '<span class="sched-badge">12:00 NN</span>'
                '<span class="sched class="sched-badge">05:00-badge">05:00 PM</span></div>'
                '</div PM</span></div>'
                '</div>',
                unsafe>',
                unsafe_allow_html=True)
       _allow_html=True)
        st.mark st.markdown('down('</div</div>',>', unsafe_allow_html=True)

    with sensor_col:
        if not unsafe_allow_html=True)

    with sensor_col:
        if not latest.empty latest.empty:
            last_:
            last_ts = pd.tots = pd.to_datetime_datetime(latest(latest['timestamp']).['timestamp']).max()
max()
            st.markdown            st.markdown(
                f'(
                f'<div style="<div style="text-align:right;fonttext-align:right;font-size:-size:11px11px;color;color:#388e3:#388e3c;c;'
                f'margin-bottom:12'
                f'margin-bottom:12px;">🔄px;">🔄 Updated {last_ Updated {last_ts.strts.strftime("%H:%ftime("%H:%M:%S")}</divM:%S")}</div>',
                unsafe>',
                unsafe_allow_html=True_allow_html=True)

        st.markdown('<div class)

        st.markdown('<div class="section="section-title">-title">🤖🤖 AI Health AI Health Recommendation</ Recommendation</div>div>', unsafe_allow_html=True', unsafe_allow_html=True)
       )
        p1 = latest p1 = latest[latest[latest['plant['plant_id'] == _id'] == 1]
1]
        if not p1.empty and model and scal        if not p1.empty and model and scaler:
            tryer:
            try:
                feat = np.array:
                feat = np.array([[float([[float(p1(p1.iloc.iloc[0]['temp[0]['temp_c']),
                                 _c'] float(p),
                                  float(p1.il1.ilococ[0]['[0]['humidityhumidity']),
']),
                                  float(p1                                  float(p1.iloc.iloc[0]['ph'])][0]['ph'])]])
                pred = model.predict])
                pred = model.predict(scaler.transform(feat))(scaler.transform(feat))[0]
               [0]
                if pred == -1:
                    st.error("🚨 if pred == -1:
                    st.error("🚨 **ALERT** — Anomalous **ALERT** — Anomalous conditions detected in the conditions detected in the greenhouse.")
 greenhouse.")
                else                else:
                   :
                    st.success("✅ **HEALTHY** — Crop environment st.success("✅ **HEALTHY** — Crop environment is optimal is optimal.")
           .")
            except Exception as e except Exception as e:
               :
                st.info(f"AI model processing... st.info(f"AI model processing... ({e ({e})")
        else})")
        else:
           :
            st.warning(" st.warning("Awaiting sensor data orAwaiting sensor data or AI model...")

 AI model...")

        st        st.markdown("<div.markdown("<div style=' style='margin:14pxmargin: 0 414px 0 4px;'></div>",px;'></div>", unsafe_allow_html=True)

        st.markdown unsafe_allow_html=True)

        st.markdown('<div class="section-title('<div class="section-title">">🔔 Recent🔔 Recent Alerts</div>', Alerts</div>', unsafe_allow_html unsafe_allow_html=True)
        alerts = []
        for=True)
        alerts = []
        for _, plant _, plant in latest.iterrows():
            pid  in latest.iterrows():
            pid  = int(plant = int(plant['plant_id'])
['plant_id'])
            soil            soil = float(plant['soil = float(plant['soil_moisture_moisture'])
            ph  '])
            ph   = float = float(plant['ph(plant['ph'])
            if soil'])
            if soil < SO < SOIL_DRYIL_DRY:
               :
                alerts.append alerts.append(f"(f"🌱🌱 Plant {pid}: Plant {pid}: soil too dry ({ soil too dry ({soil:.0f}%)soil:.0f}%)")
           ")
            elif soil elif soil > SOIL_WET:
 > SOIL_WET:
                alerts                alerts.append(f".append(f"🌱 Plant🌱 Plant {pid}: soil {pid}: soil too wet ({soil too wet ({soil:.0f}:.0f}%)")
%)")
            if            if ph ph < PH_L < PH_LOW orOW or ph > ph > PH_H PH_HIGH:
                alertsIGH:
                alerts.append(f.append(f""🧪 Plant🧪 Plant {pid {pid}: pH}: pH out of out of range ({ range ({ph:.ph:.2f})")
2f})")
        if        if avg_temp < TEMP_L avg_temp < TEMP_LOW or avg_temp > TEMOW or avg_temp > TEMP_HIGH:
            alertsP_HIGH:
            alerts.append(f".append(f"🌡️ Temperature: {avg🌡️ Temperature: {avg_temp:.1f_temp:.1f}°}°C out of range")
       C out of range")
        if avg_hum < HUM if avg_hum < HUM_LOW_LOW or avg or avg_hum > HUM_HIGH:
            alerts.append(f"💧 Humidity: {avg_hum:.0f}% out_hum > HUM_HIGH:
            alerts.append(f"💧 Humidity: {avg_hum:.0f}% out of range")

        if alerts of range")

        if alerts:
           :
            for a in alerts for a in alerts[:6[:6]:
                st.mark]:
                st.markdown(fdown(f'<div class'<div class="alert="alert-item">{-item">{a}</div>', unsafea}</div>', unsafe_allow_html=True_allow_html=True)
       )
        else:
            else:
            st.success st.success("("✅ All greenhouse parameters✅ All greenhouse parameters are within are within range.")

# = range.")

# ======================================================================================================================
=====
# PAGE: ANALYSIS# PAGE: ANALYSIS
# =============================================================
# ==============================================================
elif=
elif page == "AN page == "ANALYSISALYSIS":
    st.markdown("""
    <div style="margin-bottom:18px;">
       ":
    st.markdown("""
    <div style="margin-bottom:18px;">
        <div style=" <div style="font-sizefont-size:24:24px;font-weightpx;font-weight:900;color:#fff:900;color:#fff;">Historical;">Historical Trends</div>
 Trends</       div>
        <div style <div style="font-size:="font-size:13px13px;color:#66bb6;color:#66bb6a;letter-spacing:1pxa;letter-spacing:1px;margin;margin-top:4px-top:4px;">
           ;">
            Sensor data over time — per plant</div Sensor data over time — per plant</div>
    </div>>
    </div>""", unsafe_allow_html""", unsafe_allow_html=True)

    if not latest=True)

    if not latest.empty:
        sc1,.empty:
        sc1, sc2 sc2, sc, sc3 = st.columns([13 = st.columns([1, 1,, 1, 2 2])
        with sc1:
            sensor_choice])
        with sc1:
            sensor_choice = st.selectbox("Sensor", [
                "Temperature (°C)", = st.selectbox("Sensor", [
                "Temperature (°C)", "Humidity (%)", " "Humidity (%)", "pH", "Soil Moisture (%)"])
        with sc2:
            plant_sel = st.selectbox("pH", "Soil Moisture (%)"])
        with sc2:
            plant_sel = st.selectbox("Plant",Plant", list(range(1 list(range(1, , 11)))
11)))
        with        with sc3 sc3:
           :
            time_range time_range = st = st.selectbox.selectbox("Time("Time range", ["24 range", ["24 hours", hours", "7 days", "30 days"])
 "7 days", "30 days"])
            hours = {"24 hours            hours = {"24 hours": 24, "7": 24, "7 days": 168, " days": 168, "30 days30 days": ": 720}[time_range]

720}[time_range]

               hist_df = get_historical hist_df = get_historical_data(_data(plant_id=plant_selplant_id=plant_sel, hours=, hours=hours)
       hours)
        if not if not hist_df hist_df.empty:
            col.empty:
            col_map = {
               _map = {
                "Temperature (°C) "Temperature (°C)": ("temp": ("temp_c",       "°C_c",       "°C"),
                "Hum"),
                "Humidity (%)idity (%)":    ":     ("hum ("humidity",      "%idity",      "%"),
               "),
                "pH":               ("ph",            "pH"),
                "Soil Moisture (%)":("soil_moisture "pH":               ("ph",            "pH"),
                "Soil Moisture (%)":("soil_moisture", "%"),
           ", "%"),
            }
            y_col }
            y_col, y, y_label = col_map_label = col_map[sensor_choice[sensor_choice]
            fig =]
            fig = px.line px.line(hist_df, x='(hist_df, x='timestamp', y=y_col,
timestamp', y=y                          title_col,
                          title=f"{sensor_=f"{sensor_choicechoice} — Plant {plant_} — Plant {plant_sel}")
sel}")
            fig.update_layout            fig.update_layout(yaxis(yaxis_title=y_label,
_title=y                              paper_label,
                              paper_bg_bgcolor='rgba(0color='rgba(0,0,0,0,0,0)',
,0)',
                              plot                              plot_bg_bgcolor='color='rgbargba(13(13,17,17,23,23,0.85)',
,0.85                              font)',
                              font_color='_color='#a#a5d5d6a7',
6a7',
                              title_font_color='#ffffff                              title_font_color='#ffffff')
            st.plot')
            st.plotly_chly_chart(fart(fig, use_containerig, use_container_width=True_width=True)

            if sensor)

            if sensor_choice == "_choice == "Soil MoistSoil Moisture (%)ure (%)":
               ":
                st.mark st.markdowndown('<div class="section('<div class-title">="section-title">🌱🌱 Current Soil — All Current Soil — All Plants</div> Plants</div>',
                           ',
                            unsafe_ unsafe_allow_htmlallow_html=True)
=True)
                bar = px                bar = px.bar(latest.bar(latest.sort_values.sort_values('plant_id'),
('plant_id'),
                             x                             x='plant='plant_id', y='_id', y='soil_msoil_moistoisture',
ure',
                             color='soil                             color='soil_moisture_moisture', color_continuous_scale='Greens',
                             labels={'plant_id': 'Plant', 'soil_moisture':', color_continuous_scale='Greens',
                             labels={'plant_id': 'Plant', 'soil_moisture': 'Soil 'Soil %' %'})
               })
                bar.update bar.update_layout(paper_b_layout(paper_bgcolor='rgbagcolor='rgba((0,0,0,0,0,0)',
                                  plot_bgcolor0,0)',
                                  plot_bgcolor='rg='rgba(ba(13,17,13,17,23,0.23,0.85)',
                                  font_color85)',
                                  font_color='#a5d6='#a5d6a7')
               a7')
                st.plot st.plotly_chart(ly_chart(bar, use_container_width=Truebar, use_container_width=True)
       )
        else:
            st else:
            st.warning.warning("No data for this plant in the selected time range.")
("No data for this plant in the selected time range.")
    else:
        st.w    else:
        st.warning("arning("No data available yet.")

#No data available yet.")

# ==============================================================
# PAGE: SYSTEM LOGS
# ==============================================================
elif page == " ==============================================================
# PAGE: SYSTEM LOGS
# ==============================================================
elif page == "LOGSLOGS":
   ":
    st.mark st.markdown("down("""
""
    <div style    <div style="margin-bottom:18px="margin-bottom:18px;">
        <div;">
        <div style=" style="font-sizefont-size:24:24px;font-weightpx;font-weight:900:900;color:#fff;">System;color:#fff;">System Logs</div Logs</div>
       >
        <div style=" <div style="font-sizefont-size:13:13px;color:#66bb6a;letter-sppx;color:#66bb6a;letter-spacingacing:1px;margin-top:1px;margin-top:4px;">
            Last:4px;">
            Last 24 hours of sensor activity 24 hours of sensor activity</div>
   </div>
    </div>""", unsafe </div>""", unsafe_allow_html=True_allow_html=True)

   )

    logs = logs = get_historical_data get_historical_data(plant(plant_id=None, hours_id=None, hours=24=24)
   )
    if if not logs.empty not logs.empty:
       :
        def def classify(r):
            if r['temp_c'] < TEMP_LOW classify(r):
            if r['temp_c'] < TEMP_LOW or r or r['temp['temp_c'] > TEMP_H_c'] > TEMP_HIGH:IGH:       return "       return "🌡️🌡️ Temp alert"
            Temp alert"
            if r['hum if r['humidity']idity'] < HUM < HUM_LOW_LOW or r or r['hum['humidity']idity'] > HUM > HUM_HIGH_HIGH:     return ":    💧 return "💧 Humidity alert Humidity alert"
            if r"
            if r['ph['ph']'] < PH_L < PH_LOW or r['OW or r['ph'] > PH_HIGHph'] > PH_HIGH:                   return "🧪:                   return "🧪 pH alert"
            if r pH alert"
            if r['soil_moisture['soil_moisture']'] < SOIL_DRY or r[' < SOIL_DRY or r['soil_moisture']soil_moisture'] > SO > SOIL_WIL_WET: return "🌱ET: return "🌱 Soil alert"
 Soil alert"
            return "            return "Normal"
Normal"
        logs['event        logs['event'] = logs.apply(class'] = logs.apply(classifyify, axis, axis=1=1)
       )
        cols = cols = ['timestamp ['timestamp', 'plant_id', 'temp_c', 'humidity', '', 'plant_id', 'temp_c', 'humidity', 'soil_moisture',soil_moisture', 'ph 'ph', 'event']
', 'event']
        cfg        cfg  = {"timestamp  = {"timestamp": "Time", "plant_id": "Plant", "temp_c": "": "Time", "plant_id": "Plant", "temp_c": "Temp (°Temp (°C)",
                "C)",
                "humhumidityidity": "Hum (%)": "Hum (%)", "soil_m", "oistsoil_moisture": "Soil %", "ph": "pH", "event": "Event"}
ure": "Soil %", "ph": "pH", "event": "Event"}
        if        if 'image_url' 'image_url' in logs.columns:
            cols in logs.columns:
            cols.insert(-1, 'image.insert(-1, 'image_url')
            cfg['image_url')
            cfg['image_url'] = st_url'] = st.column_config.L.column_config.LinkColumninkColumn("📸 Image")
       ("📸 Image")
        st.dataframe(log st.dataframe(logss[cols].tail(50),[cols].tail(50), use_container_width=True use_container_width=True,
                    ,
                     hide_index hide_index=True,=True, column_config column_config=cfg)
   =cfg)
    else:
        st.info(" else:
        st.info("No logsNo logs available.")

 available.")

# =========================================================# ==============================================================
=====
# PAGE: USER# PAGE: USER MANAGEMENT
 MANAGEMENT
# =========================================================# ==============================================================
=====
elif pageelif page == "USERS":
    == "USERS":
    st.mark st.markdown("down("""
   ""
    <div style="margin <div style="margin-bottom:-bottom:18px18px;">
       ;">
        <div <div style="font-size style="font-size:24px;:24font-weightpx;font-weight:900:900;color:#fff;">Admin;color:#fff;">Admin Control Panel Control Panel</div</div>
       >
        <div <div style="font-size style="font-size:13:13px;px;color:#66bbcolor:#66bb6a;letter-spacing:1px;margin-top:4px;">
            Registered user accounts</div>
    </div>""", unsafe_allow_html=True)
    st.table(pd.DataFrame({
6a;letter-spacing:1px;margin-top:4px;">
            Registered user accounts</div>
    </div>""", unsafe_allow_html=True)
    st.table(pd.DataFrame({
        "Username": ["        "Username": ["adminadmin@ag@agribot.airibot.ai", "user", "user@agribot@agribot.ai"],
.ai"],
        "Role":        "Role":     ["     ["AdministratorAdministrator",   ",    "Standard User"]
    } "Standard User"]
    }))
   ))
    st.info st.info("Future("Future feature: add / feature: add / remove users via database.")