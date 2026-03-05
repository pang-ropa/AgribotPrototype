import streamlit as st
import pandas as pd
import joblib
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np
from datetime import datetime

# 1. SETUP & AUTHENTICATION
st.set_page_config(page_title="AgriBot-AI Monitoring", layout="wide", page_icon="🌱")

@st.cache_resource
def load_ai_model():
    """Loads the Brain (Anomaly Detection)"""
    try:
        model = joblib.load('anomaly_model.pkl')
        scaler = joblib.load('anomaly_scaler.pkl')
        return model, scaler
    except:
        return None, None

def get_google_sheet_data():
    """Fetches latest data from the Cloud"""
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        # Matches your filename in Chapter III
        sheet = client.open("Agribot-AI-datasheet").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Google Sheets Connection Error: {e}")
        return pd.DataFrame()

# 2. APP LOGIC
model, scaler = load_ai_model()
df = get_google_sheet_data()

# Header
st.title("🌱 AgriBot-AI: Crop Monitoring System")
st.markdown("---")

if not df.empty:
    # Get latest data
    latest = df.iloc[-1]
    
    # 3. TOP METRICS (Real-time Numbers)
    m1, m2, m3 = st.columns(3)
    # Ensure column names match your Google Sheet exactly!
    temp = latest.get('Temperature (°C)', 0)
    hum = latest.get('Humidity (%)', 0)
    ph = latest.get('pH Level', 0)

    m1.metric("Temperature", f"{temp}°C")
    m2.metric("Humidity", f"{hum}%")
    m3.metric("pH Level", f"{ph}")

    # 4. AI ANOMALY DETECTION
    st.subheader("🤖 AI Analysis")
    if model and scaler:
        # Predict
        features = np.array([[temp, hum, ph]])
        features_scaled = scaler.transform(features)
        prediction = model.predict(features_scaled)[0] # -1 is anomaly, 1 is normal
        
        if prediction == -1:
            st.error("⚠️ ANOMALY DETECTED: Environmental levels are abnormal!")
            st.warning("Advice: Check water pH levels and greenhouse ventilation.")
        else:
            st.success("✅ SYSTEM NORMAL: Conditions are optimal for lettuce growth.")
    else:
        st.info("AI Model files not found. Displaying raw data only.")

    # 5. DATA VISUALIZATION (History)
    st.subheader("📈 Environmental Trends")
    st.line_chart(df[['Temperature (°C)', 'Humidity (%)']])
    
    # 6. DOWNLOAD REPORT (Your "Professional" Step)
    report_data = f"Agribot Report\nTime: {datetime.now()}\nTemp: {temp}\nPH: {ph}\nStatus: {'Anomaly' if prediction == -1 else 'Normal'}"
    st.download_button("Download Current Report", report_data, file_name="agribot_report.txt")

else:
    st.warning("No data found in Google Sheets. Please ensure the Raspberry Pi is sending data.")