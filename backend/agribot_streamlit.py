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

    # Inject CSS separately (no f-string needed — no dynamic values)
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

    # Inject header HTML separately (f-string only for logo_html — no CSS braces conflict)
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
# GLOBAL CSS
# ============================================================
st.markdown("""<style>
/* ── Core layout ─────────────────────────────────────────── */
[data-testid="stHeader"]{background:transparent!important;}
#MainMenu{visibility:hidden;}footer{visibility:hidden;}
[data-testid="stDecoration"]{display:none;}

/* ── Sidebar ─────────────────────────────────────────────── */
section[data-testid="stSidebar"]{
    width:260px!important;
    background:linear-gradient(180deg,#0a0d12 0%,#0d1117 100%)!important;
    border-right:1px solid rgba(46,125,50,0.5)!important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{
    display:flex!important;flex-direction:column!important;
    align-items:center!important;padding:0 16px 28px!important;
}
[data-testid="stSidebar"] [data-testid="stElementToolbar"]{display:none!important;}

/* ── Sidebar nav radio ───────────────────────────────────── */
.stRadio>div{gap:4px!important;width:100%!important;flex-direction:column!important;}
.stRadio label{
    font-size:12px!important;font-weight:700!important;
    color:#81c784!important;letter-spacing:1px!important;
    text-transform:uppercase!important;
    background:transparent!important;
    border:none!important;border-radius:8px!important;
    padding:10px 14px!important;width:100%!important;
    cursor:pointer!important;transition:all 0.2s!important;
}
.stRadio label:hover{
    background:rgba(76,175,80,0.12)!important;
    color:#fff!important;
}
div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked){
    background:rgba(46,125,50,0.22)!important;
    border-left:3px solid #4CAF50!important;
    color:#fff!important;padding-left:11px!important;
}
.stRadio [data-baseweb="radio"]>div:first-child{display:none!important;}
.stRadio [data-testid="stMarkdownContainer"] p{margin:0!important;}

/* ── Sidebar button (logout) ─────────────────────────────── */
[data-testid="stSidebar"] .stButton>button{
    background:rgba(46,125,50,0.12)!important;
    border:1px solid rgba(76,175,80,0.3)!important;
    color:#81c784!important;border-radius:10px!important;
    width:100%!important;font-size:12px!important;
    font-weight:700!important;letter-spacing:1px!important;
    text-transform:uppercase!important;padding:10px!important;
    transition:all 0.2s!important;
}
[data-testid="stSidebar"] .stButton>button:hover{
    background:rgba(198,40,40,0.15)!important;
    border-color:rgba(198,40,40,0.5)!important;
    color:#ef9a9a!important;
}

/* ── Metric cards ────────────────────────────────────────── */
div[data-testid="stMetric"]{
    background:rgba(13,17,23,0.85)!important;
    border:1px solid rgba(76,175,80,0.3)!important;
    border-radius:16px!important;padding:20px 16px!important;
    text-align:center!important;
}
div[data-testid="stMetricLabel"]{
    font-weight:700!important;font-size:11px!important;
    color:#66bb6a!important;letter-spacing:2px!important;
    text-transform:uppercase!important;justify-content:center!important;
}
div[data-testid="stMetricValue"]{
    font-size:34px!important;font-weight:900!important;
    color:#ffffff!important;margin-top:4px!important;
}

/* ── Custom cards ────────────────────────────────────────── */
.cam-card{
    background:rgba(13,17,23,0.9);
    border:1px solid rgba(46,125,50,0.4);
    border-radius:18px;padding:20px;
}
.sensor-row{
    background:rgba(13,17,23,0.85);
    border:1px solid rgba(46,125,50,0.25);
    border-radius:14px;padding:16px 18px;
    margin-bottom:10px;display:flex;
    align-items:center;justify-content:space-between;
}
.s-label{font-size:11px;font-weight:700;color:#66bb6a;
    text-transform:uppercase;letter-spacing:1.5px;margin-bottom:3px;}
.s-val{font-size:26px;font-weight:900;color:#fff;line-height:1;}
.s-unit{font-size:13px;color:#a5d6a7;margin-left:2px;}
.s-ok  {font-size:11px;color:#4CAF50;margin-top:3px;}
.s-warn{font-size:11px;color:#FF9800;margin-top:3px;}
.s-bad {font-size:11px;color:#f44336;margin-top:3px;}
.s-icon{font-size:26px;opacity:0.6;}

.section-title{
    font-size:13px;font-weight:700;color:#66bb6a;
    letter-spacing:2px;text-transform:uppercase;
    margin-bottom:14px;margin-top:2px;
    border-left:3px solid #4CAF50;padding-left:10px;
}
.alert-item{
    padding:9px 14px;background:rgba(183,28,28,0.12);
    border:1px solid rgba(183,28,28,0.3);
    color:#ef9a9a;border-radius:10px;margin:5px 0;font-size:13px;
}
.sched-badge{
    display:inline-block;background:rgba(21,101,192,0.2);
    border:1px solid rgba(21,101,192,0.5);border-radius:6px;
    padding:2px 9px;font-size:11px;color:#90CAF9;
    font-weight:700;margin:0 2px;
}
.cam-meta{font-size:11px;color:#66bb6a;margin-top:8px;line-height:1.7;}
.drive-link{
    display:inline-block;margin-top:10px;
    background:rgba(46,125,50,0.15);
    border:1px solid rgba(76,175,80,0.3);
    border-radius:8px;padding:6px 12px;
    color:#81c784;font-size:12px;text-decoration:none;
}
.cam-placeholder{
    display:flex;flex-direction:column;align-items:center;
    justify-content:center;min-height:340px;
    background:rgba(46,125,50,0.04);
    border:2px dashed rgba(46,125,50,0.3);
    border-radius:14px;text-align:center;padding:40px;
}
</style>""", unsafe_allow_html=True)

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
# SIDEBAR
# ============================================================
sheet    = get_sheet()
logo_b64 = file_to_b64(ACTUAL_LOGO)

with st.sidebar:
    # Logo + branding
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

    # System online indicator
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
        <div style="font-size:26px;font-weight:900;color:#ffffff;
                    letter-spacing:0.3px;line-height:1.2;">
            Real-Time Monitoring</div>
        <div style="font-size:13px;color:#66bb6a;letter-spacing:1px;margin-top:4px;">
            Greenhouse Overview — AgriBot-AI Crop System</div>
    </div>""", unsafe_allow_html=True)

    if latest.empty:
        st.warning("No sensor data yet — waiting for the Pi...")
        st.stop()

    # Aggregate across all plants (greenhouse-level view)
    avg_temp = float(latest['temp_c'].mean())
    avg_hum  = float(latest['humidity'].mean())
    avg_ph   = float(latest['ph'].mean())
    avg_soil = float(latest['soil_moisture'].mean())

    # ── 4 summary metric cards ─────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TEMP",     f"{avg_temp:.1f} °C")
    m2.metric("HUMIDITY", f"{avg_hum:.0f} %")
    m3.metric("PH",       f"{avg_ph:.2f}")
    m4.metric("SOIL",     f"{avg_soil:.0f} %")

    st.markdown("<div style='margin:18px 0 6px;'></div>", unsafe_allow_html=True)

    # ── Latest image (load once) ────────────────────────────────
    with st.spinner("Loading latest capture..."):
        img_data = get_latest_image()

    # ══════════════════════════════════════════════════════════
    # MAIN ROW: Camera image (left) | Sensor details (right)
    # ══════════════════════════════════════════════════════════
    cam_col, sensor_col = st.columns([3, 2], gap="large")

    # ── LEFT: latest captured image ───────────────────────────
    with cam_col:
        st.markdown('<div class="cam-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📷 Plant Health Feed</div>',
                    unsafe_allow_html=True)

        if img_data.get("url"):
            st.image(img_data["url"], use_container_width=True)
            pid_txt = f"🥬 Plant {img_data['plant_id']}" if img_data.get("plant_id") else ""
            ts_txt  = f"🕒 {img_data['timestamp']}"       if img_data.get("timestamp") else ""
            st.markdown(
                f'<div class="cam-meta">'
                f'{pid_txt}&nbsp;&nbsp;{ts_txt}<br>'
                f'Captured at '
                f'<span class="sched-badge">7:00 AM</span>'
                f'<span class="sched-badge">12:00 NN</span>'
                f'<span class="sched-badge">12:30 PM</span>'
                f'</div>'
                f'<a href="{img_data["url"]}" target="_blank" class="drive-link">'
                f'☁️ View in Google Drive ↗</a>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="cam-placeholder">'
                '<div style="font-size:54px;margin-bottom:16px;">📷</div>'
                '<div style="font-size:15px;font-weight:700;color:#4CAF50;">No image yet</div>'
                '<div style="font-size:12px;color:#2e7d32;margin-top:8px;">'
                'Pi captures at '
                '<span class="sched-badge">7:00 AM</span>'
                '<span class="sched-badge">12:00 NN</span>'
                '<span class="sched-badge">12:30 PM</span></div>'
                '</div>',
                unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── RIGHT: AI recommendation + Alerts ────────────────────
    with sensor_col:
        # Last updated timestamp
        if not latest.empty:
            last_ts = pd.to_datetime(latest['timestamp']).max()
            st.markdown(
                f'<div style="text-align:right;font-size:11px;color:#388e3c;'
                f'margin-bottom:12px;">🔄 Updated {last_ts.strftime("%H:%M:%S")}</div>',
                unsafe_allow_html=True)

        # AI Recommendation
        st.markdown('<div class="section-title">🤖 AI Health Recommendation</div>',
                    unsafe_allow_html=True)
        p1 = latest[latest['plant_id'] == 1]
        if not p1.empty and model and scaler:
            try:
                feat = np.array([[float(p1.iloc[0]['temp_c']),
                                  float(p1.iloc[0]['humidity']),
                                  float(p1.iloc[0]['ph'])]])
                pred = model.predict(scaler.transform(feat))[0]
                if pred == -1:
                    st.error("🚨 **ALERT** — Anomalous conditions detected in the greenhouse.")
                else:
                    st.success("✅ **HEALTHY** — Crop environment is optimal.")
            except Exception as e:
                st.info(f"AI model processing... ({e})")
        else:
            st.warning("Awaiting sensor data or AI model...")

        st.markdown("<div style='margin:14px 0 4px;'></div>", unsafe_allow_html=True)

        # Recent Alerts
        st.markdown('<div class="section-title">🔔 Recent Alerts</div>',
                    unsafe_allow_html=True)
        alerts = []
        for _, plant in latest.iterrows():
            pid  = int(plant['plant_id'])
            soil = float(plant['soil_moisture'])
            ph   = float(plant['ph'])
            if soil < SOIL_DRY:
                alerts.append(f"🌱 Plant {pid}: soil too dry ({soil:.0f}%)")
            elif soil > SOIL_WET:
                alerts.append(f"🌱 Plant {pid}: soil too wet ({soil:.0f}%)")
            if ph < PH_LOW or ph > PH_HIGH:
                alerts.append(f"🧪 Plant {pid}: pH out of range ({ph:.2f})")
        if avg_temp < TEMP_LOW or avg_temp > TEMP_HIGH:
            alerts.append(f"🌡️ Temperature: {avg_temp:.1f}°C out of range")
        if avg_hum < HUM_LOW or avg_hum > HUM_HIGH:
            alerts.append(f"💧 Humidity: {avg_hum:.0f}% out of range")

        if alerts:
            for a in alerts[:6]:
                st.markdown(f'<div class="alert-item">{a}</div>', unsafe_allow_html=True)
        else:
            st.success("✅ All greenhouse parameters are within range.")

# ==============================================================
# PAGE: ANALYSIS
# ==============================================================
elif page == "ANALYSIS":
    st.markdown("""
    <div style="margin-bottom:18px;">
        <div style="font-size:24px;font-weight:900;color:#fff;">Historical Trends</div>
        <div style="font-size:13px;color:#66bb6a;letter-spacing:1px;margin-top:4px;">
            Sensor data over time — per plant</div>
    </div>""", unsafe_allow_html=True)

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
                "Temperature (°C)": ("temp_c",       "°C"),
                "Humidity (%)":     ("humidity",      "%"),
                "pH":               ("ph",            "pH"),
                "Soil Moisture (%)":("soil_moisture", "%"),
            }
            y_col, y_label = col_map[sensor_choice]
            fig = px.line(hist_df, x='timestamp', y=y_col,
                          title=f"{sensor_choice} — Plant {plant_sel}")
            fig.update_layout(yaxis_title=y_label,
                              paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(13,17,23,0.85)',
                              font_color='#a5d6a7',
                              title_font_color='#ffffff')
            st.plotly_chart(fig, use_container_width=True)

            if sensor_choice == "Soil Moisture (%)":
                st.markdown('<div class="section-title">🌱 Current Soil — All Plants</div>',
                            unsafe_allow_html=True)
                bar = px.bar(latest.sort_values('plant_id'),
                             x='plant_id', y='soil_moisture',
                             color='soil_moisture', color_continuous_scale='Greens',
                             labels={'plant_id': 'Plant', 'soil_moisture': 'Soil %'})
                bar.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                                  plot_bgcolor='rgba(13,17,23,0.85)',
                                  font_color='#a5d6a7')
                st.plotly_chart(bar, use_container_width=True)
        else:
            st.warning("No data for this plant in the selected time range.")
    else:
        st.warning("No data available yet.")

# ==============================================================
# PAGE: SYSTEM LOGS
# ==============================================================
elif page == "LOGS":
    st.markdown("""
    <div style="margin-bottom:18px;">
        <div style="font-size:24px;font-weight:900;color:#fff;">System Logs</div>
        <div style="font-size:13px;color:#66bb6a;letter-spacing:1px;margin-top:4px;">
            Last 24 hours of sensor activity</div>
    </div>""", unsafe_allow_html=True)

    logs = get_historical_data(plant_id=None, hours=24)
    if not logs.empty:
        def classify(r):
            if r['temp_c'] < TEMP_LOW or r['temp_c'] > TEMP_HIGH:       return "🌡️ Temp alert"
            if r['humidity'] < HUM_LOW or r['humidity'] > HUM_HIGH:     return "💧 Humidity alert"
            if r['ph'] < PH_LOW or r['ph'] > PH_HIGH:                   return "🧪 pH alert"
            if r['soil_moisture'] < SOIL_DRY or r['soil_moisture'] > SOIL_WET: return "🌱 Soil alert"
            return "Normal"
        logs['event'] = logs.apply(classify, axis=1)
        cols = ['timestamp', 'plant_id', 'temp_c', 'humidity', 'soil_moisture', 'ph', 'event']
        cfg  = {"timestamp": "Time", "plant_id": "Plant", "temp_c": "Temp (°C)",
                "humidity": "Hum (%)", "soil_moisture": "Soil %", "ph": "pH", "event": "Event"}
        if 'image_url' in logs.columns:
            cols.insert(-1, 'image_url')
            cfg['image_url'] = st.column_config.LinkColumn("📸 Image")
        st.dataframe(logs[cols].tail(50), use_container_width=True,
                     hide_index=True, column_config=cfg)
    else:
        st.info("No logs available.")

# ==============================================================
# PAGE: USER MANAGEMENT
# ==============================================================
elif page == "USERS":
    st.markdown("""
    <div style="margin-bottom:18px;">
        <div style="font-size:24px;font-weight:900;color:#fff;">Admin Control Panel</div>
        <div style="font-size:13px;color:#66bb6a;letter-spacing:1px;margin-top:4px;">
            Registered user accounts</div>
    </div>""", unsafe_allow_html=True)
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