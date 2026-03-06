import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
import time

# 1. PAGE CONFIG
st.set_page_config(page_title="AgriBot-AI | Monitor", layout="wide")

# 2. ELDERLY-FRIENDLY UI STYLING (High Contrast, Big Text)
st.markdown("""
    <style>
    /* Dark background for high contrast */
    .stApp { background-color: #050505; color: #ffffff; }

    /* HUGE Sidebar Title and Navigation */
    .sidebar-logo { text-align: center; margin-bottom: 10px; }
    .st-emotion-cache-17l363p { font-size: 24px !important; font-weight: bold; } /* Sidebar labels */
    
    /* BIG METRIC CARDS - No extra space */
    div[data-testid="stMetric"] {
        background-color: #111111;
        border: 2px solid #22c55e;
        padding: 15px !important;
        border-radius: 10px;
        text-align: center;
    }
    
    /* Make the numbers MASSIVE for easy reading */
    [data-testid="stMetricValue"] { 
        font-size: 50px !important; 
        font-weight: 800 !important; 
        color: #22c55e !important;
    }
    [data-testid="stMetricLabel"] { 
        font-size: 20px !important; 
        color: #ffffff !important; 
        text-transform: uppercase;
    }

    /* Tighten the block spacing */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-width: 95% !important;
    }

    /* Big Bold Buttons/Toggles */
    .stHeader { font-size: 30px !important; }
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

# 4. SIDEBAR - SIMPLE & BIG
with st.sidebar:
    # --- LOGO SECTION ---
    # Put your logo file in the 'backend' folder and name it 'logo.png'
    if os.path.exists("backend/logo.png"):
        st.image("backend/logo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align:center; color:#22c55e;'>🌱 AGRIBOT-AI</h1>", unsafe_allow_html=True)
    
    st.markdown("---")
    page = st.radio("SELECT VIEW:", ["📡 LIVE MONITOR", "📈 TRENDS", "📜 HISTORY"], index=0)
    st.markdown("---")
    source = st.selectbox("DATA SOURCE:", ["Live Data (Pi)", "Training Data"])
    current_sheet = "Agribot-Live-Data" if source == "Live Data (Pi)" else "Agribot-AI-Training-Data"

# 5. MAIN CONTENT
model, scaler = load_assets()
df = get_data(current_sheet)

if df.empty:
    st.error("⚠️ NO DATA! Please check if the Raspberry Pi is turned ON.")
else:
    latest = df.iloc[-1]

    if page == "📡 LIVE MONITOR":
        st.header(f"CURRENT SYSTEM STATUS")
        
        # 4 BIG CARDS - NO GAP
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TEMP", f"{latest.get('Temperature (°C)', 0)}°C")
        m2.metric("HUMIDITY", f"{latest.get('Humidity (%)', 0)}%")
        m3.metric("PH", f"{latest.get('pH Level', 0)}")
        m4.metric("SOIL", f"{latest.get('Soil Moisture', 0)}%")

        st.markdown("---")
        
        col_img, col_ai = st.columns([1.2, 1])
        
        with col_img:
            st.subheader("📸 LIVE PLANT VIEW")
            img_path = "backend/mock_images"
            if os.path.exists(img_path):
                imgs = [f for f in os.listdir(img_path) if f.endswith(('.jpg', '.png'))]
                if imgs: st.image(os.path.join(img_path, imgs[-1]), use_container_width=True)
        
        with col_ai:
            st.subheader("🤖 AI ADVICE")
            if model and scaler:
                features = np.array([[latest['Temperature (°C)'], latest['Humidity (%)'], latest['pH Level']]])
                prediction = model.predict(scaler.transform(features))[0]
                
                if prediction == -1:
                    st.error("🚨 PROBLEM DETECTED!\nCheck water and fans.")
                else:
                    st.success("✅ EVERYTHING OK\nNo action needed.")
            
            st.markdown("---")
            st.write("**SYSTEM CONTROL:**")
            st.toggle("WATER PUMP", value=(latest['pH Level'] > 6.5))
            st.toggle("FANS", value=(latest['Temperature (°C)'] > 28))

    elif page == "📈 TRENDS":
        st.header("PAST 24 HOURS")
        st.line_chart(df[['Temperature (°C)', 'Humidity (%)']].tail(50))
        st.area_chart(df['pH Level'].tail(50))

    elif page == "📜 HISTORY":
        st.header("DATA LOGS")
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)

# 6. REFRESH
time.sleep(10)
st.rerun()