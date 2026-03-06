import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
import time
import base64

# --- 1. SET PAGE CONFIG (MUST BE FIRST) ---
LOGO_PATH = "backend/agribotailogo.png"

st.set_page_config(
    page_title="AgriBot-AI | Live Monitor",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🌱",
    layout="wide"
)

# --- 2. THE "FAVICON & HEADER" HACK ---
# This forces the browser to show your logo in the tab and clears the red header line
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

header_html = ""
if os.path.exists(LOGO_PATH):
    bin_str = get_base64(LOGO_PATH)
    header_html = f'<link rel="icon" href="data:image/png;base64,{bin_str}">'

st.markdown(header_html + """
    <style>
    /* 1. HIDE THE RED DECORATION LINE */
    [data-testid="stDecoration"] { display: none; }
    
    /* 2. PUSH EVERYTHING DOWN (Fixes the "cut off" issue at the top) */
    .block-container {
        padding-top: 5.5rem !important; 
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }

    /* 3. BIG METRIC BOXES - ADAPTIVE COLORS */
    div[data-testid="stMetric"] {
        background-color: rgba(34, 197, 94, 0.1); 
        border: 3px solid #22c55e;
        padding: 25px !important;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    /* 4. MASSIVE TEXT FOR ELDERLY VISIBILITY */
    [data-testid="stMetricValue"] { 
        font-size: 65px !important; 
        font-weight: 900 !important; 
    }
    
    [data-testid="stMetricLabel"] { 
        font-size: 24px !important; 
        font-weight: 700 !important;
        text-transform: uppercase;
        color: #22c55e !important;
    }

    /* 5. SIDEBAR CLEANUP */
    section[data-testid="stSidebar"] { padding-top: 0px; }
    .stRadio > label { font-size: 22px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

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
        # ONLY READS LIVE DATA FOR FARMERS
        sheet = client.open("Agribot-Live-Data").sheet1
        return pd.DataFrame(sheet.get_all_records())
    except: return pd.DataFrame()

# --- 4. SIDEBAR ---
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.title("🌱 AGRIBOT")
    
    st.markdown("---")
    page = st.radio("GO TO:", ["📡 LIVE MONITOR", "📈 TRENDS", "📜 LOGS"], index=0)
    st.markdown("---")
    st.info("System: Active")

# --- 5. DATA PROCESSING ---
model, scaler = load_assets()
df = get_data()

# PLACEHOLDER LOGIC: If sheet is empty, show "--" so boxes don't disappear
if df.empty:
    latest = {"Temperature (°C)": "--", "Humidity (%)": "--", "pH Level": "--", "Soil Moisture": "--"}
    st.warning("📡 SEARCHING FOR PI... Boxes will update once data arrives.")
else:
    latest = df.iloc[-1]

# --- 6. PAGE 1: LIVE MONITOR ---
if page == "📡 LIVE MONITOR":
    st.header("GREENHOUSE REAL-TIME STATUS")
    
    # THE 4 BIG BOXES
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TEMP", f"{latest.get('Temperature (°C)')}°C")
    m2.metric("HUMIDITY", f"{latest.get('Humidity (%)')}%")
    m3.metric("PH LEVEL", f"{latest.get('pH Level')}")
    m4.metric("SOIL", f"{latest.get('Soil Moisture')}%")

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_cam, col_ai = st.columns([1.5, 1])
    
    with col_cam:
        st.subheader("📸 LATEST PLANT PHOTO")
        mock_dir = "backend/mock_images"
        if os.path.exists(mock_dir):
            files = [f for f in os.listdir(mock_dir) if f.lower().endswith(('.png', '.jpg'))]
            if files:
                latest_file = sorted(files)[-1]
                st.image(os.path.join(mock_dir, latest_file), use_container_width=True)
            else: st.info("No photos yet.")
        else: st.info("Create folder: backend/mock_images")
    
    with col_ai:
        st.subheader("🤖 AI ADVICE")
        if not df.empty and model and scaler:
            try:
                features = np.array([[float(latest['Temperature (°C)']), float(latest['Humidity (%)']), float(latest['pH Level'])]])
                prediction = model.predict(scaler.transform(features))[0]
                if prediction == -1:
                    st.error("### 🚨 ALERT: ANOMALY\nCheck environment immediately!")
                else:
                    st.success("### ✅ STATUS: OPTIMAL\nPlants are doing great.")
            except: st.info("AI warming up...")
        else:
            st.info("AI waiting for data...")
        
        st.markdown("---")
        st.write("**MANUAL OVERRIDE:**")
        st.toggle("WATER PUMP", value=False)
        st.toggle("FANS", value=False)

# --- PAGE 2: TRENDS ---
elif page == "📈 TRENDS":
    st.header("PERFORMANCE HISTORY")
    if not df.empty:
        st.subheader("Air Conditions")
        st.line_chart(df[['Temperature (°C)', 'Humidity (%)']].tail(100))
        st.subheader("pH Level")
        st.area_chart(df['pH Level'].tail(100))
    else: st.write("Waiting for data to graph...")

# --- PAGE 3: LOGS ---
elif page == "📜 LOGS":
    st.header("DATA RECORDS")
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)

# --- 7. REFRESH ---
time.sleep(10)
st.rerun()