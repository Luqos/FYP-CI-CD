"""
Unit tests for backend/shared/parking_logic.py using standard unittest library
"""

import unittest
from decimal import Decimal
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.shared.parking_logic import (
    validate_and_evaluate_reading,
    compute_confidence,
    calculate_billing,
    generate_session_id,
    is_reading_stale,
    convert_floats_to_decimals,
    convert_decimals_to_native,
    STATUS_AVAILABLE,
    STATUS_OCCUPIED,
    STATUS_SENSOR_ERROR,
)


class TestParkingLogic(unittest.TestCase):

    def test_distance_boundary_validation(self):
        # Min distance boundary: 2 cm -> OCCUPIED
        status, conf, health, dist = validate_and_evaluate_reading(2.0)
        self.assertEqual(status, STATUS_OCCUPIED)
        self.assertEqual(dist, 2.0)

        # Threshold boundary: 30 cm -> OCCUPIED
        status, conf, health, dist = validate_and_evaluate_reading(30.0)
        self.assertEqual(status, STATUS_OCCUPIED)
        self.assertEqual(dist, 30.0)

        # Above threshold: 30.1 cm -> AVAILABLE
        status, conf, health, dist = validate_and_evaluate_reading(30.1)
        self.assertEqual(status, STATUS_AVAILABLE)

        # Max distance boundary: 400 cm -> AVAILABLE
        status, conf, health, dist = validate_and_evaluate_reading(400.0)
        self.assertEqual(status, STATUS_AVAILABLE)
        
        # Out of bounds (High distance or timeout -1.0) -> AVAILABLE
        self.assertEqual(validate_and_evaluate_reading(400.1)[0], STATUS_AVAILABLE)
        self.assertEqual(validate_and_evaluate_reading(999.0)[0], STATUS_AVAILABLE)
        self.assertEqual(validate_and_evaluate_reading(-1.0)[0], STATUS_AVAILABLE)

        # Invalid / sensor noise (too close)
        self.assertEqual(validate_and_evaluate_reading(1.9)[0], STATUS_SENSOR_ERROR)
        self.assertEqual(validate_and_evaluate_reading(None)[0], STATUS_SENSOR_ERROR)
        self.assertEqual(validate_and_evaluate_reading("invalid")[0], STATUS_SENSOR_ERROR)

    def test_confidence_calculation(self):
        # Exact threshold (30 cm) -> min bounded confidence 0.10
        self.assertEqual(compute_confidence(30.0), 0.10)

        # Far from threshold (0 cm difference effectively bounded at 1.0)
        self.assertEqual(compute_confidence(60.0), 1.00)
        self.assertEqual(compute_confidence(0.0), 1.00)

        # Accept valid device confidence if provided
        self.assertEqual(compute_confidence(15.0, device_confidence=0.95), 0.95)
        # Ignore invalid device confidence
        self.assertEqual(compute_confidence(15.0, device_confidence=1.5), 0.50)

    def test_exact_billing_logic(self):
        # 5 minutes -> RM 0.00 (within 10-minute grace period)
        duration_mins, billing_rm = calculate_billing(5 * 60)
        self.assertEqual(duration_mins, 5)
        self.assertEqual(billing_rm, 0.00)

        # 10 minutes -> RM 0.00 (exact boundary)
        duration_mins, billing_rm = calculate_billing(10 * 60)
        self.assertEqual(duration_mins, 10)
        self.assertEqual(billing_rm, 0.00)

        # 15 minutes -> RM 2.00 (1 started hour)
        duration_mins, billing_rm = calculate_billing(15 * 60)
        self.assertEqual(duration_mins, 15)
        self.assertEqual(billing_rm, 2.00)

        # 61 minutes -> RM 4.00 (2 started hours)
        duration_mins, billing_rm = calculate_billing(61 * 60)
        self.assertEqual(duration_mins, 61)
        self.assertEqual(billing_rm, 4.00)

    def test_session_id_generation(self):
        session_id = generate_session_id("A01", 1781510400)
        self.assertTrue(session_id.startswith("A01-1781510400-"))
        self.assertEqual(len(session_id.split("-")), 3)

    def test_stale_reading_detection(self):
        current_epoch = 1000
        self.assertFalse(is_reading_stale(950, current_epoch))  # 50s old -> not stale
        self.assertTrue(is_reading_stale(930, current_epoch))   # 70s old -> stale (>60s)

    def test_dynamodb_decimal_conversions(self):
        payload = {
            "distanceCm": 14.2,
            "nested": {"confidence": 0.91},
            "slotId": "A01",
        }
        converted = convert_floats_to_decimals(payload)
        self.assertIsInstance(converted["distanceCm"], Decimal)
        self.assertIsInstance(converted["nested"]["confidence"], Decimal)
        self.assertEqual(str(converted["distanceCm"]), "14.2")

        native = convert_decimals_to_native(converted)
        self.assertIsInstance(native["distanceCm"], float)
        self.assertEqual(native["distanceCm"], 14.2)


if __name__ == "__main__":
    unittest.main()
