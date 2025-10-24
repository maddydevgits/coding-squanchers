# ESP32 SmartBed Multi-Sensor System

A comprehensive IoT sensor system using ESP32 with multiple sensors for health monitoring and environmental sensing, featuring MQTT data publishing to HiveMQ broker.

## Components Used

- **ESP32 Development Board**
- **MAX30102** - Heart Rate & SpO2 Sensor
- **BMP280** - Temperature, Pressure & Humidity Sensor
- **DHT11** - Temperature & Humidity Sensor
- **Flame Sensor** - Fire Detection
- **OLED Display (SSD1306)** - 128x64 I2C Display
- **Buzzer** - Audio Alert System

## Features

- Real-time heart rate and SpO2 monitoring
- Dual temperature and humidity sensing (BMP280 + DHT11)
- Environmental sensing (pressure from BMP280)
- Fire detection with immediate buzzer alert
- OLED display showing all sensor readings
- MQTT data publishing to HiveMQ broker
- WiFi connectivity
- JSON formatted data transmission

## Wiring Diagram

```
ESP32 Pin Connections:

┌─────────────────┐
│       ESP32     │
├─────────────────┤
│ 3.3V  ──────────┤─── VCC (MAX30102, BMP280, OLED, Flame Sensor, DHT11)
│ GND   ──────────┤─── GND (All components)
│ GPIO21 ─────────┤─── SDA (I2C Data - MAX30102, BMP280, OLED)
│ GPIO22 ─────────┤─── SCL (I2C Clock - MAX30102, BMP280, OLED)
│ GPIO26 ─────────┤─── Data (DHT11 Data Pin)
│ GPIO34 ─────────┤─── DO (Flame Sensor Digital Output)
│ GPIO25 ─────────┤─── + (Buzzer Positive)
│ GND   ──────────┤─── - (Buzzer Negative)
└─────────────────┘

Component Details:
┌─────────────────────────────────────────────────────────────┐
│ MAX30102 (I2C Address: 0x57)                               │
│ ├─ VCC → 3.3V                                               │
│ ├─ GND → GND                                                │
│ ├─ SDA → GPIO21                                             │
│ └─ SCL → GPIO22                                             │
├─────────────────────────────────────────────────────────────┤
│ BMP280 (I2C Address: 0x76)                                 │
│ ├─ VCC → 3.3V                                               │
│ ├─ GND → GND                                                │
│ ├─ SDA → GPIO21                                             │
│ └─ SCL → GPIO22                                             │
├─────────────────────────────────────────────────────────────┤
│ OLED SSD1306 (I2C Address: 0x3C)                           │
│ ├─ VCC → 3.3V                                               │
│ ├─ GND → GND                                                │
│ ├─ SDA → GPIO21                                             │
│ └─ SCL → GPIO22                                             │
├─────────────────────────────────────────────────────────────┤
│ DHT11 Temperature & Humidity Sensor                         │
│ ├─ VCC → 3.3V                                               │
│ ├─ GND → GND                                                │
│ └─ Data → GPIO26                                            │
├─────────────────────────────────────────────────────────────┤
│ Flame Sensor                                                │
│ ├─ VCC → 3.3V                                               │
│ ├─ GND → GND                                                │
│ └─ DO → GPIO34                                              │
├─────────────────────────────────────────────────────────────┤
│ Buzzer                                                      │
│ ├─ + → GPIO25                                               │
│ └─ - → GND                                                  │
└─────────────────────────────────────────────────────────────┘
```

## Required Libraries

Install the following libraries through Arduino IDE Library Manager:

1. **SparkFun MAX301x Particle Sensor Library**
   - Search for "SparkFun MAX301x Particle Sensor Library"
   - Install by SparkFun Electronics

2. **Adafruit SSD1306**
   - Search for "Adafruit SSD1306"
   - Install by Adafruit

3. **Adafruit BME280 Library**
   - Search for "Adafruit BME280 Library"
   - Install by Adafruit

4. **Adafruit DHT Sensor Library**
   - Search for "Adafruit DHT Sensor Library"
   - Install by Adafruit

5. **PubSubClient**
   - Search for "PubSubClient"
   - Install by Nick O'Leary

## Setup Instructions

### 1. Hardware Setup
1. Connect all components according to the wiring diagram above
2. Ensure proper power supply (3.3V for all sensors)
3. Double-check I2C connections (SDA/SCL)
4. Verify flame sensor and buzzer connections

### 2. Software Configuration

1. **Update WiFi Credentials**
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```

2. **Upload Code**
   - Open `esp32_sensor_system.ino` in Arduino IDE
   - Select ESP32 board from Tools → Board
   - Select appropriate COM port
   - Upload the code

### 3. MQTT Configuration

The system automatically connects to HiveMQ broker:
- **Broker**: broker.hivemq.com
- **Port**: 1883
- **Client ID**: ESP32_SensorSystem

### 4. MQTT Topics

The system publishes data to the following topics:

- `sensors/temperature` - BMP280 Temperature readings (°C)
- `sensors/pressure` - BMP280 Pressure readings (hPa)
- `sensors/humidity` - BMP280 Humidity readings (%)
- `sensors/dht11_temperature` - DHT11 Temperature readings (°C)
- `sensors/dht11_humidity` - DHT11 Humidity readings (%)
- `sensors/heartrate` - Heart rate (BPM)
- `sensors/spo2` - Blood oxygen saturation (%)
- `sensors/flame` - Flame detection status
- `sensors/status` - Combined JSON data

## Data Format

### Individual Sensor Topics
Each sensor publishes its value as a simple string:
```
sensors/temperature: "23.5"
sensors/dht11_temperature: "23.2"
sensors/humidity: "45.2"
sensors/dht11_humidity: "44.8"
sensors/heartrate: "72"
```

### Combined JSON Data (sensors/status)
```json
{
  "bmp280_temperature": 23.5,
  "bmp280_pressure": 1013.25,
  "bmp280_humidity": 45.2,
  "dht11_temperature": 23.2,
  "dht11_humidity": 44.8,
  "heartrate": 72,
  "spo2": 98,
  "flame_detected": false,
  "timestamp": 1234567890
}
```

## Testing MQTT Data

You can test the MQTT data using any MQTT client:

### Using MQTT Explorer
1. Download MQTT Explorer
2. Connect to broker.hivemq.com:1883
3. Subscribe to `sensors/+` to see all sensor data
4. Subscribe to `sensors/status` for combined JSON data

### Using mosquitto CLI
```bash
# Subscribe to all sensor topics
mosquitto_sub -h broker.hivemq.com -p 1883 -t "sensors/+"

# Subscribe to combined data only
mosquitto_sub -h broker.hivemq.com -p 1883 -t "sensors/status"
```

## Troubleshooting

### Common Issues

1. **MAX30102 Not Detected**
   - Check I2C wiring (SDA/SCL)
   - Verify power supply (3.3V)
   - Ensure proper I2C address (0x57)

2. **BMP280 Not Detected**
   - Check I2C wiring
   - Verify I2C address (0x76)
   - Some BMP280 modules use address 0x77

3. **OLED Display Not Working**
   - Check I2C address (0x3C)
   - Verify power connections
   - Some displays use 0x3D address

4. **DHT11 Not Working**
   - Check data pin connection (GPIO26)
   - Verify power supply (3.3V)
   - Ensure proper pull-up resistor (4.7kΩ recommended)
   - Check for loose connections

5. **WiFi Connection Failed**
   - Verify SSID and password
   - Check WiFi signal strength
   - Ensure 2.4GHz network (ESP32 doesn't support 5GHz)

6. **MQTT Connection Failed**
   - Check internet connectivity
   - Verify broker address and port
   - Check firewall settings

### Serial Monitor Output
Monitor the Serial output (115200 baud) for debugging:
```
ESP32 Multi-Sensor System Starting...
WiFi connected
IP address: 192.168.1.100
MQTT connected
Sensor Data:
BMP280 Temperature: 23.5 °C
BMP280 Pressure: 1013.25 hPa
BMP280 Humidity: 45.2 %
DHT11 Temperature: 23.2 °C
DHT11 Humidity: 44.8 %
Heart Rate: 72 BPM
SpO2: 98 %
Flame: SAFE
Data published to MQTT
```

## Features Explained

### Heart Rate & SpO2 Monitoring
- Uses MAX30102 sensor with advanced algorithms
- Provides real-time heart rate (BPM) and blood oxygen saturation (%)
- Requires finger placement on sensor for accurate readings

### Environmental Monitoring
- BMP280 provides temperature, pressure, and humidity
- DHT11 provides additional temperature and humidity readings
- Dual sensor setup allows for comparison and redundancy
- High accuracy and low power consumption
- Suitable for indoor environmental monitoring

### Fire Detection
- Flame sensor detects fire presence
- Immediate buzzer alert when fire detected
- Publishes emergency alert to MQTT

### Display Interface
- Real-time sensor readings on OLED display
- System status indicators
- Easy-to-read format

## Customization

### Adding More Sensors
1. Define new pins and variables
2. Initialize sensor in setup()
3. Read sensor data in readSensors()
4. Add MQTT topic and publish data
5. Update display if needed

### Modifying MQTT Topics
Change topic names in the code:
```cpp
const char* topic_custom = "your/custom/topic";
```

### Adjusting Reading Intervals
Modify the sensor reading interval:
```cpp
const unsigned long sensorReadInterval = 5000; // 5 seconds
```

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Verify wiring connections
3. Test individual components
4. Monitor Serial output for error messages
