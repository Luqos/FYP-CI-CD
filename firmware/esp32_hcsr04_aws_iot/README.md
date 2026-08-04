# ESP32 Dual HC-SR04 Firmware Guide

This sketch connects a single ESP32 microcontroller with **two HC-SR04 ultrasonic sensors** to monitor parking bays **Slot A01** and **Slot A02**, publishing live telemetry to AWS IoT Core over MQTT TLS every 5 seconds.

## Pinout Wiring Table (2 Sensors)

| Component | HC-SR04 Pin | ESP32 Pin | Description |
|---|---|---|---|
| **Sensor 1 (Slot A01)** | `VCC` | `5V` / `VIN` | 5V Power Supply (Shared) |
| | `GND` | `GND` | Common Ground (Shared) |
| | `TRIG` | `GPIO 5` | Ultrasonic Trigger Output |
| | `ECHO` | `GPIO 18` | Ultrasonic Echo Input |
| **Sensor 2 (Slot A02)** | `VCC` | `5V` / `VIN` | 5V Power Supply (Shared) |
| | `GND` | `GND` | Common Ground (Shared) |
| | `TRIG` | `GPIO 19` | Ultrasonic Trigger Output |
| | `ECHO` | `GPIO 21` | Ultrasonic Echo Input |

> [!TIP]
> **Voltage Recommendation**:
> standard HC-SR04 ECHO outputs 5V logic signals. While many ESP32 GPIOs tolerate 5V signals, placing a simple resistor divider (e.g. 1kΩ resistor in series between ECHO and GPIO, and 2kΩ between GPIO and GND) reduces 5V to 3.3V for safe long-term operation.

---

## Setup & Flashing Steps

### 1. Arduino IDE Setup
- Install Arduino IDE 2.x
- Add ESP32 Board Manager URL: `https://dl.espressif.com/dl/package_esp32_index.json`
- Install **esp32** by Espressif Systems under Board Manager.
- Select Board: **ESP32 Dev Module**

### 2. Install Required Libraries
Open **Tools -> Manage Libraries** and install:
1. **PubSubClient** by Nick O'Leary
2. **ArduinoJson** by Benoit Blanchon (v6.x)

### 3. Configure Credentials
1. Copy `secrets_template.h` to `secrets.h` in the same directory:
   ```bash
   cp secrets_template.h secrets.h
   ```
2. Open `secrets.h` and fill in:
   - `WIFI_SSID` & `WIFI_PASSWORD`
   - `AWS_IOT_ENDPOINT` (Find using `aws iot describe-endpoint --endpoint-type iot:Data-ATS`)
   - `AWS_CERT_CA` (Amazon Root CA 1 certificate)
   - `AWS_CERT_CRT` (Device Certificate)
   - `AWS_CERT_PRIVATE` (Device Private Key)

### 4. Upload & Monitor
- Connect your ESP32 board via USB.
- Select your COM port under **Tools -> Port**.
- Click **Upload**.
- Open **Serial Monitor** at **115200 baud** to see real-time distance readings and MQTT publish confirmation!
