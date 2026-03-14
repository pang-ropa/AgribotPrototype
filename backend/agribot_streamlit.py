import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
import base64
import subprocess
import time
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

# --- Try importing picamera2 (only works on Pi) ---
try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False

# ============================================
# PAGE CONFIG
# ============================================
LOGO_PATH    = r"C:\Users\admin\Downloads\AgribotPrototype\backend\agribotailogo.png"
PI_LOGO_PATH = os.path.expanduser("~/env/Thesis code/backend/agribotailogologo.png")
ACTUAL_LOGO  = PI_LOGO_PATH if os.path.exists(PI_LOGO_PATH) else (LOGO_PATH if os.path.exists(LOGO_PATH) else "")

# Google Sheets config
CREDENTIALS_FILE = os.path.expanduser("~/env/Thesis code/credentials.json")
SPREADSHEET_ID   = "1mYScsUkoZn84FIoO_QMaku3gZT3Z9df72kPE3ray9-A"

# Camera capture config (local snapshots from dashboard)
SAVE_DIR      = os.path.expanduser("~/captures")
GDRIVE_FOLDER = "gdrive:AgriBot/captures"
os.makedirs(SAVE_DIR, exist_ok=True)

st.set_page_config(
    page_title="AgriBot-AI | Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# BACKGROUND IMAGE
# ============================================
def set_background(image_file):
    if not os.path.exists(image_file):
        return
    ext  = os.path.splitext(image_file)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:{mime};base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.45);
            z-index: 0;
            pointer-events: none;
        }}
        </style>""", unsafe_allow_html=True)

# ============================================
# LOGIN SYSTEM
# ============================================
users = {
    "admin@agribot.ai": {"password": "admin123", "role": "admin"},
    "user@agribot.ai":  {"password": "user123",  "role": "user"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

def login():
    bg_path = r"C:\Users\admin\Downloads\AgribotPrototype\backend\background.jpg"
    pi_bg   = os.path.expanduser("~/env/Thesis code/backend/background.jpg")
    bg      = pi_bg if os.path.exists(pi_bg) else bg_path
    set_background(bg)

    logo_html = ""
    if ACTUAL_LOGO:
        with open(ACTUAL_LOGO, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        logo_html = f'''<div style="display:flex;justify-content:center;margin-bottom:15px;">
            <img src="data:image/png;base64,{logo_b64}"
            style="width:130px;height:130px;border-radius:50%;
                   border:3px solid #4CAF50;object-fit:cover;" /></div>'''

    st.markdown(f"""
    <style>
    #MainMenu {{visibility:hidden;}} footer {{visibility:hidden;}}
    [data-testid="stForm"] {{
        background: linear-gradient(160deg,rgba(56,142,60,0.55) 0%,rgba(76,175,80,0.45) 50%,rgba(129,199,132,0.40) 100%) !important;
        backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
        border-radius: 18px; border: 1px solid rgba(165,214,167,0.5);
        box-shadow: 0 8px 32px rgba(0,0,0,0.25); padding: 30px 40px 40px 40px;
    }}
    [data-testid="stForm"] input {{
        background: rgba(255,255,255,0.12) !important; color: white !important;
        border: 1px solid rgba(165,214,167,0.6) !important; border-radius: 10px !important;
    }}
    [data-testid="stForm"] input::placeholder {{ color: rgba(220,240,220,0.7) !important; }}
    [data-testid="stForm"] button[kind="primaryFormSubmit"] {{
        background: linear-gradient(90deg,#388e3c,#66bb6a) !important;
        border: none !important; color: white !important; font-weight: 700 !important;
        border-radius: 10px !important; letter-spacing: 1px;
    }}
    .stTextInput label {{ color: #e8f5e9 !important; font-weight: 600 !important; }}
    .login-title {{ text-align:center;font-size:42px;font-weight:800;color:white;
        text-shadow:0 2px 8px rgba(0,0,0,0.5);margin-bottom:4px; }}
    .login-tagline {{ text-align:center;color:#a5d6a7;margin-bottom:20px;font-size:15px; }}
    </style>
    <div style="display:flex;flex-direction:column;align-items:center;margin-top:60px;">
        {logo_html}
        <div class="login-title">AgriBot-AI</div>
        <div class="login-tagline">Smart Farming · Intelligent Monitoring</div>
    </div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_form"):
            email    = st.text_input("Email", placeholder="admin@agribot.ai or user@agribot.ai")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                if email in users and users[email]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.role = users[email]["role"]
                    st.success("Login Successful")
                    st.rerun()
                else:
                    st.error("Invalid email or password")

if not st.session_state.logged_in:
    login()
    st.stop()

# ============================================
# GLOBAL CSS
# ============================================
st.markdown("""
<style>
[data-testid="stHeader"] { background-color: transparent !important; }
button[kind="headerNoSpacing"] {
    visibility: visible !important; background-color: #2E7D32 !important;
    color: white !important; border-radius: 12px !important;
    padding: 10px 15px !important; top: 15px !important;
    left: 15px !important; z-index: 999999 !important;
}
section[data-testid="stSidebar"] {
    width: 280px !important; background-color: #0E1117 !important;
    border-right: 2px solid #2e7d32 !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    display: flex !important; flex-direction: column !important;
    align-items: center !important; padding: 0 14px 24px 14px !important;
}
[data-testid="stSidebar"] [data-testid="stElementToolbar"] { display: none !important; }
.sidebar-logo-wrap {
    display: flex; flex-direction: column; align-items: center;
    padding-top: 30px; margin-bottom: 4px; width: 100%;
}
.sidebar-logo-ring {
    padding: 3px; border-radius: 50%;
    background: linear-gradient(135deg,#4CAF50,#1b5e20);
    box-shadow: 0 0 16px rgba(76,175,80,0.35); margin-bottom: 12px;
}
.sidebar-logo-ring img {
    border-radius: 50%; display: block; width: 115px; height: 115px;
    object-fit: cover; background: #0E1117;
}
.sidebar-title { text-align:center;font-size:20px;font-weight:800;color:#4CAF50;margin-bottom:2px; }
.sidebar-tagline { text-align:center;font-size:10px;color:#66bb6a;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px; }
.sidebar-divider { width:60%;height:2px;background:linear-gradient(90deg,transparent,#4CAF50,transparent);border-radius:2px;margin:14px auto 18px auto; }
.sidebar-nav-label { font-size:9px;font-weight:700;color:#388e3c;letter-spacing:2.5px;text-transform:uppercase;width:100%;padding:0 2px;margin-bottom:6px; }
.stRadio > div { gap:5px !important; width:100% !important; flex-direction:column !important; }
.stRadio label {
    font-size:13px !important; font-weight:600 !important; color:#a5d6a7 !important;
    background:rgba(46,125,50,0.08) !important; border:1px solid rgba(76,175,80,0.18) !important;
    border-radius:8px !important; padding:10px 14px !important; width:100% !important;
    cursor:pointer !important; transition:all 0.15s ease !important;
}
.stRadio label:hover { background:rgba(76,175,80,0.18) !important; border-color:#4CAF50 !important; color:#ffffff !important; }
div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {
    background:rgba(46,125,50,0.35) !important; border:1px solid #4CAF50 !important;
    color:#ffffff !important; box-shadow:0 0 8px rgba(76,175,80,0.25) !important;
}
.stRadio [data-baseweb="radio"] > div:first-child { display:none !important; }
.stRadio [data-testid="stMarkdownContainer"] p { margin:0 !important; }
.sidebar-status {
    display:flex; align-items:center; gap:8px; background:rgba(46,125,50,0.18);
    border:1px solid #2e7d32; border-radius:8px; padding:9px 14px; width:100%;
    margin-top:14px; margin-bottom:8px; box-sizing:border-box;
}
.status-dot {
    width:8px; height:8px; background:#4CAF50; border-radius:50%;
    box-shadow:0 0 6px #4CAF50; animation:blink 2s ease-in-out infinite; flex-shrink:0;
}
@keyframes blink { 0%,100%{opacity:1;box-shadow:0 0 5px #4CAF50;} 50%{opacity:0.6;box-shadow:0 0 12px #4CAF50;} }
.status-text { font-size:11px; font-weight:700; color:#81c784; letter-spacing:1.5px; text-transform:uppercase; }
[data-testid="stSidebar"] .stButton > button {
    background:transparent !important; border:1px solid #2e7d32 !important;
    color:#81c784 !important; border-radius:8px !important; width:100% !important;
    font-size:13px !important; font-weight:600 !important; padding:9px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background:rgba(211,47,47,0.12) !important; border-color:#c62828 !important; color:#ef9a9a !important;
}
.role-badge {
    font-size:9px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase;
    padding:3px 10px; border-radius:20px; background:rgba(76,175,80,0.12);
    border:1px solid #2e7d32; color:#81c784; margin-top:4px;
}
div[data-testid="stMetric"] {
    background:rgba(46,125,50,0.15) !important; border:1px solid #4CAF50 !important;
    border-radius:15px !important; padding:15px !important; text-align:center !important;
}
div[data-testid="stMetricLabel"] { margin-top:10px !important; font-weight:bold !important; color:#A5D6A7 !important; justify-content:center !important; }
div[data-testid="stMetricValue"] { margin-top:-5px !important; font-size:32px !important; }
#MainMenu {visibility:hidden;} footer {visibility:hidden;}
[data-testid="stDecoration"] {display:none;}
.cam-card {
    background: rgba(14,17,23,0.85);
    border: 1px solid #2e7d32;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 14px;
}
.cam-stat {
    background: rgba(46,125,50,0.15);
    border: 1px solid #388e3c;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 6px 0;
    color: #a5d6a7;
    font-size: 13px;
}
.upload-badge-ok  { background:#1b5e20; color:#a5d6a7; border-radius:8px; padding:6px 12px; font-size:12px; font-weight:700; }
.upload-badge-err { background:#b71c1c; color:#ef9a9a; border-radius:8px; padding:6px 12px; font-size:12px; font-weight:700; }
.drive2-badge {
    background: rgba(46,125,50,0.2);
    border: 1px solid #4CAF50;
    border-radius: 8px;
    padding: 8px 12px;
    color: #a5d6a7;
    font-size: 12px;
    margin-top: 6px;
    word-break: break-all;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# DATA LOADING
# ============================================
@st.cache_resource
def load_assets():
    try:
        model  = joblib.load('backend/anomaly_model.pkl')
        scaler = joblib.load('backend/anomaly_scaler.pkl')
        return model, scaler
    except:
        return None, None

@st.cache_resource
def get_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
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
        client = gspread.authorize(creds)
        # Open by ID so sheet name changes don't break it
        return client.open_by_key(SPREADSHEET_ID).sheet1
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
    except:
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
    except:
        return pd.DataFrame()

# ============================================
# NEW: get latest Drive 2 image URL from Sheet
# ============================================
def get_latest_drive2_image_url():
    """
    Reads the image_url column from the Sheet (plant_id == 1 rows).
    Returns the most recent non-empty URL, or empty string.
    """
    if sheet is None:
        return ""
    try:
        df = pd.DataFrame(sheet.get_all_records())
        if df.empty or 'image_url' not in df.columns:
            return ""
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        plant1 = df[df['plant_id'] == 1].sort_values('timestamp', ascending=False)
        for _, row in plant1.iterrows():
            url = str(row.get('image_url', '')).strip()
            if url.startswith("http"):
                return url
        return ""
    except:
        return ""

# ============================================
# CAMERA HELPERS
# ============================================
@st.cache_resource
def get_camera():
    if not CAMERA_AVAILABLE:
        return None
    try:
        cam = Picamera2()
        cfg = cam.create_preview_configuration(
            main={"size": (1280, 720), "format": "RGB888"}
        )
        cam.configure(cfg)
        cam.start()
        time.sleep(1)
        return cam
    except Exception as e:
        st.error(f"Camera init error: {e}")
        return None

def capture_image(cam):
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"agribot_{ts}.jpg"
    filepath = os.path.join(SAVE_DIR, filename)
    frame    = cam.capture_array()
    Image.fromarray(frame).save(filepath)
    return filepath, filename

def upload_to_drive(filepath):
    try:
        r = subprocess.run(
            ["rclone", "copy", filepath, GDRIVE_FOLDER],
            capture_output=True, text=True, timeout=30
        )
        return r.returncode == 0, r.stderr
    except Exception as e:
        return False, str(e)

def upload_all_to_drive():
    try:
        r = subprocess.run(
            ["rclone", "copy", SAVE_DIR, GDRIVE_FOLDER],
            capture_output=True, text=True, timeout=60
        )
        return r.returncode == 0, r.stderr
    except Exception as e:
        return False, str(e)

def get_recent_files(n=8):
    try:
        files = sorted([f for f in os.listdir(SAVE_DIR) if f.endswith('.jpg')])
        return files[-n:]
    except:
        return []

# ============================================
# SIDEBAR
# ============================================
sheet = get_sheet()
with st.sidebar:
    logo_b64 = ""
    if ACTUAL_LOGO:
        with open(ACTUAL_LOGO, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()

    role_label = "Administrator" if st.session_state.role == "admin" else "Field User"
    st.markdown(f"""
    <div class="sidebar-logo-wrap">
        <div class="sidebar-logo-ring">
            <img src="data:image/png;base64,{logo_b64}" />
        </div>
        <div class="sidebar-title">AgriBot-AI</div>
        <div class="sidebar-tagline">Crop Monitoring System</div>
        <div style="margin-top:8px;">
            <span class="role-badge">{"👑 " if st.session_state.role=="admin" else "🌿 "}{role_label}</span>
        </div>
    </div>
    <div class="sidebar-divider"></div>
    <div class="sidebar-nav-label">Navigation</div>
    """, unsafe_allow_html=True)

    if st.session_state.role == "admin":
        page = st.radio("", ["📡  Live Dashboard","📷  Camera Feed","📈  Analysis","📜  System Logs","👥  User Management"], label_visibility="collapsed")
    else:
        page = st.radio("", ["📡  Live Dashboard","📷  Camera Feed","📈  Analysis"], label_visibility="collapsed")

    page_map = {
        "📡  Live Dashboard":  "📡 LIVE DASHBOARD",
        "📷  Camera Feed":     "📷 CAMERA FEED",
        "📈  Analysis":        "📈 ANALYSIS",
        "📜  System Logs":     "📜 SYSTEM LOGS",
        "👥  User Management": "👥 USER MANAGEMENT"
    }
    page = page_map.get(page, page)

    st.markdown("""
    <div class="sidebar-status">
        <div class="status-dot"></div>
        <span class="status-text">SYSTEM ONLINE</span>
    </div>""", unsafe_allow_html=True)

    if st.button("⏻  Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

# ============================================
# MAIN CONTENT
# ============================================
model, scaler = load_assets()
latest = get_latest_readings()

# ---- LIVE DASHBOARD ----
if page == "📡 LIVE DASHBOARD":
    st.title("Real-Time Monitoring – 10 Lettuces")
    if latest.empty:
        st.warning("No data yet. Waiting for sensor readings...")
        st.stop()

    avg_temp = latest['temp_c'].mean()
    avg_hum  = latest['humidity'].mean()
    avg_ph   = (latest['ph1'].mean() + latest['ph2'].mean()) / 2
    avg_soil = latest['soil_moisture'].mean()

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("🌡️ TEMP",      f"{avg_temp:.1f} °C")
    col2.metric("💧 HUMIDITY",  f"{avg_hum:.0f} %")
    col3.metric("🧪 pH (avg)",  f"{avg_ph:.2f}")
    col4.metric("🌱 SOIL (avg)",f"{avg_soil:.0f} %")
    st.markdown("---")

    col_l, col_r = st.columns([1.3,1], gap="large")

    with col_l:
        st.subheader("🌿 Plant Health Feed")
        latest_s = latest.sort_values('plant_id')
        row1 = st.columns(5)
        row2 = st.columns(5)
        for idx, (_, plant) in enumerate(latest_s.iterrows()):
            col = row1[idx] if idx < 5 else row2[idx-5]
            pid    = int(plant['plant_id'])
            soil   = plant['soil_moisture']
            ph_avg = (plant['ph1'] + plant['ph2']) / 2
            health = "✅ Healthy"
            if soil < 30:                        health = "⚠️ Dry"
            elif soil > 80:                      health = "⚠️ Wet"
            if ph_avg < 5.5 or ph_avg > 6.5:    health = "🔴 pH Alert"
            with col:
                st.markdown("<span style='font-size:2rem;'>🥬</span>", unsafe_allow_html=True)
                st.markdown(f"**Lettuce #{pid}**<br>{health}<br>Soil: {soil:.0f}%", unsafe_allow_html=True)

    with col_r:
        st.subheader("🤖 AI Health Recommendation")
        plant1 = latest[latest['plant_id'] == 1]
        if not plant1.empty and model and scaler:
            try:
                features = np.array([[float(plant1.iloc[0]['temp_c']),
                                      float(plant1.iloc[0]['humidity']),
                                      (float(plant1.iloc[0]['ph1'])+float(plant1.iloc[0]['ph2']))/2]])
                pred = model.predict(scaler.transform(features))[0]
                if pred == -1:
                    st.error("### 🚨 ALERT\nAnomalous conditions detected.")
                else:
                    st.success("### ✅ HEALTHY\nCrop environment is optimal.")
            except Exception as e:
                st.info(f"AI processing... ({e})")
        else:
            st.warning("Awaiting sensor data or AI model...")

        # ---- NEW: latest Drive 2 image from Sheet ----
        st.markdown("### 📸 Latest Lettuce Image")
        drive2_url = get_latest_drive2_image_url()
        if drive2_url:
            st.image(drive2_url,
                     caption="Latest capture — Plant 1 (from Drive 2)",
                     use_container_width=True)
            st.markdown(
                f'<div class="drive2-badge">☁️ Stored in Drive 2<br>'
                f'<a href="{drive2_url}" target="_blank" style="color:#81c784;">View in Drive</a></div>',
                unsafe_allow_html=True)
        else:
            st.info("No image yet. Pi script will upload on next 30s cycle.")
        # ---- END NEW ----

        st.markdown("### 🔔 Recent Alerts")
        alerts = []
        for _, plant in latest.iterrows():
            pid = int(plant['plant_id'])
            if plant['soil_moisture'] < 20 or plant['soil_moisture'] > 80:
                alerts.append(f"🌱 Plant {pid} soil: {plant['soil_moisture']:.0f}%")
            ap = (plant['ph1'] + plant['ph2']) / 2
            if ap < 5.5 or ap > 6.5:
                alerts.append(f"🧪 Plant {pid} pH: {ap:.2f}")
        if avg_temp < 15 or avg_temp > 30:
            alerts.append(f"🌡️ Temp out of range: {avg_temp:.1f}°C")
        if avg_hum < 50 or avg_hum > 85:
            alerts.append(f"💧 Humidity out of range: {avg_hum:.0f}%")
        if alerts:
            for alert in alerts[:5]:
                st.markdown(f'<div style="padding:5px;background:#ffebee;color:#b71c1c;border-radius:5px;margin:5px 0;">{alert}</div>', unsafe_allow_html=True)
        else:
            st.info("✅ All parameters within range.")

# ---- CAMERA FEED PAGE ----
elif page == "📷 CAMERA FEED":
    st.title("📷 AgriBot Camera — Live Feed & Capture")

    if not CAMERA_AVAILABLE:
        st.error("❌ picamera2 is not installed. Run: `sudo apt install -y python3-picamera2`")
        st.stop()

    cam = get_camera()
    if cam is None:
        st.error("❌ Camera not initialized. Check hardware connection and try rebooting.")
        st.code("rpicam-hello --list-cameras", language="bash")
        st.stop()

    col_feed, col_ctrl = st.columns([3, 1])

    with col_ctrl:
        st.markdown('<div class="cam-card">', unsafe_allow_html=True)
        st.markdown("### ⚙️ Controls")
        auto_upload      = st.toggle("☁️ Auto Upload to Drive", value=True)
        capture_interval = st.slider("Auto-capture every (sec)", 10, 300, 60)
        live_mode        = st.toggle("▶️ Live Feed", value=True)
        resolution       = st.selectbox("Resolution", ["1280x720", "1920x1080", "640x480"], index=0)
        st.markdown("---")
        do_capture    = st.button("📸 Capture Now",        use_container_width=True)
        do_upload_all = st.button("☁️ Upload All to Drive", use_container_width=True)
        do_stop       = st.button("⏹ Stop Feed",           use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ---- NEW: Drive 2 latest image in camera sidebar ----
        st.markdown('<div class="cam-card">', unsafe_allow_html=True)
        st.markdown("### 🖼️ Last Drive 2 Upload")
        drive2_url = get_latest_drive2_image_url()
        if drive2_url:
            st.image(drive2_url,
                     caption="Pi script — latest upload",
                     use_container_width=True)
            st.markdown(
                f'<div class="drive2-badge">☁️ From agribot_pi_final.py<br>'
                f'<a href="{drive2_url}" target="_blank" style="color:#81c784;">Open in Drive</a></div>',
                unsafe_allow_html=True)
        else:
            st.markdown("<div class='cam-stat'>No Drive 2 image yet</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        # ---- END NEW ----

        # Stats
        st.markdown('<div class="cam-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Stats")
        total_files = len(get_recent_files(999))
        st.markdown(f'<div class="cam-stat">📁 Local snapshots: <b>{total_files}</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="cam-stat">🕒 Interval: <b>{capture_interval}s</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="cam-stat">☁️ Auto-upload: <b>{"ON" if auto_upload else "OFF"}</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="cam-stat">📡 Pi uploads to Drive 2 every 30s</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Recent local captures
        st.markdown('<div class="cam-card">', unsafe_allow_html=True)
        st.markdown("### 🗂️ Local Snapshots")
        recent = get_recent_files(6)
        if recent:
            for f in reversed(recent):
                st.markdown(f"<div class='cam-stat'>📁 {f}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='cam-stat'>No local snapshots yet</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_feed:
        st.markdown("### 🎥 Live Camera Feed")
        status_placeholder = st.empty()
        frame_placeholder  = st.empty()
        upload_placeholder = st.empty()

        # Manual capture
        if do_capture:
            try:
                filepath, filename = capture_image(cam)
                status_placeholder.success(f"📸 Captured: `{filename}`")
                if auto_upload:
                    ok, err = upload_to_drive(filepath)
                    if ok:
                        upload_placeholder.markdown(
                            f'<span class="upload-badge-ok">☁️ Uploaded: {filename}</span>',
                            unsafe_allow_html=True)
                    else:
                        upload_placeholder.markdown(
                            f'<span class="upload-badge-err">⚠️ Upload failed: {err}</span>',
                            unsafe_allow_html=True)
            except Exception as e:
                status_placeholder.error(f"Capture error: {e}")

        # Upload all local
        if do_upload_all:
            with st.spinner("Uploading all captures to Google Drive..."):
                ok, err = upload_all_to_drive()
            if ok:
                upload_placeholder.success("☁️ All local files uploaded!")
            else:
                upload_placeholder.error(f"Upload failed: {err}")

        # Live feed loop
        if live_mode and not do_stop:
            last_auto_capture = time.time()
            st.markdown(
                '<div style="border:1px solid #2e7d32;border-radius:12px;padding:4px;background:#0a0d12;">',
                unsafe_allow_html=True)
            while live_mode:
                try:
                    frame = cam.capture_array()
                    frame_placeholder.image(frame, channels="RGB", use_container_width=True)

                    if (time.time() - last_auto_capture) >= capture_interval:
                        filepath, filename = capture_image(cam)
                        last_auto_capture = time.time()
                        status_placeholder.info(f"🔄 Auto-captured: `{filename}`")
                        if auto_upload:
                            ok, err = upload_to_drive(filepath)
                            if ok:
                                upload_placeholder.markdown(
                                    f'<span class="upload-badge-ok">☁️ Auto-uploaded: {filename}</span>',
                                    unsafe_allow_html=True)
                            else:
                                upload_placeholder.markdown(
                                    f'<span class="upload-badge-err">⚠️ Auto-upload failed</span>',
                                    unsafe_allow_html=True)
                    time.sleep(0.05)
                except Exception as e:
                    status_placeholder.error(f"Feed error: {e}")
                    break
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            try:
                frame = cam.capture_array()
                frame_placeholder.image(frame, channels="RGB",
                    caption="Static snapshot — enable Live Feed for streaming",
                    use_container_width=True)
            except Exception as e:
                st.warning(f"Could not grab frame: {e}")

        # Last local snapshot below feed
        recent = get_recent_files(1)
        if recent:
            st.markdown("---")
            st.markdown("**Last local snapshot:**")
            last_img_path = os.path.join(SAVE_DIR, recent[-1])
            try:
                st.image(last_img_path, caption=recent[-1], use_container_width=True)
            except:
                pass

# ---- ANALYSIS PAGE ----
elif page == "📈 ANALYSIS":
    st.title("Historical Trends – Individual Sensors")
    if not latest.empty:
        col_s1,col_s2,col_s3 = st.columns([1,1,2])
        with col_s1:
            sensor_choice = st.selectbox("Sensor", ["Temperature (°C)","Humidity (%)","pH (avg)","Soil Moisture (%)"])
        with col_s2:
            plant_sel = st.selectbox("Plant", list(range(1,11)))
        with col_s3:
            time_range = st.selectbox("Time range", ["24 hours","7 days","30 days"])
            hours = 24 if time_range=="24 hours" else (168 if time_range=="7 days" else 720)
        hist_df = get_historical_data(plant_id=plant_sel, hours=hours)
        if not hist_df.empty:
            if sensor_choice == "Temperature (°C)":   y_col,y_label = 'temp_c','°C'
            elif sensor_choice == "Humidity (%)":     y_col,y_label = 'humidity','%'
            elif sensor_choice == "pH (avg)":
                hist_df['ph_avg'] = (hist_df['ph1']+hist_df['ph2'])/2
                y_col,y_label = 'ph_avg','pH'
            else: y_col,y_label = 'soil_moisture','%'
            fig = px.line(hist_df, x='timestamp', y=y_col,
                          title=f"{sensor_choice} - Plant {plant_sel}")
            fig.update_layout(yaxis_title=y_label)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No historical data for this plant yet.")
    else:
        st.warning("No data available.")

# ---- SYSTEM LOGS ----
elif page == "📜 SYSTEM LOGS":
    st.title("System Activity Logs")
    logs = get_historical_data(plant_id=None, hours=24)
    if not logs.empty:
        def classify(row):
            if row['temp_c'] < 15 or row['temp_c'] > 30:          return "🌡️ Temp alert"
            if row['humidity'] < 50 or row['humidity'] > 85:       return "💧 Humidity alert"
            if (row['ph1']+row['ph2'])/2 < 5.5 or (row['ph1']+row['ph2'])/2 > 6.5: return "🧪 pH alert"
            if row['soil_moisture'] < 20 or row['soil_moisture'] > 80: return "🌱 Soil alert"
            return "Normal"
        logs['event'] = logs.apply(classify, axis=1)

        # Show image_url as clickable link if column exists
        display_cols = ['timestamp','plant_id','temp_c','humidity','ph1','ph2','soil_moisture','event']
        col_config   = {
            "timestamp":    "Time",
            "plant_id":     "Plant",
            "temp_c":       "Temp (°C)",
            "humidity":     "Hum (%)",
            "ph1":          "pH1",
            "ph2":          "pH2",
            "soil_moisture":"Soil %",
            "event":        "Event"
        }
        if 'image_url' in logs.columns:
            display_cols.insert(-1, 'image_url')
            col_config['image_url'] = st.column_config.LinkColumn("📸 Image")

        st.dataframe(
            logs[display_cols].tail(20),
            use_container_width=True,
            hide_index=True,
            column_config=col_config
        )
    else:
        st.info("No logs available.")

# ---- USER MANAGEMENT ----
elif page == "👥 USER MANAGEMENT":
    st.title("Admin Control Panel")
    st.subheader("Registered Users")
    st.table(pd.DataFrame({
        "Username": ["admin@agribot.ai","user@agribot.ai"],
        "Role":     ["Administrator","Standard User"]
    }))
    st.info("Future feature: add / remove users via database")

# ============================================
# AUTO-REFRESH (non-camera pages only)
# ============================================
if page != "📷 CAMERA FEED":
    time.sleep(30)
    st.rerun()