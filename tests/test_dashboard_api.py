"""
Unit tests for backend/dashboard_api/app.py using unittest.TestCase
"""

import json
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.dashboard_api.app import lambda_handler


def make_api_event(method="GET", path="/health", body=None, query=None):
    event = {
        "requestContext": {
            "http": {
                "method": method,
                "path": path,
            }
        },
        "queryStringParameters": query or {},
    }
    if body:
        event["body"] = json.dumps(body)
    return event


class TestDashboardApi(unittest.TestCase):

    def test_health_endpoint(self):
        event = make_api_event("GET", "/health")
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["status"], "healthy")

    def test_options_cors_preflight(self):
        event = make_api_event("OPTIONS", "/slots")
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["headers"]["Access-Control-Allow-Origin"], "*")

    @patch("backend.dashboard_api.app.boto3")
    def test_get_all_slots(self, mock_boto3):
        mock_resource = MagicMock()
        mock_table = MagicMock()
        mock_boto3.resource.return_value = mock_resource
        mock_resource.Table.return_value = mock_table

        mock_table.scan.return_value = {
            "Items": [
                {
                    "slotId": "A01",
                    "status": "OCCUPIED",
                    "distanceCm": 14.2,
                    "confidence": 0.91,
                    "lastSeenEpoch": 9999999999,
                    "lastSeenIso": "2026-06-15T12:00:00Z",
                    "sensorHealth": "ONLINE",
                }
            ]
        }

        event = make_api_event("GET", "/slots")
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertIn("slots", body)
        self.assertEqual(body["summary"]["occupied"], 1)

    def test_invalid_input_validation(self):
        # Invalid limit parameter
        event = make_api_event("GET", "/events", query={"limit": "999"})
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 400)

        # Invalid slotId
        event = make_api_event("POST", "/ingest-test", body={"slotId": "invalid slot id!"})
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 400)


if __name__ == "__main__":
    unittest.main()
