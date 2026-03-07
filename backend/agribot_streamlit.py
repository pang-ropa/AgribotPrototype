import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- 1. PAGE CONFIG ---
LOGO_PATH = "backend/agribotailogo.png"

st.set_page_config(
    page_title="AgriBot-AI | Dashboard",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. THE FINAL UI FIX (BLOCKING FULLSCREEN & CENTERING LOGO) ---
css_code = """
    <style>
    /* 1. REMOVE FULLSCREEN/ENLARGE BUTTONS ON ALL IMAGES */
    button[title="View fullscreen"], 
    .st-emotion-cache-15zrgzn, 
    .st-emotion-cache-zq5wms {
        display: none !important;
    }
    
    /* Completely disable interaction with sidebar images (no hover effects) */
    [data-testid="stSidebar"] [data-testid="stImage"] {
        pointer-events: none !important;
        display: flex !important;
        justify-content: center !important;
    }

    /* 2. CENTER THE LOGO AND TITLE IN SIDEBAR */
    section[data-testid="stSidebar"] {
        width: 350px !important;
        background-color: #0E1117 !important;
        border-right: 2px solid #4CAF50;
    }

    [data-testid="stSidebar"] [data-testid="stImage"] img {
        border-radius: 50% !important;
        border: 4px solid #4CAF50 !important;
        width: 160px !important;
        height: 160px !important;
        object-fit: cover !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    .sidebar-title {
        text-align: center !important;
        color: #4CAF50 !important;
        font-size: 24px !important;
        font-weight: 800 !important;
        margin-top: 10px !important;
        width: 100% !important;
    }

    .sidebar-hr {
        height: 2px;
        background-color: #4CAF50;
        width: 50%;
        margin: 5px auto 20px auto !important;
    }

    /* 3. FIX SENSOR METRIC BOXES (GREEN GLOW) */
    div[data-testid="stMetric"] {
        background: rgba(46, 125, 50, 0.1) !important;
        border: 1px solid #4CAF50 !important;
        border-radius: 15px !important;
        padding: 15px !important;
        text-align: center !important;
    }

    /* HIDE STREAMLIT BRANDING */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# --- 3. DATA LOGIC ---
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

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH)
    
    st.markdown('<div class="sidebar-title">AgriBot-AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-hr"></div>', unsafe_allow_html=True)
    
    page = st.radio("", ["📡 LIVE DASHBOARD", "📈 ANALYSIS", "📜 SYSTEM LOGS"], label_visibility="collapsed")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.success("🟢 SYSTEM: ONLINE")

# --- 5. MAIN CONTENT ---
model, scaler = load_assets()
df = get_data()

latest = df.iloc[-1] if not df.empty else {"Temperature (°C)": 0, "Humidity (%)": 0, "pH Level": 0, "Soil Moisture": 0}

if page == "📡 LIVE DASHBOARD":
    st.title("Real-Time Monitoring")
    
    # SENSOR ROW
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("TEMP", f"{latest.get('Temperature (°C)', '0')}°C")
    with m2: st.metric("HUMIDITY", f"{latest.get('Humidity (%)', '0')}%")
    with m3: st.metric("PH", f"{latest.get('pH Level', '0')}")
    with m4: st.metric("SOIL", f"{latest.get('Soil Moisture', '0')}%")

    st.markdown("---")
    
    col_l, col_r = st.columns([1.5, 1], gap="large")
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
                    st.error("### 🚨 ANOMALY\nEnvironment unstable.")
                else:
                    st.success("### ✅ OPTIMAL\nCrop is healthy.")
            except: st.info("Analyzing data...")
        else:
            st.warning("Awaiting Raspberry Pi data...")

# Refresh every 10 seconds
time.sleep(10)
st.rerun()