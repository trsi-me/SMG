/*
 * كود Arduino/ESP32 للتعرف على النباتات SMG
 * Plant Recognition Hardware Code for Arduino/ESP32
 * 
 * المكونات المطلوبة:
 * - Arduino/ESP32
 * - حساس رطوبة التربة (Soil Moisture Sensor)
 * - حساس درجة الحرارة (DHT22 أو DS18B20)
 * - حساس الرطوبة (DHT22)
 * - شاشة LCD 16x2 مع I2C
 * 
 * التوصيلات:
 * - Soil Sensor: A0
 * - DHT22: Pin 2
 * - LCD I2C: SDA, SCL
 */

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>
#include <ArduinoJson.h>

// إعدادات الحساسات
#define SOIL_SENSOR_PIN A0
#define DHT_PIN 2
#define DHT_TYPE DHT22

// إعدادات LCD
LiquidCrystal_I2C lcd(0x27, 16, 2); // عنوان I2C للشاشة

// إعدادات DHT
DHT dht(DHT_PIN, DHT_TYPE);

// متغيرات
String deviceId = "ESP32-001";
unsigned long lastSensorRead = 0;
const unsigned long sensorInterval = 30000; // 30 ثانية

void setup() {
  Serial.begin(9600);
  
  // تهيئة LCD
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("SMG Plant");
  lcd.setCursor(0, 1);
  lcd.print("System Ready");
  
  // تهيئة DHT
  dht.begin();
  
  delay(2000);
  lcd.clear();
  
  Serial.println("SMG Plant Recognition System Started");
}

void loop() {
  // قراءة الحساسات كل 30 ثانية
  if (millis() - lastSensorRead >= sensorInterval) {
    readAndSendSensorData();
    lastSensorRead = millis();
  }
  
  // قراءة الأوامر من Serial
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "READ") {
      readAndSendSensorData();
    } else if (command.startsWith("LCD:")) {
      // تنسيق: LCD:LINE1:LINE2
      handleLCDCommand(command);
    } else if (command.startsWith("{")) {
      // أمر JSON
      handleJSONCommand(command);
    }
  }
  
  delay(100);
}

void readAndSendSensorData() {
  // قراءة حساس التربة (0-1023)
  int soilRaw = analogRead(SOIL_SENSOR_PIN);
  
  // قراءة درجة الحرارة والرطوبة
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  // قراءة البطارية (محاكاة)
  float battery = 100.0; // يمكن إضافة حساس بطارية حقيقي
  
  // التحقق من قراءة DHT
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Error reading DHT sensor!");
    temperature = 0.0;
    humidity = 0.0;
  }
  
  // إنشاء JSON
  StaticJsonDocument<256> doc;
  doc["device_id"] = deviceId;
  doc["soil_raw"] = soilRaw;
  doc["temperature_c"] = temperature;
  doc["humidity_percent"] = humidity;
  doc["battery"] = battery;
  doc["timestamp"] = millis();
  
  // إرسال JSON
  serializeJson(doc, Serial);
  Serial.println();
  
  // عرض على LCD
  displaySensorData(soilRaw, temperature, humidity);
}

void displaySensorData(int soilRaw, float temp, float humidity) {
  // حساب نسبة رطوبة التربة (0-100%)
  int soilPercent = map(soilRaw, 0, 1023, 100, 0);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("S:");
  lcd.print(soilPercent);
  lcd.print("% T:");
  lcd.print(temp, 1);
  lcd.print("C");
  
  lcd.setCursor(0, 1);
  lcd.print("H:");
  lcd.print(humidity, 1);
  lcd.print("% B:");
  lcd.print(100);
  lcd.print("%");
}

void handleLCDCommand(String command) {
  // تنسيق: LCD:LINE1:LINE2
  int firstColon = command.indexOf(':');
  int secondColon = command.indexOf(':', firstColon + 1);
  
  if (secondColon > 0) {
    String line1 = command.substring(firstColon + 1, secondColon);
    String line2 = command.substring(secondColon + 1);
    
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(line1);
    lcd.setCursor(0, 1);
    lcd.print(line2);
  }
}

void handleJSONCommand(String jsonString) {
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, jsonString);
  
  if (error) {
    Serial.print("JSON Error: ");
    Serial.println(error.c_str());
    return;
  }
  
  if (doc.containsKey("command") && doc["command"] == "LCD") {
    String line1 = doc["line1"] | "";
    String line2 = doc["line2"] | "";
    
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(line1);
    lcd.setCursor(0, 1);
    lcd.print(line2);
  }
}

void displayPlantInfo(String plantName, String healthStatus) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Plant: ");
  lcd.print(plantName.substring(0, 9));
  
  lcd.setCursor(0, 1);
  lcd.print("Status: ");
  lcd.print(healthStatus.substring(0, 8));
}

