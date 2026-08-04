"""
Python CLI Sequence Simulator using AWS CLI `aws iot-data publish`
Simulates telemetry sequence for 2 slots (A01, A02) through state transitions.
"""

import json
import subprocess
import sys
import time


def get_iot_endpoint() -> str:
    cmd = [
        "aws", "iot", "describe-endpoint",
        "--endpoint-type", "iot:Data-ATS",
        "--query", "endpointAddress",
        "--output", "text"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        raise RuntimeError(f"Failed to discover AWS IoT endpoint: {res.stderr}")
    return res.stdout.strip()


def publish_telemetry(endpoint: str, slot_id: str, distance_cm: float):
    topic = f"smart-parking/slot/{slot_id}/telemetry"
    payload = {
        "slotId": slot_id,
        "distanceCm": distance_cm,
        "deviceId": f"sim-{slot_id}"
    }

    cmd = [
        "aws", "iot-data", "publish",
        "--endpoint-url", f"https://{endpoint}",
        "--topic", topic,
        "--cli-binary-format", "raw-in-base64-out",
        "--payload", json.dumps(payload)
    ]

    print(f"[SIMULATOR] Publishing to '{topic}': distanceCm={distance_cm}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[SIMULATOR ERROR] Failed to publish: {res.stderr}")
    else:
        print("[SIMULATOR SUCCESS] Telemetry sent.")


def run_sequence():
    print("=== AWS Academy Smart Parking IoT Simulator Sequence ===")
    try:
        endpoint = get_iot_endpoint()
        print(f"Discovered IoT ATS Endpoint: {endpoint}\n")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    steps = [
        ("A01", 85.0, "Step 1: Slot A01 AVAILABLE"),
        ("A01", 14.2, "Step 2: Slot A01 OCCUPIED (Starts Session)"),
        ("A01", 12.0, "Step 3: Slot A01 STILL OCCUPIED"),
        ("A01", 90.0, "Step 4: Slot A01 AVAILABLE (Ends Session & Bills)"),
        ("A02", 999.0, "Step 5: Slot A02 SENSOR_ERROR"),
        ("A02", 75.0, "Step 6: Slot A02 RECOVERED to AVAILABLE")
    ]

    for slot_id, dist, desc in steps:
        print(f"\n---> {desc}")
        publish_telemetry(endpoint, slot_id, dist)
        time.sleep(3)

    print("\n=== Simulation Sequence Complete! ===")


if __name__ == "__main__":
    run_sequence()
