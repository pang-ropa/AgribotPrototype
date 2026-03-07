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

# --- 2. THE ULTIMATE UI CSS (FIXED LOGO & PERSISTENT TOGGLE) ---
css_code = """
    <style>
    /* 1. SIDEBAR RETRIEVAL FIX: Keep the 'Open' button visible and green */
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    button[kind="headerNoSpacing"] {
        visibility: visible !important;
        background-color: #2E7D32 !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 10px 15px !important;
        top: 15px !important;
        left: 15px !important;
        box-shadow: 0 4px 15px rgba(46, 125, 50, 0.3);
        z-index: 999999 !important;
    }

    /* 2. SIDEBAR LOGO: DEAD CENTER & NO ENLARGE BUTTONS */
    section[data-testid="stSidebar"] {
        width: 350px !important;
        background-color: #0E1117 !important;
        border-right: 2px solid #4CAF50;
    }

    /* Target the image block to remove zoom/enlarge icons */
    [data-testid="stSidebar"] [data-testid="stImage"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        padding-top: 50px !important;
        pointer-events: none !important; /* Disables enlarge/click-to-zoom */
    }
    
    [data-testid="stSidebar"] [data-testid="stImage"] img {
        border-radius: 50% !important;
        border: 4px solid #4CAF50 !important;
        width: 180px !important;
        height: 180px !important;
        object-fit: cover !important;
        margin: 0 auto !important; /* Force browser to center */
    }

    /* 3. NAVIGATION ALIGNMENT (Vertical Stack) */
    .stRadio > div {
        gap: 15px;
        padding-top: 30px;
        align-items: center;
        justify-content: center;
    }
    
    .stRadio label {
        font-size: 19px !important;
        font-weight: 600 !important;
        color: #4CAF50 !important;
        text-align: center;
        width: 100%;
        background-color: transparent !important;
    }

    /* 4. MAIN DASHBOARD CONTENT */
    .block-container {
        padding: 3rem 5rem !important;
    }

    div[data-testid="stMetric"] {
        background: rgba(46, 125, 50, 0.1) !important;
        border: 2px solid #4CAF50 !important;
        border-radius: 20px !important;
        padding: 20px !important;
        text-align: center !important;
    }

    /* HIDE STREAMLIT BRANDING */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}
    </style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# --- 3. DATA & ASSETS LOGIC ---
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
    if os.path.exists(LOGO_PATH):
        # We use a container to ensure centering logic is respected
        st.image(LOGO_PATH)
    
    st.markdown("<h2 style='text-align: center; color: #4CAF50; margin-top: -15px;'>AgriBot-AI</h2>", unsafe_allow_html=True)
    st.markdown("<div style='height: 2px; background-color: #4CAF50; margin: 0px 70px;'></div>", unsafe_allow_html=True)
    
    page = st.radio("", ["📡 LIVE DASHBOARD", "📈 ANALYSIS", "📜 SYSTEM LOGS"], label_visibility="collapsed")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.success("🟢 SYSTEM: ONLINE")

# --- 5. MAIN CONTENT ---
model, scaler = load_assets()
df = get_data()

# Ensure variables exist even if data fails
if not df.empty:
    latest = df.iloc[-1]
else:
    latest = {"Temperature (°C)": 0, "Humidity (%)": 0, "pH Level": 0, "Soil Moisture": 0}

if page == "📡 LIVE DASHBOARD":
    st.title("Real-Time Monitoring")
    
    # SENSOR ROW
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("TEMP", f"{latest.get('Temperature (°C)', '0')}°C")
    with m2: st.metric("HUMIDITY", f"{latest.get('Humidity (%)', '0')}%")
    with m3: st.metric("PH", f"{latest.get('pH Level', '0')}")
    with m4: st.metric("SOIL", f"{latest.get('Soil Moisture', '0')}%")

    st.markdown("---")
    
    col_l, col_r = st.columns([1.3, 1], gap="large")
    with col_l:
        st.subheader("📸 Plant Health Feed")
        mock_dir = "backend/mock_images"
        if os.path.exists(mock_dir):
            files = [f for f in os.listdir(mock_dir) if f.lower().endswith(('.png', '.jpg'))]
            if files:
                st.image(os.path.join(mock_dir, sorted(files)[-1]), use_container_width=True)
    
    with col_r:
        st.subheader("🤖 AI Health Analysis")
        if not df.empty and model and scaler:
            try:
                features = np.array([[float(latest['Temperature (°C)']), float(latest['Humidity (%)']), float(latest['pH Level'])]])
                pred = model.predict(scaler.transform(features))[0]
                if pred == -1:
                    st.error("### 🚨 ALERT\nAnomalous growth conditions detected.")
                else:
                    st.success("### ✅ HEALTHY\nGrowth parameters are optimal.")
            except: st.info("Synchronizing with sensor array...")
        else:
            st.warning("Waiting for Raspberry Pi data...")

elif page == "📈 ANALYSIS":
    st.title("Historical Trends")
    if not df.empty:
        st.line_chart(df[['Temperature (°C)', 'Humidity (%)', 'Soil Moisture']])

elif page == "📜 SYSTEM LOGS":
    st.title("System Event Logs")
    if not df.empty:
        st.table(df.tail(15))

# --- 6. REFRESH ---
time.sleep(10)
st.rerun()