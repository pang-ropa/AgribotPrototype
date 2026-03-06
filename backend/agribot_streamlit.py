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
    initial_sidebar_state="expanded" 
)

# --- 2. CSS: PERSISTENT SIDEBAR & ALIGNMENT ---
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

css_code = """
    <style>
    /* Global Reset */
    header {visibility: hidden;}
    [data-testid="stDecoration"] { display: none; }
    
    /* 1. SIDEBAR BASE */
    section[data-testid="stSidebar"] {
        width: 350px !important;
        background-color: rgba(46, 125, 50, 0.05) !important;
        border-right: 2px solid #4CAF50;
    }

    /* 2. PERSISTENT RETRIEVAL BUTTON (The "Where is it?" Fix) */
    /* This styles the standard Streamlit 'open' button so it's always visible and green */
    button[kind="headerNoSpacing"] {
        display: flex !important;
        visibility: visible !important;
        left: 10px !important;
        top: 10px !important;
        color: #2E7D32 !important;
        background-color: #ffffff !important;
        border: 2px solid #4CAF50 !important;
        border-radius: 10px !important;
        z-index: 999999;
    }

    /* 3. ALIGNED CIRCULAR LOGO */
    [data-testid="stSidebar"] [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        padding-top: 20px;
    }
    
    [data-testid="stSidebar"] [data-testid="stImage"] img {
        border-radius: 50% !important;
        border: 4px solid #4CAF50 !important;
        width: 160px !important;
        height: 160px !important;
        object-fit: cover;
    }

    /* 4. NAVIGATION ALIGNMENT (Vertical Stack) */
    .stRadio > div {
        gap: 10px;
        padding: 20px 0;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    .stRadio label {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #2E7D32 !important;
        background: transparent !important;
        border: 1px solid transparent;
        transition: 0.3s;
        width: 100%;
        text-align: center;
    }

    /* 5. METRIC PILLS */
    div[data-testid="stMetric"] {
        background: white !important;
        border: 2px solid #4CAF50 !important;
        border-radius: 35px !important;
        padding: 20px !important;
        text-align: center !important;
    }

    /* Dark Mode Support */
    @media (prefers-color-scheme: dark) {
        div[data-testid="stMetric"] { background: #1a1a1a !important; }
        [data-testid="stMetricValue"] { color: #81C784 !important; }
        section[data-testid="stSidebar"] { background-color: #0E1117 !important; }
    }
    </style>
"""

st.markdown(css_code, unsafe_allow_html=True)

# --- 3. DATA LOADING ---
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
    # Centered Logo aligned with Nav
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH)
    
    st.markdown("<h2 style='text-align: center; color: #2E7D32; margin-top: -10px;'>AgriBot-AI</h2>", unsafe_allow_html=True)
    st.markdown("<div style='height: 2px; background-color: #4CAF50; margin: 10px 40px;'></div>", unsafe_allow_html=True)
    
    # Navigation list
    page = st.radio("", ["📡 DASHBOARD", "📈 ANALYSIS", "📜 LOGS"], label_visibility="collapsed")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.success("🟢 SYSTEM: ONLINE")

# --- 5. MAIN PAGE ---
model, scaler = load_assets()
df = get_data()
latest = df.iloc[-1] if not df.empty else {"Temperature (°C)": "--", "Humidity (%)": "--", "pH Level": "--", "Soil Moisture": "--"}

if page == "📡 DASHBOARD":
    st.title("Real-Time Monitoring")
    
    # SENSOR PILLS
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("TEMP", f"{latest.get('Temperature (°C)')}°C")
    with m2: st.metric("HUMIDITY", f"{latest.get('Humidity (%)')}%")
    with m3: st.metric("PH", f"{latest.get('pH Level')}")
    with m4: st.metric("SOIL", f"{latest.get('Soil Moisture')}%")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # CONTENT GRID
    col_l, col_r = st.columns([1.2, 1], gap="large")
    with col_l:
        st.subheader("📸 Plant Health Feed")
        mock_dir = "backend/mock_images"
        if os.path.exists(mock_dir):
            files = [f for f in os.listdir(mock_dir) if f.lower().endswith(('.png', '.jpg'))]
            if files:
                st.image(os.path.join(mock_dir, sorted(files)[-1]), use_container_width=True)
    
    with col_r:
        st.subheader("🤖 AI Health Status")
        if not df.empty and model and scaler:
            try:
                features = np.array([[float(latest['Temperature (°C)']), float(latest['Humidity (%)']), float(latest['pH Level'])]])
                pred = model.predict(scaler.transform(features))[0]
                if pred == -1:
                    st.error("### 🚨 ALERT\nAnomalies detected in crop environment.")
                else:
                    st.success("### ✅ OPTIMAL\nGrowth conditions are stabilized.")
            except: st.info("Syncing...")

# --- 6. AUTO-REFRESH ---
time.sleep(10)
st.rerun()