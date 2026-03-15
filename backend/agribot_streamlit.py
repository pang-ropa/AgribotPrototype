import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
import base64
import time
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import plotly.express as px

# ============================================================
# PATHS — resolved relative to this script
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

LOGO_PATH = os.path.join(SCRIPT_DIR, "agribotailogo.png")
BG_PATH   = os.path.join(SCRIPT_DIR, "background.jpg")
PI_LOGO   = os.path.expanduser("~/env/Thesis code/backend/agribotailogo.png")
PI_BG     = os.path.expanduser("~/env/Thesis code/backend/background.jpg")
WIN_LOGO  = r"C:\Users\admin\Downloads\AgribotPrototype\backend\agribotailogo.png"
WIN_BG    = r"C:\Users\admin\Downloads\AgribotPrototype\backend\background.jpg"

ACTUAL_LOGO = next((p for p in [LOGO_PATH, PI_LOGO, WIN_LOGO] if os.path.exists(p)), "")
ACTUAL_BG   = next((p for p in [BG_PATH,   PI_BG,   WIN_BG]   if os.path.exists(p)), "")

CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "..", "credentials.json")
if not os.path.exists(CREDENTIALS_FILE):
    CREDENTIALS_FILE = os.path.expanduser("~/env/Thesis code/credentials.json")

SPREADSHEET_ID = "1mYScsUkoZn84FIoO_QMaku3gZT3Z9df72kPE3ray9-A"

# ── Sheet columns (agribot_pi_final.py) ───────────────────────
# A:timestamp | B:plant_id | C:temp_c | D:humidity
# E:soil_moisture | F:ph | G:image_url
# 10 rows/cycle · 1 cycle/minute

# ── Tab favicon: use actual thesis logo if available ──────────
_page_icon = "🌱"
if ACTUAL_LOGO:
    try:
        from PIL import Image as _PILImage
        _page_icon = _PILImage.open(ACTUAL_LOGO)
    except Exception:
        _page_icon = "🌱"

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

def gdrive_thumbnail(url: str, size: str = "w800") -> str:
    """Convert Drive view URL → thumbnail URL that st.image() can render."""
    if not url:
        return ""
    try:
        if "id=" in url:
            file_id = url.split("id=")[1].split("&")[0]
            return f"https://drive.google.com/thumbnail?id={file_id}&sz={size}"
    except Exception:
        pass
    return url

def set_background(path: str):
    b64 = file_to_b64(path)
    if not b64:
        return
    ext  = os.path.splitext(path)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:{mime};base64,{b64}");
            background-size:cover; background-position:center;
            background-repeat:no-repeat; background-attachment:fixed;
        }}
        .stApp::before {{
            content:""; position:fixed; inset:0;
            background:rgba(0,0,0,0.48); z-index:0; pointer-events:none;
        }}
        </style>""", unsafe_allow_html=True)

# ============================================================
# LOGIN
# ============================================================
USERS = {
    "admin@agribot.ai": {"password": "admin123", "role": "admin"},
    "user@agribot.ai":  {"password": "user123",  "role": "user"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role      = None

def login():
    set_background(ACTUAL_BG)
    logo_b64  = file_to_b64(ACTUAL_LOGO)
    logo_html = (
        '<div style="display:flex;justify-content:center;margin-bottom:18px;">'
        f'<img src="data:image/png;base64,{logo_b64}" '
        'style="width:130px;height:130px;border-radius:50%;'
        'border:3px solid #4CAF50;object-fit:cover;'
        'box-shadow:0 0 24px rgba(76,175,80,0.45);"/></div>'
    ) if logo_b64 else ""

    st.markdown(f"""
    <style>
    #MainMenu{{visibility:hidden;}} footer{{visibility:hidden;}}
    [data-testid="stForm"]{{
        background:linear-gradient(160deg,rgba(56,142,60,0.55) 0%,
            rgba(76,175,80,0.45) 50%,rgba(129,199,132,0.40) 100%)!important;
        backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
        border-radius:18px;border:1px solid rgba(165,214,167,0.5);
        box-shadow:0 8px 32px rgba(0,0,0,0.25);padding:30px 40px 40px 40px;
    }}
    [data-testid="stForm"] input{{
        background:rgba(255,255,255,0.12)!important;color:white!important;
        border:1px solid rgba(165,214,167,0.6)!important;border-radius:10px!important;
    }}
    [data-testid="stForm"] input::placeholder{{color:rgba(220,240,220,0.7)!important;}}
    [data-testid="stForm"] button[kind="primaryFormSubmit"]{{
        background:linear-gradient(90deg,#388e3c,#66bb6a)!important;
        border:none!important;color:white!important;font-weight:700!important;
        border-radius:10px!important;letter-spacing:1px;
    }}
    .stTextInput label{{color:#e8f5e9!important;font-weight:600!important;}}
    </style>
    <div style="display:flex;flex-direction:column;align-items:center;margin-top:60px;">
        {logo_html}
        <div style="text-align:center;font-size:42px;font-weight:800;color:white;
            text-shadow:0 2px 8px rgba(0,0,0,0.5);margin-bottom:4px;">AgriBot-AI</div>
        <div style="text-align:center;color:#a5d6a7;margin-bottom:20px;font-size:15px;">
            Smart Farming · Intelligent Monitoring</div>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login_form"):
            email    = st.text_input("Email",    placeholder="admin@agribot.ai or user@agribot.ai")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            if st.form_submit_button("Login", use_container_width=True):
                if email in USERS and USERS[email]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.role      = USERS[email]["role"]
                    st.success("Login Successful")
                    st.rerun()
                else:
                    st.error("Invalid email or password")

if not st.session_state.logged_in:
    login()
    st.stop()

# ============================================================
# GLOBAL CSS
# ============================================================
st.markdown("""
<style>
[data-testid="stHeader"]{background-color:transparent!important;}
section[data-testid="stSidebar"]{
    width:270px!important;background-color:#0E1117!important;
    border-right:2px solid #2e7d32!important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{
    display:flex!important;flex-direction:column!important;
    align-items:center!important;padding:0 14px 24px 14px!important;
}
[data-testid="stSidebar"] [data-testid="stElementToolbar"]{display:none!important;}
.stRadio>div{gap:5px!important;width:100%!important;flex-direction:column!important;}
.stRadio label{
    font-size:13px!important;font-weight:600!important;color:#a5d6a7!important;
    background:rgba(46,125,50,0.08)!important;border:1px solid rgba(76,175,80,0.18)!important;
    border-radius:8px!important;padding:10px 14px!important;width:100%!important;
    cursor:pointer!important;transition:all 0.15s ease!important;
}
.stRadio label:hover{background:rgba(76,175,80,0.18)!important;
    border-color:#4CAF50!important;color:#fff!important;}
div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked){
    background:rgba(46,125,50,0.35)!important;border:1px solid #4CAF50!important;
    color:#fff!important;box-shadow:0 0 8px rgba(76,175,80,0.25)!important;
}
.stRadio [data-baseweb="radio"]>div:first-child{display:none!important;}
.stRadio [data-testid="stMarkdownContainer"] p{margin:0!important;}
[data-testid="stSidebar"] .stButton>button{
    background:transparent!important;border:1px solid #2e7d32!important;
    color:#81c784!important;border-radius:8px!important;width:100%!important;
    font-size:13px!important;font-weight:600!important;padding:9px!important;
}
[data-testid="stSidebar"] .stButton>button:hover{
    background:rgba(211,47,47,0.12)!important;border-color:#c62828!important;
    color:#ef9a9a!important;
}
div[data-testid="stMetric"]{
    background:rgba(46,125,50,0.15)!important;border:1px solid #4CAF50!important;
    border-radius:14px!important;padding:18px 14px!important;text-align:center!important;
    margin-bottom:10px!important;
}
div[data-testid="stMetricLabel"]{
    font-weight:bold!important;color:#A5D6A7!important;
    justify-content:center!important;font-size:13px!important;
}
div[data-testid="stMetricValue"]{font-size:30px!important;color:#ffffff!important;}
#MainMenu{visibility:hidden;} footer{visibility:hidden;}
[data-testid="stDecoration"]{display:none;}

/* Camera image frame */
.cam-frame{
    background:rgba(14,17,23,0.92);
    border:2px solid #2e7d32;
    border-radius:16px;
    padding:14px;
    height:100%;
}
.cam-frame-title{
    font-size:14px;font-weight:700;color:#a5d6a7;
    margin-bottom:10px;letter-spacing:0.5px;
}
.cam-no-image{
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    background:rgba(46,125,50,0.06);border:2px dashed #2e7d32;
    border-radius:12px;padding:60px 20px;text-align:center;
    min-height:320px;
}
/* Sensor info card */
.sensor-card{
    background:rgba(14,17,23,0.88);
    border:1px solid #2e7d32;
    border-radius:12px;
    padding:14px 16px;
    margin-bottom:10px;
}
.sensor-label{
    font-size:11px;font-weight:700;color:#66bb6a;
    text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;
}
.sensor-value{
    font-size:28px;font-weight:800;color:#ffffff;line-height:1.2;
}
.sensor-unit{font-size:14px;color:#a5d6a7;margin-left:3px;}
.sensor-status-ok  {font-size:11px;color:#4CAF50;margin-top:2px;}
.sensor-status-warn{font-size:11px;color:#FF9800;margin-top:2px;}
.sensor-status-bad {font-size:11px;color:#f44336;margin-top:2px;}

/* AI / Alert boxes */
.ai-box{
    background:rgba(14,17,23,0.88);border:1px solid #2e7d32;
    border-radius:14px;padding:18px;margin-bottom:10px;
}
.alert-item{
    padding:8px 12px;background:#ffebee;color:#b71c1c;
    border-radius:8px;margin:5px 0;font-size:13px;
}
.sched-badge{
    display:inline-block;background:rgba(21,101,192,0.25);
    border:1px solid #1565C0;border-radius:6px;
    padding:2px 9px;font-size:11px;color:#90CAF9;
    font-weight:700;margin:1px 2px;
}
.cam-stat{
    background:rgba(46,125,50,0.15);border:1px solid #388e3c;
    border-radius:10px;padding:10px 14px;margin:5px 0;
    color:#a5d6a7;font-size:13px;
}
.drive-badge{
    background:rgba(46,125,50,0.2);border:1px solid #4CAF50;
    border-radius:8px;padding:6px 10px;color:#a5d6a7;
    font-size:11px;margin-top:8px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA FUNCTIONS
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
        st.error(f"Database Error: {e}")
        return None

@st.cache_data(ttl=30)
def get_latest_readings():
    """Most recent row per plant_id."""
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
def get_latest_single_image() -> str:
    """
    Returns the single most recently uploaded image URL across ALL plants.
    Converts to thumbnail format so st.image() renders it correctly.
    """
    if sheet is None:
        return ""
    try:
        df = pd.DataFrame(sheet.get_all_records())
        if df.empty or 'image_url' not in df.columns:
            return ""
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp', ascending=False)
        for _, row in df.iterrows():
            raw = str(row.get('image_url', '')).strip()
            if raw.startswith("http"):
                return gdrive_thumbnail(raw, size="w1200")
        return ""
    except Exception:
        return ""

@st.cache_data(ttl=30)
def get_latest_image_per_plant() -> dict:
    """Returns {plant_id: thumbnail_url} for all 10 plants."""
    result = {i: "" for i in range(1, 11)}
    if sheet is None:
        return result
    try:
        df = pd.DataFrame(sheet.get_all_records())
        if df.empty or 'image_url' not in df.columns:
            return result
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp', ascending=False)
        for pid in range(1, 11):
            for _, row in df[df['plant_id'] == pid].iterrows():
                raw = str(row.get('image_url', '')).strip()
                if raw.startswith("http"):
                    result[pid] = gdrive_thumbnail(raw, size="w600")
                    break
    except Exception:
        pass
    return result

# ============================================================
# SIDEBAR
# ============================================================
sheet     = get_sheet()
logo_b64  = file_to_b64(ACTUAL_LOGO)
role_icon = "👑 " if st.session_state.role == "admin" else "🌿 "
role_lbl  = "Administrator" if st.session_state.role == "admin" else "Field User"

with st.sidebar:
    st.markdown(f"""
    <div style="display:flex;flex-direction:column;align-items:center;
                padding-top:28px;margin-bottom:4px;width:100%;">
        <div style="padding:3px;border-radius:50%;
                    background:linear-gradient(135deg,#4CAF50,#1b5e20);
                    box-shadow:0 0 18px rgba(76,175,80,0.4);margin-bottom:12px;">
            <img src="data:image/png;base64,{logo_b64}"
                 style="border-radius:50%;display:block;width:115px;height:115px;
                        object-fit:cover;background:#0E1117;"/>
        </div>
        <div style="text-align:center;font-size:20px;font-weight:800;
                    color:#4CAF50;margin-bottom:2px;">AgriBot-AI</div>
        <div style="text-align:center;font-size:10px;color:#66bb6a;
                    letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;">
            Crop Monitoring System</div>
        <div style="font-size:9px;font-weight:700;letter-spacing:1.5px;
                    text-transform:uppercase;padding:3px 10px;border-radius:20px;
                    background:rgba(76,175,80,0.12);border:1px solid #2e7d32;
                    color:#81c784;margin-top:2px;">{role_icon}{role_lbl}</div>
    </div>
    <div style="width:60%;height:2px;background:linear-gradient(90deg,transparent,
                #4CAF50,transparent);border-radius:2px;margin:14px auto 16px auto;"></div>
    <div style="font-size:9px;font-weight:700;color:#388e3c;letter-spacing:2.5px;
                text-transform:uppercase;width:100%;padding:0 2px;margin-bottom:6px;">
        Navigation</div>
    """, unsafe_allow_html=True)

    # ── Navigation — Camera Feed removed ─────────────────────
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
    <div style="display:flex;align-items:center;gap:8px;background:rgba(46,125,50,0.18);
                border:1px solid #2e7d32;border-radius:8px;padding:9px 14px;
                width:100%;margin-top:14px;margin-bottom:8px;box-sizing:border-box;">
        <div style="width:8px;height:8px;background:#4CAF50;border-radius:50%;
                    box-shadow:0 0 6px #4CAF50;animation:pulse 2s infinite;
                    flex-shrink:0;"></div>
        <span style="font-size:11px;font-weight:700;color:#81c784;
                     letter-spacing:1.5px;text-transform:uppercase;">SYSTEM ONLINE</span>
    </div>
    <style>
    @keyframes pulse{
        0%,100%{opacity:1;box-shadow:0 0 5px #4CAF50;}
        50%{opacity:0.6;box-shadow:0 0 14px #4CAF50;}
    }
    </style>""", unsafe_allow_html=True)

    if st.button("⏻  Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.role      = None
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

def health_status(soil, ph):
    if ph < PH_LOW or ph > PH_HIGH:  return "🔴 pH Alert", "#f44336"
    if soil < SOIL_DRY:              return "⚠️ Too Dry",  "#FF9800"
    if soil > SOIL_WET:              return "⚠️ Too Wet",  "#FF9800"
    return                                  "✅ Healthy",   "#4CAF50"

def sensor_status_class(val, low, high):
    return "sensor-status-ok" if low <= val <= high else "sensor-status-warn"

# ==============================================================
# PAGE: LIVE DASHBOARD
# Layout (matches wireframe):
#   ┌─────────────────────────┬──────────────┐
#   │  Latest Camera Image    │  Soil        │
#   │  (big, left)            │  Humidity    │
#   │                         │  Temp        │
#   │                         │  pH          │
#   ├─────────────────────────┴──────────────┤
#   │  AI Recommendation  │  Recent Alerts   │
#   └─────────────────────────────────────────┘
# ==============================================================
if page == "DASHBOARD":
    st.title("Real-Time Monitoring – 10 Lettuces")

    if latest.empty:
        st.warning("No data yet — waiting for sensor readings from the Pi...")
        st.stop()

    # Aggregate sensor values across all plants
    avg_temp = float(latest['temp_c'].mean())
    avg_hum  = float(latest['humidity'].mean())
    avg_ph   = float(latest['ph'].mean())
    avg_soil = float(latest['soil_moisture'].mean())

    # ── Fetch the single latest captured image ─────────────────
    with st.spinner("Loading latest image..."):
        latest_img_url = get_latest_single_image()

    # Find which plant + timestamp corresponds to that image
    latest_img_plant = ""
    latest_img_ts    = ""
    if not latest.empty and latest_img_url:
        try:
            df_all = pd.DataFrame(sheet.get_all_records())
            df_all['timestamp'] = pd.to_datetime(df_all['timestamp'])
            df_all = df_all.sort_values('timestamp', ascending=False)
            for _, row in df_all.iterrows():
                if str(row.get('image_url', '')).startswith("http"):
                    latest_img_plant = int(row['plant_id'])
                    latest_img_ts    = row['timestamp'].strftime("%b %d %Y · %I:%M %p")
                    break
        except Exception:
            pass

    st.markdown("---")

    # ══════════════════════════════════════════════════════════
    # TOP ROW:  Camera (left 3/5)  |  Sensor metrics (right 2/5)
    # ══════════════════════════════════════════════════════════
    cam_col, sensor_col = st.columns([3, 2], gap="large")

    with cam_col:
        st.markdown('<div class="cam-frame">', unsafe_allow_html=True)
        st.markdown(
            '<div class="cam-frame-title">📷 Latest Captured Image</div>',
            unsafe_allow_html=True)

        if latest_img_url:
            st.image(latest_img_url, use_container_width=True)
            caption_parts = []
            if latest_img_plant:
                caption_parts.append(f"🥬 Plant {latest_img_plant}")
            if latest_img_ts:
                caption_parts.append(f"🕒 {latest_img_ts}")
            caption_parts.append("Captured at "
                "<span class='sched-badge'>7:00 AM</span>"
                "<span class='sched-badge'>12:00 NN</span>"
                "<span class='sched-badge'>12:30 PM</span>")
            st.markdown(
                f'<div style="margin-top:8px;font-size:12px;color:#81c784;">'
                f'{" &nbsp;|&nbsp; ".join(caption_parts)}</div>',
                unsafe_allow_html=True)
            if latest_img_url:
                st.markdown(
                    f'<div class="drive-badge">☁️ Stored in Google Drive &nbsp;|&nbsp; '
                    f'<a href="{latest_img_url}" target="_blank" style="color:#81c784;">'
                    f'View full image ↗</a></div>',
                    unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="cam-no-image">'
                '<div style="font-size:52px;margin-bottom:14px;">📷</div>'
                '<div style="font-size:15px;font-weight:700;color:#4CAF50;margin-bottom:6px;">'
                'No image captured yet</div>'
                '<div style="font-size:12px;color:#388e3c;">'
                'Pi captures at '
                '<span class="sched-badge">7:00 AM</span>'
                '<span class="sched-badge">12:00 NN</span>'
                '<span class="sched-badge">12:30 PM</span></div>'
                '</div>',
                unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with sensor_col:
        # ── Soil Moisture ──────────────────────────────────────
        soil_status = "✅ Normal" if SOIL_DRY <= avg_soil <= SOIL_WET else "⚠️ Out of range"
        soil_cls    = "sensor-status-ok" if SOIL_DRY <= avg_soil <= SOIL_WET else "sensor-status-warn"
        st.markdown(
            f'<div class="sensor-card">'
            f'<div class="sensor-label">🌱 Soil Moisture (avg)</div>'
            f'<div class="sensor-value">{avg_soil:.0f}'
            f'<span class="sensor-unit">%</span></div>'
            f'<div class="{soil_cls}">{soil_status}</div>'
            f'</div>', unsafe_allow_html=True)

        # ── Humidity ──────────────────────────────────────────
        hum_status = "✅ Normal" if HUM_LOW <= avg_hum <= HUM_HIGH else "⚠️ Out of range"
        hum_cls    = "sensor-status-ok" if HUM_LOW <= avg_hum <= HUM_HIGH else "sensor-status-warn"
        st.markdown(
            f'<div class="sensor-card">'
            f'<div class="sensor-label">💧 Humidity</div>'
            f'<div class="sensor-value">{avg_hum:.0f}'
            f'<span class="sensor-unit">%</span></div>'
            f'<div class="{hum_cls}">{hum_status}</div>'
            f'</div>', unsafe_allow_html=True)

        # ── Temperature ───────────────────────────────────────
        temp_status = "✅ Normal" if TEMP_LOW <= avg_temp <= TEMP_HIGH else "⚠️ Out of range"
        temp_cls    = "sensor-status-ok" if TEMP_LOW <= avg_temp <= TEMP_HIGH else "sensor-status-warn"
        st.markdown(
            f'<div class="sensor-card">'
            f'<div class="sensor-label">🌡️ Temperature</div>'
            f'<div class="sensor-value">{avg_temp:.1f}'
            f'<span class="sensor-unit">°C</span></div>'
            f'<div class="{temp_cls}">{temp_status}</div>'
            f'</div>', unsafe_allow_html=True)

        # ── pH ────────────────────────────────────────────────
        ph_status = "✅ Normal" if PH_LOW <= avg_ph <= PH_HIGH else "🔴 Out of range"
        ph_cls    = "sensor-status-ok" if PH_LOW <= avg_ph <= PH_HIGH else "sensor-status-bad"
        st.markdown(
            f'<div class="sensor-card">'
            f'<div class="sensor-label">🧪 pH</div>'
            f'<div class="sensor-value">{avg_ph:.2f}'
            f'<span class="sensor-unit">pH</span></div>'
            f'<div class="{ph_cls}">{ph_status}</div>'
            f'</div>', unsafe_allow_html=True)

        # ── Last updated timestamp ─────────────────────────────
        if not latest.empty and 'timestamp' in latest.columns:
            last_ts = pd.to_datetime(latest['timestamp']).max()
            st.markdown(
                f'<div style="text-align:center;font-size:11px;color:#4CAF50;'
                f'margin-top:6px;">🔄 Last updated: {last_ts.strftime("%H:%M:%S")}</div>',
                unsafe_allow_html=True)

    st.markdown("---")

    # ══════════════════════════════════════════════════════════
    # BOTTOM ROW:  AI Recommendation  |  Recent Alerts
    # ══════════════════════════════════════════════════════════
    ai_col, alert_col = st.columns(2, gap="large")

    with ai_col:
        st.subheader("🤖 AI Health Recommendation")
        p1 = latest[latest['plant_id'] == 1]
        if not p1.empty and model and scaler:
            try:
                feat = np.array([[float(p1.iloc[0]['temp_c']),
                                  float(p1.iloc[0]['humidity']),
                                  float(p1.iloc[0]['ph'])]])
                pred = model.predict(scaler.transform(feat))[0]
                if pred == -1:
                    st.error("### 🚨 ALERT\nAnomalous conditions detected.")
                else:
                    st.success("### ✅ HEALTHY\nCrop environment is optimal.")
            except Exception as e:
                st.info(f"AI processing... ({e})")
        else:
            st.warning("Awaiting sensor data or AI model...")

    with alert_col:
        st.subheader("🔔 Recent Alerts")
        alerts = []
        for _, plant in latest.iterrows():
            pid  = int(plant['plant_id'])
            soil = float(plant['soil_moisture'])
            ph   = float(plant['ph'])
            if soil < SOIL_DRY or soil > SOIL_WET:
                alerts.append(f"🌱 Plant {pid} soil: {soil:.0f}%")
            if ph < PH_LOW or ph > PH_HIGH:
                alerts.append(f"🧪 Plant {pid} pH: {ph:.2f}")
        if avg_temp < TEMP_LOW or avg_temp > TEMP_HIGH:
            alerts.append(f"🌡️ Temp: {avg_temp:.1f}°C out of range")
        if avg_hum < HUM_LOW or avg_hum > HUM_HIGH:
            alerts.append(f"💧 Humidity: {avg_hum:.0f}% out of range")
        if alerts:
            for a in alerts[:6]:
                st.markdown(
                    f'<div class="alert-item">{a}</div>',
                    unsafe_allow_html=True)
        else:
            st.success("✅ All parameters within range.")

# ==============================================================
# PAGE: ANALYSIS
# ==============================================================
elif page == "ANALYSIS":
    st.title("Historical Trends – Individual Sensors")
    if not latest.empty:
        sc1, sc2, sc3 = st.columns([1, 1, 2])
        with sc1:
            sensor_choice = st.selectbox("Sensor", [
                "Temperature (°C)", "Humidity (%)", "pH", "Soil Moisture (%)"])
        with sc2:
            plant_sel = st.selectbox("Plant", list(range(1, 11)))
        with sc3:
            time_range = st.selectbox("Time range", ["24 hours", "7 days", "30 days"])
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
            fig.update_layout(yaxis_title=y_label,
                              paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(14,17,23,0.8)',
                              font_color='#a5d6a7')
            st.plotly_chart(fig, use_container_width=True)

            if sensor_choice == "Soil Moisture (%)" and not latest.empty:
                st.subheader("🌱 Soil Moisture — All 10 Plants (current)")
                bar = px.bar(latest.sort_values('plant_id'),
                             x='plant_id', y='soil_moisture',
                             color='soil_moisture', color_continuous_scale='Greens',
                             labels={'plant_id': 'Plant', 'soil_moisture': 'Soil %'})
                bar.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                                  plot_bgcolor='rgba(14,17,23,0.8)',
                                  font_color='#a5d6a7')
                st.plotly_chart(bar, use_container_width=True)
        else:
            st.warning("No historical data for this plant yet.")
    else:
        st.warning("No data available.")

# ==============================================================
# PAGE: SYSTEM LOGS
# ==============================================================
elif page == "LOGS":
    st.title("System Activity Logs")
    logs = get_historical_data(plant_id=None, hours=24)
    if not logs.empty:
        def classify(row):
            if row['temp_c'] < TEMP_LOW or row['temp_c'] > TEMP_HIGH:
                return "🌡️ Temp alert"
            if row['humidity'] < HUM_LOW or row['humidity'] > HUM_HIGH:
                return "💧 Humidity alert"
            if row['ph'] < PH_LOW or row['ph'] > PH_HIGH:
                return "🧪 pH alert"
            if row['soil_moisture'] < SOIL_DRY or row['soil_moisture'] > SOIL_WET:
                return "🌱 Soil alert"
            return "Normal"
        logs['event'] = logs.apply(classify, axis=1)
        display_cols = ['timestamp','plant_id','temp_c','humidity','soil_moisture','ph','event']
        col_cfg = {
            "timestamp": "Time", "plant_id": "Plant", "temp_c": "Temp (°C)",
            "humidity": "Hum (%)", "soil_moisture": "Soil %", "ph": "pH", "event": "Event"
        }
        if 'image_url' in logs.columns:
            display_cols.insert(-1, 'image_url')
            col_cfg['image_url'] = st.column_config.LinkColumn("📸 Image")
        st.dataframe(logs[display_cols].tail(50), use_container_width=True,
                     hide_index=True, column_config=col_cfg)
    else:
        st.info("No logs available.")

# ==============================================================
# PAGE: USER MANAGEMENT
# ==============================================================
elif page == "USERS":
    st.title("Admin Control Panel")
    st.subheader("Registered Users")
    st.table(pd.DataFrame({
        "Username": ["admin@agribot.ai", "user@agribot.ai"],
        "Role":     ["Administrator",    "Standard User"]
    }))
    st.info("Future feature: add / remove users via database.")

# ============================================================
# AUTO-REFRESH every 30 s
# ============================================================
time.sleep(30)
st.rerun()