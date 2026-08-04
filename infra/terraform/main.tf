# Main Terraform Manifest for AWS Academy Smart Parking Prototype

locals {
  common_tags = {
    Project     = var.project_name
    Environment = "AWS-Academy"
    ManagedBy   = "Terraform"
  }
}
