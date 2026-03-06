"""
Flask Web Server for Plant Sensor Monitoring
Receives sensor data from Raspberry Pi and detects anomalies
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
import pickle
import os
from collections import deque
import numpy as np

app = Flask(__name__)

# Configuration
MAX_READINGS = 100
SENSOR_READINGS = deque(maxlen=MAX_READINGS)
PORT = 5000

# Load anomaly detection model and scaler
MODEL_PATH = 'anomaly_model.pkl'
SCALER_PATH = 'anomaly_scaler.pkl'

model = None
scaler = None

def load_model():
    """Load the pre-trained anomaly detection model"""
    global model, scaler
    try:
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            print(f"✓ Anomaly detection model loaded from {MODEL_PATH}")
        else:
            print(f"⚠ Model file not found at {MODEL_PATH}")
            model = None
            
        if os.path.exists(SCALER_PATH):
            with open(SCALER_PATH, 'rb') as f:
                scaler = pickle.load(f)
            print(f"✓ Scaler loaded from {SCALER_PATH}")
        else:
            print(f"⚠ Scaler file not found at {SCALER_PATH}")
            scaler = None
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        model = None
        scaler = None

def detect_anomaly(temperature, humidity, ph):
    """
    Detect if sensor readings are anomalous
    Returns: (is_anomaly, anomaly_score)
    """
    if model is None or scaler is None:
        # If model not loaded, use simple rule-based detection
        return check_basic_anomalies(temperature, humidity, ph)
    
    try:
        # Prepare data for model
        features = np.array([[temperature, humidity, ph]])
        features_scaled = scaler.transform(features)
        
        # Get anomaly prediction
        is_anomaly = model.predict(features_scaled)[0]
        
        # Get decision function score (if available)
        try:
            anomaly_score = abs(model.decision_function(features_scaled)[0])
        except:
            anomaly_score = float(is_anomaly)
        
        return bool(is_anomaly == -1), float(anomaly_score)
    except Exception as e:
        print(f"Error in anomaly detection: {e}")
        return check_basic_anomalies(temperature, humidity, ph)

def check_basic_anomalies(temperature, humidity, ph):
    """
    Basic rule-based anomaly detection if model is not available
    """
    is_anomaly = False
    score = 0.0
    
    # Temperature bounds (0-50°C reasonable for indoor plants)
    if temperature < 0 or temperature > 50:
        is_anomaly = True
        score += 1.0
    
    # Humidity bounds (0-100%)
    if humidity < 0 or humidity > 100:
        is_anomaly = True
        score += 1.0
    
    # pH bounds (most plants prefer 6.0-7.5)
    if ph < 4.0 or ph > 9.0:
        is_anomaly = True
        score += 1.0
    
    return is_anomaly, min(score, 3.0) / 3.0

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')

@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    """
    Receive sensor data from Raspberry Pi
    Expected JSON: {
        "temperature": float,
        "humidity": float,
        "ph": float,
        "plant_id": str (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['temperature', 'humidity', 'ph']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        temperature = float(data['temperature'])
        humidity = float(data['humidity'])
        ph = float(data['ph'])
        plant_id = data.get('plant_id', 'Plant-1')
        
        # Detect anomalies
        is_anomaly, anomaly_score = detect_anomaly(temperature, humidity, ph)
        
        # Create reading record
        reading = {
            'timestamp': datetime.now().isoformat(),
            'temperature': temperature,
            'humidity': humidity,
            'ph': ph,
            'plant_id': plant_id,
            'is_anomaly': is_anomaly,
            'anomaly_score': anomaly_score,
            'status': 'ANOMALY' if is_anomaly else 'NORMAL'
        }
        
        SENSOR_READINGS.append(reading)
        
        print(f"[{reading['timestamp']}] {plant_id} - "
              f"Temp: {temperature:.1f}°C, Humidity: {humidity:.1f}%, "
              f"pH: {ph:.2f}, Status: {reading['status']}")
        
        return jsonify({
            'success': True,
            'status': reading['status'],
            'anomaly_score': anomaly_score
        }), 200
    
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/latest', methods=['GET'])
def get_latest():
    """Get the latest sensor reading"""
    if not SENSOR_READINGS:
        return jsonify({'error': 'No readings available'}), 404
    
    latest = SENSOR_READINGS[-1]
    return jsonify(latest), 200

@app.route('/api/history', methods=['GET'])
def get_history():
    """
    Get sensor reading history
    Query params:
    - limit: number of readings (default: 100)
    - plant_id: filter by plant (optional)
    """
    limit = request.args.get('limit', 100, type=int)
    plant_id = request.args.get('plant_id', None)
    
    readings = list(SENSOR_READINGS)
    
    if plant_id:
        readings = [r for r in readings if r['plant_id'] == plant_id]
    
    readings = readings[-limit:]
    
    return jsonify({
        'count': len(readings),
        'readings': readings
    }), 200

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about sensor readings"""
    if not SENSOR_READINGS:
        return jsonify({'error': 'No readings available'}), 404
    
    plant_id = request.args.get('plant_id', None)
    readings = list(SENSOR_READINGS)
    
    if plant_id:
        readings = [r for r in readings if r['plant_id'] == plant_id]
    
    if not readings:
        return jsonify({'error': 'No readings for this plant'}), 404
    
    # Extract values
    temperatures = [r['temperature'] for r in readings]
    humidities = [r['humidity'] for r in readings]
    phs = [r['ph'] for r in readings]
    anomalies = [r for r in readings if r['is_anomaly']]
    
    stats = {
        'total_readings': len(readings),
        'anomaly_count': len(anomalies),
        'anomaly_percentage': round((len(anomalies) / len(readings) * 100), 2) if readings else 0,
        'temperature': {
            'current': readings[-1]['temperature'],
            'avg': round(np.mean(temperatures), 2),
            'min': round(np.min(temperatures), 2),
            'max': round(np.max(temperatures), 2)
        },
        'humidity': {
            'current': readings[-1]['humidity'],
            'avg': round(np.mean(humidities), 2),
            'min': round(np.min(humidities), 2),
            'max': round(np.max(humidities), 2)
        },
        'ph': {
            'current': readings[-1]['ph'],
            'avg': round(np.mean(phs), 2),
            'min': round(np.min(phs), 2),
            'max': round(np.max(phs), 2)
        },
        'last_reading_time': readings[-1]['timestamp']
    }
    
    return jsonify(stats), 200

@app.route('/api/clear', methods=['POST'])
def clear_data():
    """Clear all sensor readings (for testing)"""
    SENSOR_READINGS.clear()
    return jsonify({'success': True, 'message': 'All readings cleared'}), 200

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Plant Sensor Monitoring System - Flask Server")
    print("=" * 60)
    
    # Load anomaly detection model
    load_model()
    
    print(f"\n✓ Server starting on http://localhost:{PORT}")
    print(f"✓ Dashboard: http://localhost:{PORT}/")
    print(f"✓ API: http://localhost:{PORT}/api/sensor-data")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',  # Listen on all network interfaces
        port=PORT,
        debug=True
    )
