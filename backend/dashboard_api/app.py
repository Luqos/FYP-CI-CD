"""
AWS Lambda Handler: dashboard_api
Triggered by Amazon API Gateway HTTP API.
Exposes REST API endpoints for the S3 static website dashboard.
"""

import csv
import datetime
import io
import json
import logging
import os
import sys
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

try:
    import boto3
except ImportError:
    boto3 = None

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared.ingestion_service import (
    process_telemetry_ingestion,
    set_admin_slot_mode,
    validate_slot_id,
)
from shared.parking_logic import (
    STATUS_AVAILABLE,
    STATUS_MAINTENANCE,
    STATUS_OCCUPIED,
    STATUS_OFFLINE,
    STATUS_SENSOR_ERROR,
    convert_decimals_to_native,
    is_reading_stale,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}

DEFAULT_PROTOTYPE_SLOTS = {
    "A01": {"distanceCm": 85.0, "status": STATUS_AVAILABLE},
    "A02": {"distanceCm": 90.0, "status": STATUS_AVAILABLE},
}


def build_response(status_code: int, body: Any) -> Dict[str, Any]:
    """Helper to build API Gateway HTTP response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body) if not isinstance(body, str) else body,
    }


def normalize_request_path(event: dict) -> Tuple[str, str]:
    """Extracts HTTP method and normalizes request path by stripping stage prefixes like /dev."""
    request_context = event.get("requestContext", {})
    http_info = request_context.get("http", {})
    http_method = http_info.get("method", event.get("httpMethod", "GET")).upper()

    raw_path = http_info.get("path") or event.get("rawPath") or event.get("path") or "/"

    path = raw_path
    if path.startswith("/dev/"):
        path = path[4:]
    elif path == "/dev":
        path = "/"
    elif path.startswith("/prod/"):
        path = path[5:]
    elif path == "/prod":
        path = "/"

    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]

    return http_method, path


def lambda_handler(event: dict, context: any) -> dict:
    """Main API Gateway HTTP API handler."""
    logger.info(f"Received API Gateway event: {json.dumps(event)}")

    http_method, path = normalize_request_path(event)
    logger.info(f"Normalized request: method={http_method}, path={path}")

    if http_method == "OPTIONS":
        return build_response(200, {"message": "OK"})

    try:
        if path == "/health" and http_method == "GET":
            return get_health()

        elif path == "/slots" and http_method == "GET":
            return get_all_slots()

        elif path.startswith("/slots/") and http_method == "GET":
            slot_id = path.split("/slots/")[1].strip("/")
            return get_single_slot(slot_id)

        elif path == "/events" and http_method == "GET":
            query_params = event.get("queryStringParameters") or {}
            slot_id = query_params.get("slotId")
            limit_str = query_params.get("limit", "20")
            return get_events(slot_id, limit_str)

        elif path == "/ingest-test" and http_method == "POST":
            body = parse_json_body(event)
            return handle_ingest_test(body)

        elif path == "/reports/daily" and http_method == "POST":
            body = parse_json_body(event)
            return handle_daily_report(body)

        elif path.startswith("/admin/slot/") and http_method == "POST":
            parts = path.split("/")
            if len(parts) >= 5:
                slot_id = parts[3]
                action = parts[4]
                if action == "maintenance":
                    return handle_admin_override(slot_id, STATUS_MAINTENANCE)
                elif action == "available":
                    return handle_admin_override(slot_id, STATUS_AVAILABLE)

        return build_response(404, {"error": f"Endpoint '{path}' not found"})

    except ValueError as ve:
        logger.warning(f"Validation error handling request {path}: {ve}")
        return build_response(400, {"error": str(ve)})
    except Exception as e:
        logger.error(f"Internal server error handling request {path}: {e}", exc_info=True)
        return build_response(500, {"error": "Internal Server Error"})


def parse_json_body(event: dict) -> dict:
    body_raw = event.get("body")
    if not body_raw:
        return {}
    if isinstance(body_raw, dict):
        return body_raw
    try:
        return json.loads(body_raw)
    except Exception:
        raise ValueError("Invalid JSON request body")


def get_health() -> dict:
    return build_response(
        200,
        {
            "status": "healthy",
            "service": "smart-parking-dashboard-api",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
    )


def get_all_slots() -> dict:
    slot_table_name = os.environ.get("SLOT_STATE_TABLE", "ParkingSlotState")
    items = []
    if boto3:
        try:
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table(slot_table_name)
            items = table.scan().get("Items", [])
        except Exception as e:
            logger.warning(f"DynamoDB scan error: {e}")

    now_epoch = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Ensure prototype slots A01 and A02 are always represented in items list if missing from DynamoDB
    existing_slot_ids = {i.get("slotId") for i in items if isinstance(i, dict) and i.get("slotId")}
    for default_id, default_data in DEFAULT_PROTOTYPE_SLOTS.items():
        if default_id not in existing_slot_ids:
            items.append({
                "slotId": default_id,
                "status": default_data["status"],
                "distanceCm": Decimal(str(default_data["distanceCm"])),
                "confidence": Decimal("1.0"),
                "sensorHealth": "ONLINE",
                "lastSeenEpoch": now_epoch,
                "lastSeenIso": now_iso,
            })

    slots = []
    summary = {
        "total": 0,
        "available": 0,
        "occupied": 0,
        "offline": 0,
        "sensorError": 0,
        "maintenance": 0,
    }

    for item in items:
        native_item = convert_decimals_to_native(item)
        slot_id = native_item.get("slotId")
        persisted_status = native_item.get("status", STATUS_AVAILABLE)
        last_seen = native_item.get("lastSeenEpoch", 0)

        is_stale = is_reading_stale(last_seen, now_epoch)
        sensor_health = "OFFLINE" if is_stale else native_item.get("sensorHealth", "ONLINE")
        effective_status = STATUS_OFFLINE if is_stale else persisted_status

        slot_record = {
            "slotId": slot_id,
            "status": effective_status,
            "persistedStatus": persisted_status,
            "distanceCm": native_item.get("distanceCm"),
            "confidence": native_item.get("confidence"),
            "sensorHealth": sensor_health,
            "lastSeenIso": native_item.get("lastSeenIso"),
            "isStale": is_stale,
        }
        if native_item.get("currentSessionId"):
            slot_record["currentSessionId"] = native_item.get("currentSessionId")
        slots.append(slot_record)

        summary["total"] += 1
        if effective_status == STATUS_AVAILABLE:
            summary["available"] += 1
        elif effective_status == STATUS_OCCUPIED:
            summary["occupied"] += 1
        elif effective_status == STATUS_OFFLINE:
            summary["offline"] += 1
        elif effective_status == STATUS_SENSOR_ERROR:
            summary["sensorError"] += 1
        elif effective_status == STATUS_MAINTENANCE:
            summary["maintenance"] += 1

    slots.sort(key=lambda s: s["slotId"])
    return build_response(200, {"slots": slots, "summary": summary})


def get_single_slot(slot_id: str) -> dict:
    if not validate_slot_id(slot_id):
        raise ValueError(f"Invalid slotId parameter: '{slot_id}'")

    slot_table_name = os.environ.get("SLOT_STATE_TABLE", "ParkingSlotState")
    item = None
    if boto3:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(slot_table_name)
        response = table.get_item(Key={"slotId": slot_id})
        item = response.get("Item")

    if not item:
        if slot_id in DEFAULT_PROTOTYPE_SLOTS:
            now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            default_data = DEFAULT_PROTOTYPE_SLOTS[slot_id]
            item = {
                "slotId": slot_id,
                "status": default_data["status"],
                "distanceCm": Decimal(str(default_data["distanceCm"])),
                "confidence": Decimal("1.0"),
                "sensorHealth": "ONLINE",
                "lastSeenIso": now_iso,
                "lastSeenEpoch": int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
            }
        else:
            return build_response(404, {"error": f"Slot '{slot_id}' not found"})

    native_item = convert_decimals_to_native(item)
    now_epoch = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    last_seen = native_item.get("lastSeenEpoch", 0)

    is_stale = is_reading_stale(last_seen, now_epoch)
    effective_status = STATUS_OFFLINE if is_stale else native_item.get("status")

    native_item["isStale"] = is_stale
    native_item["effectiveStatus"] = effective_status
    if is_stale:
        native_item["sensorHealth"] = "OFFLINE"

    return build_response(200, native_item)


def get_events(slot_id: Optional[str], limit_str: str) -> dict:
    try:
        limit = int(limit_str)
        if limit < 1 or limit > 100:
            raise ValueError()
    except Exception:
        raise ValueError("Query parameter 'limit' must be an integer between 1 and 100")

    events_table_name = os.environ.get("EVENTS_TABLE", "ParkingEvents")
    items = []
    if boto3:
        try:
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table(events_table_name)
            if slot_id:
                if not validate_slot_id(slot_id):
                    raise ValueError(f"Invalid slotId: '{slot_id}'")
                response = table.query(
                    KeyConditionExpression="slotId = :sid",
                    ExpressionAttributeValues={":sid": slot_id},
                    ScanIndexForward=False,
                    Limit=limit,
                )
                items = response.get("Items", [])
            else:
                response = table.scan(Limit=limit)
                items = response.get("Items", [])
                items.sort(key=lambda x: x.get("eventKey", ""), reverse=True)
                items = items[:limit]
        except Exception as e:
            logger.warning(f"DynamoDB events error: {e}")

    native_items = [convert_decimals_to_native(i) for i in items]
    return build_response(200, {"events": native_items, "count": len(native_items)})


def handle_ingest_test(body: dict) -> dict:
    slot_id = body.get("slotId")
    if not slot_id or not validate_slot_id(slot_id):
        raise ValueError("Missing or invalid slotId in payload")

    result = process_telemetry_ingestion(payload=body, topic_slot_id=slot_id)
    return build_response(200, result)


def handle_admin_override(slot_id: str, target_status: str) -> dict:
    if not validate_slot_id(slot_id):
        raise ValueError(f"Invalid slotId: {slot_id}")

    result = set_admin_slot_mode(slot_id=slot_id, target_status=target_status)
    return build_response(200, result)


def handle_daily_report(body: dict) -> dict:
    date_str = body.get("date")
    kl_tz = datetime.timezone(datetime.timedelta(hours=8))
    now_kl = datetime.datetime.now(kl_tz)

    if not date_str:
        date_str = now_kl.strftime("%Y-%m-%d")
    else:
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Query parameter 'date' must be in YYYY-MM-DD format")

    reports_bucket = os.environ.get("REPORTS_BUCKET")
    events_table_name = os.environ.get("EVENTS_TABLE", "ParkingEvents")

    if not reports_bucket:
        raise ValueError("REPORTS_BUCKET environment variable is not configured")

    items = []
    filtered_events = []
    s3_key = f"daily/{date_str}/parking-events.csv"

    if boto3:
        try:
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table(events_table_name)
            s3_client = boto3.client("s3")

            start_dt_kl = datetime.datetime.strptime(f"{date_str}T00:00:00+08:00", "%Y-%m-%dT%H:%M:%S%z")
            end_dt_kl = datetime.datetime.strptime(f"{date_str}T23:59:59.999999+08:00", "%Y-%m-%dT%H:%M:%S.%f%z")

            start_iso_utc = start_dt_kl.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            end_iso_utc = end_dt_kl.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.999Z")

            items = table.scan().get("Items", [])

            for item in items:
                event_time = str(item.get("eventTime", ""))
                if start_iso_utc <= event_time <= end_iso_utc:
                    filtered_events.append(convert_decimals_to_native(item))

            filtered_events.sort(key=lambda x: x.get("eventTime", ""))

            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow([
                "slotId",
                "eventTime",
                "eventType",
                "previousStatus",
                "newStatus",
                "distanceCm",
                "confidence",
                "sessionId",
                "durationMinutes",
                "billingAmountRM",
            ])

            for ev in filtered_events:
                writer.writerow([
                    ev.get("slotId", ""),
                    ev.get("eventTime", ""),
                    ev.get("eventType", ""),
                    ev.get("previousStatus", ""),
                    ev.get("newStatus", ""),
                    ev.get("distanceCm", ""),
                    ev.get("confidence", ""),
                    ev.get("sessionId", ""),
                    ev.get("durationMinutes", ""),
                    ev.get("billingAmountRM", ""),
                ])

            csv_bytes = csv_buffer.getvalue().encode("utf-8")
            s3_client.put_object(
                Bucket=reports_bucket,
                Key=s3_key,
                Body=csv_bytes,
                ContentType="text/csv",
            )
        except Exception as e:
            logger.error(f"Report generation error: {e}")

    return build_response(
        200,
        {
            "date": date_str,
            "recordCount": len(filtered_events),
            "bucket": reports_bucket,
            "key": s3_key,
        },
    )
