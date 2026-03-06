import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
import time

# 1. PAGE CONFIG & THEME (Dark Mode IoT Aesthetic)
st.set_page_config(page_title="AgriBot-AI | Smart Management", layout="wide", page_icon="🌱")

# CUSTOM CSS FOR ALIGNMENT AND SPACING
st.markdown("""
    <style>
    /* Overall page margin and background */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Metric Card Spacing and Alignment */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #22c55e;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        text-align: center;
    }

    /* Centering Metric Content */
    [data-testid="stMetricValue"] { font-size: 32px !important; }
    [data-testid="stMetricLabel"] { font-size: 16px !important; color: #8899a6 !important; }

    /* Container for spacing between elements */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    
    /* Sidebar styling */
    .stSidebar { background-color: #010409; border-right: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA UTILITIES
@st.cache_resource
def load_assets():
    try:
        model = joblib.load('backend/anomaly_model.pkl')
        scaler = joblib.load('backend/anomaly_scaler.pkl')
        return model, scaler
    except: return None, None

def get_data(sheet_name):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name('backend/credentials.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open(sheet_name).sheet1
        return pd.DataFrame(sheet.get_all_records())
    except: return pd.DataFrame()

# 3. SIDEBAR NAVIGATION
st.sidebar.title("🌱 AgriBot-AI")
st.sidebar.caption("NCF-ATDC Greenhouse System")
st.sidebar.markdown("---")

source_mode = st.sidebar.radio("📁 Database Mode:", ["Live Data (Pi)", "Training Data (Static)"])
current_sheet = "Agribot-Live-Data" if source_mode == "Live Data (Pi)" else "Agribot-AI-Training-Data"

st.sidebar.markdown("---")
page = st.sidebar.selectbox("📍 Navigate To:", ["Live Dashboard", "Environmental Analysis", "System Logs"])

model, scaler = load_assets()
df = get_data(current_sheet)

# 4. PAGE LOGIC
if df.empty:
    st.warning(f"📡 Waiting for data in '{current_sheet}'...")
else:
    latest = df.iloc[-1]

    # --- PAGE 1: LIVE DASHBOARD ---
    if page == "Live Dashboard":
        st.title(f"🚀 {source_mode} Dashboard")
        st.write(f"**Last Sync:** {latest.get('Timestamp', 'N/A')}")
        
        # SENSOR METRICS WITH ALIGNED SPACING
        m1, m2, m3, m4 = st.columns(4, gap="medium")
        with m1: st.metric("🌡️ Temp", f"{latest.get('Temperature (°C)', 0)}°C")
        with m2: st.metric("💧 Humidity", f"{latest.get('Humidity (%)', 0)}%")
        with m3: st.metric("🧪 pH Level", f"{latest.get('pH Level', 0)}")
        with m4: st.metric("🪴 Soil Moist.", f"{latest.get('Soil Moisture', 0)}%")

        st.markdown("---")
        
        # ALIGNED CONTENT AREA
        col_img, col_ai = st.columns([1.5, 1], gap="large")
        
        with col_img:
            st.subheader("📸 Plant Monitoring Feed")
            img_path = "backend/mock_images"
            if os.path.exists(img_path):
                imgs = [f for f in os.listdir(img_path) if f.endswith(('.jpg', '.png'))]
                if imgs: st.image(os.path.join(img_path, imgs[-1]), use_container_width=True)
                else: st.info("Standby for visual data...")

        with col_ai:
            st.subheader("🤖 AI Health Recommendation")
            with st.container():
                if model and scaler:
                    # Input features must match training order
                    features = np.array([[latest['Temperature (°C)'], latest['Humidity (%)'], latest['pH Level']]])
                    prediction = model.predict(scaler.transform(features))[0]
                    
                    if prediction == -1:
                        st.error("### 🚨 ANOMALY DETECTED\n\nConditions are currently unstable. Automated correction engaged.")
                    else:
                        st.success("### ✅ SYSTEM OPTIMAL\n\nHydroponic environment is within healthy growth parameters.")
                
                st.write("---")
                st.write("**Automated Management:**")
                st.toggle("Nutrient Pump", value=(latest['pH Level'] > 6.5))
                st.toggle("Ventilation", value=(latest['Temperature (°C)'] > 28))

    # --- PAGE 2: ANALYSIS (GRAPHS) ---
    elif page == "Environmental Analysis":
        st.title("📈 Historical Trend Analysis")
        st.markdown(f"Displaying trends from **{current_sheet}**")
        
        # Spaced containers for graphs
        with st.container():
            st.subheader("Atmospheric Trends (Temp vs Humidity)")
            st.line_chart(df[['Temperature (°C)', 'Humidity (%)']].tail(100))
        
        st.write("---")
        
        with st.container():
            st.subheader("Water Quality (pH Level Stability)")
            st.area_chart(df['pH Level'].tail(100))

    # --- PAGE 3: LOGS ---
    elif page == "System Logs":
        st.title("📋 Recorded System Logs")
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)

# 5. REFRESH LOGIC
time.sleep(10)
st.rerun()