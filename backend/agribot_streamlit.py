import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- PAGE CONFIG ---
LOGO_PATH = "backend/agribotailogo.png"

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
# CUSTOM CSS (modern styling)
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

def get_data():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        elif os.path.exists('backend/credentials.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('backend/credentials.json', scope)
        else:
            st.error("Authentication Error: secrets.toml or credentials.json missing.")
            return pd.DataFrame()

        client = gspread.authorize(creds)
        sheet = client.open("Agribot-Live-Data").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return pd.DataFrame()

# --- COLUMN FINDER (flexible) ---
def find_column(df, possible_names, must_contain=None, exclude=None):
    for name in possible_names:
        for col in df.columns:
            col_lower = col.lower()
            if name.lower() in col_lower:
                if must_contain and must_contain.lower() not in col_lower:
                    continue
                if exclude and exclude.lower() in col_lower:
                    continue
                return col
    return None

# ============================================
# SIDEBAR (with role‑based pages)
# ============================================
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH)

    st.markdown('<div class="sidebar-title">AgriBot-AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-hr"></div>', unsafe_allow_html=True)

    # Role‑based page options
    if st.session_state.role == "admin":
        page = st.radio(
            "",
            ["📡 LIVE DASHBOARD", "📈 ANALYSIS", "📜 SYSTEM LOGS", "👥 USER MANAGEMENT"],
            label_visibility="collapsed"
        )
    else:
        page = st.radio(
            "",
            ["📡 LIVE DASHBOARD", "📈 ANALYSIS"],
            label_visibility="collapsed"
        )

    st.success("🟢 SYSTEM: ONLINE")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

# ============================================
# LOAD DATA & MAP COLUMNS
# ============================================
model, scaler = load_assets()
df = get_data()

if not df.empty:
    # Optional debug expander (remove after verification)
    with st.expander("🔍 Debug: Sheet Columns"):
        st.write("**Columns found:**", list(df.columns))
        st.write("**First row:**", df.iloc[0].to_dict())
        st.write("**Last row:**", df.iloc[-1].to_dict())

    # Timestamp handling
    timestamp_col = find_column(df, possible_names=['timestamp', 'time', 'datetime'])
    if timestamp_col:
        try:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
            df = df.set_index(timestamp_col).sort_index()
        except Exception as e:
            st.warning(f"Could not parse timestamp column '{timestamp_col}': {e}")
    else:
        st.info("No timestamp column – charts will use row numbers.")

    # Sensor columns (temperature prefers Celsius)
    temp_col = find_column(df, possible_names=['temperature', 'temp', 't'], must_contain='c', exclude='f')
    if temp_col is None:
        temp_col = find_column(df, possible_names=['temperature', 'temp', 't'])
        if temp_col:
            st.warning(f"⚠️ Using '{temp_col}' for temperature – verify it's Celsius.")

    hum_col  = find_column(df, possible_names=['humidity', 'humid'])
    ph_col   = find_column(df, possible_names=['ph', 'ph level', 'ph value'])
    soil_col = find_column(df, possible_names=['soil moisture', 'moisture', 'soil'])

    # Latest values
    val_temp = df[temp_col].iloc[-1] if temp_col else 0
    val_hum  = df[hum_col].iloc[-1]  if hum_col else 0
    val_ph   = df[ph_col].iloc[-1]   if ph_col else 0
    val_soil = df[soil_col].iloc[-1] if soil_col else 0

    if not temp_col: st.warning("⚠️ Temperature column not found.")
    if not hum_col:  st.warning("⚠️ Humidity column not found.")
    if not ph_col:   st.warning("⚠️ pH column not found.")
    if not soil_col: st.warning("⚠️ Soil moisture column not found.")
else:
    val_temp = val_hum = val_ph = val_soil = 0

# ============================================
# PAGE RENDERING
# ============================================

# --- LIVE DASHBOARD ---
if page == "📡 LIVE DASHBOARD":
    st.title("Real-Time Monitoring")

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("TEMP", f"{val_temp}°C")
    with m2: st.metric("HUMIDITY", f"{val_hum}%")
    with m3: st.metric("PH", f"{val_ph}")
    with m4: st.metric("SOIL", f"{val_soil}%")

    st.markdown("---")

    col_l, col_r = st.columns([1.3, 1], gap="large")
    with col_l:
        st.subheader("📸 Plant Health Feed")
        mock_dir = "backend/mock_images"
        if os.path.exists(mock_dir):
            files = [f for f in os.listdir(mock_dir) if f.lower().endswith(('.png', '.jpg'))]
            if files:
                # Show the most recent image (sorted by name)
                st.image(os.path.join(mock_dir, sorted(files)[-1]), use_container_width=True)
            else:
                st.info("No images found. Please capture and upload images to the mock_images folder.")
        else:
            st.info("Camera feed not available. Create a folder 'backend/mock_images' and add images to simulate.")

    with col_r:
        st.subheader("🤖 AI Health Recommendation")
        if not df.empty and model and scaler and temp_col and hum_col and ph_col:
            try:
                features = np.array([[float(val_temp), float(val_hum), float(val_ph)]])
                pred = model.predict(scaler.transform(features))[0]
                if pred == -1:
                    st.error("### 🚨 ALERT\nAnomalous conditions detected. Adjusting irrigation...")
                else:
                    st.success("### ✅ HEALTHY\nCrop environment is optimal.")
            except Exception as e:
                st.info(f"Processing sensor data with AI model... (error: {e})")
        else:
            st.warning("Awaiting sensor data or AI model...")

# --- ANALYSIS PAGE ---
elif page == "📈 ANALYSIS":
    st.title("Historical Trends – Individual Sensors")

    if not df.empty:
        def plot_variable(col, title, unit=""):
            if col:
                st.subheader(f"{title}")
                chart_data = df[[col]].copy()
                chart_data[col] = pd.to_numeric(chart_data[col], errors='coerce')
                chart_data = chart_data.dropna()
                if not chart_data.empty:
                    st.line_chart(chart_data, use_container_width=True)
                    if unit:
                        st.caption(f"*Values in {unit}*")
                else:
                    st.info(f"No valid numeric data for {title}.")
            else:
                st.info(f"ℹ️ {title} data not available.")

        plot_variable(temp_col, "🌡️ Temperature", "°C")
        plot_variable(hum_col,  "💧 Humidity", "%")
        plot_variable(ph_col,   "🧪 pH Level")
        plot_variable(soil_col, "🪴 Soil Moisture", "%")
    else:
        st.warning("No historical data available yet.")

# --- SYSTEM LOGS ---
elif page == "📜 SYSTEM LOGS":
    st.title("System Activity Logs")
    if not df.empty:
        st.table(df.tail(20))
    else:
        st.warning("No logs available.")

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
# AUTO‑REFRESH
# ============================================
time.sleep(10)
st.rerun()