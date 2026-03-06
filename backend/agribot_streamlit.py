import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
import time
import base64

# --- 1. PAGE CONFIG & FAVICON ---
LOGO_PATH = "backend/agribotailogo.png"

st.set_page_config(
    page_title="AgriBot-AI | Smart Monitor",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🌱",
    layout="wide"
)

# --- 2. THE "LETTUCE PALETTE" ADAPTIVE CSS ---
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

# Palette: Fresh Green (#4CAF50), Deep Leaf (#2E7D32), and soft Mint washes
css_code = """
    <style>
    /* 1. REMOVE STREAMLIT BRANDS */
    header {visibility: hidden;}
    [data-testid="stDecoration"] { display: none; }
    
    /* 2. ADAPTIVE BACKGROUND & PADDING */
    .block-container {
        padding-top: 5rem !important; 
        max-width: 95% !important;
    }

    /* 3. SIDEBAR - 1/3 Height logic for Nav */
    section[data-testid="stSidebar"] {
        width: 350px !important;
    }
    
    /* Increase Nav Menu Size */
    .stRadio > div { gap: 20px; }
    .stRadio label { 
        font-size: 22px !important; 
        font-weight: 600 !important;
        padding: 10px !important;
    }

    /* 4. METRIC BOXES - LETTUCE GRADIENT & SHADES */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(46, 125, 50, 0.05) 100%) !important;
        border: 2px solid #4CAF50 !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1) !important;
        padding: 40px 20px !important;
        border-radius: 24px !important;
        transition: transform 0.3s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: #81C784 !important;
    }
    
    /* Sensor Text Colors */
    [data-testid="stMetricValue"] { 
        font-size: 60px !important; 
        font-weight: 800 !important; 
        color: #2E7D32 !important; /* Deep Lettuce Green */
    }
    
    [data-testid="stMetricLabel"] { 
        font-size: 20px !important; 
        letter-spacing: 1.5px;
        color: #4CAF50 !important; /* Fresh Green */
    }

    /* 5. AI ALERTS - Shade Matching */
    .stAlert {
        border-radius: 20px !important;
        border-left: 10px solid #2E7D32 !important;
    }
    </style>
"""

if os.path.exists(LOGO_PATH):
    bin_str = get_base64(LOGO_PATH)
    st.markdown(f'<link rel="icon" href="data:image/png;base64,{bin_str}">', unsafe_allow_html=True)

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

# --- 4. SIDEBAR ---
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
    page = st.radio("NAVIGATION", ["📡 Live Dashboard", "📈 Environmental Analysis", "📜 System Logs"])
    st.markdown("---")
    st.markdown("<h3 style='color:#4CAF50; text-align:center;'>System: ONLINE</h3>", unsafe_allow_html=True)

# --- 5. DATA PROCESSING ---
model, scaler = load_assets()
df = get_data()

if df.empty:
    latest = {"Temperature (°C)": "--", "Humidity (%)": "--", "pH Level": "--", "Soil Moisture": "--"}
else:
    latest = df.iloc[-1]

# --- 6. MAIN CONTENT ---
if page == "📡 Live Dashboard":
    st.markdown(f"<h1 style='color:#2E7D32;'>Real-Time Monitoring</h1>", unsafe_allow_html=True)
    
    # Adaptive Sensor Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Temperature", f"{latest.get('Temperature (°C)')}°C")
    m2.metric("Humidity", f"{latest.get('Humidity (%)')}%")
    m3.metric("pH Level", f"{latest.get('pH Level')}")
    m4.metric("Soil Moisture", f"{latest.get('Soil Moisture', '--')}%")

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_cam, col_ai = st.columns([1.6, 1])
    
    with col_cam:
        st.subheader("📸 Plant Health Feed")
        mock_dir = "backend/mock_images"
        if os.path.exists(mock_dir):
            files = [f for f in os.listdir(mock_dir) if f.lower().endswith(('.png', '.jpg'))]
            if files:
                latest_file = sorted(files)[-1]
                st.image(os.path.join(mock_dir, latest_file), use_container_width=True)
    
    with col_ai:
        st.subheader("🤖 AI Health Recommendation")
        if not df.empty and model and scaler:
            try:
                features = np.array([[float(latest['Temperature (°C)']), float(latest['Humidity (%)']), float(latest['pH Level'])]])
                prediction = model.predict(scaler.transform(features))[0]
                if prediction == -1:
                    st.error("### 🚨 ANOMALY DETECTED\nConditions are deviating from the 'Lettuce Optimal' range. Auto-ventilation engaged.")
                else:
                    st.success("### ✅ HEALTHY\nEnvironment is perfectly stabilized for optimal crop growth.")
            except: st.info("Calibrating AI...")

elif page == "📈 Environmental Analysis":
    st.title("Growth Analytics")
    if not df.empty:
        st.line_chart(df[['Temperature (°C)', 'Humidity (%)']].tail(50))
    else: st.info("No historical data to visualize yet.")

elif page == "📜 System Logs":
    st.title("Data Records")
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)

# --- 7. AUTO-REFRESH ---
time.sleep(10)
st.rerun()