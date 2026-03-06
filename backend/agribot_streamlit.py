import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
import time

# 1. PAGE CONFIG - Sets the Logo on the Website Tab
LOGO_PATH = "backend/agribotailogo.png"

st.set_page_config(
    page_title="AgriBot-AI | Monitor",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🌱",
    layout="wide"
)

# 2. ADAPTIVE CSS (Works for both Light and Dark themes)
st.markdown(f"""
    <style>
    /* Hide the red decoration line */
    [data-testid="stDecoration"] {{ display: none; }}
    
    /* Adaptable Metric Cards */
    div[data-testid="stMetric"] {{
        background-color: rgba(34, 197, 94, 0.1); /* Subtle green tint */
        border: 2px solid #22c55e;
        padding: 20px !important;
        border-radius: 15px;
        text-align: center;
    }}
    
    /* Huge Adaptive Sensor Numbers */
    [data-testid="stMetricValue"] {{ 
        font-size: 55px !important; 
        font-weight: 900 !important; 
    }}
    
    /* Clear Sensor Labels */
    [data-testid="stMetricLabel"] {{ 
        font-size: 20px !important; 
        letter-spacing: 1px;
    }}

    /* Sidebar Logo Centering */
    .sidebar-img {{
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }}
    
    .block-container {{ padding-top: 2rem !important; }}
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
    page = st.radio("MAIN MENU", ["📡 LIVE MONITOR", "📈 TRENDS", "📜 LOGS"], index=0)
    st.markdown("---")
    st.info("Status: System Active")

# 5. DATA PROCESSING
model, scaler = load_assets()
df_live = get_data("Agribot-Live-Data")

if df_live.empty:
    st.warning("⚠️ CONNECTING TO SENSORS... Please ensure the Raspberry Pi is active.")
else:
    latest = df_live.iloc[-1]

    # --- PAGE 1: LIVE MONITOR ---
    if page == "📡 LIVE MONITOR":
        st.header("GREENHOUSE REAL-TIME STATUS")
        
        # 4 Big Cards
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TEMP", f"{latest.get('Temperature (°C)', 0)}°C")
        m2.metric("HUMIDITY", f"{latest.get('Humidity (%)', 0)}%")
        m3.metric("PH LEVEL", f"{latest.get('pH Level', 0)}")
        m4.metric("SOIL", f"{latest.get('Soil Moisture', 0)}%")

        st.markdown("---")
        
        col_cam, col_ai = st.columns([1.5, 1])
        
        with col_cam:
            st.subheader("📸 PLANT PHOTO")
            # MOCK IMAGE LOGIC
            mock_path = "backend/mock_images"
            if os.path.exists(mock_path):
                imgs = [f for f in os.listdir(mock_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if imgs:
                    # Show the most recent photo
                    latest_img = sorted(imgs)[-1]
                    st.image(os.path.join(mock_path, latest_img), caption="Latest Capture", use_container_width=True)
                else:
                    st.info("No images found in backend/mock_images/")
            else:
                st.info("Missing 'backend/mock_images' folder.")
        
        with col_ai:
            st.subheader("🤖 AI ANALYSIS")
            if model and scaler:
                # Features: Temp, Hum, pH
                features = np.array([[latest['Temperature (°C)'], latest['Humidity (%)'], latest['pH Level']]])
                prediction = model.predict(scaler.transform(features))[0]
                
                if prediction == -1:
                    st.error("### 🚨 ALERT: ANOMALY\nAction: Check cooling and pH.")
                else:
                    st.success("### ✅ HEALTHY\nAction: No intervention needed.")
            
            st.markdown("---")
            st.write("**MANUAL OVERRIDE:**")
            st.toggle("WATER PUMP", value=(latest['pH Level'] > 6.5))
            st.toggle("EXHAUST FANS", value=(latest['Temperature (°C)'] > 28))

    # --- PAGE 2: TRENDS ---
    elif page == "📈 TRENDS":
        st.header("PAST PERFORMANCE")
        st.line_chart(df_live[['Temperature (°C)', 'Humidity (%)']].tail(50))
        st.area_chart(df_live['pH Level'].tail(50))

    # --- PAGE 3: LOGS ---
    elif page == "📜 LOGS":
        st.header("DATA RECORDS")
        st.dataframe(df_live.sort_index(ascending=False), use_container_width=True)

# 6. AUTO-REFRESH
time.sleep(10)
st.rerun()