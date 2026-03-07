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

# --- 2. THE ULTIMATE UI CSS (FIXED ALIGNMENT & RETRIEVAL) ---
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

css_code = """
    <style>
    /* 1. SIDEBAR RETRIEVAL FIX: This button stays visible even when UI is 'hidden' */
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

    /* 2. SIDEBAR STYLING & PERFECT LOGO CENTERING */
    section[data-testid="stSidebar"] {
        width: 350px !important;
        background-color: #0E1117 !important;
        border-right: 2px solid #4CAF50;
    }

    /* Target the image container to force absolute center */
    [data-testid="stSidebar"] [data-testid="stImage"] {
        display: flex !important;
        justify-content: center !important;
        padding-top: 40px !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stImage"] img {
        border-radius: 50% !important;
        border: 4px solid #4CAF50 !important;
        width: 180px !important;
        height: 180px !important;
        object-fit: cover !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* 3. NAVIGATION ALIGNMENT */
    .stRadio > div {
        gap: 12px;
        padding-top: 25px;
        align-items: center;
        justify-content: center;
    }
    
    .stRadio label {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #2E7D32 !important;
        text-align: center;
        width: 100%;
        cursor: pointer;
    }

    /* 4. MAIN CONTENT CARDS */
    .block-container {
        padding: 3rem 5rem !important;
    }

    div[data-testid="stMetric"] {
        background: rgba(46, 125, 50, 0.1) !important;
        border: 2px solid #4CAF50 !important;
        border-radius: 25px !important;
        padding: 20px !important;
        text-align: center !important;
    }

    /* Hide standard Streamlit garbage */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}
    </style>
"""

st.markdown(css_code, unsafe_allow_html=True)

# --- 3. DATA & ASSETS (RE-RESTORED FULL LOGIC) ---
@st.cache_resource
def load_assets():
    try:
        model = joblib.load('backend/anomaly_model.pkl')
        scaler = joblib.load('backend/anomaly_scaler.pkl')
        return model, scaler
    except Exception as e:
        return None, None

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
        data = pd.DataFrame(sheet.get_all_records())
        return data
    except Exception as e:
        return pd.DataFrame()

# --- 4. SIDEBAR NAVIGATION ---
with st.sidebar:
    # Centered Logo
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH)
    
    st.markdown("<h2 style='text-align: center; color: #4CAF50; margin-top: -10px;'>AgriBot-AI</h2>", unsafe_allow_html=True)
    st.markdown("<div style='height: 2px; background-color: #4CAF50; margin: 5px 60px;'></div>", unsafe_allow_html=True)
    
    # Navigation Buttons
    page = st.radio("", ["📡 LIVE DASHBOARD", "📈 ANALYSIS", "📜 SYSTEM LOGS"], label_visibility="collapsed")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.success("🟢 SYSTEM: ONLINE")

# --- 5. MAIN PAGE LOGIC ---
model, scaler = load_assets()
df = get_data()

# Robust check for latest data
if not df.empty:
    latest = df.iloc[-1]
else:
    latest = {
        "Temperature (°C)": 0, 
        "Humidity (%)": 0, 
        "pH Level": 0, 
        "Soil Moisture": 0,
        "Nitrogen (mg/L)": 0,
        "Phosphorus (mg/L)": 0,
        "Potassium (mg/L)": 0
    }

if page == "📡 LIVE DASHBOARD":
    st.title("Real-Time Monitoring")
    
    # METRIC ROW
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("TEMP", f"{latest.get('Temperature (°C)', '--')}°C")
    with m2: st.metric("HUMIDITY", f"{latest.get('Humidity (%)', '--')}%")
    with m3: st.metric("PH LEVEL", f"{latest.get('pH Level', '--')}")
    with m4: st.metric("SOIL MOISTURE", f"{latest.get('Soil Moisture', '--')}%")

    st.markdown("---")
    
    # CONTENT GRID
    col_left, col_right = st.columns([1.2, 1], gap="large")
    
    with col_left:
        st.subheader("📸 Plant Health Feed")
        mock_dir = "backend/mock_images"
        if os.path.exists(mock_dir):
            files = [f for f in os.listdir(mock_dir) if f.lower().endswith(('.png', '.jpg'))]
            if files:
                st.image(os.path.join(mock_dir, sorted(files)[-1]), use_container_width=True)
            else:
                st.warning("No camera feed detected.")
    
    with col_right:
        st.subheader("🤖 AI Analysis")
        if not df.empty and model and scaler:
            try:
                # Prediction logic using model/scaler
                features = np.array([[float(latest['Temperature (°C)']), float(latest['Humidity (%)']), float(latest['pH Level'])]])
                pred = model.predict(scaler.transform(features))[0]
                if pred == -1:
                    st.error("### 🚨 ANOMALY DETECTED\nConditions outside optimal range.")
                else:
                    st.success("### ✅ HEALTHY\nGrowth conditions are stable.")
            except:
                st.info("AI Model synchronizing...")
        else:
            st.warning("Waiting for sensor/model data...")

elif page == "📈 ANALYSIS":
    st.title("Environmental Analysis")
    if not df.empty:
        st.line_chart(df[['Temperature (°C)', 'Humidity (%)', 'Soil Moisture']])
        st.subheader("NPK Levels")
        st.bar_chart(df[['Nitrogen (mg/L)', 'Phosphorus (mg/L)', 'Potassium (mg/L)']].tail(10))

elif page == "📜 SYSTEM LOGS":
    st.title("System Logs & Alerts")
    if not df.empty:
        st.table(df.tail(20))

# --- 6. AUTO-REFRESH ---
time.sleep(10)
st.rerun()