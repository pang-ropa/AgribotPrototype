import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
import time
import base64

# --- 1. PAGE CONFIG ---
LOGO_PATH = "backend/agribotailogo.png"

st.set_page_config(
    page_title="AgriBot-AI | Dashboard",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🌱",
    layout="wide",
    initial_sidebar_state="expanded" # Ensures it starts open
)

# --- 2. CSS: ALIGNED LOGO & SIDEBAR PERSISTENCE ---
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

css_code = """
    <style>
    /* Global Reset */
    header {visibility: hidden;}
    [data-testid="stDecoration"] { display: none; }
    
    /* 1. SIDEBAR ALIGNMENT & WIDTH */
    section[data-testid="stSidebar"] {
        width: 350px !important;
        background-color: rgba(46, 125, 50, 0.05) !important;
        border-right: 2px solid #4CAF50;
    }

    /* 2. CIRCULAR LOGO - Aligned to Nav Elements */
    [data-testid="stSidebar"] [data-testid="stImage"] {
        text-align: center;
        padding-bottom: 0px !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stImage"] img {
        border-radius: 50% !important;
        border: 4px solid #4CAF50 !important;
        object-fit: cover;
        width: 180px !important; /* Slightly smaller for better nav alignment */
        height: 180px !important;
        margin: 0 auto !important;
    }

    /* 3. NAVIGATION SYMMETRY */
    .stRadio > div {
        gap: 15px;
        padding-top: 20px;
        align-items: center; /* Center nav items with the logo above */
    }
    
    .stRadio label {
        font-size: 20px !important;
        font-weight: 600 !important;
        color: #2E7D32 !important;
        text-align: center;
        width: 100%;
    }

    /* 4. THE "BACK" BUTTON (Sidebar Toggle) Fix */
    /* This ensures the arrow to bring the sidebar back is always visible and green */
    button[kind="headerNoSpacing"] {
        color: #4CAF50 !important;
        background-color: white !important;
        border-radius: 50% !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    /* 5. METRIC PILLS & CONTENT */
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 2px solid #4CAF50 !important;
        padding: 20px !important;
        border-radius: 35px !important;
        text-align: center !important;
    }

    @media (prefers-color-scheme: dark) {
        div[data-testid="stMetric"] { background: #1a1a1a !important; }
        [data-testid="stMetricValue"] { color: #81C784 !important; }
    }
    </style>
"""

st.markdown(css_code, unsafe_allow_html=True)

# --- 3. DATA & ASSETS ---
@st.cache_resource
def load_assets():
    try:
        model = joblib.load('backend/anomaly_model.pkl')
        scaler = joblib.load('backend/anomaly_scaler.pkl')
        return model, scaler
    except: return None, None

def get_data():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name('backend/credentials.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open("Agribot-Live-Data").sheet1
        return pd.DataFrame(sheet.get_all_records())
    except: return pd.DataFrame()

# --- 4. SIDEBAR (LOGO + NAV) ---
with st.sidebar:
    # Logo positioned at top center to align with navigation below
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH)
    
    st.markdown("<h3 style='text-align: center; color: #2E7D32; margin-top: -10px;'>AgriBot-AI</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Navigation list is now visually centered under the logo
    page = st.radio("", ["📡 LIVE MONITOR", "📈 GROWTH TRENDS", "📜 SYSTEM LOGS"], label_visibility="collapsed")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.success("🟢 SYSTEM ONLINE")

# --- 5. MAIN CONTENT ---
model, scaler = load_assets()
df = get_data()
latest = df.iloc[-1] if not df.empty else {"Temperature (°C)": "--", "Humidity (%)": "--", "pH Level": "--", "Soil Moisture": "--"}

if page == "📡 LIVE MONITOR":
    st.title("Real-Time Monitoring")
    
    # PILL SENSORS
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("TEMP", f"{latest.get('Temperature (°C)')}°C")
    with m2: st.metric("HUMIDITY", f"{latest.get('Humidity (%)')}%")
    with m3: st.metric("PH", f"{latest.get('pH Level')}")
    with m4: st.metric("SOIL", f"{latest.get('Soil Moisture')}%")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # SPLIT VIEW
    col_l, col_r = st.columns([1.2, 1], gap="large")
    with col_l:
        st.subheader("📸 Plant Health Feed")
        mock_dir = "backend/mock_images"
        if os.path.exists(mock_dir):
            files = [f for f in os.listdir(mock_dir) if f.lower().endswith(('.png', '.jpg'))]
            if files:
                st.image(os.path.join(mock_dir, sorted(files)[-1]), use_container_width=True)
    
    with col_r:
        st.subheader("🤖 AI Analysis")
        if not df.empty and model and scaler:
            try:
                features = np.array([[float(latest['Temperature (°C)']), float(latest['Humidity (%)']), float(latest['pH Level'])]])
                pred = model.predict(scaler.transform(features))[0]
                if pred == -1:
                    st.error("### 🚨 ANOMALY\nUnusual sensor patterns detected. Checking irrigation valves...")
                else:
                    st.success("### ✅ HEALTHY\nConditions are optimal for lettuce growth.")
            except: st.info("Syncing AI...")

# --- 6. AUTO-REFRESH ---
time.sleep(10)
st.rerun()