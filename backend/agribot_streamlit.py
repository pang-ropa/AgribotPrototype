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

# --- PAGE CONFIG ---
LOGO_PATH = "backend/agribotailogo.png"

st.set_page_config(
    page_title="AgriBot-AI | Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# LOGIN SYSTEM
# ============================================
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "user":  {"password": "user123",  "role": "user"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

def login():
    st.title("🔐 AgriBot-AI Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = users[username]["role"]
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

if not st.session_state.logged_in:
    login()
    st.stop()

# ============================================
# CSS (WHITE UI + FORCE DARK TEXT)
# ============================================
css_code = """
<style>

/* MAIN BACKGROUND */
[data-testid="stAppViewContainer"]{
    background-color:#F6F7FB;
}

/* REMOVE HEADER */
[data-testid="stHeader"]{
    background:transparent;
}

/* FORCE TEXT COLORS */
[data-testid="stAppViewContainer"] * {
    color: #111827 !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"]{
    background:white;
    border-right:1px solid #E5E7EB;
    padding-top:20px;
}

/* SIDEBAR LOGO */
[data-testid="stSidebar"] img{
    width:60px;
    margin:auto;
    display:block;
}

/* SIDEBAR TITLE */
.sidebar-title{
    text-align:center;
    font-size:20px;
    font-weight:700;
    color:#2E7D32 !important;
    margin-top:5px;
    margin-bottom:20px;
}

/* NAVIGATION */
.stRadio label{
    font-size:16px;
    font-weight:500;
    padding:8px;
    border-radius:6px;
}
.stRadio label:hover{
    background:#F3F4F6;
}

/* METRIC CARDS */
div[data-testid="stMetric"]{
    background:white;
    border-radius:10px;
    padding:15px;
    border:1px solid #E5E7EB;
    box-shadow:0px 2px 6px rgba(0,0,0,0.05);
}

/* METRIC TEXT */
div[data-testid="stMetricLabel"]{
    color:#6B7280 !important;
    font-weight:600;
}
div[data-testid="stMetricValue"]{
    font-size:28px;
    font-weight:700;
    color:#111827 !important;
}

/* INPUTS */
input, textarea {
    color:#111827 !important;
    background:white !important;
}

/* BUTTON */
.stButton button{
    border-radius:8px;
    background:#2E7D32;
    color:white !important;
    border:none;
}

/* REMOVE STREAMLIT BRANDING */
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}

</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# ============================================
# DATA LOADING
# ============================================
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
        elif os.path.exists('backend/credentials.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('backend/credentials.json', scope)
        else:
            return pd.DataFrame()

        client = gspread.authorize(creds)
        sheet = client.open("Agribot-Live-Data").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def find_column(df, possible_names):
    for name in possible_names:
        for col in df.columns:
            if name.lower() in col.lower():
                return col
    return None

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=60)

    st.markdown('<div class="sidebar-title">AgriBot-AI</div>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        page = st.radio("Navigation", ["Dashboard", "Analysis", "System Logs", "Users"])
    else:
        page = st.radio("Navigation", ["Dashboard", "Analysis"])

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# ============================================
# LOAD DATA
# ============================================
model, scaler = load_assets()
df = get_data()

if not df.empty:
    temp_col = find_column(df, ['temp'])
    hum_col  = find_column(df, ['humid'])
    ph_col   = find_column(df, ['ph'])
    soil_col = find_column(df, ['soil'])

    val_temp = df[temp_col].iloc[-1] if temp_col else 0
    val_hum  = df[hum_col].iloc[-1] if hum_col else 0
    val_ph   = df[ph_col].iloc[-1] if ph_col else 0
    val_soil = df[soil_col].iloc[-1] if soil_col else 0
else:
    val_temp = val_hum = val_ph = val_soil = 0

# ============================================
# DASHBOARD
# ============================================
if page == "Dashboard":
    st.markdown("## Dashboard")
    st.caption("Smart Hydroponics Monitoring System")

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("🌡 Temperature", f"{val_temp}°C")
    with m2: st.metric("💧 Humidity", f"{val_hum}%")
    with m3: st.metric("🧪 pH", f"{val_ph}")
    with m4: st.metric("🌱 Soil", f"{val_soil}%")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Sensor Trends")
        if not df.empty:
            st.line_chart(df)

    with col2:
        st.subheader("AI Status")
        if model and scaler:
            st.success("System Running Normally")
        else:
            st.warning("AI Model not loaded")

# ============================================
# ANALYSIS
# ============================================
elif page == "Analysis":
    st.title("Analysis")
    if not df.empty:
        st.line_chart(df)

# ============================================
# LOGS
# ============================================
elif page == "System Logs":
    st.title("Logs")
    if not df.empty:
        st.dataframe(df.tail(20))

# ============================================
# USERS
# ============================================
elif page == "Users":
    st.title("Users")
    st.table(pd.DataFrame({
        "Username": ["admin", "user"],
        "Role": ["Admin", "User"]
    }))

# AUTO REFRESH
time.sleep(10)
st.rerun()