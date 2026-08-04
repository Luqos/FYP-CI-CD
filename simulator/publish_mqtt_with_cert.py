"""
Python Certificate-Based MQTT Publisher using paho-mqtt
Requires: pip install paho-mqtt
"""

import json
import os
import ssl
import sys
import time

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Error: paho-mqtt is required. Run: pip install paho-mqtt")
    sys.exit(1)

# paho-mqtt 2.x requires CallbackAPIVersion; fall back gracefully for 1.x
try:
    from paho.mqtt.client import CallbackAPIVersion
    _MQTT_CALLBACK_API = CallbackAPIVersion.VERSION1
except ImportError:
    _MQTT_CALLBACK_API = None


def main():
    endpoint = os.environ.get("AWS_IOT_ENDPOINT")
    client_id = os.environ.get("CLIENT_ID", "sim-cert-publisher")
    topic = os.environ.get("TOPIC", "smart-parking/slot/A01/telemetry")
    ca_path = os.environ.get("ROOT_CA_PATH", "certs/AmazonRootCA1.pem")
    cert_path = os.environ.get("CERT_PATH", "certs/device-certificate.pem.crt")
    key_path = os.environ.get("PRIVATE_KEY_PATH", "certs/private.pem.key")

    if not endpoint:
        print("Error: AWS_IOT_ENDPOINT environment variable is required.")
        sys.exit(1)

    if _MQTT_CALLBACK_API is not None:
        client = mqtt.Client(callback_api_version=_MQTT_CALLBACK_API, client_id=client_id, protocol=mqtt.MQTTv311)
    else:
        client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
    client.tls_set(
        ca_certs=ca_path,
        certfile=cert_path,
        keyfile=key_path,
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLSv1_2,
    )

    print(f"Connecting to AWS IoT Core at {endpoint}:8883...")
    client.connect(endpoint, 8883, keepalive=60)
    client.loop_start()

    payload = {
        "slotId": "A01",
        "distanceCm": 14.2,
        "deviceId": client_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    print(f"Publishing to {topic}: {json.dumps(payload)}")
    info = client.publish(topic, json.dumps(payload), qos=1)
    info.wait_for_publish()
    print("Published successfully!")

    time.sleep(2)
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
