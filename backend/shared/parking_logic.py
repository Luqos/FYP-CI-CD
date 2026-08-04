"""
Pure parking domain logic and validation functions for Smart Parking AWS Academy.
"""

import math
import uuid
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

# Core Constants
MIN_DISTANCE_CM: float = 2.0
MAX_DISTANCE_CM: float = 400.0
OCCUPIED_THRESHOLD_CM: float = 30.0
STALE_AFTER_SECONDS: int = 60
GRACE_PERIOD_MINUTES: int = 10
HOURLY_RATE_RM: float = 2.00

# Status Definitions
STATUS_AVAILABLE = "AVAILABLE"
STATUS_OCCUPIED = "OCCUPIED"
STATUS_SENSOR_ERROR = "SENSOR_ERROR"
STATUS_MAINTENANCE = "MAINTENANCE"
STATUS_OFFLINE = "OFFLINE"

SENSOR_HEALTH_ONLINE = "ONLINE"
SENSOR_HEALTH_OFFLINE = "OFFLINE"


def validate_and_evaluate_reading(
    distance_input: Any,
    device_confidence: Optional[Any] = None,
) -> Tuple[str, float, str, Optional[float]]:
    """
    Validates distance input and determines slot status, confidence, and sensor health.

    Returns:
        (status, confidence, sensor_health, valid_distance_cm)
    """
    # Check if distance is missing or non-numeric
    if distance_input is None:
        return STATUS_SENSOR_ERROR, 0.0, SENSOR_HEALTH_ONLINE, None

    try:
        distance_cm = float(distance_input)
    except (ValueError, TypeError):
        return STATUS_SENSOR_ERROR, 0.0, SENSOR_HEALTH_ONLINE, None

    # Check distance range bounds
    if distance_cm < MIN_DISTANCE_CM or distance_cm > MAX_DISTANCE_CM:
        return STATUS_SENSOR_ERROR, 0.0, SENSOR_HEALTH_ONLINE, None

    # Evaluate status based on threshold
    if distance_cm <= OCCUPIED_THRESHOLD_CM:
        status = STATUS_OCCUPIED
    else:
        status = STATUS_AVAILABLE

    # Calculate or validate confidence
    confidence = compute_confidence(distance_cm, device_confidence)

    return status, confidence, SENSOR_HEALTH_ONLINE, distance_cm


def compute_confidence(distance_cm: float, device_confidence: Optional[Any] = None) -> float:
    """
    Validates device confidence if numeric [0.0, 1.0], otherwise calculates distance-based confidence.
    """
    if device_confidence is not None:
        try:
            conf_val = float(device_confidence)
            if 0.0 <= conf_val <= 1.0:
                return round(conf_val, 2)
        except (ValueError, TypeError):
            pass

    # Formula: round(min(1.0, max(0.1, abs(distanceCm - 30) / 30)), 2)
    dist_diff = abs(distance_cm - OCCUPIED_THRESHOLD_CM)
    calculated = dist_diff / OCCUPIED_THRESHOLD_CM
    bounded = max(0.1, min(1.0, calculated))
    return round(bounded, 2)


def calculate_billing(duration_seconds: float) -> Tuple[int, float]:
    """
    Calculates duration in minutes and billing amount in RM.
    Rules:
      First 10 minutes: RM 0.00
      After 10 minutes: RM 2.00 per started hour based on total duration.
    """
    duration_minutes = math.ceil(max(0.0, duration_seconds) / 60.0)
    if duration_minutes <= GRACE_PERIOD_MINUTES:
        billing_rm = 0.00
    else:
        hours = math.ceil(duration_minutes / 60.0)
        billing_rm = hours * HOURLY_RATE_RM

    return duration_minutes, round(billing_rm, 2)


def generate_session_id(slot_id: str, start_epoch: int) -> str:
    """Generates a collision-safe session ID: {slotId}-{startEpoch}-{uuid8}"""
    uuid8 = uuid.uuid4().hex[:8]
    return f"{slot_id}-{start_epoch}-{uuid8}"


def is_reading_stale(last_seen_epoch: int, current_epoch: int) -> bool:
    """Checks if reading is older than STALE_AFTER_SECONDS (60 seconds)."""
    return (current_epoch - last_seen_epoch) > STALE_AFTER_SECONDS


def convert_floats_to_decimals(obj: Any) -> Any:
    """
    Recursively converts float and numeric float-like strings/values to Decimal for DynamoDB serialization.
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimals(v) for v in obj]
    return obj


def convert_decimals_to_native(obj: Any) -> Any:
    """
    Recursively converts Decimal objects back to native Python int/float for JSON API output.
    """
    if isinstance(obj, Decimal):
        # Convert to int if whole number, otherwise float
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_native(v) for v in obj]
    return obj
