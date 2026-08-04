"""
Shared ingestion service for Smart Parking AWS Academy.
Reusable persistence operation used by both ingest_sensor_data Lambda and dashboard_api /ingest-test endpoint.
"""

import datetime
import logging
import os
import re
import uuid
from decimal import Decimal
from typing import Any, Dict, Optional

try:
    import boto3
except ImportError:
    boto3 = None

from .parking_logic import (
    STATUS_AVAILABLE,
    STATUS_MAINTENANCE,
    STATUS_OCCUPIED,
    STATUS_SENSOR_ERROR,
    calculate_billing,
    convert_decimals_to_native,
    convert_floats_to_decimals,
    generate_session_id,
    validate_and_evaluate_reading,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SLOT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


def validate_slot_id(slot_id: str) -> bool:
    """Validates slotId format ^[A-Za-z0-9_-]{1,32}$"""
    if not slot_id or not isinstance(slot_id, str):
        return False
    return bool(SLOT_ID_PATTERN.match(slot_id))


def process_telemetry_ingestion(
    payload: Dict[str, Any],
    topic_slot_id: Optional[str] = None,
    slot_table_name: Optional[str] = None,
    events_table_name: Optional[str] = None,
    dynamodb_resource: Optional[Any] = None,
    dynamodb_client: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Ingests and processes sensor telemetry payload.
    Supports wrapped IoT Rule events or direct JSON payloads.
    """
    if not slot_table_name:
        slot_table_name = os.environ.get("SLOT_STATE_TABLE", "ParkingSlotState")
    if not events_table_name:
        events_table_name = os.environ.get("EVENTS_TABLE", "ParkingEvents")

    if not dynamodb_resource and boto3:
        dynamodb_resource = boto3.resource("dynamodb")
    if not dynamodb_client and boto3:
        dynamodb_client = boto3.client("dynamodb")

    raw_telemetry = payload.get("payload", payload) if isinstance(payload, dict) else payload
    if not isinstance(raw_telemetry, dict):
        raw_telemetry = {}

    slot_id = topic_slot_id or raw_telemetry.get("slotId")
    if not slot_id or not validate_slot_id(slot_id):
        raise ValueError(f"Invalid or missing slotId: '{slot_id}'")

    distance_input = raw_telemetry.get("distanceCm")
    device_confidence = raw_telemetry.get("confidence")

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    current_epoch = int(now_utc.timestamp())
    now_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    new_status, confidence, sensor_health, valid_distance_cm = validate_and_evaluate_reading(
        distance_input=distance_input,
        device_confidence=device_confidence,
    )

    existing_item = None
    if dynamodb_resource:
        slot_table = dynamodb_resource.Table(slot_table_name)
        try:
            response = slot_table.get_item(Key={"slotId": slot_id})
            existing_item = response.get("Item")
        except Exception as e:
            logger.warning(f"Could not read existing state for slot {slot_id}: {e}")

    prev_status = existing_item.get("status") if existing_item else None
    current_session_id = existing_item.get("currentSessionId") if existing_item else None
    current_session_start = existing_item.get("currentSessionStartedEpoch") if existing_item else None

    # Handle MAINTENANCE lock
    if prev_status == STATUS_MAINTENANCE:
        logger.info(f"Slot {slot_id} is in MAINTENANCE mode. Telemetry metrics updated, status locked.")
        if dynamodb_resource:
            update_expr = (
                "SET distanceCm = :dist, confidence = :conf, lastSeenEpoch = :epoch, "
                "lastSeenIso = :iso, sensorHealth = :health, updatedBy = :by"
            )
            expr_attr = {
                ":dist": convert_floats_to_decimals(valid_distance_cm if valid_distance_cm is not None else -1),
                ":conf": convert_floats_to_decimals(confidence),
                ":epoch": current_epoch,
                ":iso": now_iso,
                ":health": sensor_health,
                ":by": "iot_telemetry",
            }
            slot_table.update_item(
                Key={"slotId": slot_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_attr,
            )

        return {
            "slotId": slot_id,
            "status": STATUS_MAINTENANCE,
            "previousStatus": STATUS_MAINTENANCE,
            "eventCreated": False,
            "message": "Telemetry updated while slot remains in MAINTENANCE mode",
        }

    is_first_reading = existing_item is None
    status_changed = prev_status != new_status
    should_create_event = is_first_reading or status_changed

    if prev_status == STATUS_SENSOR_ERROR and new_status == STATUS_SENSOR_ERROR:
        should_create_event = False

    next_session_id = current_session_id
    next_session_start = current_session_start
    session_duration_mins = None
    billing_rm = 0.0

    if new_status == STATUS_OCCUPIED:
        if not current_session_id:
            next_session_id = generate_session_id(slot_id, current_epoch)
            next_session_start = current_epoch
    elif new_status == STATUS_AVAILABLE and prev_status == STATUS_OCCUPIED:
        if current_session_start:
            duration_sec = current_epoch - int(current_session_start)
            session_duration_mins, billing_rm = calculate_billing(duration_sec)
        next_session_id = None
        next_session_start = None

    event_id = str(uuid.uuid4())
    event_time_ms = now_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    event_key = f"{event_time_ms}#{event_id}"

    slot_item: Dict[str, Any] = {
        "slotId": slot_id,
        "status": new_status,
        "distanceCm": convert_floats_to_decimals(valid_distance_cm if valid_distance_cm is not None else -1),
        "confidence": convert_floats_to_decimals(confidence),
        "lastSeenEpoch": current_epoch,
        "lastSeenIso": now_iso,
        "sensorHealth": sensor_health,
        "updatedBy": "iot_telemetry",
    }
    if next_session_id:
        slot_item["currentSessionId"] = next_session_id
        slot_item["currentSessionStartedEpoch"] = int(next_session_start)

    if dynamodb_resource or dynamodb_client:
        if should_create_event:
            event_type = "FIRST_READING" if is_first_reading else "STATUS_CHANGE"
            event_item: Dict[str, Any] = {
                "slotId": slot_id,
                "eventKey": event_key,
                "eventTime": event_time_ms,
                "eventId": event_id,
                "eventType": event_type,
                "previousStatus": prev_status or "NONE",
                "newStatus": new_status,
                "distanceCm": convert_floats_to_decimals(valid_distance_cm if valid_distance_cm is not None else -1),
                "confidence": convert_floats_to_decimals(confidence),
                "rawPayload": convert_floats_to_decimals(raw_telemetry),
            }
            if next_session_id or current_session_id:
                event_item["sessionId"] = current_session_id or next_session_id
            if session_duration_mins is not None:
                event_item["durationMinutes"] = session_duration_mins
                event_item["billingAmountRM"] = convert_floats_to_decimals(billing_rm)

            if dynamodb_client:
                transact_items = [
                    {
                        "Put": {
                            "TableName": slot_table_name,
                            "Item": {k: _to_dynamodb_attr(v) for k, v in slot_item.items()},
                        }
                    },
                    {
                        "Put": {
                            "TableName": events_table_name,
                            "Item": {k: _to_dynamodb_attr(v) for k, v in event_item.items()},
                        }
                    },
                ]
                try:
                    dynamodb_client.transact_write_items(TransactItems=transact_items)
                except Exception as e:
                    logger.warning(f"TransactWrite failed, retrying write once: {e}")
                    if dynamodb_resource:
                        dynamodb_resource.Table(slot_table_name).put_item(Item=slot_item)
                        dynamodb_resource.Table(events_table_name).put_item(Item=event_item)
            elif dynamodb_resource:
                dynamodb_resource.Table(slot_table_name).put_item(Item=slot_item)
                dynamodb_resource.Table(events_table_name).put_item(Item=event_item)
        elif dynamodb_resource:
            dynamodb_resource.Table(slot_table_name).put_item(Item=slot_item)

    return convert_decimals_to_native({
        "slotId": slot_id,
        "status": new_status,
        "previousStatus": prev_status,
        "distanceCm": valid_distance_cm,
        "confidence": confidence,
        "sensorHealth": sensor_health,
        "eventCreated": should_create_event,
        "eventKey": event_key if should_create_event else None,
        "billingAmountRM": billing_rm if session_duration_mins is not None else None,
    })


def set_admin_slot_mode(
    slot_id: str,
    target_status: str,
    slot_table_name: Optional[str] = None,
    events_table_name: Optional[str] = None,
    dynamodb_resource: Optional[Any] = None,
) -> Dict[str, Any]:
    if not validate_slot_id(slot_id):
        raise ValueError(f"Invalid slotId: {slot_id}")

    if target_status not in (STATUS_MAINTENANCE, STATUS_AVAILABLE):
        raise ValueError(f"Invalid target admin status: {target_status}")

    if not slot_table_name:
        slot_table_name = os.environ.get("SLOT_STATE_TABLE", "ParkingSlotState")
    if not events_table_name:
        events_table_name = os.environ.get("EVENTS_TABLE", "ParkingEvents")

    if not dynamodb_resource and boto3:
        dynamodb_resource = boto3.resource("dynamodb")

    existing_item = {}
    if dynamodb_resource:
        slot_table = dynamodb_resource.Table(slot_table_name)
        existing_resp = slot_table.get_item(Key={"slotId": slot_id})
        existing_item = existing_resp.get("Item", {})

    prev_status = existing_item.get("status", "NONE")

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    current_epoch = int(now_utc.timestamp())
    now_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    event_id = str(uuid.uuid4())
    event_time_ms = now_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    event_key = f"{event_time_ms}#{event_id}"

    new_slot_item: Dict[str, Any] = {
        "slotId": slot_id,
        "status": target_status,
        "distanceCm": existing_item.get("distanceCm", Decimal("-1")),
        "confidence": existing_item.get("confidence", Decimal("1.0")),
        "lastSeenEpoch": current_epoch,
        "lastSeenIso": now_iso,
        "sensorHealth": "ONLINE",
        "updatedBy": "admin_override",
    }

    event_item: Dict[str, Any] = {
        "slotId": slot_id,
        "eventKey": event_key,
        "eventTime": event_time_ms,
        "eventId": event_id,
        "eventType": "ADMIN_OVERRIDE",
        "previousStatus": prev_status,
        "newStatus": target_status,
        "rawPayload": {"overrideBy": "admin", "targetStatus": target_status},
    }

    if dynamodb_resource:
        slot_table = dynamodb_resource.Table(slot_table_name)
        events_table = dynamodb_resource.Table(events_table_name)
        slot_table.put_item(Item=new_slot_item)
        events_table.put_item(Item=event_item)

    return convert_decimals_to_native({
        "slotId": slot_id,
        "status": target_status,
        "previousStatus": prev_status,
        "eventKey": event_key,
        "message": f"Admin override updated slot {slot_id} to {target_status}",
    })


def _to_dynamodb_attr(val: Any) -> Dict[str, Any]:
    if val is None:
        return {"NULL": True}
    elif isinstance(val, bool):
        return {"BOOL": val}
    elif isinstance(val, (int, Decimal)):
        return {"N": str(val)}
    elif isinstance(val, float):
        return {"N": str(Decimal(str(val)))}
    elif isinstance(val, str):
        return {"S": val}
    elif isinstance(val, dict):
        return {"M": {k: _to_dynamodb_attr(v) for k, v in val.items()}}
    elif isinstance(val, list):
        return {"L": [_to_dynamodb_attr(v) for v in val]}
    return {"S": str(val)}
