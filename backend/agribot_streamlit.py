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
    layout="wide"
)

# --- 2. BALANCED GRID CSS (Mimicking your Drawing) ---
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

css_code = """
    <style>
    /* Global Reset */
    header {visibility: hidden;}
    [data-testid="stDecoration"] { display: none; }
    
    /* Main Content Spacing - Balanced */
    .block-container {
        padding: 3rem 5rem !important;
        max-width: 100% !important;
    }

    /* SIDEBAR - Unified with Logo as per sketch */
    section[data-testid="stSidebar"] {
        width: 350px !important;
        background-color: rgba(46, 125, 50, 0.05) !important;
        border-right: 2px solid #4CAF50;
    }
    
    /* Navigation Menu Spacing (1/3 height logic) */
    .stRadio > div {
        gap: 30px;
        padding-top: 50px;
    }
    
    .stRadio label {
        font-size: 24px !important;
        font-weight: 600 !important;
        color: #2E7D32 !important;
        padding: 15px !important;
        border-radius: 12px;
    }

    /* THE METRIC CARDS - Rounded Pills from Sketch */
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 2px solid #4CAF50 !important;
        padding: 25px !important;
        border-radius: 30px !important; /* Rounded pill style from drawing */
        box-shadow: 0 4px 10px rgba(0,0,0,0.05) !important;
        text-align: center !important;
    }

    /* LARGE TITLES */
    h1, h2, h3 {
        color: #2E7D32 !important;
        font-family: 'Inter', sans-serif;
    }

    /* CARD BALANCING: Plant Feed & AI Status */
    .element-container img {
        border-radius: 25px;
        border: 2px solid #4CAF50;
    }
    
    .stAlert {
        border-radius: 25px !important;
        padding: 2rem !important;
    }

    /* DARK/WHITE MODE ADAPTIVE TEXT */
    @media (prefers-color-scheme: dark) {
        div[data-testid="stMetric"] { background: #1a1a1a !important; }
        [data-testid="stMetricValue"] { color: #81C784 !important; }
    }
    @media (prefers-color-scheme: light) {
        [data-testid="stMetricValue"] { color: #2E7D32 !important; }
    }
    </style>
"""

if os.path.exists(LOGO_PATH):
    bin_str = get_base64(LOGO_PATH)
    st.markdown(f'<link rel="icon" href="data:image/png;base64,{bin_str}">', unsafe_allow_html=True)

st.markdown(css_code, unsafe_allow_html=True)

# --- 3. ASSET LOADING ---
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
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    st.markdown("---")
    page = st.radio("MAIN MENU", ["📡 LIVE DASHBOARD", "📈 ANALYSIS", "📜 LOGS"], label_visibility="collapsed")
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.success("🟢 SYSTEM: ONLINE")

# --- 5. CONTENT ---
model, scaler = load_assets()
df = get_data()
latest = df.iloc[-1] if not df.empty else {"Temperature (°C)": "--", "Humidity (%)": "--", "pH Level": "--", "Soil Moisture": "--"}

if page == "📡 LIVE DASHBOARD":
    st.title("Real-Time Monitoring")
    
    # ROW 1: SENSOR PILLS (Top of your sketch)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("TEMP", f"{latest.get('Temperature (°C)')}°C")
    with m2: st.metric("HUMIDITY", f"{latest.get('Humidity (%)')}%")
    with m3: st.metric("PH", f"{latest.get('pH Level')}")
    with m4: st.metric("SOIL", f"{latest.get('Soil Moisture')}%")

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # ROW 2: SPLIT VIEW (Plant Health vs AI Recommendations)
    col_left, col_right = st.columns([1.2, 1], gap="large")
    
    with col_left:
        st.subheader("📸 Plant Health Feed")
        mock_dir = "backend/mock_images"
        if os.path.exists(mock_dir):
            files = [f for f in os.listdir(mock_dir) if f.lower().endswith(('.png', '.jpg'))]
            if files:
                st.image(os.path.join(mock_dir, sorted(files)[-1]), use_container_width=True)
    
    with col_right:
        st.subheader("🤖 AI Recommendation")
        if not df.empty and model and scaler:
            try:
                features = np.array([[float(latest['Temperature (°C)']), float(latest['Humidity (%)']), float(latest['pH Level'])]])
                pred = model.predict(scaler.transform(features))[0]
                if pred == -1:
                    st.error("### 🚨 ATTENTION\nAbnormal conditions detected. Check pH and humidity levels.")
                else:
                    st.success("### ✅ OPTIMAL\nEnvironment is stabilized. No action required.")
            except: st.info("Calibrating...")
        else:
            st.info("Awaiting sensor handshake...")

# --- REFRESH ---
time.sleep(10)
st.rerun()