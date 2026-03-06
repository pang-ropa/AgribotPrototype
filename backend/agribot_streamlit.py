import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# 1. PAGE CONFIG & THEME
st.set_page_config(page_title="AgriBot-AI | Smart Management", layout="wide", page_icon="🌱")

# Professional Dark Theme Styling
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #22c55e;
        padding: 15px;
        border-radius: 10px;
    }
    .stSidebar { background-color: #010409; }
    </style>
    """, unsafe_allow_html=True)

# 2. CORE FUNCTIONS
@st.cache_resource
def load_assets():
    try:
        model = joblib.load('backend/anomaly_model.pkl')
        scaler = joblib.load('backend/anomaly_scaler.pkl')
        return model, scaler
    except:
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
        sheet = client.open("Agribot-AI-datasheet").sheet1
        return pd.DataFrame(sheet.get_all_records())
    except Exception as e:
        return pd.DataFrame()

# 3. SIDEBAR NAVIGATION
st.sidebar.title("🌱 AgriBot-AI")
st.sidebar.markdown("---")
# This is how you switch between the Dashboard and the Graphs
page = st.sidebar.radio("Navigation Menu:", ["📊 Live Dashboard", "📈 Environmental Analysis", "📋 History & Logs"])

model, scaler = load_assets()
df = get_data()

if df.empty:
    st.warning("📡 Waiting for Raspberry Pi data...")
    latest = {"Temperature (°C)": 0, "Humidity (%)": 0, "pH Level": 0}
else:
    latest = df.iloc[-1]

# --- MENU 1: LIVE DASHBOARD (AI Recommendations here) ---
if page == "📊 Live Dashboard":
    st.title("Real-Time Monitoring")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Temperature", f"{latest.get('Temperature (°C)', 0)}°C")
    col2.metric("Humidity", f"{latest.get('Humidity (%)', 0)}%")
    col3.metric("pH Level", f"{latest.get('pH Level', 0)}")
    col4.metric("System", "ONLINE")

    st.markdown("---")
    
    left, right = st.columns([2, 1])
    with left:
        st.subheader("📸 Plant Health Feed")
        img_path = "backend/mock_images"
        if os.path.exists(img_path):
            imgs = [f for f in os.listdir(img_path) if f.endswith(('.jpg', '.png'))]
            if imgs: st.image(os.path.join(img_path, imgs[-1]), use_container_width=True)
            else: st.info("Camera feed offline.")

    with right:
        # HERE IS THE AI RECOMMENDATION
        st.subheader("🤖 AI Recommendations")
        if not df.empty and model and scaler:
            features = np.array([[latest['Temperature (°C)'], latest['Humidity (%)'], latest['pH Level']]])
            prediction = model.predict(scaler.transform(features))[0]
            if prediction == -1:
                st.error("### ⚠️ ANOMALY")
                st.write("**Recommendation:** Check pH and Ventilation immediately.")
            else:
                st.success("### ✅ NORMAL")
                st.write("**Recommendation:** Conditions are optimal.")

# --- MENU 2: ENVIRONMENTAL ANALYSIS (Graphs here) ---
elif page == "📈 Environmental Analysis":
    st.title("Environmental Trend Analysis")
    if not df.empty:
        # HERE ARE THE GRAPHS
        st.subheader("Temperature & Humidity History")
        st.line_chart(df[['Temperature (°C)', 'Humidity (%)']].tail(50))
        
        st.subheader("pH Level Stability")
        st.area_chart(df['pH Level'].tail(50))
    else:
        st.info("Graphs will appear once Raspberry Pi starts sending data.")

# --- MENU 3: LOGS ---
elif page == "📋 History & Logs":
    st.title("System Operation Logs")
    if not df.empty:
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)

# Auto-refresh loop
time.sleep(10)
st.rerun()