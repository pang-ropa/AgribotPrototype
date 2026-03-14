import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
import random
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import time
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIG ---
LOGO_PATH = "backend/agribotailogo.png"

st.set_page_config(
    page_title="AgriBot-AI | Dashboard",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# KIOSK MODE CHECK (must be before login)
# ============================================
# If the URL contains ?kiosk=true, auto-login as user and enable auto‑cycling
if "kiosk" in st.query_params and st.query_params["kiosk"] == "true":
    st.session_state.logged_in = True
    st.session_state.role = "user"
    st.session_state.kiosk_mode = True
    if "page_index" not in st.session_state:
        st.session_state.page_index = 0

# ============================================
# LOGIN SYSTEM (with Enter‑key support)
# ============================================
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "user":  {"password": "user123",  "role": "user"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

def login():
    st.title("🔐 AgriBot-AI Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
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
# CUSTOM CSS (unchanged)
# ============================================
css_code = """
    <style>
    [data-testid="stHeader"] { background-color: transparent !important; }
    button[kind="headerNoSpacing"] {
        visibility: visible !important;
        background-color: #2E7D32 !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 10px 15px !important;
        top: 15px !important;
        left: 15px !important;
        z-index: 999999 !important;
    }
    section[data-testid="stSidebar"] {
        width: 350px !important;
        background-color: #0E1117 !important;
        border-right: 2px solid #4CAF50;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: flex-start !important;
    }
    [data-testid="stSidebar"] [data-testid="stImage"] {
        pointer-events: none !important;
        user-select: none !important;
        display: flex !important;
        justify-content: center !important;
        padding-top: 40px !important;
        margin-bottom: 0px !important;
    }
    [data-testid="stSidebar"] [data-testid="stElementToolbar"] { display: none !important; }
    [data-testid="stSidebar"] [data-testid="stImage"] img {
        border-radius: 50% !important;
        border: 4px solid #4CAF50 !important;
        width: 170px !important;
        height: 170px !important;
        object-fit: cover !important;
    }
    .sidebar-title {
        text-align: center !important;
        color: #4CAF50 !important;
        font-size: 26px !important;
        font-weight: 800 !important;
        margin-top: 15px !important;
        margin-bottom: 5px !important;
        width: 100% !important;
        display: block !important;
    }
    .sidebar-hr {
        height: 3px;
        background-color: #4CAF50;
        width: 60%;
        margin: 5px auto 25px auto !important;
        border-radius: 5px;
    }
    .stRadio > div {
        gap: 10px;
        align-items: center;
        justify-content: center;
        width: 100% !important;
    }
    .stRadio label {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #4CAF50 !important;
        text-align: center;
        width: 100%;
        cursor: pointer;
    }
    div[data-testid="stMetric"] {
        background: rgba(46, 125, 50, 0.15) !important;
        border: 1px solid #4CAF50 !important;
        border-radius: 15px !important;
        padding: 15px !important;
        text-align: center !important;
    }
    div[data-testid="stMetricLabel"] {
        margin-top: 10px !important; 
        font-weight: bold !important;
        color: #A5D6A7 !important;
        justify-content: center !important;
    }
    div[data-testid="stMetricValue"] {
        margin-top: -5px !important;
        font-size: 32px !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}
    </style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# ============================================
# DATA LOADING & ASSETS
# ============================================
@st.cache_resource
def load_assets():
    try:
        model = joblib.load('backend/anomaly_model.pkl')
        scaler = joblib.load('backend/anomaly_scaler.pkl')
        return model, scaler
    except:
        return None, None

@st.cache_resource
def get_sheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        elif os.path.exists('backend/credentials.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('backend/credentials.json', scope)
        else:
            st.error("Authentication Error: secrets.toml or credentials.json missing.")
            return None
        client = gspread.authorize(creds)
        return client.open("Agribot-Live-Data").sheet1
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

sheet = get_sheet()

# ============================================
# DATA FETCHING FUNCTIONS (10‑plant aware)
# ============================================
@st.cache_data(ttl=10)
def get_latest_readings():
    if sheet is None:
        return pd.DataFrame()
    try:
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        if df.empty:
            return pd.DataFrame()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        latest = df.sort_values('timestamp').groupby('plant_id').last().reset_index()
        return latest
    except Exception as e:
        st.error(f"Data fetch error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_historical_data(plant_id=None, hours=24):
    if sheet is None:
        return pd.DataFrame()
    try:
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        if df.empty:
            return df
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        cutoff = datetime.now() - timedelta(hours=hours)
        df = df[df['timestamp'] >= cutoff]
        if plant_id is not None:
            df = df[df['plant_id'] == plant_id]
        return df.sort_values('timestamp')
    except:
        return pd.DataFrame()

# ============================================
# SIDEBAR (role‑based pages, with kiosk mode)
# ============================================
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH)

    st.markdown('<div class="sidebar-title">AgriBot-AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-hr"></div>', unsafe_allow_html=True)

    # Define page options based on role
    if st.session_state.role == "admin":
        page_options = ["📡 LIVE DASHBOARD", "📈 ANALYSIS", "📜 SYSTEM LOGS", "👥 USER MANAGEMENT"]
    else:
        page_options = ["📡 LIVE DASHBOARD", "📈 ANALYSIS"]

    # Kiosk mode: auto‑select page, hide radio
    if st.session_state.get("kiosk_mode", False):
        # Use session state index to select page
        idx = st.session_state.get("page_index", 0) % len(page_options)
        page = page_options[idx]
        # Show a small indicator instead of the radio
        st.caption(f"🔄 Auto‑cycling: **{page}**")
        # Optionally add a manual override button to exit kiosk?
        if st.button("Exit Kiosk"):
            st.session_state.kiosk_mode = False
            st.rerun()
    else:
        # Normal interactive mode: radio selection
        page = st.radio("", page_options, label_visibility="collapsed")

    st.success("🟢 SYSTEM: ONLINE")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.kiosk_mode = False
        st.rerun()

# ============================================
# MAIN CONTENT
# ============================================
model, scaler = load_assets()
latest = get_latest_readings()

# --- LIVE DASHBOARD ---
if page == "📡 LIVE DASHBOARD":
    st.title("Real-Time Monitoring – 10 Lettuces")

    if latest.empty:
        st.warning("No data yet. Waiting for sensor readings...")
        st.stop()

    avg_temp = latest['temp_c'].mean()
    avg_hum = latest['humidity'].mean()
    avg_ph = (latest['ph1'].mean() + latest['ph2'].mean()) / 2
    avg_soil = latest['soil_moisture'].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌡️ TEMP", f"{avg_temp:.1f} °C")
    col2.metric("💧 HUMIDITY", f"{avg_hum:.0f} %")
    col3.metric("🧪 pH (avg)", f"{avg_ph:.2f}")
    col4.metric("🌱 SOIL (avg)", f"{avg_soil:.0f} %")

    st.markdown("---")

    col_l, col_r = st.columns([1.3, 1], gap="large")

    with col_l:
        st.subheader("🌿 Plant Health Feed")
        latest = latest.sort_values('plant_id')
        row1 = st.columns(5)
        row2 = st.columns(5)
        for idx, (_, plant) in enumerate(latest.iterrows()):
            col = row1[idx] if idx < 5 else row2[idx-5]
            pid = int(plant['plant_id'])
            soil = plant['soil_moisture']
            ph_avg = (plant['ph1'] + plant['ph2']) / 2

            health = "✅ Healthy"
            if soil < 30:
                health = "⚠️ Dry"
            elif soil > 80:
                health = "⚠️ Wet"
            if ph_avg < 5.5 or ph_avg > 6.5:
                health = "🔴 pH Alert"

            with col:
                if plant['image_path'] and plant['image_path'].startswith('http'):
                    st.image(plant['image_path'], width=100)
                else:
                    st.markdown("<span style='font-size:2rem;'>🥬</span>", unsafe_allow_html=True)
                st.markdown(f"**Lettuce #{pid}**<br>{health}<br>Soil: {soil:.0f}%", unsafe_allow_html=True)

    with col_r:
        st.subheader("🤖 AI Health Recommendation")
        plant1 = latest[latest['plant_id'] == 1]
        if not plant1.empty and model and scaler:
            try:
                temp_val = float(plant1.iloc[0]['temp_c'])
                hum_val  = float(plant1.iloc[0]['humidity'])
                ph_val   = (float(plant1.iloc[0]['ph1']) + float(plant1.iloc[0]['ph2'])) / 2
                features = np.array([[temp_val, hum_val, ph_val]])
                pred = model.predict(scaler.transform(features))[0]
                if pred == -1:
                    st.error("### 🚨 ALERT\nAnomalous conditions detected. Adjusting irrigation...")
                else:
                    st.success("### ✅ HEALTHY\nCrop environment is optimal.")
            except Exception as e:
                st.info(f"Processing sensor data with AI model... (error: {e})")
        else:
            st.warning("Awaiting sensor data or AI model...")

        st.markdown("### 🔔 Recent Alerts")
        alerts = []
        for _, plant in latest.iterrows():
            pid = int(plant['plant_id'])
            if plant['soil_moisture'] < 20 or plant['soil_moisture'] > 80:
                alerts.append(f"🌱 Plant {pid} soil: {plant['soil_moisture']:.0f}%")
            avg_ph = (plant['ph1'] + plant['ph2']) / 2
            if avg_ph < 5.5 or avg_ph > 6.5:
                alerts.append(f"🧪 Plant {pid} pH: {avg_ph:.2f}")
        if avg_temp < 15 or avg_temp > 30:
            alerts.append(f"🌡️ Temp out of range: {avg_temp:.1f}°C")
        if avg_hum < 50 or avg_hum > 85:
            alerts.append(f"💧 Humidity out of range: {avg_hum:.0f}%")
        if alerts:
            for alert in alerts[:5]:
                st.markdown(f'<div style="padding:5px; background:#ffebee; color:#b71c1c; border-radius:5px; margin:5px 0;">{alert}</div>', unsafe_allow_html=True)
        else:
            st.info("✅ All parameters within range.")

# --- ANALYSIS PAGE ---
elif page == "📈 ANALYSIS":
    st.title("Historical Trends – Individual Sensors")

    if not latest.empty:
        col_s1, col_s2, col_s3 = st.columns([1,1,2])
        with col_s1:
            sensor_choice = st.selectbox("Sensor", ["Temperature (°C)", "Humidity (%)", "pH (avg)", "Soil Moisture (%)"])
        with col_s2:
            plant_sel = st.selectbox("Plant", list(range(1,11)))
        with col_s3:
            time_range = st.selectbox("Time range", ["24 hours", "7 days", "30 days"])
            hours = 24 if time_range == "24 hours" else (168 if time_range == "7 days" else 720)

        hist_df = get_historical_data(plant_id=plant_sel, hours=hours)
        if not hist_df.empty:
            if sensor_choice == "Temperature (°C)":
                y_col = 'temp_c'
                y_label = "°C"
            elif sensor_choice == "Humidity (%)":
                y_col = 'humidity'
                y_label = "%"
            elif sensor_choice == "pH (avg)":
                hist_df['ph_avg'] = (hist_df['ph1'] + hist_df['ph2']) / 2
                y_col = 'ph_avg'
                y_label = "pH"
            else:
                y_col = 'soil_moisture'
                y_label = "%"

            fig = px.line(hist_df, x='timestamp', y=y_col, title=f"{sensor_choice} - Plant {plant_sel}")
            fig.update_layout(yaxis_title=y_label)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No historical data for this plant yet.")
    else:
        st.warning("No data available.")

# --- SYSTEM LOGS (only for admin) ---
elif page == "📜 SYSTEM LOGS":
    st.title("System Activity Logs")
    logs = get_historical_data(plant_id=None, hours=24)
    if not logs.empty:
        def classify(row):
            if row['temp_c'] < 15 or row['temp_c'] > 30:
                return "🌡️ Temp alert"
            if row['humidity'] < 50 or row['humidity'] > 85:
                return "💧 Humidity alert"
            avg_ph = (row['ph1'] + row['ph2']) / 2
            if avg_ph < 5.5 or avg_ph > 6.5:
                return "🧪 pH alert"
            if row['soil_moisture'] < 20 or row['soil_moisture'] > 80:
                return "🌱 Soil alert"
            return "Normal"
        logs['event'] = logs.apply(classify, axis=1)
        st.dataframe(
            logs[['timestamp', 'plant_id', 'temp_c', 'humidity', 'ph1', 'ph2', 'soil_moisture', 'event']].tail(20),
            use_container_width=True,
            hide_index=True,
            column_config={
                "timestamp": "Time",
                "plant_id": "Plant",
                "temp_c": "Temp (°C)",
                "humidity": "Hum (%)",
                "ph1": "pH1",
                "ph2": "pH2",
                "soil_moisture": "Soil %",
                "event": "Event"
            }
        )
    else:
        st.info("No logs available.")

# --- USER MANAGEMENT (Admin only) ---
elif page == "👥 USER MANAGEMENT":
    st.title("Admin Control Panel")
    st.subheader("Registered Users")
    user_data = pd.DataFrame({
        "Username": ["admin", "user"],
        "Role": ["Administrator", "Standard User"]
    })
    st.table(user_data)
    st.info("Future feature: add / remove users via database")

# ============================================
# AUTO‑REFRESH AND PAGE CYCLING (kiosk mode)
# ============================================
time.sleep(10)

# If in kiosk mode, advance to the next page
if st.session_state.get("kiosk_mode", False):
    st.session_state.page_index = st.session_state.get("page_index", 0) + 1

st.rerun()