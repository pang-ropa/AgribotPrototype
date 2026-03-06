import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
import time

# 1. PAGE CONFIG & FAVICON (Tab Logo)
# MUST BE THE FIRST COMMAND
LOGO_PATH = "backend/agribotailogo.png"

st.set_page_config(
    page_title="AgriBot-AI | Live Monitor",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🌱",
    layout="wide"
)

# 2. THE "FORCE LOGO" & THEME FIX
# This piece of code forces the browser to replace the Streamlit Crown with your logo
if os.path.exists(LOGO_PATH):
    import base64
    def get_base64(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    
    bin_str = get_base64(LOGO_PATH)
    st.markdown(f"""
        <link rel="icon" href="data:image/png;base64,{bin_str}">
        <style>
            /* HIDE THE RED LINE AT TOP */
            [data-testid="stDecoration"] {{ display: none; }}
            
            /* PUSH EVERYTHING DOWN SO IT'S VISIBLE */
            .block-container {{
                padding-top: 5rem !important; 
                max-width: 95% !important;
            }}

            /* ADAPTIVE BOXES - FORCE VISIBILITY */
            div[data-testid="stMetric"] {{
                background-color: rgba(34, 197, 94, 0.1); 
                border: 3px solid #22c55e;
                padding: 25px !important;
                border-radius: 15px;
                text-align: center;
            }}
            
            /* BIG TEXT FOR ELDERLY */
            [data-testid="stMetricValue"] {{ font-size: 55px !important; font-weight: 900 !important; }}
            [data-testid="stMetricLabel"] {{ font-size: 22px !important; font-weight: 700 !important; }}
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

# 4. SIDEBAR
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.title("🌱 AGRIBOT")
    
    st.markdown("---")
    page = st.radio("GO TO:", ["📡 LIVE MONITOR", "📈 TRENDS", "📜 LOGS"], index=0)
    st.markdown("---")
    st.info("System: Monitoring Active")

# 5. DATA PROCESSING
model, scaler = load_assets()
df_live = get_data("Agribot-Live-Data")

# --- AUTO-APPEAR LOGIC ---
# If the sheet is empty, we show "Empty" boxes so the user sees the design
if df_live.empty:
    latest = {"Temperature (°C)": "--", "Humidity (%)": "--", "pH Level": "--", "Soil Moisture": "--"}
    st.warning("📡 WAITING FOR RASPBERRY PI... The boxes will update once the sensor starts.")
else:
    latest = df_live.iloc[-1]

# --- PAGE 1: LIVE MONITOR ---
if page == "📡 LIVE MONITOR":
    st.header("GREENHOUSE REAL-TIME STATUS")
    
    # THE BOXES ARE BACK (Static placeholders if no data, real numbers if data exists)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TEMP", f"{latest.get('Temperature (°C)')}°C")
    m2.metric("HUMIDITY", f"{latest.get('Humidity (%)')}%")
    m3.metric("PH LEVEL", f"{latest.get('pH Level')}")
    m4.metric("SOIL", f"{latest.get('Soil Moisture')}%")

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_cam, col_ai = st.columns([1.5, 1])
    
    with col_cam:
        st.subheader("📸 LATEST PHOTO")
        mock_dir = "backend/mock_images"
        if os.path.exists(mock_dir):
            files = [f for f in os.listdir(mock_dir) if f.lower().endswith(('.png', '.jpg'))]
            if files:
                latest_file = sorted(files)[-1]
                st.image(os.path.join(mock_dir, latest_file), use_container_width=True)
            else: st.info("No photos yet.")
    
    with col_ai:
        st.subheader("🤖 AI ANALYSIS")
        # Only try to predict if we actually have numbers (not "--")
        if not df_live.empty and model and scaler:
            features = np.array([[latest['Temperature (°C)'], latest['Humidity (%)'], latest['pH Level']]])
            prediction = model.predict(scaler.transform(features))[0]
            if prediction == -1: st.error("### 🚨 ALERT: ANOMALY")
            else: st.success("### ✅ STATUS: NORMAL")
        else:
            st.info("AI waiting for sensor data...")

# --- OTHER PAGES ---
elif page == "📈 TRENDS":
    st.header("PERFORMANCE HISTORY")
    if not df_live.empty:
        st.line_chart(df_live[['Temperature (°C)', 'Humidity (%)']].tail(50))
    else: st.write("No data to graph yet.")

elif page == "📜 LOGS":
    st.header("DATA RECORDS")
    st.dataframe(df_live.sort_index(ascending=False), use_container_width=True)

# 6. REFRESH
time.sleep(10)
st.rerun()