from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import random
import time
import os
import gspread
import joblib
import numpy as np
from oauth2client.service_account import ServiceAccountCredentials

app = FastAPI()

# 1. SECURITY: ENABLE CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. LOAD LAWRENCE'S AI (Anomaly Detection Model)
# These files must be in the same folder as main.py
try:
    model = joblib.load('anomaly_model.pkl')
    scaler = joblib.load('anomaly_scaler.pkl')
    print("✓ SUCCESS: Real ML Anomaly Model Loaded")
except Exception as e:
    print(f"⚠ WARNING: Model files not found. Using simulation mode. Error: {e}")
    model, scaler = None, None

# 3. GOOGLE SHEETS SETUP
# Requires 'credentials.json' in the backend folder
sheet = None
try:
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    # Ensure the Sheet name matches exactly
    spreadsheet = client.open("Agribot-AI-datasheet") 
    sheet = spreadsheet.sheet1
    print("✓ SUCCESS: Google Sheets Connected")
except Exception as e:
    print(f"⚠ WARNING: Google Sheets not connected. Check credentials.json. Error: {e}")

# 4. STATIC FILES (For Lettuce Images)
if not os.path.exists("mock_images"):
    os.makedirs("mock_images")
app.mount("/images", StaticFiles(directory="mock_images"), name="images")

# 5. THE AI LOGIC (Integrated from Lawrence's anomaly_utility.py)
def analyze_environment(temp, hum, ph):
    if model and scaler:
        # Prepare data for Lawrence's Isolation Forest model
        X = np.array([[temp, hum, ph]])
        X_normalized = scaler.transform(X)
        prediction = model.predict(X_normalized)[0] 
        
        # 1 = Normal, -1 = Anomaly
        if prediction == -1:
            return "Anomaly Detected", "Warning: Environmental levels are abnormal!"
        return "Normal", "System conditions are stable."
    
    # Fallback if no model is present
    return "Simulating", "Add model files to enable real AI."

@app.get("/system-data")
async def get_system_data():
    # Simulate current readings
    temp = round(random.uniform(20.0, 35.0), 1)
    hum = round(random.uniform(50.0, 90.0), 1)
    ph = round(random.uniform(5.0, 8.0), 1)
    
    # Run Real AI Analysis
    status, advice = analyze_environment(temp, hum, ph)
    
    # Pick a random lettuce image for the feed
    images = os.listdir("mock_images")
    selected_img = random.choice(images) if images else ""
    
    payload = {
        "sensors": {"temp": temp, "ph": ph, "humidity": hum},
        "ai_analysis": {"status": status, "image": selected_img, "advice": advice},
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Upload to Google Sheets if connected
    if sheet:
        try:
            sheet.append_row([payload["timestamp"], temp, hum, ph, status])
        except Exception as e:
            print(f"Upload failed: {e}")
            
    return payload

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)