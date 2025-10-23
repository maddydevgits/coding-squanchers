#!/usr/bin/env python3
"""
MQTT Test Client for ESP32 Sensor System
This script subscribes to all sensor topics and displays the data in real-time.
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "ESP32_TestClient"

# Topic subscriptions
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

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker."""
    if rc == 0:
        print(f"✅ Connected to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
        print("📡 Subscribing to sensor topics...")
        
        # Subscribe to all topics
        for topic in TOPICS:
            client.subscribe(topic)
            print(f"   📋 Subscribed to: {topic}")
        
        print("\n" + "="*60)
        print("🔄 Waiting for sensor data...")
        print("="*60 + "\n")
    else:
        print(f"❌ Failed to connect to MQTT broker. Return code: {rc}")

def on_message(client, userdata, msg):
    """Callback for when a message is received."""
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Handle different topic types
    if topic == "sensors/status":
        # Parse JSON data
        try:
            data = json.loads(payload)
            print(f"🕐 {timestamp} - 📊 Combined Sensor Data:")
            print(f"   🌡️  BMP280 Temperature: {data.get('bmp280_temperature', 'N/A')}°C")
            print(f"   🌡️  DHT11 Temperature: {data.get('dht11_temperature', 'N/A')}°C")
            print(f"   📊 Pressure: {data.get('bmp280_pressure', 'N/A')} hPa")
            print(f"   💧 BMP280 Humidity: {data.get('bmp280_humidity', 'N/A')}%")
            print(f"   💧 DHT11 Humidity: {data.get('dht11_humidity', 'N/A')}%")
            print(f"   ❤️  Heart Rate: {data.get('heartrate', 'N/A')} BPM")
            print(f"   🩸 SpO2: {data.get('spo2', 'N/A')}%")
            print(f"   🔥 Flame: {'🚨 DETECTED' if data.get('flame_detected') else '✅ Safe'}")
            print(f"   ⏰ Timestamp: {data.get('timestamp', 'N/A')}")
        except json.JSONDecodeError:
            print(f"🕐 {timestamp} - ❌ Invalid JSON data: {payload}")
    else:
        # Individual sensor data
        sensor_name = topic.split('/')[-1].title()
        emoji_map = {
            'Temperature': '🌡️',
            'Pressure': '📊', 
            'Humidity': '💧',
            'Dht11_Temperature': '🌡️',
            'Dht11_Humidity': '💧',
            'Heartrate': '❤️',
            'Spo2': '🩸',
            'Flame': '🔥'
        }
        
        emoji = emoji_map.get(sensor_name, '📡')
        
        if topic == "sensors/flame":
            status = "🚨 DETECTED" if payload.lower() == "true" else "✅ Safe"
            print(f"🕐 {timestamp} - {emoji} {sensor_name}: {status}")
        else:
            print(f"🕐 {timestamp} - {emoji} {sensor_name}: {payload}")

def on_disconnect(client, userdata, rc):
    """Callback for when the client disconnects."""
    if rc != 0:
        print(f"⚠️  Unexpected disconnection from MQTT broker. Return code: {rc}")
    else:
        print("👋 Disconnected from MQTT broker")

def main():
    """Main function to run the MQTT test client."""
    print("🚀 ESP32 Sensor System - MQTT Test Client")
    print("="*50)
    print(f"🔗 Connecting to: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"🆔 Client ID: {MQTT_CLIENT_ID}")
    print()
    
    # Create MQTT client
    client = mqtt.Client(MQTT_CLIENT_ID)
    
    # Set callback functions
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        # Connect to broker
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Start the loop
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping MQTT test client...")
        client.disconnect()
        print("👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
