import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# 1. PAGE CONFIGURATION (Matches your index.html theme)
st.set_page_config(page_title="AgriBot-AI | Live System", layout="wide", page_icon="🌱")

# Custom CSS to match your "Slate" and "Green" theme from index.html
st.markdown("""
    <style>
    .main { background-color: #0f172a; color: #f8fafc; }
    div[data-testid="metric-container"] {
        background-color: #1e293b;
        border-left: 5px solid #22c55e;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNCTIONS
@st.cache_resource
def load_assets():
    """Load the Brain (Model) and Scaler"""
    try:
        model = joblib.load('anomaly_model.pkl')
        scaler = joblib.load('anomaly_scaler.pkl')
        return model, scaler
    except:
        return None, None

def get_data():
    """Fetch from Google Sheets"""
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open("Agribot-AI-datasheet").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

# 3. HEADER
st.title("🌱 AGRIBOT-AI")
st.caption("NCF-ATDC Greenhouse Monitoring System")

# 4. DATA REFRESH LOOP
model, scaler = load_assets()
df = get_data()

if not df.empty:
    latest = df.iloc[-1]
    
    # Extract Sensor Values
    temp = latest.get('Temperature (°C)', 0)
    hum = latest.get('Humidity (%)', 0)
    ph = latest.get('pH Level', 0)

    # 5. METRIC CARDS (Matches your index.html cards)
    col1, col2, col3 = st.columns(3)
    col1.metric("Temperature", f"{temp}°C")
    col2.metric("Humidity", f"{hum}%")
    
    # PH Color Logic from your index.html
    ph_status = "NORMAL"
    if ph < 5.5 or ph > 6.5:
        ph_status = "ATTENTION"
        col3.metric("pH Level", ph, delta="- OUT OF RANGE", delta_color="inverse")
    else:
        col3.metric("pH Level", ph, delta="OPTIMAL")

    st.markdown("---")

    # 6. LIVE IMAGE FEED & AI ANALYSIS
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.subheader("📸 Live AI Analysis")
        # Grabs the latest image from your mock_images folder
        img_folder = "mock_images"
        if os.path.exists(img_folder):
            images = [f for f in os.listdir(img_folder) if f.endswith(('.jpg', '.png'))]
            if images:
                st.image(os.path.join(img_folder, images[-1]), use_container_width=True)
            else:
                st.info("Waiting for camera feed...")

    with right_col:
        st.subheader("🤖 AI Recommendations")
        # Run the AI Prediction
        if model and scaler:
            features = np.array([[temp, hum, ph]])
            prediction = model.predict(scaler.transform(features))[0]
            
            if prediction == -1:
                st.error("### ⚠️ ANOMALY DETECTED")
                st.write("**Status:** Environment Unstable")
                st.write("**Advice:** Check greenhouse ventilation and water pH levels immediately.")
            else:
                st.success("### ✅ SYSTEM NORMAL")
                st.write("**Status:** Conditions Optimal")
                st.write("**Advice:** No action required. Lettuce growth is on track.")
        
        # 7. DOWNLOAD REPORT (The professional touch)
        report_text = f"AGRIBOT REPORT\nTimestamp: {datetime.now()}\nTemp: {temp}C\nHum: {hum}%\npH: {ph}"
        st.download_button("📩 Download Status Report", report_text, file_name="agribot_report.txt")

    # 8. TREND CHART (Matches your Chart.js)
    st.subheader("📈 Environmental Trends")
    # Show last 20 readings
    chart_data = df[['Temperature (°C)', 'Humidity (%)']].tail(20)
    st.line_chart(chart_data)

    # Auto-refresh logic (every 5 seconds)
    time.sleep(5)
    st.rerun()

else:
    st.error("Connection Error: Google Sheet is empty or Credentials invalid.")