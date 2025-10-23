/*
 * ESP32 Multi-Sensor System
 * Components: MAX30102, BMP280, Flame Sensor, OLED Display, Buzzer
 * MQTT Publisher to hivemq.com
 * 
 * Libraries Required:
 * - SparkFun MAX301x Particle Sensor Library
 * - Adafruit SSD1306
 * - Adafruit BME280
 * - WiFi
 * - PubSubClient
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_BME280.h>
#include <DHT.h>
#include "MAX30105.h"
#include "heartRate.h"

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT settings
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* mqtt_client_id = "ESP32_SensorSystem";

// MQTT topics
const char* topic_heartrate = "sensors/heartrate";
const char* topic_spo2 = "sensors/spo2";
const char* topic_temperature = "sensors/temperature";
const char* topic_pressure = "sensors/pressure";
const char* topic_humidity = "sensors/humidity";
const char* topic_dht11_temp = "sensors/dht11_temperature";
const char* topic_dht11_humidity = "sensors/dht11_humidity";
const char* topic_flame = "sensors/flame";
const char* topic_status = "sensors/status";

// Pin definitions
#define FLAME_SENSOR_PIN 34
#define BUZZER_PIN 25
#define DHT11_PIN 26
#define DHT11_TYPE DHT11
#define OLED_SDA 21
#define OLED_SCL 22
#define OLED_RESET -1

// Sensor objects
MAX30105 particleSensor;
Adafruit_BME280 bme;
DHT dht(DHT11_PIN, DHT11_TYPE);
Adafruit_SSD1306 display(128, 64, &Wire, OLED_RESET);

// WiFi and MQTT clients
WiFiClient espClient;
PubSubClient client(espClient);

// Heart rate calculation variables
byte rates[RATE_SIZE];
byte rateSpot = 0;
long lastBeat = 0;
float beatsPerMinute;
int beatAvg;

// SpO2 calculation variables
double avered = 0;
double aveir = 0;
double sumirrms = 0;
double sumredrms = 0;
int SpO2 = 0;
int ESpO2 = 90;
double FSpO2 = 0.7;
double frate = 0.95;
int i = 0;
int Num = 100;

// Sensor data
float temperature = 0;
float pressure = 0;
float humidity = 0;
float dht11_temperature = 0;
float dht11_humidity = 0;
bool flameDetected = false;
unsigned long lastSensorRead = 0;
const unsigned long sensorReadInterval = 2000; // Read sensors every 2 seconds

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 Multi-Sensor System Starting...");
  
  // Initialize display
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
    for(;;);
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println("ESP32 Sensor System");
  display.println("Initializing...");
  display.display();
  
  // Initialize pins
  pinMode(FLAME_SENSOR_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  
  // Initialize DHT11
  dht.begin();
  
  // Initialize I2C
  Wire.begin(OLED_SDA, OLED_SCL);
  
  // Initialize MAX30102
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("MAX30102 was not found. Please check wiring/power.");
    display.println("MAX30102 Error!");
    display.display();
    while (1);
  }
  
  // Configure MAX30102
  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x0A);
  particleSensor.setPulseAmplitudeIR(0x0A);
  particleSensor.setPulseAmplitudeGreen(0x0A);
  
  // Initialize BMP280
  if (!bme.begin(0x76)) {
    Serial.println("Could not find a valid BMP280 sensor, check wiring!");
    display.println("BMP280 Error!");
    display.display();
    while (1);
  }
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  
  // Connect to MQTT broker
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  
  display.clearDisplay();
  display.setCursor(0,0);
  display.println("System Ready!");
  display.println("WiFi: Connected");
  display.println("MQTT: Connecting...");
  display.display();
  
  Serial.println("Setup complete!");
}

void loop() {
  // Reconnect MQTT if needed
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  // Read sensors every interval
  if (millis() - lastSensorRead >= sensorReadInterval) {
    readSensors();
    updateDisplay();
    publishData();
    lastSensorRead = millis();
  }
  
  // Check flame sensor continuously for immediate response
  checkFlameSensor();
  
  delay(100);
}

void readSensors() {
  // Read BMP280 data
  temperature = bme.readTemperature();
  pressure = bme.readPressure() / 100.0F; // Convert to hPa
  humidity = bme.readHumidity();
  
  // Read DHT11 data
  dht11_temperature = dht.readTemperature();
  dht11_humidity = dht.readHumidity();
  
  // Check if DHT11 readings are valid
  if (isnan(dht11_temperature) || isnan(dht11_humidity)) {
    Serial.println("Failed to read from DHT11 sensor!");
    dht11_temperature = 0;
    dht11_humidity = 0;
  }
  
  // Read MAX30102 data
  long irValue = particleSensor.getIR();
  long redValue = particleSensor.getRed();
  
  // Heart rate calculation
  if (checkForBeat(irValue) == true) {
    long delta = millis() - lastBeat;
    lastBeat = millis();
    beatsPerMinute = 60 / (delta / 1000.0);
    
    if (beatsPerMinute < 255 && beatsPerMinute > 20) {
      rates[rateSpot++] = (byte)beatsPerMinute;
      rateSpot %= RATE_SIZE;
      
      beatAvg = 0;
      for (byte x = 0 ; x < RATE_SIZE ; x++)
        beatAvg += rates[x];
      beatAvg /= RATE_SIZE;
    }
  }
  
  // SpO2 calculation
  avered = avered * frate + (double)redValue * (1.0 - frate);
  aveir = aveir * frate + (double)irValue * (1.0 - frate);
  sumredrms += (redValue - avered) * (redValue - avered);
  sumirrms += (irValue - aveir) * (irValue - aveir);
  
  if ((i % Num) == 0) {
    double R = (sqrt(sumredrms) / avered) / (sqrt(sumirrms) / aveir);
    SpO2 = -23.3 * (R - 0.4) + 100;
    if (SpO2 > 100) SpO2 = 100;
    if (SpO2 < 70) SpO2 = 70;
    ESpO2 = FSpO2 * ESpO2 + (1.0 - FSpO2) * SpO2;
    sumredrms = 0.0; sumirrms = 0.0; SpO2 = 0;
  }
  i++;
  
  // Read flame sensor
  flameDetected = digitalRead(FLAME_SENSOR_PIN) == LOW; // Assuming active LOW
  
  Serial.println("Sensor Data:");
  Serial.println("BMP280 Temperature: " + String(temperature) + " °C");
  Serial.println("BMP280 Pressure: " + String(pressure) + " hPa");
  Serial.println("BMP280 Humidity: " + String(humidity) + " %");
  Serial.println("DHT11 Temperature: " + String(dht11_temperature) + " °C");
  Serial.println("DHT11 Humidity: " + String(dht11_humidity) + " %");
  Serial.println("Heart Rate: " + String(beatAvg) + " BPM");
  Serial.println("SpO2: " + String(ESpO2) + " %");
  Serial.println("Flame: " + String(flameDetected ? "DETECTED" : "SAFE"));
}

void checkFlameSensor() {
  if (digitalRead(FLAME_SENSOR_PIN) == LOW) {
    flameDetected = true;
    // Activate buzzer for flame detection
    digitalWrite(BUZZER_PIN, HIGH);
    delay(100);
    digitalWrite(BUZZER_PIN, LOW);
    
    // Publish immediate flame alert
    String flameAlert = "{\"flame_detected\":true,\"timestamp\":" + String(millis()) + "}";
    client.publish(topic_flame, flameAlert.c_str());
  } else {
    flameDetected = false;
  }
}

void updateDisplay() {
  display.clearDisplay();
  display.setCursor(0,0);
  
  display.println("ESP32 Sensor System");
  display.println("BMP280: " + String(temperature, 1) + "C " + String(humidity, 1) + "%");
  display.println("DHT11: " + String(dht11_temperature, 1) + "C " + String(dht11_humidity, 1) + "%");
  display.println("Press: " + String(pressure, 1) + "hPa");
  display.println("HR: " + String(beatAvg) + " SpO2: " + String(ESpO2) + "%");
  display.println("Flame: " + String(flameDetected ? "ALERT!" : "OK"));
  
  display.display();
}

void publishData() {
  if (client.connected()) {
    // Publish individual sensor data
    client.publish(topic_temperature, String(temperature).c_str());
    client.publish(topic_pressure, String(pressure).c_str());
    client.publish(topic_humidity, String(humidity).c_str());
    client.publish(topic_dht11_temp, String(dht11_temperature).c_str());
    client.publish(topic_dht11_humidity, String(dht11_humidity).c_str());
    client.publish(topic_heartrate, String(beatAvg).c_str());
    client.publish(topic_spo2, String(ESpO2).c_str());
    client.publish(topic_flame, String(flameDetected).c_str());
    
    // Publish combined JSON data
    String jsonData = "{";
    jsonData += "\"bmp280_temperature\":" + String(temperature) + ",";
    jsonData += "\"bmp280_pressure\":" + String(pressure) + ",";
    jsonData += "\"bmp280_humidity\":" + String(humidity) + ",";
    jsonData += "\"dht11_temperature\":" + String(dht11_temperature) + ",";
    jsonData += "\"dht11_humidity\":" + String(dht11_humidity) + ",";
    jsonData += "\"heartrate\":" + String(beatAvg) + ",";
    jsonData += "\"spo2\":" + String(ESpO2) + ",";
    jsonData += "\"flame_detected\":" + String(flameDetected ? "true" : "false") + ",";
    jsonData += "\"timestamp\":" + String(millis());
    jsonData += "}";
    
    client.publish(topic_status, jsonData.c_str());
    
    Serial.println("Data published to MQTT");
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(mqtt_client_id)) {
      Serial.println("connected");
      display.clearDisplay();
      display.setCursor(0,0);
      display.println("System Ready!");
      display.println("WiFi: Connected");
      display.println("MQTT: Connected");
      display.display();
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}
