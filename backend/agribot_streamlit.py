# -*- coding: utf-8 -*-
import time
from datetime import datetime
import RPi.GPIO as GPIO
import smbus
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# --- 1. SYSTEM SYNC (Prevents Connection Errors) ---
os.system("sudo timedatectl set-ntp True")

# --- 2. HARDWARE SETUP ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# I2C for ADS1115 (PH and Soil Moisture)
i2c_bus = smbus.SMBus(1)
ADS1115_ADDRESS = 0x48

# DHT22 Setup
try:
    import board
    import adafruit_dht
    dht_device = adafruit_dht.DHT22(board.D4, use_pulseio=False)
except ImportError:
    print("❌ Library missing. Run: pip install adafruit-circuitpython-dht gpiod")

# --- 3. GOOGLE SHEETS SETUP ---
CREDENTIALS_FILE = 'credentials.json'
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_sheet_connection():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        return client.open("Agribot-Live-Data").sheet1
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

sheet = get_sheet_connection()

# --- 4. SENSOR FUNCTIONS ---
def read_adc_channel(channel):
    """Read raw voltage from ADS1115."""
    try:
        config = 0xC383 | (channel << 12)
        config_bytes = [(config >> 8) & 0xFF, config & 0xFF]
        i2c_bus.write_i2c_block_data(ADS1115_ADDRESS, 0x01, config_bytes)
        time.sleep(0.01)
        data = i2c_bus.read_i2c_block_data(ADS1115_ADDRESS, 0x00, 2)
        raw_adc = (data[0] << 8) | data[1]
        if raw_adc > 32767: raw_adc -= 65536
        return round((raw_adc / 32767.0) * 4.096, 4)
    except: return 0.0

def get_ph(voltage):
    """Calibrated for PH-4502C."""
    offset = -2.0 
    ph_value = 3.5 * voltage + offset
    return round(ph_value, 2)

def get_soil_moisture(voltage):
    """Calibrated for HW-080 (Dry 3.0V, Wet 1.1V)."""
    try:
        percentage = ((3.0 - voltage) / (3.0 - 1.1)) * 100
        return round(max(0, min(100, percentage)), 2)
    except: return 0.0

# --- 5. MAIN LOOP ---
print("🌱 AgriBot-AI Pi System: ONLINE")

while True:
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Read DHT22
        try:
            temp_air = dht_device.temperature
            hum_air = dht_device.humidity
            if temp_air is None or hum_air is None:
                raise RuntimeError("Sensor returned None")
        except RuntimeError:
            time.sleep(2)
            continue

        # Read Analog Sensors
        ph_volt = read_adc_channel(0)
        soil_volt = read_adc_channel(1)
        
        ph_level = get_ph(ph_volt)
        soil_moisture = get_soil_moisture(soil_volt)
        temp_f = round((temp_air * 9 / 5) + 32, 2)

        # --- 6. DATA SYNC ---
        if sheet:
            # Column order must match sheet headers:
            # Timestamp, Temperature (C), Humidity (%), Temperature (F), Soil Moisture, pH Level
            row = [timestamp, temp_air, hum_air, temp_f, soil_moisture, ph_level]
            sheet.append_row(row)
            print(f"✅ Uploaded: {temp_air}°C | {hum_air}% | pH {ph_level}")
        else:
            # Try to reconnect if connection was lost
            sheet = get_sheet_connection()
        
        time.sleep(10)

    except KeyboardInterrupt:
        print("\n⏹️ System Stopped.")
        GPIO.cleanup()
        break
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(5)