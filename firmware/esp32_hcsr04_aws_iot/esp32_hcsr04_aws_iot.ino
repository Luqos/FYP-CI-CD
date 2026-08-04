/*
 * Dual-Sensor ESP32 AWS IoT Core Smart Parking Telemetry Publisher
 * Hardware: ESP32 + 2x HC-SR04 Ultrasonic Sensors for Slots A01 & A02
 *
 * Pinout Connections:
 * - Sensor 1 (Slot A01): TRIG -> GPIO 5, ECHO -> GPIO 18
 * - Sensor 2 (Slot A02): TRIG -> GPIO 19, ECHO -> GPIO 21
 * - VCC -> 5V / VIN (Common for both sensors)
 * - GND -> GND (Common ground)
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// Rename secrets_template.h to secrets.h and populate credentials
#include "secrets.h"

// Pin Definitions for Sensor 1 (Slot A01)
#define TRIG_PIN_A01 5
#define ECHO_PIN_A01 18

// Pin Definitions for Sensor 2 (Slot A02)
#define TRIG_PIN_A02 19
#define ECHO_PIN_A02 21

// Topics for MQTT Telemetry
const char* TOPIC_A01 = "smart-parking/slot/A01/telemetry";
const char* TOPIC_A02 = "smart-parking/slot/A02/telemetry";

const unsigned long PUBLISH_INTERVAL_MS = 5000;
unsigned long lastPublishTime = 0;

WiFiClientSecure net = WiFiClientSecure();
PubSubClient client(net);

void connectToWiFi() {
  Serial.print("Connecting to Wi-Fi SSID: ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi Connected! IP Address: ");
  Serial.println(WiFi.localIP());
}

void connectToAWS() {
  net.setCACert(AWS_CERT_CA);
  net.setCertificate(AWS_CERT_CRT);
  net.setPrivateKey(AWS_CERT_PRIVATE);

  client.setServer(AWS_IOT_ENDPOINT, 8883);

  Serial.println("Connecting to AWS IoT Core...");
  while (!client.connected()) {
    String clientId = "ESP32-DualSensor-" + String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) {
      Serial.println("Connected to AWS IoT Core!");
    } else {
      Serial.print("AWS IoT Connection failed, rc=");
      Serial.print(client.state());
      Serial.println(". Retrying in 5 seconds...");
      delay(5000);
    }
  }
}

float measureDistanceCm(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long durationMicroSec = pulseIn(echoPin, HIGH, 30000); // 30ms timeout (~5m max)
  if (durationMicroSec == 0) {
    return -1.0; // Timeout or sensor error
  }

  // Speed of sound = 343 m/s = 0.0343 cm/us
  float distanceCm = (durationMicroSec * 0.0343) / 2.0;
  return distanceCm;
}

void publishSlotTelemetry(const char* slotId, const char* topic, int trigPin, int echoPin) {
  float distanceCm = measureDistanceCm(trigPin, echoPin);
  
  Serial.print("[SENSOR] Slot ");
  Serial.print(slotId);
  Serial.print(" Distance: ");
  Serial.print(distanceCm);
  Serial.println(" cm");

  StaticJsonDocument<200> doc;
  doc["slotId"] = slotId;
  if (distanceCm > 0) {
    doc["distanceCm"] = serialized(String(distanceCm, 1));
    doc["status"] = (distanceCm <= 30.0) ? "OCCUPIED" : "AVAILABLE";
  } else {
    doc["distanceCm"] = -1;
    doc["status"] = "SENSOR_ERROR";
  }
  doc["deviceId"] = "esp32-dual-sensor";
  doc["firmwareVersion"] = "1.1.0";

  char jsonBuffer[256];
  serializeJson(doc, jsonBuffer);

  Serial.print("[MQTT] Publishing to [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(jsonBuffer);

  if (client.publish(topic, jsonBuffer)) {
    Serial.println(" -> Publish OK!");
  } else {
    Serial.println(" -> Publish Failed!");
  }
}

void setup() {
  Serial.begin(115200);

  // Setup Sensor 1 pins
  pinMode(TRIG_PIN_A01, OUTPUT);
  pinMode(ECHO_PIN_A01, INPUT);

  // Setup Sensor 2 pins
  pinMode(TRIG_PIN_A02, OUTPUT);
  pinMode(ECHO_PIN_A02, INPUT);

  connectToWiFi();
  connectToAWS();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }

  if (!client.connected()) {
    connectToAWS();
  }

  client.loop();

  unsigned long now = millis();
  if (now - lastPublishTime >= PUBLISH_INTERVAL_MS) {
    lastPublishTime = now;

    // Read & publish Slot A01
    publishSlotTelemetry("A01", TOPIC_A01, TRIG_PIN_A01, ECHO_PIN_A01);
    delay(200); // 200ms gap to avoid acoustic interference between sensors

    // Read & publish Slot A02
    publishSlotTelemetry("A02", TOPIC_A02, TRIG_PIN_A02, ECHO_PIN_A02);
  }
}
