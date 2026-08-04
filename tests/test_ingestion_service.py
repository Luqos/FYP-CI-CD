"""
Unit tests for backend/shared/ingestion_service.py using unittest.TestCase
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.shared.ingestion_service import (
    process_telemetry_ingestion,
    set_admin_slot_mode,
    validate_slot_id,
)
from backend.shared.parking_logic import (
    STATUS_AVAILABLE,
    STATUS_OCCUPIED,
    STATUS_MAINTENANCE,
    STATUS_SENSOR_ERROR,
)


class TestIngestionService(unittest.TestCase):

    def test_validate_slot_id(self):
        self.assertTrue(validate_slot_id("A01"))
        self.assertTrue(validate_slot_id("slot-123_B"))
        self.assertFalse(validate_slot_id(""))
        self.assertFalse(validate_slot_id("invalid slot spaces!"))
        self.assertFalse(validate_slot_id("a" * 33))

    @patch("backend.shared.ingestion_service.boto3")
    def test_process_telemetry_ingestion_new_slot(self, mock_boto3):
        mock_resource = MagicMock()
        mock_client = MagicMock()
        mock_table = MagicMock()

        mock_boto3.resource.return_value = mock_resource
        mock_boto3.client.return_value = mock_client
        mock_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {}  # First reading for slot

        payload = {"slotId": "A01", "distanceCm": 14.2}
        result = process_telemetry_ingestion(
            payload=payload,
            dynamodb_resource=mock_resource,
            dynamodb_client=mock_client,
        )

        self.assertEqual(result["slotId"], "A01")
        self.assertEqual(result["status"], STATUS_OCCUPIED)
        self.assertTrue(result["eventCreated"])
        self.assertTrue(mock_client.transact_write_items.called)

    @patch("backend.shared.ingestion_service.boto3")
    def test_admin_override_maintenance(self, mock_boto3):
        mock_resource = MagicMock()
        mock_table = MagicMock()
        mock_boto3.resource.return_value = mock_resource
        mock_resource.Table.return_value = mock_table

        mock_table.get_item.return_value = {
            "Item": {"slotId": "A01", "status": STATUS_OCCUPIED, "currentSessionId": "A01-123-abc"}
        }

        result = set_admin_slot_mode(
            slot_id="A01",
            target_status=STATUS_MAINTENANCE,
            dynamodb_resource=mock_resource,
        )

        self.assertEqual(result["slotId"], "A01")
        self.assertEqual(result["status"], STATUS_MAINTENANCE)
        self.assertEqual(mock_table.put_item.call_count, 2)


if __name__ == "__main__":
    unittest.main()
