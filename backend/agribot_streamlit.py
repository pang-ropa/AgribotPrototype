import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
import time
import base64

# --- 1. ABSOLUTE FIRST COMMAND (FAVICON/TAB LOGO) ---
LOGO_PATH = "backend/agribotailogo.png"

st.set_page_config(
    page_title="AgriBot-AI | Live Monitor",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🌱",
    layout="wide"
)

# --- 2. THE "FORCE THEME" HACK (Kills the Crown & Fixes Alignment) ---
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

# Injecting CSS to force the UI to change
css_code = """
    <style>
    /* 1. HIDE THE STREAMLIT RED LINE & HAMBURGER MENU */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stDecoration"] { display: none; }
    
    /* 2. PUSH CONTENT DOWN (Fixes the "cut off" red part) */
    .block-container {
        padding-top: 6rem !important; 
        max-width: 95% !important;
    }

    /* 3. BIG METRIC BOXES - ADAPTIVE */
    div[data-testid="stMetric"] {
        background-color: rgba(34, 197, 94, 0.15) !important; 
        border: 4px solid #22c55e !important;
        padding: 30px !important;
        border-radius: 20px !important;
        text-align: center !important;
    }
    
    /* 4. MASSIVE TEXT FOR FARMERS */
    [data-testid="stMetricValue"] { 
        font-size: 70px !important; 
        font-weight: 900 !important; 
    }
    
    [data-testid="stMetricLabel"] { 
        font-size: 26px !important; 
        font-weight: 700 !important;
        color: #22c55e !important;
    }

    /* 5. SIDEBAR TEXT SIZE */
    .stRadio > label { font-size: 24px !important; font-weight: bold !important; }
    </style>
"""

if os.path.exists(LOGO_PATH):
    bin_str = get_base64(LOGO_PATH)
    # This specifically forces the browser tab to update
    st.markdown(f'<link rel="icon" href="data:image/png;base64,{bin_str}">', unsafe_allow_html=True)

st.markdown(css_code, unsafe_allow_html=True)

# --- 3. DATA & AI LOADING ---
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
        # ONLY READS LIVE DATA
        sheet = client.open("Agribot-Live-Data").sheet1
        return pd.DataFrame(sheet.get_all_records())
    except: return pd.DataFrame()

# --- 4. SIDEBAR ---
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    page = st.radio("CHOOSE VIEW:", ["📡 LIVE MONITOR", "📈 TRENDS", "📜 LOGS"])
    st.markdown("---")
    st.success("🟢 SYSTEM ONLINE")

# --- 5. DATA PROCESSING ---
model, scaler = load_assets()
df = get_data()

# Ensure we have placeholders so the boxes stay visible
if df.empty:
    latest = {"Temperature (°C)": "--", "Humidity (%)": "--", "pH Level": "--", "Soil Moisture": "--"}
    st.warning("📡 WAITING FOR PI CONNECTION... Sensor boxes are ready.")
else:
    latest = df.iloc[-1]

# --- 6. PAGE 1: LIVE MONITOR ---
if page == "📡 LIVE MONITOR":
    st.header("GREENHOUSE REAL-TIME STATUS")
    
    # 4 BIG BOXES
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TEMP", f"{latest.get('Temperature (°C)')}°C")
    m2.metric("HUMIDITY", f"{latest.get('Humidity (%)')}%")
    m3.metric("PH LEVEL", f"{latest.get('pH Level')}")
    m4.metric("SOIL", f"{latest.get('Soil Moisture')}%")

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_cam, col_ai = st.columns([1.5, 1])
    
    with col_cam:
        st.subheader("📸 PLANT PHOTO")
        mock_dir = "backend/mock_images"
        if os.path.exists(mock_dir):
            files = [f for f in os.listdir(mock_dir) if f.lower().endswith(('.png', '.jpg'))]
            if files:
                latest_file = sorted(files)[-1]
                st.image(os.path.join(mock_dir, latest_file), use_container_width=True)
    
    with col_ai:
        st.subheader("🤖 AI ADVICE")
        if not df.empty and model and scaler:
            try:
                # Features: Temp, Hum, pH
                features = np.array([[float(latest['Temperature (°C)']), float(latest['Humidity (%)']), float(latest['pH Level'])]])
                prediction = model.predict(scaler.transform(features))[0]
                if prediction == -1:
                    st.error("### 🚨 ALERT: ANOMALY")
                    st.write("Action: Check water pump & ventilation.")
                else:
                    st.success("### ✅ STATUS: OPTIMAL")
                    st.write("Action: No intervention needed.")
            except: st.info("Calculating...")
        
        st.markdown("---")
        st.write("**MANUAL OVERRIDE:**")
        st.toggle("WATER PUMP", value=False)
        st.toggle("FANS", value=False)

# --- OTHER PAGES ---
elif page == "📈 TRENDS":
    st.header("PAST 24 HOURS")
    if not df.empty:
        st.line_chart(df[['Temperature (°C)', 'Humidity (%)']].tail(100))
        st.area_chart(df['pH Level'].tail(100))

elif page == "📜 LOGS":
    st.header("DATA RECORDS")
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)

# --- 7. REFRESH ---
time.sleep(10)
st.rerun()