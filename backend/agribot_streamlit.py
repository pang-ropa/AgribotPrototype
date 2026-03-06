import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# 1. PAGE CONFIG & STYLING (Inspired by SmartHydro UI)
st.set_page_config(page_title="AgriBot-AI | Smart Management", layout="wide", page_icon="🌱")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    [data-testid="stMetricValue"] { font-size: 24px; color: #1f77b4; }
    .stSidebar { background-color: #0e1117; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA UTILITIES
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
    except:
        return pd.DataFrame()

# 3. SIDEBAR NAVIGATION (Matching Thesis Design)
st.sidebar.title("🌱 AgriBot-AI")
st.sidebar.write("Logged in as: **Admin**")
page = st.sidebar.radio("Navigation", ["Dashboard", "Environmental Analysis", "Summary Report", "System Logs"])

model, scaler = load_assets()
df = get_data()

# 4. PAGE LOGIC
if df.empty:
    st.error("⚠️ No data found. Ensure the Raspberry Pi is sending data to Google Sheets.")
else:
    # PAGE 1: MAIN DASHBOARD
    if page == "Dashboard":
        st.title("SmartHydro Dashboard")
        latest = df.iloc[-1]
        
        # Real-time Metrics (Thesis Fig 4)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Temperature", f"{latest['Temperature (°C)']}°C")
        c2.metric("Humidity", f"{latest['Humidity (%)']}%")
        c3.metric("pH Level", latest['pH Level'])
        c4.metric("Light Level", "--- LUX") # Placeholder for Lux sensor mentioned in thesis

        st.markdown("### 🤖 AI System Status")
        features = np.array([[latest['Temperature (°C)'], latest['Humidity (%)'], latest['pH Level']]])
        prediction = model.predict(scaler.transform(features))[0] if model else 1
        
        if prediction == -1:
            st.error("🚨 ANOMALY DETECTED: Parameters are outside optimal growth range!")
        else:
            st.success("✅ SYSTEM NORMAL: Environment is stable.")

    # PAGE 2: ANALYSIS (Thesis Fig 5)
    elif page == "Environmental Analysis":
        st.title("📈 Detailed Trend Analysis")
        tab1, tab2 = st.tabs(["pH & Nutrients", "Temperature & Humidity"])
        
        with tab1:
            st.subheader("pH Level Variations")
            st.line_chart(df['pH Level'].tail(50))
        with tab2:
            st.subheader("Temp & Humidity Trends")
            st.line_chart(df[['Temperature (°C)', 'Humidity (%)']].tail(50))

    # PAGE 3: SUMMARY REPORT (Thesis Fig 6)
    elif page == "Summary Report":
        st.title("📊 Historical Data Summary")
        # Added Filter Logic from Thesis
        filter_opt = st.selectbox("Filter Data:", ["All Data", "Latest 10", "Latest 50"])
        
        display_df = df.copy()
        if filter_opt == "Latest 10": display_df = df.tail(10)
        elif filter_opt == "Latest 50": display_df = df.tail(50)
        
        st.dataframe(display_df.sort_index(ascending=False), use_container_width=True)

    # PAGE 4: LOGS (Thesis Fig 7)
    elif page == "System Logs":
        st.title("📋 Operation Logs")
        st.info("Logs the activation of components based on AI decisions.")
        
        # Simulated log generation based on current data
        log_data = []
        for i, row in df.tail(10).iterrows():
            status = "Normal"
            msg = "Systems Idle"
            if row['pH Level'] < 5.5: 
                status = "Alert"; msg = "pH Low: Turning ON pH Up Motor"
            elif row['Temperature (°C)'] > 30: 
                status = "Alert"; msg = "High Temp: Exhaust Fan ON"
            
            log_data.append({"Timestamp": row.get('Timestamp', 'N/A'), "Status": status, "Message": msg})
        
        st.table(pd.DataFrame(log_data))

# Auto-refresh every 30 seconds
time.sleep(30)
st.rerun()