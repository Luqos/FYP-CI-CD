provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = "AWS-Academy-Learner-Lab"
      ManagedBy   = "Terraform"
    }
  }
}

data "aws_caller_identity" "current" {}
