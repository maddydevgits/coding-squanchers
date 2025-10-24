# SmartBed Dashboard - Flask Web Application

A comprehensive web dashboard for monitoring ESP32 sensor data in real-time using Flask, MongoDB, and Tailwind CSS.

## Features

- **Real-time MQTT Data Reception**: Connects to HiveMQ broker to receive sensor data
- **MongoDB Storage**: Stores all sensor readings for historical analysis
- **Beautiful Dashboard**: Modern UI with Tailwind CSS
- **Health Monitoring**: Heart rate and SpO2 tracking with visual indicators
- **Environment Monitoring**: Dual temperature and humidity sensors (BMP280 + DHT11)
- **Safety Monitoring**: Fire detection with alert system
- **Historical Charts**: Interactive charts showing data trends
- **Responsive Design**: Works on desktop and mobile devices

## Prerequisites

- Python 3.7+
- MongoDB (local or cloud)
- ESP32 sensor system running and publishing MQTT data

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up MongoDB**
   
   **Option A: Local MongoDB**
   ```bash
   # Install MongoDB locally
   # Start MongoDB service
   mongod
   ```

   **Option B: MongoDB Atlas (Cloud)**
   - Create account at [MongoDB Atlas](https://www.mongodb.com/atlas)
   - Create a cluster
   - Get connection string

3. **Configure Environment Variables**
   ```bash
   # Create .env file
   cp .env.example .env
   
   # Edit .env with your MongoDB URI
   MONGODB_URI=mongodb://localhost:27017/smart_bed_db
   # OR for Atlas:
   # MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/smart_bed_db
   ```

## Running the Application

1. **Start the Flask Application**
   ```bash
   python app.py
   ```

2. **Access the Dashboard**
   - Open browser and go to: `http://localhost:5000`
   - The dashboard will automatically connect to MQTT and start receiving data

## API Endpoints

### GET `/api/latest-data`
Returns the most recent sensor data.

**Response:**
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
  "timestamp": 1234567890,
  "last_updated": "2024-01-01T12:00:00"
}
```

### GET `/api/historical-data?limit=100`
Returns historical sensor data.

### GET `/api/sensor-readings/<sensor_name>?limit=50`
Returns readings for a specific sensor.

### GET `/api/stats`
Returns system statistics and current values.

## Dashboard Features

### Health Monitoring Section
- **Heart Rate**: Real-time BPM with progress bar
- **Blood Oxygen (SpO2)**: Oxygen saturation percentage
- Visual indicators for normal/abnormal ranges

### Environment Monitoring Section
- **Dual Temperature Sensors**: BMP280 and DHT11 readings
- **Dual Humidity Sensors**: BMP280 and DHT11 readings
- **Atmospheric Pressure**: BMP280 pressure readings

### Safety Monitoring Section
- **Fire Detection**: Real-time flame sensor status
- **Alert System**: Visual alerts when fire is detected
- **System Status**: Overall system health

### Historical Data Section
- **Temperature Trends**: Line chart showing temperature over time
- **Heart Rate Trends**: Line chart showing heart rate patterns
- Real-time chart updates

## Data Flow

1. **ESP32 Sensors** → MQTT Broker (HiveMQ)
2. **MQTT Broker** → Flask MQTT Client
3. **Flask App** → MongoDB Storage
4. **Flask App** → Web Dashboard (Real-time updates)

## MQTT Topics Monitored

- `sensors/temperature` - BMP280 temperature
- `sensors/pressure` - BMP280 pressure
- `sensors/humidity` - BMP280 humidity
- `sensors/dht11_temperature` - DHT11 temperature
- `sensors/dht11_humidity` - DHT11 humidity
- `sensors/heartrate` - Heart rate (BPM)
- `sensors/spo2` - Blood oxygen saturation
- `sensors/flame` - Fire detection status
- `sensors/status` - Combined JSON data

## MongoDB Collections

### `sensor_data`
Stores complete sensor readings from `sensors/status` topic.

### `sensor_readings`
Stores individual sensor readings from specific topics.

## Customization

### Adding New Sensors
1. Add new MQTT topic to `TOPICS` list
2. Update `on_mqtt_message()` function
3. Add new dashboard cards in `dashboard.html`
4. Update API endpoints if needed

### Styling
- Uses Tailwind CSS CDN
- Custom color scheme defined in JavaScript
- Responsive design with mobile support

### Charts
- Uses Chart.js for interactive charts
- Real-time updates every 2 seconds
- Configurable data points (currently 20)

## Troubleshooting

### MQTT Connection Issues
- Check broker address and port
- Verify internet connectivity
- Check firewall settings

### MongoDB Connection Issues
- Verify MongoDB URI
- Check MongoDB service status
- Verify network connectivity for Atlas

### Dashboard Not Updating
- Check browser console for errors
- Verify API endpoints are responding
- Check MQTT data flow

## Development

### Running in Development Mode
```bash
export FLASK_ENV=development
export FLASK_DEBUG=True
python app.py
```

### Logs
- MQTT connection status
- Data storage confirmations
- Error messages

## Production Deployment

### Environment Variables
```bash
export MONGODB_URI="your-production-mongodb-uri"
export FLASK_ENV=production
```

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Security Considerations

- Change default MongoDB credentials
- Use environment variables for sensitive data
- Implement authentication for production
- Use HTTPS in production
- Validate MQTT data before storage

## License

This project is open source. Feel free to modify and distribute according to your needs.
