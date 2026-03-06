import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
import time
import base64

# --- 1. PAGE CONFIG & TAB LOGO ---
LOGO_PATH = "backend/agribotailogo.png"

st.set_page_config(
    page_title="AgriBot-AI | Smart Management",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🌱",
    layout="wide"
)

# --- 2. THE DESIGN MIMICRY (Modern Light UI) ---
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

# Modern CSS to mimic the uploaded mockups
css_code = """
    <style>
    /* Main Background Color */
    .stApp {
        background-color: #F0F2F5;
    }

    /* Header & Decoration Removal */
    header {visibility: hidden;}
    [data-testid="stDecoration"] { display: none; }
    
    /* Content Padding */
    .block-container {
        padding-top: 2rem !important; 
        max-width: 95% !important;
    }

    /* SIDEBAR STYLING - Bigger Navigation */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e0e0e0;
        width: 350px !important; /* Increased width */
    }

    /* Sidebar Radio Buttons (Pill Design) */
    .stRadio > div {
        gap: 15px;
        padding-top: 20px;
    }
    
    .stRadio [data-testid="stWidgetLabel"] {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #333;
        margin-bottom: 15px;
    }

    /* Making Nav options 1/3 height of metrics */
    div[data-testid="stMarkdownContainer"] p {
        font-size: 20px !important;
    }

    /* METRIC CARDS (Mimicking the image design) */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
        padding: 40px 20px !important; /* Taller boxes */
        border-radius: 20px !important;
        text-align: left !important;
    }
    
    [data-testid="stMetricValue"] { 
        font-size: 48px !important; 
        font-weight: 800 !important; 
        color: #1a1a1a !important;
    }
    
    [data-testid="stMetricLabel"] { 
        font-size: 18px !important; 
        font-weight: 600 !important; 
        color: #666 !important;
        text-transform: uppercase;
    }

    /* AI Status & Image Containers */
    .stAlert {
        border-radius: 20px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
    }
    </style>
"""

if os.path.exists(LOGO_PATH):
    bin_str = get_base64(LOGO_PATH)
    st.markdown(f'<link rel="icon" href="data:image/png;base64,{bin_str}">', unsafe_allow_html=True)

st.markdown(css_code, unsafe_allow_html=True)

# --- 3. DATA & AI LOADING (Backend remains untouched) ---
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
    st.markdown("### NAVIGATION")
    page = st.radio("", ["📡 Live Dashboard", "📈 Environmental Analysis", "📜 History & Logs"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("#### System Status: <span style='color:#22c55e'>● Connected</span>", unsafe_allow_html=True)

# --- 5. DATA PROCESSING ---
model, scaler = load_assets()
df = get_data()

if df.empty:
    latest = {"Temperature (°C)": 0, "Humidity (%)": 0, "pH Level": 0, "Soil Moisture": 0}
else:
    latest = df.iloc[-1]

# --- 6. PAGE 1: LIVE MONITOR ---
if page == "📡 Live Dashboard":
    st.title("Real-Time Monitoring")
    
    # 4 BIG WHITE CARDS (Mimicry)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Temperature", f"{latest.get('Temperature (°C)')}°C")
    m2.metric("Humidity", f"{latest.get('Humidity (%)')}%")
    m3.metric("pH Level", f"{latest.get('pH Level')}")
    m4.metric("System", "ONLINE")

    st.markdown("---")
    
    col_cam, col_ai = st.columns([1.5, 1])
    
    with col_cam:
        st.subheader("📸 Plant Health Feed")
        mock_dir = "backend/mock_images"
        if os.path.exists(mock_dir):
            files = [f for f in os.listdir(mock_dir) if f.lower().endswith(('.png', '.jpg'))]
            if files:
                latest_file = sorted(files)[-1]
                st.image(os.path.join(mock_dir, latest_file), use_container_width=True, caption="Live Camera Feed")
    
    with col_ai:
        st.subheader("🤖 AI Recommendations")
        if not df.empty and model and scaler:
            try:
                features = np.array([[float(latest['Temperature (°C)']), float(latest['Humidity (%)']), float(latest['pH Level'])]])
                prediction = model.predict(scaler.transform(features))[0]
                if prediction == -1:
                    st.error("**Condition: Anomaly Detected**\n\nRecommendation: Check pH balance and irrigation flow.")
                else:
                    st.success("**Condition: Healthy**\n\nRecommendation: Maintain current nutrient levels.")
            except: st.info("Analyzing data...")
        else:
            st.info("Waiting for sensor data connection...")

# --- OTHER PAGES (Trends & Logs) ---
elif page == "📈 Environmental Analysis":
    st.title("Sensor History")
    if not df.empty:
        st.line_chart(df[['Temperature (°C)', 'Humidity (%)']].tail(100))
        st.area_chart(df['pH Level'].tail(100))
elif page == "📜 History & Logs":
    st.title("Data History Table")
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)

# 7. REFRESH
time.sleep(10)
st.rerun()