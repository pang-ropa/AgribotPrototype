import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
import time

# 1. PAGE CONFIG
st.set_page_config(page_title="AgriBot-AI | Live Monitor", layout="wide")

# 2. FARMER-READY CSS (Massive Text, No Red Headers, Clean Alignment)
st.markdown("""
    <style>
    /* Hide the red/orange Streamlit decoration line at the top */
    [data-testid="stDecoration"] { display: none; }
    
    /* Background and High Contrast */
    .stApp { background-color: #050505; color: #ffffff; }
    
    /* Massive Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #111111;
        border: 3px solid #22c55e;
        padding: 20px !important;
        border-radius: 15px;
        text-align: center;
    }
    
    /* Huge Sensor Numbers */
    [data-testid="stMetricValue"] { 
        font-size: 60px !important; 
        font-weight: 900 !important; 
        color: #22c55e !important;
    }
    
    /* Clear Sensor Labels */
    [data-testid="stMetricLabel"] { 
        font-size: 22px !important; 
        color: #ffffff !important; 
        letter-spacing: 2px;
    }

    /* Sidebar Clean-up */
    .stSidebar { background-color: #000000; border-right: 2px solid #22c55e; }
    
    /* Remove unnecessary padding */
    .block-container { padding-top: 2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. DATA & AI LOADING (Background Only)
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

# 4. SIDEBAR (Logo + Simple Navigation)
with st.sidebar:
    # Logo placement
    logo_path = "backend/agribotailogo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("<h1 style='text-align:center; color:#22c55e;'>🌱 AGRIBOT</h1>", unsafe_allow_html=True)
    
    st.markdown("---")
    # Farmers only see these simple options
    page = st.radio("GO TO:", ["📡 LIVE MONITOR", "📈 TRENDS", "📜 LOGS"], index=0)
    st.markdown("---")
    st.success("System: ONLINE")

# 5. DATA PROCESSING
model, scaler = load_assets()
# System reads live data for display
df_live = get_data("Agribot-Live-Data")

if df_live.empty:
    st.error("⚠️ SEARCHING FOR SENSOR DATA... Please check if the Raspberry Pi is plugged in.")
else:
    latest = df_live.iloc[-1]

    # --- PAGE 1: LIVE MONITOR ---
    if page == "📡 LIVE MONITOR":
        st.header("CURRENT GREENHOUSE STATUS")
        
        # Row 1: The Big Numbers
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TEMP", f"{latest.get('Temperature (°C)', 0)}°C")
        m2.metric("HUMIDITY", f"{latest.get('Humidity (%)', 0)}%")
        m3.metric("PH LEVEL", f"{latest.get('pH Level', 0)}")
        m4.metric("SOIL", f"{latest.get('Soil Moisture', 0)}%")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Row 2: Camera and AI
        col_cam, col_ai = st.columns([1.5, 1])
        
        with col_cam:
            st.subheader("📸 LIVE VIEW")
            img_path = "backend/mock_images"
            if os.path.exists(img_path):
                imgs = [f for f in os.listdir(img_path) if f.endswith(('.jpg', '.png'))]
                if imgs: st.image(os.path.join(img_path, imgs[-1]), use_container_width=True)
        
        with col_ai:
            st.subheader("🤖 AI STATUS")
            if model and scaler:
                features = np.array([[latest['Temperature (°C)'], latest['Humidity (%)'], latest['pH Level']]])
                prediction = model.predict(scaler.transform(features))[0]
                
                if prediction == -1:
                    st.error("🚨 ALERT: PROBLEM DETECTED!\nCheck water and air flow.")
                else:
                    st.success("✅ ALL GOOD: Plants are healthy.")
            
            st.markdown("---")
            st.write("**AUTO CONTROLS:**")
            st.toggle("WATER PUMP", value=(latest['pH Level'] > 6.5))
            st.toggle("FANS", value=(latest['Temperature (°C)'] > 28))

    # --- PAGE 2: TRENDS ---
    elif page == "📈 TRENDS":
        st.header("HISTORY (LAST 24 HOURS)")
        st.subheader("Temperature & Humidity")
        st.line_chart(df_live[['Temperature (°C)', 'Humidity (%)']].tail(100))
        st.subheader("pH Stability")
        st.area_chart(df_live['pH Level'].tail(100))

    # --- PAGE 3: LOGS ---
    elif page == "📜 LOGS":
        st.header("PAST READINGS")
        st.dataframe(df_live.sort_index(ascending=False), use_container_width=True)

# 6. REFRESH
time.sleep(10)
st.rerun()