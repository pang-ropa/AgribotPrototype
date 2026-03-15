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
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIG
# ============================================================
PI_LOGO_PATH = os.path.expanduser("~/env/Thesis code/backend/agribotailogologo.png")
WIN_LOGO_PATH = r"C:\Users\admin\Downloads\AgribotPrototype\backend\agribotailogo.png"
ACTUAL_LOGO = (PI_LOGO_PATH  if os.path.exists(PI_LOGO_PATH)  else
               WIN_LOGO_PATH if os.path.exists(WIN_LOGO_PATH) else "")

# Google Sheets config
CREDENTIALS_FILE = os.path.expanduser("~/env/Thesis code/credentials.json")
SPREADSHEET_ID   = "1mYScsUkoZn84FIoO_QMaku3gZT3Z9df72kPE3ray9-A"

# ── Sheet columns written by agribot_pi_final.py ──────────────
# A: timestamp | B: plant_id | C: temp_c | D: humidity
# E: soil_moisture | F: ph | G: image_url
# One row per plant per minute  →  10 rows per cycle

st.set_page_config(
    page_title="AgriBot-AI | Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# BACKGROUND IMAGE
# ============================================================
def set_background(image_file):
    if not os.path.exists(image_file):
        return
    ext  = os.path.splitext(image_file)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:{mime};base64,{encoded}");
            background-size: cover; background-position: center;
            background-repeat: no-repeat; background-attachment: fixed;
        }}
        .stApp::before {{
            content:""; position:fixed; inset:0;
            background:rgba(0,0,0,0.45); z-index:0; pointer-events:none;
        }}
        </style>""", unsafe_allow_html=True)

# ============================================================
# LOGIN SYSTEM
# ============================================================
users = {
    "admin@agribot.ai": {"password": "admin123", "role": "admin"},
    "user@agribot.ai":  {"password": "user123",  "role": "user"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

def login():
    pi_bg  = os.path.expanduser("~/env/Thesis code/backend/background.jpg")
    win_bg = r"C:\Users\admin\Downloads\AgribotPrototype\backend\background.jpg"
    bg     = pi_bg if os.path.exists(pi_bg) else win_bg
    set_background(bg)

    logo_html = ""
    if ACTUAL_LOGO:
        with open(ACTUAL_LOGO, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        logo_html = f'''<div style="display:flex;justify-content:center;margin-bottom:15px;">
            <img src="data:image/png;base64,{logo_b64}"
            style="width:130px;height:130px;border-radius:50%;
                   border:3px solid #4CAF50;object-fit:cover;"/></div>'''

    st.markdown(f"""
    <style>
    #MainMenu{{visibility:hidden;}} footer{{visibility:hidden;}}
    [data-testid="stForm"]{{
        background:linear-gradient(160deg,rgba(56,142,60,0.55) 0%,rgba(76,175,80,0.45) 50%,rgba(129,199,132,0.40) 100%) !important;
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
    .login-title{{text-align:center;font-size:42px;font-weight:800;color:white;
        text-shadow:0 2px 8px rgba(0,0,0,0.5);margin-bottom:4px;}}
    .login-tagline{{text-align:center;color:#a5d6a7;margin-bottom:20px;font-size:15px;}}
    </style>
    <div style="display:flex;flex-direction:column;align-items:center;margin-top:60px;">
        {logo_html}
        <div class="login-title">AgriBot-AI</div>
        <div class="login-tagline">Smart Farming · Intelligent Monitoring</div>
    </div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            email     = st.text_input("Email", placeholder="admin@agribot.ai or user@agribot.ai")
            password  = st.text_input("Password", type="password", placeholder="••••••••")
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

# ============================================================
# GLOBAL CSS
# ============================================================
st.markdown("""
<style>
[data-testid="stHeader"]{background-color:transparent!important;}
button[kind="headerNoSpacing"]{
    visibility:visible!important;background-color:#2E7D32!important;
    color:white!important;border-radius:12px!important;
    padding:10px 15px!important;top:15px!important;
    left:15px!important;z-index:999999!important;
}
section[data-testid="stSidebar"]{
    width:280px!important;background-color:#0E1117!important;
    border-right:2px solid #2e7d32!important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{
    display:flex!important;flex-direction:column!important;
    align-items:center!important;padding:0 14px 24px 14px!important;
}
[data-testid="stSidebar"] [data-testid="stElementToolbar"]{display:none!important;}
.sidebar-logo-wrap{
    display:flex;flex-direction:column;align-items:center;
    padding-top:30px;margin-bottom:4px;width:100%;
}
.sidebar-logo-ring{
    padding:3px;border-radius:50%;
    background:linear-gradient(135deg,#4CAF50,#1b5e20);
    box-shadow:0 0 16px rgba(76,175,80,0.35);margin-bottom:12px;
}
.sidebar-logo-ring img{
    border-radius:50%;display:block;width:115px;height:115px;
    object-fit:cover;background:#0E1117;
}
.sidebar-title{text-align:center;font-size:20px;font-weight:800;color:#4CAF50;margin-bottom:2px;}
.sidebar-tagline{text-align:center;font-size:10px;color:#66bb6a;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;}
.sidebar-divider{width:60%;height:2px;background:linear-gradient(90deg,transparent,#4CAF50,transparent);border-radius:2px;margin:14px auto 18px auto;}
.sidebar-nav-label{font-size:9px;font-weight:700;color:#388e3c;letter-spacing:2.5px;text-transform:uppercase;width:100%;padding:0 2px;margin-bottom:6px;}
.stRadio>div{gap:5px!important;width:100%!important;flex-direction:column!important;}
.stRadio label{
    font-size:13px!important;font-weight:600!important;color:#a5d6a7!important;
    background:rgba(46,125,50,0.08)!important;border:1px solid rgba(76,175,80,0.18)!important;
    border-radius:8px!important;padding:10px 14px!important;width:100%!important;
    cursor:pointer!important;transition:all 0.15s ease!important;
}
.stRadio label:hover{background:rgba(76,175,80,0.18)!important;border-color:#4CAF50!important;color:#ffffff!important;}
div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked){
    background:rgba(46,125,50,0.35)!important;border:1px solid #4CAF50!important;
    color:#ffffff!important;box-shadow:0 0 8px rgba(76,175,80,0.25)!important;
}
.stRadio [data-baseweb="radio"]>div:first-child{display:none!important;}
.stRadio [data-testid="stMarkdownContainer"] p{margin:0!important;}
.sidebar-status{
    display:flex;align-items:center;gap:8px;background:rgba(46,125,50,0.18);
    border:1px solid #2e7d32;border-radius:8px;padding:9px 14px;width:100%;
    margin-top:14px;margin-bottom:8px;box-sizing:border-box;
}
.status-dot{
    width:8px;height:8px;background:#4CAF50;border-radius:50%;
    box-shadow:0 0 6px #4CAF50;animation:blink 2s ease-in-out infinite;flex-shrink:0;
}
@keyframes blink{0%,100%{opacity:1;box-shadow:0 0 5px #4CAF50;}50%{opacity:0.6;box-shadow:0 0 12px #4CAF50;}}
.status-text{font-size:11px;font-weight:700;color:#81c784;letter-spacing:1.5px;text-transform:uppercase;}
[data-testid="stSidebar"] .stButton>button{
    background:transparent!important;border:1px solid #2e7d32!important;
    color:#81c784!important;border-radius:8px!important;width:100%!important;
    font-size:13px!important;font-weight:600!important;padding:9px!important;
}
[data-testid="stSidebar"] .stButton>button:hover{
    background:rgba(211,47,47,0.12)!important;border-color:#c62828!important;color:#ef9a9a!important;
}
.role-badge{
    font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
    padding:3px 10px;border-radius:20px;background:rgba(76,175,80,0.12);
    border:1px solid #2e7d32;color:#81c784;margin-top:4px;
}
div[data-testid="stMetric"]{
    background:rgba(46,125,50,0.15)!important;border:1px solid #4CAF50!important;
    border-radius:15px!important;padding:15px!important;text-align:center!important;
}
div[data-testid="stMetricLabel"]{margin-top:10px!important;font-weight:bold!important;color:#A5D6A7!important;justify-content:center!important;}
div[data-testid="stMetricValue"]{margin-top:-5px!important;font-size:32px!important;}
#MainMenu{visibility:hidden;} footer{visibility:hidden;}
[data-testid="stDecoration"]{display:none;}

/* Plant camera cards */
.plant-cam-card{
    background:rgba(14,17,23,0.88);
    border:1px solid #2e7d32;
    border-radius:14px;
    padding:14px;
    margin-bottom:12px;
    text-align:center;
}
.plant-cam-title{
    font-size:13px;font-weight:700;color:#a5d6a7;margin-bottom:8px;
    letter-spacing:0.5px;
}
.plant-cam-time{
    font-size:10px;color:#66bb6a;margin-top:6px;
}
.plant-cam-no-img{
    background:rgba(46,125,50,0.08);border:1px dashed #388e3c;
    border-radius:10px;padding:24px 8px;color:#4CAF50;font-size:28px;
    margin-bottom:6px;
}
.cam-stat{
    background:rgba(46,125,50,0.15);border:1px solid #388e3c;
    border-radius:10px;padding:10px 14px;margin:5px 0;
    color:#a5d6a7;font-size:13px;
}
.drive-badge{
    background:rgba(46,125,50,0.2);border:1px solid #4CAF50;
    border-radius:8px;padding:6px 10px;color:#a5d6a7;
    font-size:11px;margin-top:5px;word-break:break-all;
}
.schedule-badge{
    display:inline-block;background:rgba(21,101,192,0.25);
    border:1px solid #1565C0;border-radius:6px;
    padding:3px 10px;font-size:11px;color:#90CAF9;
    font-weight:700;letter-spacing:0.5px;margin:2px 3px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA LOADING
# ============================================================
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
        return client.open_by_key(SPREADSHEET_ID).sheet1
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

@st.cache_data(ttl=30)
def get_latest_readings():
    """
    Returns one row per plant (the most recent reading for each plant_id).
    Columns: timestamp | plant_id | temp_c | humidity | soil_moisture | ph | image_url
    """
    if sheet is None:
        return pd.DataFrame()
    try:
        df = pd.DataFrame(sheet.get_all_records())
        if df.empty:
            return df
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # Keep the last row per plant (most recent reading)
        return df.sort_values('timestamp').groupby('plant_id').last().reset_index()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_historical_data(plant_id=None, hours=24):
    """
    Returns all rows within the last `hours` hours, optionally filtered by plant_id.
    """
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

def get_plant_image_url(plant_id: int) -> str:
    """
    Returns the most recent non-empty image_url for a specific plant_id.
    Used to display per-plant Drive images on the Camera Feed page.
    """
    if sheet is None:
        return ""
    try:
        df = pd.DataFrame(sheet.get_all_records())
        if df.empty or 'image_url' not in df.columns:
            return ""
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        plant_df = df[df['plant_id'] == plant_id].sort_values('timestamp', ascending=False)
        for _, row in plant_df.iterrows():
            url = str(row.get('image_url', '')).strip()
            if url.startswith("http"):
                return url
        return ""
    except:
        return ""

def get_all_plant_image_urls() -> dict:
    """
    Returns {plant_id: latest_image_url} for all 10 plants in a single Sheet read.
    """
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
            plant_rows = df[df['plant_id'] == pid]
            for _, row in plant_rows.iterrows():
                url = str(row.get('image_url', '')).strip()
                if url.startswith("http"):
                    result[pid] = url
                    break
        return result
    except:
        return result

# ============================================================
# SIDEBAR
# ============================================================
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
        page = st.radio("", [
            "📡  Live Dashboard",
            "📷  Camera Feed",
            "📈  Analysis",
            "📜  System Logs",
            "👥  User Management"
        ], label_visibility="collapsed")
    else:
        page = st.radio("", [
            "📡  Live Dashboard",
            "📷  Camera Feed",
            "📈  Analysis"
        ], label_visibility="collapsed")

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

# ============================================================
# MAIN CONTENT
# ============================================================
model, scaler = load_assets()
latest = get_latest_readings()

# ── pH thresholds (single sensor) ─────────────────────────────
PH_LOW, PH_HIGH       = 5.5, 6.5
SOIL_DRY, SOIL_WET    = 30, 80
TEMP_LOW, TEMP_HIGH   = 15, 30
HUM_LOW,  HUM_HIGH    = 50, 85

# ==============================================================
# PAGE: LIVE DASHBOARD
# ==============================================================
if page == "📡 LIVE DASHBOARD":
    st.title("Real-Time Monitoring – 10 Lettuces")

    if latest.empty:
        st.warning("No data yet. Waiting for sensor readings from the Pi...")
        st.stop()

    # ── Summary metrics ────────────────────────────────────────
    avg_temp = latest['temp_c'].mean()
    avg_hum  = latest['humidity'].mean()
    avg_ph   = latest['ph'].mean()          # single ph column
    avg_soil = latest['soil_moisture'].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌡️ TEMP",       f"{avg_temp:.1f} °C")
    col2.metric("💧 HUMIDITY",   f"{avg_hum:.0f} %")
    col3.metric("🧪 pH",         f"{avg_ph:.2f}")     # one pH sensor
    col4.metric("🌱 SOIL (avg)", f"{avg_soil:.0f} %")
    st.markdown("---")

    col_l, col_r = st.columns([1.3, 1], gap="large")

    with col_l:
        st.subheader("🌿 Plant Health Feed")
        latest_s = latest.sort_values('plant_id')
        row1 = st.columns(5)
        row2 = st.columns(5)
        for idx, (_, plant) in enumerate(latest_s.iterrows()):
            col = row1[idx] if idx < 5 else row2[idx - 5]
            pid   = int(plant['plant_id'])
            soil  = plant['soil_moisture']   # per-plant soil reading
            ph    = plant['ph']              # shared pH per cycle

            health = "✅ Healthy"
            if soil < SOIL_DRY:                   health = "⚠️ Dry"
            elif soil > SOIL_WET:                 health = "⚠️ Wet"
            if ph < PH_LOW or ph > PH_HIGH:       health = "🔴 pH Alert"

            with col:
                st.markdown("<span style='font-size:2rem;'>🥬</span>",
                            unsafe_allow_html=True)
                st.markdown(
                    f"**Lettuce #{pid}**<br>{health}<br>"
                    f"Soil: {soil:.0f}%<br>pH: {ph:.2f}",
                    unsafe_allow_html=True)

    with col_r:
        st.subheader("🤖 AI Health Recommendation")
        plant1 = latest[latest['plant_id'] == 1]
        if not plant1.empty and model and scaler:
            try:
                features = np.array([[
                    float(plant1.iloc[0]['temp_c']),
                    float(plant1.iloc[0]['humidity']),
                    float(plant1.iloc[0]['ph'])      # single ph
                ]])
                pred = model.predict(scaler.transform(features))[0]
                if pred == -1:
                    st.error("### 🚨 ALERT\nAnomalous conditions detected.")
                else:
                    st.success("### ✅ HEALTHY\nCrop environment is optimal.")
            except Exception as e:
                st.info(f"AI processing... ({e})")
        else:
            st.warning("Awaiting sensor data or AI model...")

        # Latest captured image for Plant 1 from Drive
        st.markdown("### 📸 Latest Lettuce Image — Plant 1")
        plant1_url = get_plant_image_url(1)
        if plant1_url:
            st.image(plant1_url,
                     caption="Most recent capture — Plant 1 (from Google Drive)",
                     use_container_width=True)
            st.markdown(
                f'<div class="drive-badge">☁️ Stored in Google Drive<br>'
                f'<a href="{plant1_url}" target="_blank" style="color:#81c784;">'
                f'View full image ↗</a></div>',
                unsafe_allow_html=True)
        else:
            st.info("No image yet — Pi captures at 7:00 AM, 12:00 NN, 12:30 PM.")

        # Alerts
        st.markdown("### 🔔 Recent Alerts")
        alerts = []
        for _, plant in latest.iterrows():
            pid  = int(plant['plant_id'])
            soil = plant['soil_moisture']
            ph   = plant['ph']
            if soil < SOIL_DRY or soil > SOIL_WET:
                alerts.append(f"🌱 Plant {pid} soil: {soil:.0f}%")
            if ph < PH_LOW or ph > PH_HIGH:
                alerts.append(f"🧪 Plant {pid} pH: {ph:.2f}")
        if avg_temp < TEMP_LOW or avg_temp > TEMP_HIGH:
            alerts.append(f"🌡️ Temp out of range: {avg_temp:.1f}°C")
        if avg_hum < HUM_LOW or avg_hum > HUM_HIGH:
            alerts.append(f"💧 Humidity out of range: {avg_hum:.0f}%")
        if alerts:
            for alert in alerts[:5]:
                st.markdown(
                    f'<div style="padding:5px;background:#ffebee;color:#b71c1c;'
                    f'border-radius:5px;margin:5px 0;">{alert}</div>',
                    unsafe_allow_html=True)
        else:
            st.info("✅ All parameters within range.")

# ==============================================================
# PAGE: CAMERA FEED
# Shows the 10 Drive image URLs uploaded by agribot_pi_final.py
# ==============================================================
elif page == "📷 CAMERA FEED":
    st.title("📷 AgriBot Camera — Plant Image Gallery")
    st.markdown(
        "Images are captured by the Pi robot at "
        "<span class='schedule-badge'>7:00 AM</span>"
        "<span class='schedule-badge'>12:00 NN</span>"
        "<span class='schedule-badge'>12:30 PM</span>"
        " and uploaded to Google Drive automatically.",
        unsafe_allow_html=True)
    st.markdown("---")

    # Controls row
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1, 1, 2])
    with ctrl_col1:
        selected_plant = st.selectbox("Focus on plant", ["All Plants"] + [f"Plant {i}" for i in range(1, 11)])
    with ctrl_col2:
        if st.button("🔄 Refresh Images", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with ctrl_col3:
        st.markdown(
            '<div class="cam-stat" style="margin-top:0;">📡 Pi script captures 10 plants per session '
            '(1 min travel + 5 s exposure each)</div>',
            unsafe_allow_html=True)

    st.markdown("---")

    # Load all 10 plant URLs in one Sheet read
    with st.spinner("Loading plant images from Google Drive..."):
        all_urls = get_all_plant_image_urls()

    # ── All-plant grid view ────────────────────────────────────
    if selected_plant == "All Plants":
        st.subheader("🌿 All 10 Plants — Latest Captures")
        uploaded_count = sum(1 for u in all_urls.values() if u)
        st.markdown(
            f'<div class="cam-stat" style="margin-bottom:14px;">'
            f'📊 Images available: <b>{uploaded_count} / 10</b> plants</div>',
            unsafe_allow_html=True)

        # 5-per-row grid
        row1_cols = st.columns(5)
        row2_cols = st.columns(5)
        for plant_id in range(1, 11):
            col = row1_cols[plant_id - 1] if plant_id <= 5 else row2_cols[plant_id - 6]
            url = all_urls[plant_id]
            with col:
                st.markdown(f'<div class="plant-cam-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="plant-cam-title">🥬 Plant {plant_id}</div>', unsafe_allow_html=True)
                if url:
                    st.image(url, use_container_width=True)
                    st.markdown(
                        f'<div class="plant-cam-time">'
                        f'<a href="{url}" target="_blank" style="color:#81c784;font-size:10px;">'
                        f'View in Drive ↗</a></div>',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '<div class="plant-cam-no-img">📷</div>'
                        '<div style="font-size:11px;color:#4CAF50;">No image yet</div>',
                        unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # ── Single-plant focus view ────────────────────────────────
    else:
        pid = int(selected_plant.split(" ")[1])
        url = all_urls[pid]

        detail_col, info_col = st.columns([2, 1])

        with detail_col:
            st.subheader(f"🥬 Plant {pid} — Detailed View")
            if url:
                st.image(url, caption=f"Latest capture — Plant {pid}", use_container_width=True)
                st.markdown(
                    f'<div class="drive-badge">☁️ Google Drive — Plant {pid} latest image<br>'
                    f'<a href="{url}" target="_blank" style="color:#81c784;">Open full image ↗</a></div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="plant-cam-card" style="padding:40px;text-align:center;">'
                    '<div style="font-size:48px;margin-bottom:12px;">📷</div>'
                    '<div style="color:#4CAF50;font-weight:600;">No image captured yet</div>'
                    '<div style="color:#388e3c;font-size:12px;margin-top:6px;">'
                    'Pi captures at 7:00 AM · 12:00 NN · 12:30 PM</div></div>',
                    unsafe_allow_html=True)

        with info_col:
            st.subheader("📊 Plant Sensor Data")
            if not latest.empty:
                row = latest[latest['plant_id'] == pid]
                if not row.empty:
                    r = row.iloc[0]
                    soil = r['soil_moisture']
                    ph   = r['ph']
                    st.markdown(f'<div class="cam-stat">🌡️ Temperature: <b>{r["temp_c"]:.1f} °C</b></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="cam-stat">💧 Humidity: <b>{r["humidity"]:.0f} %</b></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="cam-stat">🌱 Soil Moisture: <b>{soil:.1f} %</b> '
                                f'{"⚠️" if soil < SOIL_DRY or soil > SOIL_WET else "✅"}</div>',
                                unsafe_allow_html=True)
                    st.markdown(f'<div class="cam-stat">🧪 pH: <b>{ph:.2f}</b> '
                                f'{"⚠️" if ph < PH_LOW or ph > PH_HIGH else "✅"}</div>',
                                unsafe_allow_html=True)
                    st.markdown(f'<div class="cam-stat">🕒 Last update: <b>{r["timestamp"].strftime("%H:%M:%S")}</b></div>',
                                unsafe_allow_html=True)
                else:
                    st.info(f"No sensor data for Plant {pid} yet.")
            else:
                st.info("No sensor data available.")

            st.markdown("---")
            st.markdown("**📷 Other Plant Images**")
            other_ids = [i for i in range(1, 11) if i != pid]
            for oid in other_ids:
                o_url = all_urls[oid]
                icon  = "✅" if o_url else "⬜"
                label = f"Plant {oid}"
                if o_url:
                    st.markdown(
                        f'<div class="cam-stat" style="padding:6px 12px;">'
                        f'{icon} <a href="{o_url}" target="_blank" style="color:#81c784;">{label}</a></div>',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        f'<div class="cam-stat" style="padding:6px 12px;color:#388e3c;">'
                        f'{icon} {label} — no image yet</div>',
                        unsafe_allow_html=True)

# ==============================================================
# PAGE: ANALYSIS
# ==============================================================
elif page == "📈 ANALYSIS":
    st.title("Historical Trends – Individual Sensors")

    if not latest.empty:
        col_s1, col_s2, col_s3 = st.columns([1, 1, 2])
        with col_s1:
            # pH is now a single sensor (removed ph1/ph2)
            sensor_choice = st.selectbox("Sensor", [
                "Temperature (°C)",
                "Humidity (%)",
                "pH",
                "Soil Moisture (%)"
            ])
        with col_s2:
            plant_sel = st.selectbox("Plant", list(range(1, 11)))
        with col_s3:
            time_range = st.selectbox("Time range", ["24 hours", "7 days", "30 days"])
            hours = 24 if time_range == "24 hours" else (168 if time_range == "7 days" else 720)

        hist_df = get_historical_data(plant_id=plant_sel, hours=hours)

        if not hist_df.empty:
            if   sensor_choice == "Temperature (°C)":  y_col, y_label = 'temp_c',        '°C'
            elif sensor_choice == "Humidity (%)":       y_col, y_label = 'humidity',       '%'
            elif sensor_choice == "pH":                 y_col, y_label = 'ph',             'pH'   # single ph
            else:                                       y_col, y_label = 'soil_moisture',  '%'

            fig = px.line(
                hist_df, x='timestamp', y=y_col,
                title=f"{sensor_choice} — Plant {plant_sel}"
            )
            fig.update_layout(
                yaxis_title=y_label,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(14,17,23,0.8)',
                font_color='#a5d6a7'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Soil moisture comparison across all plants
            if sensor_choice == "Soil Moisture (%)":
                st.subheader("🌱 Soil Moisture — All 10 Plants (latest readings)")
                if not latest.empty:
                    soil_fig = px.bar(
                        latest.sort_values('plant_id'),
                        x='plant_id', y='soil_moisture',
                        title="Current Soil Moisture per Plant",
                        color='soil_moisture',
                        color_continuous_scale='Greens',
                        labels={'plant_id': 'Plant', 'soil_moisture': 'Soil Moisture (%)'}
                    )
                    soil_fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(14,17,23,0.8)',
                        font_color='#a5d6a7'
                    )
                    st.plotly_chart(soil_fig, use_container_width=True)
        else:
            st.warning("No historical data for this plant yet.")
    else:
        st.warning("No data available.")

# ==============================================================
# PAGE: SYSTEM LOGS
# ==============================================================
elif page == "📜 SYSTEM LOGS":
    st.title("System Activity Logs")

    logs = get_historical_data(plant_id=None, hours=24)

    if not logs.empty:
        def classify(row):
            if row['temp_c'] < TEMP_LOW or row['temp_c'] > TEMP_HIGH:
                return "🌡️ Temp alert"
            if row['humidity'] < HUM_LOW or row['humidity'] > HUM_HIGH:
                return "💧 Humidity alert"
            if row['ph'] < PH_LOW or row['ph'] > PH_HIGH:   # single ph
                return "🧪 pH alert"
            if row['soil_moisture'] < SOIL_DRY or row['soil_moisture'] > SOIL_WET:
                return "🌱 Soil alert"
            return "Normal"

        logs['event'] = logs.apply(classify, axis=1)

        # Columns from the updated sheet schema (single ph, no ph1/ph2)
        display_cols = [
            'timestamp', 'plant_id', 'temp_c', 'humidity',
            'soil_moisture', 'ph', 'event'
        ]
        col_config = {
            "timestamp":    "Time",
            "plant_id":     "Plant",
            "temp_c":       "Temp (°C)",
            "humidity":     "Hum (%)",
            "soil_moisture":"Soil %",
            "ph":           "pH",       # single ph column
            "event":        "Event"
        }

        # Add image_url as clickable link if present
        if 'image_url' in logs.columns:
            display_cols.insert(-1, 'image_url')
            col_config['image_url'] = st.column_config.LinkColumn("📸 Image")

        st.dataframe(
            logs[display_cols].tail(50),
            use_container_width=True,
            hide_index=True,
            column_config=col_config
        )
    else:
        st.info("No logs available.")

# ==============================================================
# PAGE: USER MANAGEMENT (admin only)
# ==============================================================
elif page == "👥 USER MANAGEMENT":
    st.title("Admin Control Panel")
    st.subheader("Registered Users")
    st.table(pd.DataFrame({
        "Username": ["admin@agribot.ai", "user@agribot.ai"],
        "Role":     ["Administrator", "Standard User"]
    }))
    st.info("Future feature: add / remove users via database.")

# ============================================================
# AUTO-REFRESH (every 30 s on all pages)
# ============================================================
time.sleep(30)
st.rerun()