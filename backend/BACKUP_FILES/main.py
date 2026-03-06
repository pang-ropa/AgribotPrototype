from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import gspread
import joblib
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = FastAPI()

# 1. ENABLE CORS (Required for your index.html to talk to this script)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. LOAD AI MODELS
try:
    model = joblib.load('anomaly_model.pkl')
    scaler = joblib.load('anomaly_scaler.pkl')
    print("✓ AI Models Loaded")
except:
    model, scaler = None, None
    print("⚠ AI Models not found - running in sensor-only mode")

# 3. MOUNT IMAGES FOLDER (For your Live AI Analysis feed)
if not os.path.exists("mock_images"):
    os.makedirs("mock_images")
app.mount("/images", StaticFiles(directory="mock_images"), name="images")

# 4. GOOGLE SHEETS CONNECTION
def get_latest_from_sheets():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open("Agribot-AI-datasheet").sheet1
        data = sheet.get_all_records()
        return data[-1] if data else None
    except Exception as e:
        print(f"Error fetching from Sheets: {e}")
        return None

# 5. THE API ENDPOINT (Your index.html calls this every 3 seconds)
@app.get("/system-data")
async def get_system_data():
    row = get_latest_from_sheets()
    
    # Default values if sheet is empty
    temp = row.get('Temperature (°C)', 0) if row else 0
    hum = row.get('Humidity (%)', 0) if row else 0
    ph = row.get('pH Level', 0) if row else 0
    
    # AI Inference
    status = "Normal"
    advice = "System conditions are stable."
    if model and scaler:
        features = np.array([[temp, hum, ph]])
        prediction = model.predict(scaler.transform(features))[0]
        if prediction == -1:
            status = "Anomaly Detected"
            advice = "Warning: Environmental levels are abnormal! Check pH and Ventilation."

    # Get the latest image from the folder
    images = os.listdir("mock_images")
    selected_img = images[-1] if images else "loading.jpg"

    return {
        "sensors": {"temp": temp, "humidity": hum, "ph": ph},
        "ai_analysis": {
            "status": status, 
            "advice": advice,
            "image": selected_img
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)