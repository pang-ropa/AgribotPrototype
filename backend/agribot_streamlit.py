import streamlit as st
import pandas as pd
import joblib
import gspread
import numpy as np
import os
import random
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import time
import plotly.express as px
import plotly.graph_objects as go

# --- 1. PAGE CONFIG ---
LOGO_PATH = "backend/agribotailogo.png"

st.set_page_config(
    page_title="AgriBot-AI | Dashboard",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. UI CSS (unchanged, but with minor adjustments) ---
css_code = """
    <style>
    [data-testid="stHeader"] { background-color: transparent !important; }
    button[kind="headerNoSpacing"] {
        visibility: visible !important;
        background-color: #2E7D32 !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 10px 15px !important;
        top: 15px !important;
        left: 15px !important;
        z-index: 999999 !important;
    }
    section[data-testid="stSidebar"] {
        width: 350px !important;
        background-color: #0E1117 !important;
        border-right: 2px solid #4CAF50;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: flex-start !important;
    }
    [data-testid="stSidebar"] [data-testid="stImage"] {
        pointer-events: none !important;
        user-select: none !important;
        display: flex !important;
        justify-content: center !important;
        padding-top: 40px !important;
        margin-bottom: 0px !important;
    }
    [data-testid="stSidebar"] [data-testid="stElementToolbar"] { display: none !important; }
    [data-testid="stSidebar"] [data-testid="stImage"] img {
        border-radius: 50% !important;
        border: 4px solid #4CAF50 !important;
        width: 170px !important;
        height: 170px !important;
        object-fit: cover !important;
    }
    .sidebar-title {
        text-align: center !important;
        color: #4CAF50 !important;
        font-size: 26px !important;
        font-weight: 800 !important;
        margin-top: 15px !important;
        margin-bottom: 5px !important;
        width: 100% !important;
        display: block !important;
    }
    .sidebar-hr {
        height: 3px;
        background-color: #4CAF50;
        width: 60%;
        margin: 5px auto 25px auto !important;
        border-radius: 5px;
    }
    .stRadio > div {
        gap: 10px;
        align-items: center;
        justify-content: center;
        width: 100% !important;
    }
    .stRadio label {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #4CAF50 !important;
        text-align: center;
        width: 100%;
        cursor: pointer;
    }
    div[data-testid="stMetric"] {
        background: rgba(46, 125, 50, 0.15) !important;
        border: 1px solid #4CAF50 !important;
        border-radius: 15px !important;
        padding: 15px !important;
        text-align: center !important;
    }
    div[data-testid="stMetricLabel"] {
        margin-top: 10px !important; 
        font-weight: bold !important;
        color: #A5D6A7 !important;
        justify-content: center !important;
    }
    div[data-testid="stMetricValue"] {
        margin-top: -5px !important;
        font-size: 32px !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}
    </style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# --- 3. DATA & ASSETS LOADING ---
@st.cache_resource
def load_assets():
    try:
        model = joblib.load('backend/anomaly_model.pkl')
        scaler = joblib.load('backend/anomaly_scaler.pkl')
        return model, scaler
    except:
        return None, None

model, scaler = load_assets()

# --- 4. GOOGLE SHEETS CONNECTION ---
@st.cache_resource
def get_sheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        elif os.path.exists('backend/credentials.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('backend/credentials.json', scope)
        else:
            st.error("Authentication Error: secrets.toml or credentials.json missing.")
            return None
        client = gspread.authorize(creds)
        return client.open("Agribot-Live-Data").sheet1
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

sheet = get_sheet()

# --- 5. DATA FETCHING FUNCTIONS ---
@st.cache_data(ttl=10)
def get_recent_readings():
    """Fetch all records and return latest per plant (real + simulated)."""
    if sheet is None:
        return pd.DataFrame()
    try:
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        if df.empty:
            return pd.DataFrame()
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Get latest real reading (plant_id=1)
        real_latest = df[df['plant_id'] == 1].sort_values('timestamp').iloc[-1:].copy()

        # Create simulated plants 2-10 based on real data + noise
        simulated_rows = []
        base = real_latest.iloc[0] if not real_latest.empty else None
        if base is not None:
            for pid in range(2, 11):
                new_row = base.copy()
                new_row['plant_id'] = pid
                # Add small random variations
                new_row['temp_c'] += random.uniform(-1, 1)
                new_row['humidity'] += random.uniform(-3, 3)
                new_row['soil_moisture'] += random.uniform(-5, 5)
                new_row['soil_moisture'] = max(0, min(100, new_row['soil_moisture']))
                new_row['ph1'] += random.uniform(-0.2, 0.2)
                new_row['ph1'] = max(5.0, min(7.5, new_row['ph1']))
                new_row['ph2'] = new_row['ph1'] + random.uniform(-0.1, 0.1)
                new_row['ph2'] = max(5.0, min(7.5, new_row['ph2']))
                # Use mock image
                mock_dir = "backend/mock_images"
                if os.path.exists(mock_dir):
                    mock_files = sorted([f for f in os.listdir(mock_dir) if f.lower().endswith(('.png','.jpg','.jpeg'))])
                    if mock_files and pid-1 < len(mock_files):
                        new_row['image_path'] = os.path.join(mock_dir, mock_files[pid-1])
                    else:
                        new_row['image_path'] = ""
                else:
                    new_row['image_path'] = ""
                simulated_rows.append(new_row)

        # Combine real and simulated
        if base is not None:
            real_latest['image_path'] = ""  # real plant may not have image yet
            final_df = pd.concat([real_latest] + simulated_rows, ignore_index=True)
        else:
            final_df = pd.DataFrame()
        return final_df
    except Exception as e:
        st.error(f"Data fetch error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_historical_data(plant_id=None, hours=24):
    """Return real historical data for a specific plant (if exists)."""
    if sheet is None:
        return pd.DataFrame()
    try:
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        if df.empty:
            return df
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        cutoff = datetime.now() - timedelta(hours=hours)
        df = df[df['timestamp'] >= cutoff]
        if plant_id is not None:
            df = df[df['plant_id'] == plant_id]
        return df.sort_values('timestamp')
    except:
        return pd.DataFrame()

# --- 6. SIDEBAR ---
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH)
    
    st.markdown('<div class="sidebar-title">AgriBot-AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-hr"></div>', unsafe_allow_html=True)
    
    page = st.radio("", ["📡 LIVE DASHBOARD", "📈 ANALYSIS", "📜 SYSTEM LOGS"], label_visibility="collapsed")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.success("🟢 SYSTEM: ONLINE")

# --- 7. MAIN CONTENT ---
if page == "📡 LIVE DASHBOARD":
    st.title("Real-Time Monitoring")
    
    latest = get_recent_readings()
    if latest.empty:
        st.warning("No data yet. Waiting for sensor readings...")
        st.stop()
    
    # Top metrics (averages across all 10 plants)
    avg_temp = latest['temp_c'].mean()
    avg_hum = latest['humidity'].mean()
    avg_ph = (latest['ph1'].mean() + latest['ph2'].mean()) / 2
    avg_soil = latest['soil_moisture'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌡️ TEMP", f"{avg_temp:.1f} °C")
    col2.metric("💧 HUMIDITY", f"{avg_hum:.0f} %")
    col3.metric("🧪 pH (avg)", f"{avg_ph:.2f}")
    col4.metric("🌱 SOIL (avg)", f"{avg_soil:.0f} %")
    
    st.markdown("---")
    
    col_l, col_r = st.columns([1.3, 1], gap="large")
    
    with col_l:
        st.subheader("🌿 Plant Health Feed")
        latest = latest.sort_values('plant_id')
        # Display in 2 rows of 5
        row1 = st.columns(5)
        row2 = st.columns(5)
        for idx, (_, plant) in enumerate(latest.iterrows()):
            col = row1[idx] if idx < 5 else row2[idx-5]
            pid = int(plant['plant_id'])
            soil = plant['soil_moisture']
            ph_avg = (plant['ph1'] + plant['ph2']) / 2
            
            health = "✅ Healthy"
            if soil < 30:
                health = "⚠️ Dry"
            elif soil > 80:
                health = "⚠️ Wet"
            if ph_avg < 5.5 or ph_avg > 6.5:
                health = "🔴 pH Alert"
            
            with col:
                # Image
                img_path = plant['image_path']
                if img_path and os.path.exists(img_path):
                    st.image(img_path, width=100)
                else:
                    st.markdown("<span style='font-size:2rem;'>🥬</span>", unsafe_allow_html=True)
                st.markdown(f"**Lettuce #{pid}**<br>{health}<br>Soil: {soil:.0f}%", unsafe_allow_html=True)
    
    with col_r:
        st.subheader("🤖 AI Health Recommendation")
        # Use the most recent real plant data for AI (plant 1)
        real_plant = latest[latest['plant_id'] == 1]
        if not real_plant.empty and model and scaler:
            try:
                temp_val = float(real_plant.iloc[0]['temp_c'])
                hum_val  = float(real_plant.iloc[0]['humidity'])
                ph_val   = (float(real_plant.iloc[0]['ph1']) + float(real_plant.iloc[0]['ph2'])) / 2
                features = np.array([[temp_val, hum_val, ph_val]])
                pred = model.predict(scaler.transform(features))[0]
                if pred == -1:
                    st.error("### 🚨 ALERT\nAnomalous conditions detected. Adjusting irrigation...")
                else:
                    st.success("### ✅ HEALTHY\nCrop environment is optimal.")
            except Exception as e:
                st.info(f"Processing sensor data with AI model... (error: {e})")
        else:
            st.warning("Awaiting sensor data or missing model.")
        
        # Show recent alerts
        st.markdown("### 🔔 Recent Alerts")
        alerts = []
        for _, plant in latest.iterrows():
            pid = int(plant['plant_id'])
            if plant['soil_moisture'] < 20 or plant['soil_moisture'] > 80:
                alerts.append(f"🌱 Plant {pid} soil: {plant['soil_moisture']:.0f}%")
            avg_ph = (plant['ph1'] + plant['ph2']) / 2
            if avg_ph < 5.5 or avg_ph > 6.5:
                alerts.append(f"🧪 Plant {pid} pH: {avg_ph:.2f}")
        if avg_temp < 15 or avg_temp > 30:
            alerts.append(f"🌡️ Temp out of range: {avg_temp:.1f}°C")
        if avg_hum < 50 or avg_hum > 85:
            alerts.append(f"💧 Humidity out of range: {avg_hum:.0f}%")
        if alerts:
            for alert in alerts[:5]:
                st.markdown(f'<div style="padding:5px; background:#ffebee; color:#b71c1c; border-radius:5px; margin:5px 0;">{alert}</div>', unsafe_allow_html=True)
        else:
            st.info("✅ All parameters within range.")

elif page == "📈 ANALYSIS":
    st.title("Historical Trends – Individual Sensors")
    
    # Controls
    col_s1, col_s2, col_s3 = st.columns([1,1,2])
    with col_s1:
        sensor_choice = st.selectbox("Sensor", ["Temperature (°C)", "Humidity (%)", "pH (avg)", "Soil Moisture (%)"])
    with col_s2:
        plant_sel = st.selectbox("Plant", list(range(1,11)))
    with col_s3:
        time_range = st.selectbox("Time range", ["24 hours", "7 days", "30 days"])
        hours = 24 if time_range == "24 hours" else (168 if time_range == "7 days" else 720)
    
    # Fetch real historical data for selected plant
    hist_df = get_historical_data(plant_id=plant_sel, hours=hours)
    
    if not hist_df.empty:
        if sensor_choice == "Temperature (°C)":
            y_col = 'temp_c'
            title = f"Temperature - Plant {plant_sel}"
            y_label = "°C"
        elif sensor_choice == "Humidity (%)":
            y_col = 'humidity'
            title = f"Humidity - Plant {plant_sel}"
            y_label = "%"
        elif sensor_choice == "pH (avg)":
            hist_df['ph_avg'] = (hist_df['ph1'] + hist_df['ph2']) / 2
            y_col = 'ph_avg'
            title = f"pH (avg) - Plant {plant_sel}"
            y_label = "pH"
        else:  # Soil Moisture
            y_col = 'soil_moisture'
            title = f"Soil Moisture - Plant {plant_sel}"
            y_label = "%"
        
        fig = px.line(hist_df, x='timestamp', y=y_col, title=title)
        fig.update_layout(yaxis_title=y_label)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No historical data for this plant yet. Only plant 1 has real data until more sensors are added.")

elif page == "📜 SYSTEM LOGS":
    st.title("System Activity Logs")
    logs = get_historical_data(plant_id=None, hours=24)
    if not logs.empty:
        # Add event classification
        def classify(row):
            if row['temp_c'] < 15 or row['temp_c'] > 30:
                return "🌡️ Temp alert"
            if row['humidity'] < 50 or row['humidity'] > 85:
                return "💧 Humidity alert"
            avg_ph = (row['ph1'] + row['ph2']) / 2
            if avg_ph < 5.5 or avg_ph > 6.5:
                return "🧪 pH alert"
            if row['soil_moisture'] < 20 or row['soil_moisture'] > 80:
                return "🌱 Soil alert"
            return "Normal"
        logs['event'] = logs.apply(classify, axis=1)
        st.dataframe(
            logs[['timestamp', 'plant_id', 'temp_c', 'humidity', 'ph1', 'ph2', 'soil_moisture', 'event']].tail(20),
            use_container_width=True,
            hide_index=True,
            column_config={
                "timestamp": "Time",
                "plant_id": "Plant",
                "temp_c": "Temp (°C)",
                "humidity": "Hum (%)",
                "ph1": "pH1",
                "ph2": "pH2",
                "soil_moisture": "Soil %",
                "event": "Event"
            }
        )
    else:
        st.info("No logs available.")

# --- 8. AUTO-REFRESH ---
time.sleep(10)
st.rerun()