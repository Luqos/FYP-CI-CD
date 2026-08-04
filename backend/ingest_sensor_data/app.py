"""
AWS Lambda Handler: ingest_sensor_data
Triggered by AWS IoT Topic Rule (or directly for testing).
"""

import json
import logging
import os
import sys

# Add shared directory to path if needed when packaged
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared.ingestion_service import process_telemetry_ingestion

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict, context: any) -> dict:
    """
    Lambda handler for IoT sensor ingestion.
    Event payload format can be direct JSON or IoT Rule enriched event.
    """
    logger.info(f"Received IoT event: {json.dumps(event)}")

    # Extract MQTT topic if available (e.g. smart-parking/slot/A01/telemetry)
    mqtt_topic = event.get("mqttTopic") or event.get("topic", "")
    topic_slot_id = None

    if mqtt_topic and "smart-parking/slot/" in mqtt_topic:
        parts = mqtt_topic.split("/")
        if len(parts) >= 3:
            topic_slot_id = parts[2]

    try:
        result = process_telemetry_ingestion(
            payload=event,
            topic_slot_id=topic_slot_id,
        )
        logger.info(f"Successfully processed ingestion: {result}")
        return {
            "statusCode": 200,
            "body": result,
        }
    except ValueError as ve:
        logger.warning(f"Validation error processing telemetry: {ve}")
        return {
            "statusCode": 400,
            "error": str(ve),
        }
    except Exception as e:
        logger.error(f"Error processing sensor telemetry: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "error": "Internal ingestion processing failure",
        }
