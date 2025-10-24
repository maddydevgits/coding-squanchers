from flask import Flask, render_template, jsonify, request
from flask_pymongo import PyMongo
from pymongo import MongoClient
import paho.mqtt.client as mqtt
import json
import threading
import time
from datetime import datetime, timedelta
import os
from bson import ObjectId
import statistics
import math

app = Flask(__name__)

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/smart_bed_db')
app.config['MONGO_URI'] = MONGODB_URI

# Initialize MongoDB
mongo = PyMongo(app)
db = mongo.db

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "SmartBedDashboard"

# Global variables to store latest sensor data
latest_data = {
    'bmp280_temperature': 0,
    'bmp280_pressure': 0,
    'bmp280_humidity': 0,
    'dht11_temperature': 0,
    'dht11_humidity': 0,
    'heartrate': 0,
    'spo2': 0,
    'flame_detected': False,
    'timestamp': 0,
    'last_updated': None
}

# MQTT Topics
TOPICS = [
    "sensors/temperature",
    "sensors/pressure", 
    "sensors/humidity",
    "sensors/dht11_temperature",
    "sensors/dht11_humidity",
    "sensors/heartrate",
    "sensors/spo2",
    "sensors/flame",
    "sensors/status"
]

def on_mqtt_connect(client, userdata, flags, rc):
    """Callback for when the MQTT client connects to the broker."""
    if rc == 0:
        print(f"✅ Connected to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
        print("📡 Subscribing to sensor topics...")
        
        # Subscribe to all topics
        for topic in TOPICS:
            client.subscribe(topic)
            print(f"   📋 Subscribed to: {topic}")
        
        print("🔄 MQTT client ready to receive data...")
    else:
        print(f"❌ Failed to connect to MQTT broker. Return code: {rc}")

def on_mqtt_message(client, userdata, msg):
    """Callback for when a message is received from MQTT."""
    global latest_data
    
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    timestamp = datetime.now()
    
    try:
        if topic == "sensors/status":
            # Parse JSON data
            data = json.loads(payload)
            data['timestamp'] = int(data.get('timestamp', time.time() * 1000))
            data['received_at'] = timestamp
            
            # Update global data
            latest_data.update({
                'bmp280_temperature': data.get('bmp280_temperature', 0),
                'bmp280_pressure': data.get('bmp280_pressure', 0),
                'bmp280_humidity': data.get('bmp280_humidity', 0),
                'dht11_temperature': data.get('dht11_temperature', 0),
                'dht11_humidity': data.get('dht11_humidity', 0),
                'heartrate': data.get('heartrate', 0),
                'spo2': data.get('spo2', 0),
                'flame_detected': data.get('flame_detected', False),
                'timestamp': data.get('timestamp', 0),
                'last_updated': timestamp
            })
            
            # Store in MongoDB
            db.sensor_data.insert_one(data)
            print(f"📊 Stored sensor data: {data}")
            
        else:
            # Individual sensor data
            sensor_name = topic.split('/')[-1]
            
            # Create document for individual sensor reading
            sensor_doc = {
                'sensor': sensor_name,
                'value': float(payload) if payload.replace('.', '').replace('-', '').isdigit() else payload,
                'timestamp': int(time.time() * 1000),
                'received_at': timestamp
            }
            
            # Store individual sensor reading
            db.sensor_readings.insert_one(sensor_doc)
            
            print(f"📡 Individual sensor data: {sensor_name} = {payload}")
            
    except Exception as e:
        print(f"❌ Error processing MQTT message: {e}")

def on_mqtt_disconnect(client, userdata, rc):
    """Callback for when the MQTT client disconnects."""
    if rc != 0:
        print(f"⚠️  Unexpected disconnection from MQTT broker. Return code: {rc}")
    else:
        print("👋 Disconnected from MQTT broker")

def start_mqtt_client():
    """Start the MQTT client in a separate thread."""
    client = mqtt.Client(MQTT_CLIENT_ID)
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message
    client.on_disconnect = on_mqtt_disconnect
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"❌ MQTT client error: {e}")

# Start MQTT client in background thread
mqtt_thread = threading.Thread(target=start_mqtt_client, daemon=True)
mqtt_thread.start()

@app.route('/')
def index():
    """Landing page."""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/analytics')
def analytics():
    """Analytics page."""
    return render_template('analytics.html')

@app.route('/about')
def about():
    """About page."""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact page."""
    return render_template('contact.html')

@app.route('/api/latest-data')
def get_latest_data():
    """Get the latest sensor data."""
    return jsonify(latest_data)

@app.route('/api/historical-data')
def get_historical_data():
    """Get historical sensor data."""
    limit = request.args.get('limit', 100, type=int)
    
    # Get latest sensor data from MongoDB
    data = list(db.sensor_data.find().sort('timestamp', -1).limit(limit))
    
    # Convert ObjectId to string for JSON serialization
    for item in data:
        item['_id'] = str(item['_id'])
        if 'received_at' in item:
            item['received_at'] = item['received_at'].isoformat()
    
    return jsonify(data)

@app.route('/api/sensor-readings/<sensor_name>')
def get_sensor_readings(sensor_name):
    """Get readings for a specific sensor."""
    limit = request.args.get('limit', 50, type=int)
    
    # Get sensor readings from MongoDB
    data = list(db.sensor_readings.find({'sensor': sensor_name})
                .sort('timestamp', -1).limit(limit))
    
    # Convert ObjectId to string for JSON serialization
    for item in data:
        item['_id'] = str(item['_id'])
        if 'received_at' in item:
            item['received_at'] = item['received_at'].isoformat()
    
    return jsonify(data)

@app.route('/api/stats')
def get_stats():
    """Get sensor statistics."""
    stats = {}
    
    # Get latest data for each sensor type
    latest_sensor_data = db.sensor_data.find().sort('timestamp', -1).limit(1)
    latest = list(latest_sensor_data)
    
    if latest:
        latest = latest[0]
        stats = {
            'total_readings': db.sensor_data.count_documents({}),
            'latest_update': latest.get('received_at').isoformat() if latest.get('received_at') else None,
            'current_values': {
                'bmp280_temperature': latest.get('bmp280_temperature', 0),
                'bmp280_pressure': latest.get('bmp280_pressure', 0),
                'bmp280_humidity': latest.get('bmp280_humidity', 0),
                'dht11_temperature': latest.get('dht11_temperature', 0),
                'dht11_humidity': latest.get('dht11_humidity', 0),
                'heartrate': latest.get('heartrate', 0),
                'spo2': latest.get('spo2', 0),
                'flame_detected': latest.get('flame_detected', False)
            }
        }
    
    return jsonify(stats)

@app.route('/api/sleep-analysis')
def get_sleep_analysis():
    """Get comprehensive sleep analysis."""
    # Get data from last 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)
    sleep_data = list(db.sensor_data.find({
        'received_at': {'$gte': seven_days_ago}
    }).sort('timestamp', -1))
    
    if not sleep_data:
        return jsonify({'error': 'No sleep data available'})
    
    # Analyze sleep patterns
    analysis = analyze_sleep_patterns(sleep_data)
    
    return jsonify(analysis)

def analyze_sleep_patterns(sleep_data):
    """Analyze sleep patterns from sensor data."""
    analysis = {
        'sleep_quality_score': 0,
        'average_heart_rate': 0,
        'average_spo2': 0,
        'sleep_efficiency': 0,
        'deep_sleep_percentage': 0,
        'environment_score': 0,
        'recommendations': [],
        'trends': {},
        'health_metrics': {}
    }
    
    if not sleep_data:
        return analysis
    
    # Extract metrics
    heart_rates = [data.get('heartrate', 0) for data in sleep_data if data.get('heartrate', 0) > 0]
    spo2_values = [data.get('spo2', 0) for data in sleep_data if data.get('spo2', 0) > 0]
    temperatures = []
    humidities = []
    
    for data in sleep_data:
        temp = data.get('bmp280_temperature') or data.get('dht11_temperature')
        humidity = data.get('bmp280_humidity') or data.get('dht11_humidity')
        
        if temp and temp > 0:
            temperatures.append(temp)
        if humidity and humidity > 0:
            humidities.append(humidity)
    
    # Calculate averages
    if heart_rates:
        analysis['average_heart_rate'] = round(statistics.mean(heart_rates), 1)
        analysis['health_metrics']['heart_rate_variability'] = calculate_hrv(heart_rates)
    
    if spo2_values:
        analysis['average_spo2'] = round(statistics.mean(spo2_values), 1)
    
    # Calculate sleep quality score
    analysis['sleep_quality_score'] = calculate_sleep_quality_score(
        analysis['average_heart_rate'], 
        analysis['average_spo2'],
        temperatures,
        humidities
    )
    
    # Calculate sleep efficiency (simplified)
    analysis['sleep_efficiency'] = calculate_sleep_efficiency(sleep_data)
    
    # Calculate deep sleep percentage (simplified based on heart rate patterns)
    analysis['deep_sleep_percentage'] = calculate_deep_sleep_percentage(heart_rates)
    
    # Environment analysis
    analysis['environment_score'] = calculate_environment_score(temperatures, humidities)
    
    # Generate recommendations
    analysis['recommendations'] = generate_recommendations(analysis)
    
    # Calculate trends
    analysis['trends'] = calculate_trends(sleep_data)
    
    return analysis

def calculate_hrv(heart_rates):
    """Calculate Heart Rate Variability."""
    if len(heart_rates) < 2:
        return 0
    
    # Calculate RMSSD (Root Mean Square of Successive Differences)
    differences = []
    for i in range(1, len(heart_rates)):
        diff = heart_rates[i] - heart_rates[i-1]
        differences.append(diff * diff)
    
    if differences:
        rmssd = math.sqrt(statistics.mean(differences))
        return round(rmssd, 2)
    return 0

def calculate_sleep_quality_score(avg_hr, avg_spo2, temperatures, humidities):
    """Calculate overall sleep quality score (0-100)."""
    score = 0
    
    # Heart rate scoring (optimal: 60-70 BPM)
    if avg_hr:
        if 60 <= avg_hr <= 70:
            score += 30
        elif 50 <= avg_hr < 60 or 70 < avg_hr <= 80:
            score += 20
        else:
            score += 10
    
    # SpO2 scoring (optimal: 95-100%)
    if avg_spo2:
        if avg_spo2 >= 98:
            score += 30
        elif 95 <= avg_spo2 < 98:
            score += 20
        else:
            score += 10
    
    # Temperature scoring (optimal: 18-22°C)
    if temperatures:
        avg_temp = statistics.mean(temperatures)
        if 18 <= avg_temp <= 22:
            score += 20
        elif 16 <= avg_temp < 18 or 22 < avg_temp <= 24:
            score += 15
        else:
            score += 5
    
    # Humidity scoring (optimal: 40-60%)
    if humidities:
        avg_humidity = statistics.mean(humidities)
        if 40 <= avg_humidity <= 60:
            score += 20
        elif 30 <= avg_humidity < 40 or 60 < avg_humidity <= 70:
            score += 15
        else:
            score += 5
    
    return min(score, 100)

def calculate_sleep_efficiency(sleep_data):
    """Calculate sleep efficiency percentage."""
    # Simplified calculation based on data consistency
    if len(sleep_data) < 10:
        return 0
    
    # Count consistent readings (simulating sleep periods)
    consistent_periods = 0
    total_periods = len(sleep_data) // 10
    
    for i in range(0, len(sleep_data) - 10, 10):
        period_data = sleep_data[i:i+10]
        hr_values = [d.get('heartrate', 0) for d in period_data if d.get('heartrate', 0) > 0]
        
        if len(hr_values) >= 5:
            hr_std = statistics.stdev(hr_values) if len(hr_values) > 1 else 0
            if hr_std < 10:  # Low variability indicates deep sleep
                consistent_periods += 1
    
    if total_periods > 0:
        return round((consistent_periods / total_periods) * 100, 1)
    return 0

def calculate_deep_sleep_percentage(heart_rates):
    """Calculate deep sleep percentage based on heart rate patterns."""
    if not heart_rates:
        return 0
    
    # Deep sleep typically has lower, more stable heart rates
    avg_hr = statistics.mean(heart_rates)
    deep_sleep_threshold = avg_hr * 0.9  # 10% below average
    
    deep_sleep_count = sum(1 for hr in heart_rates if hr <= deep_sleep_threshold)
    
    return round((deep_sleep_count / len(heart_rates)) * 100, 1)

def calculate_environment_score(temperatures, humidities):
    """Calculate environment quality score."""
    score = 0
    
    # Temperature scoring
    if temperatures:
        avg_temp = statistics.mean(temperatures)
        if 18 <= avg_temp <= 22:
            score += 50
        elif 16 <= avg_temp < 18 or 22 < avg_temp <= 24:
            score += 35
        else:
            score += 15
    
    # Humidity scoring
    if humidities:
        avg_humidity = statistics.mean(humidities)
        if 40 <= avg_humidity <= 60:
            score += 50
        elif 30 <= avg_humidity < 40 or 60 < avg_humidity <= 70:
            score += 35
        else:
            score += 15
    
    return min(score, 100)

def generate_recommendations(analysis):
    """Generate personalized sleep recommendations."""
    recommendations = []
    
    # Heart rate recommendations
    if analysis['average_heart_rate'] > 80:
        recommendations.append({
            'type': 'health',
            'priority': 'high',
            'message': 'Your average heart rate is elevated. Consider stress reduction techniques or consult a healthcare provider.'
        })
    elif analysis['average_heart_rate'] < 50:
        recommendations.append({
            'type': 'health',
            'priority': 'medium',
            'message': 'Your heart rate is quite low. This might be normal for athletes, but consider monitoring.'
        })
    
    # SpO2 recommendations
    if analysis['average_spo2'] < 95:
        recommendations.append({
            'type': 'health',
            'priority': 'high',
            'message': 'Blood oxygen levels are below optimal. Consider improving air quality or consulting a doctor.'
        })
    
    # Environment recommendations
    if analysis['environment_score'] < 70:
        recommendations.append({
            'type': 'environment',
            'priority': 'medium',
            'message': 'Room environment could be optimized. Check temperature (18-22°C) and humidity (40-60%).'
        })
    
    # Sleep efficiency recommendations
    if analysis['sleep_efficiency'] < 80:
        recommendations.append({
            'type': 'sleep',
            'priority': 'medium',
            'message': 'Sleep efficiency could be improved. Try maintaining consistent sleep schedule and reducing screen time before bed.'
        })
    
    # Deep sleep recommendations
    if analysis['deep_sleep_percentage'] < 20:
        recommendations.append({
            'type': 'sleep',
            'priority': 'medium',
            'message': 'Deep sleep percentage is low. Consider exercise, meditation, or reducing caffeine intake.'
        })
    
    return recommendations

def calculate_trends(sleep_data):
    """Calculate sleep trends over time."""
    trends = {
        'heart_rate_trend': 'stable',
        'sleep_quality_trend': 'stable',
        'environment_trend': 'stable'
    }
    
    if len(sleep_data) < 20:
        return trends
    
    # Split data into two halves for trend analysis
    mid_point = len(sleep_data) // 2
    recent_data = sleep_data[:mid_point]
    older_data = sleep_data[mid_point:]
    
    # Heart rate trend
    recent_hr = [d.get('heartrate', 0) for d in recent_data if d.get('heartrate', 0) > 0]
    older_hr = [d.get('heartrate', 0) for d in older_data if d.get('heartrate', 0) > 0]
    
    if recent_hr and older_hr:
        recent_avg = statistics.mean(recent_hr)
        older_avg = statistics.mean(older_hr)
        
        if recent_avg > older_avg + 2:
            trends['heart_rate_trend'] = 'increasing'
        elif recent_avg < older_avg - 2:
            trends['heart_rate_trend'] = 'decreasing'
    
    return trends

if __name__ == '__main__':
    print("🚀 Starting SmartBed Dashboard...")
    print(f"📊 MongoDB URI: {MONGODB_URI}")
    print("🌐 Starting Flask server...")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
