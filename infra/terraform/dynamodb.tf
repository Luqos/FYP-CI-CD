# DynamoDB Table 1: Live Parking Slot State
resource "aws_dynamodb_table" "slot_state" {
  name         = "${var.project_name}-ParkingSlotState"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "slotId"

  attribute {
    name = "slotId"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.enable_pitr
  }
}

# DynamoDB Table 2: Parking Events History
resource "aws_dynamodb_table" "parking_events" {
  name         = "${var.project_name}-ParkingEvents"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "slotId"
  range_key    = "eventKey"

  attribute {
    name = "slotId"
    type = "S"
  }

  attribute {
    name = "eventKey"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.enable_pitr
  }
}
