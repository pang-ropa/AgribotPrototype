import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
import time

# 1. PAGE CONFIG - Sets the Logo on the Website Tab (Favicon)
LOGO_PATH = "backend/agribotailogo.png"

st.set_page_config(
    page_title="AgriBot-AI | Live Monitor",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🌱",
    layout="wide"
)

# 2. ADAPTIVE CSS (Fixes the "Red Part" and Alignment)
st.markdown(f"""
    <style>
    /* 1. HIDE THE RED DECORATION LINE COMPLETELY */
    [data-testid="stDecoration"] {{ display: none; }}
    
    /* 2. PUSH CONTENT DOWN (Fixes the "cut off" issue at the top) */
    .block-container {{
        padding-top: 4rem !important; 
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }}

    /* 3. ADAPTABLE METRIC CARDS */
    div[data-testid="stMetric"] {{
        background-color: rgba(34, 197, 94, 0.1); 
        border: 2px solid #22c55e;
        padding: 25px !important;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    
    /* 4. HUGE TEXT FOR ELDERLY VISIBILITY */
    [data-testid="stMetricValue"] {{ 
        font-size: 50px !important; 
        font-weight: 900 !important; 
    }}
    
    [data-testid="stMetricLabel"] {{ 
        font-size: 20px !important; 
        font-weight: 700 !important;
        text-transform: uppercase;
    }}

    /* 5. SIDEBAR STYLING */
    section[data-testid="stSidebar"] {{
        padding-top: 20px;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. DATA & AI LOADING
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

# 4. SIDEBAR (Navigation & Logo)
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.title("🌱 AGRIBOT")
    
    st.markdown("---")
    # Simple navigation for personnel
    page = st.radio("GO TO:", ["📡 LIVE MONITOR", "📈 TRENDS", "📜 LOGS"], index=0)
    st.markdown("---")
    st.info("System: Active")

# 5. DATA PROCESSING
model, scaler = load_assets()
df_live = get_data("Agribot-Live-Data")

if df_live.empty:
    st.warning("⚠️ CONNECTING... Ensure the Raspberry Pi is sending data to 'Agribot-Live-Data'.")
else:
    latest = df_live.iloc[-1]

    # --- PAGE 1: LIVE MONITOR ---
    if page == "📡 LIVE MONITOR":
        st.header("GREENHOUSE REAL-TIME STATUS")
        
        # Big Metric Cards
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TEMP", f"{latest.get('Temperature (°C)', 0)}°C")
        m2.metric("HUMIDITY", f"{latest.get('Humidity (%)', 0)}%")
        m3.metric("PH LEVEL", f"{latest.get('pH Level', 0)}")
        m4.metric("SOIL", f"{latest.get('Soil Moisture', 0)}%")

        st.markdown("<br>", unsafe_allow_html=True)
        
        col_cam, col_ai = st.columns([1.5, 1])
        
        with col_cam:
            st.subheader("📸 LATEST PLANT PHOTO")
            # MOCK IMAGE LOGIC: Looks inside backend/mock_images/
            mock_dir = "backend/mock_images"
            if os.path.exists(mock_dir):
                files = [f for f in os.listdir(mock_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if files:
                    # Sort by name/time and show the newest
                    latest_file = sorted(files)[-1]
                    st.image(os.path.join(mock_dir, latest_file), use_container_width=True)
                else:
                    st.info("No photos found in backend/mock_images")
            else:
                st.info("Please create a 'backend/mock_images' folder.")
        
        with col_ai:
            st.subheader("🤖 AI ANALYSIS")
            if model and scaler:
                # Features for model: Temperature, Humidity, pH
                features = np.array([[latest['Temperature (°C)'], latest['Humidity (%)'], latest['pH Level']]])
                prediction = model.predict(scaler.transform(features))[0]
                
                if prediction == -1:
                    st.error("### 🚨 ALERT: ANOMALY\nCheck environment immediately!")
                else:
                    st.success("### ✅ STATUS: OPTIMAL\nNo intervention needed.")
            
            st.markdown("---")
            st.write("**SYSTEM OVERRIDES:**")
            st.toggle("WATER PUMP", value=(latest['pH Level'] > 6.5))
            st.toggle("FANS", value=(latest['Temperature (°C)'] > 28))

    # --- PAGE 2: TRENDS ---
    elif page == "📈 TRENDS":
        st.header("PERFORMANCE HISTORY")
        st.subheader("Air Conditions")
        st.line_chart(df_live[['Temperature (°C)', 'Humidity (%)']].tail(50))
        st.subheader("Water Quality (pH)")
        st.area_chart(df_live['pH Level'].tail(50))

    # --- PAGE 3: LOGS ---
    elif page == "📜 LOGS":
        st.header("DATA RECORDS")
        st.dataframe(df_live.sort_index(ascending=False), use_container_width=True)

# 6. AUTO-REFRESH (Every 10 seconds)
time.sleep(10)
st.rerun()