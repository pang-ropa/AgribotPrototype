import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
import time

# 1. PAGE CONFIG
st.set_page_config(page_title="AgriBot-AI | Smart Management", layout="wide", page_icon="🌱")

# 2. BALANCED UI & NAVIGATION STYLING
st.markdown("""
    <style>
    /* Main App Background */
    .stApp { background-color: #0e1117; color: #ffffff; }

    /* Sidebar Title Spacing */
    .sidebar-title {
        padding-top: 20px;
        padding-bottom: 20px;
        text-align: center;
        font-size: 28px !important;
        font-weight: 700;
        color: #22c55e;
    }

    /* Making Navigation Radio Buttons Bigger */
    div[data-testid="stSidebarNav"] { padding-top: 2rem; }
    
    /* Target the radio button labels specifically */
    div[data-testid="stWidgetLabel"] p {
        font-size: 18px !important;
        font-weight: 600 !important;
        margin-bottom: 10px !important;
    }
    
    .st-bc { font-size: 18px !important; } /* Radio text size */

    /* Balanced Container for Metrics */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #22c55e;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.6);
    }

    /* Constrain main content width for better alignment */
    .block-container {
        max-width: 1300px;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CORE FUNCTIONS
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

# 4. SIDEBAR - SPACED & BALANCED
with st.sidebar:
    st.markdown('<div class="sidebar-title">🌱 AgriBot-AI</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Selection for Database with better spacing
    source_mode = st.radio("📁 DATABASE MODE", ["Live Data (Pi)", "Training Data"], index=0)
    current_sheet = "Agribot-Live-Data" if source_mode == "Live Data (Pi)" else "Agribot-AI-Training-Data"
    
    st.markdown("<br><br>", unsafe_allow_html=True) # Extra space
    
    # Main Navigation with bigger font (handled by CSS above)
    page = st.radio("📍 NAVIGATION", ["Live Dashboard", "Environmental Analysis", "System Logs"])
    
    st.markdown("---")
    st.caption("NCF-ATDC Greenhouse System v2.0")

# 5. DATA LOADING
model, scaler = load_assets()
df = get_data(current_sheet)

# 6. MAIN CONTENT PAGES
if df.empty:
    st.warning(f"📡 Waiting for connection to {current_sheet}...")
else:
    latest = df.iloc[-1]

    # --- PAGE 1: LIVE DASHBOARD ---
    if page == "Live Dashboard":
        st.title(f"🚀 {source_mode} Monitor")
        st.write(f"**System Sync:** {latest.get('Timestamp', 'N/A')}")
        
        # Balanced Metric Row
        m1, m2, m3, m4 = st.columns(4, gap="large")
        with m1: st.metric("🌡️ TEMP", f"{latest.get('Temperature (°C)', 0)}°C")
        with m2: st.metric("💧 HUMIDITY", f"{latest.get('Humidity (%)', 0)}%")
        with m3: st.metric("🧪 pH LEVEL", f"{latest.get('pH Level', 0)}")
        with m4: st.metric("🪴 SOIL", f"{latest.get('Soil Moisture', 0)}%")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Visual Feed & AI Recommendation
        col_img, col_ai = st.columns([1.6, 1], gap="large")
        
        with col_img:
            st.subheader("📸 Live Plant Feed")
            img_path = "backend/mock_images"
            if os.path.exists(img_path):
                imgs = [f for f in os.listdir(img_path) if f.endswith(('.jpg', '.png'))]
                if imgs: st.image(os.path.join(img_path, imgs[-1]), use_container_width=True)
                else: st.info("Standby for visual data...")

        with col_ai:
            st.subheader("🤖 AI Health Report")
            if model and scaler:
                features = np.array([[latest['Temperature (°C)'], latest['Humidity (%)'], latest['pH Level']]])
                prediction = model.predict(scaler.transform(features))[0]
                
                if prediction == -1:
                    st.error("### 🚨 ANOMALY\nEnvironment unstable. Automated correction engaged.")
                else:
                    st.success("### ✅ OPTIMAL\nHydroponic environment is stable.")
            
            st.markdown("---")
            st.write("**System Overrides:**")
            st.toggle("Nutrient Dosing", value=(latest['pH Level'] > 6.5))
            st.toggle("Cooling Fans", value=(latest['Temperature (°C)'] > 28))

    # --- PAGE 2: ANALYSIS ---
    elif page == "Environmental Analysis":
        st.title("📈 Environmental Analysis")
        st.line_chart(df[['Temperature (°C)', 'Humidity (%)']].tail(100))
        st.area_chart(df['pH Level'].tail(100))

    # --- PAGE 3: LOGS ---
    elif page == "System Logs":
        st.title("📋 System Logs")
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)

# 7. REFRESH
time.sleep(10)
st.rerun()