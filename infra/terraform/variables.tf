variable "project_name" {
  description = "Name of the project used for naming resources"
  type        = string
  default     = "smart-parking-fyp"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "lab_role_arn" {
  description = "Existing AWS Academy LabRole or VocLabs role ARN used by Lambda functions"
  type        = string
}

variable "enable_pitr" {
  description = "Enable Point-in-Time Recovery on DynamoDB tables (set to false for AWS Academy compatible limits)"
  type        = bool
  default     = false
}
