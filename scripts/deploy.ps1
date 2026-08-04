# PowerShell Deployment Script for AWS Academy Smart Parking Prototype
$ErrorActionPreference = "Stop"

$rootDir = Split-Path -Parent $PSScriptRoot
$tfDir = Join-Path $rootDir "infra\terraform"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " AWS Academy Smart Parking Prototype Deployment Script  " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# Step 1: Check Identity
& (Join-Path $PSScriptRoot "check_aws_identity.ps1")

# Step 2: Detect Region
$awsRegion = aws configure get region
if (-not $awsRegion) { $awsRegion = "us-east-1" }
Write-Host "Target AWS Region: $awsRegion" -ForegroundColor Green

# Step 3: Detect LabRole / VocLabs
$labRoleArn = & (Join-Path $PSScriptRoot "find_lab_role.ps1")
if (-not $labRoleArn) {
    Write-Host "ERROR: Unable to detect AWS Academy IAM role." -ForegroundColor Red
    exit 1
}
Write-Host "Using IAM Execution Role: $labRoleArn" -ForegroundColor Green

# Step 4: Package Lambdas
& (Join-Path $PSScriptRoot "package_lambdas.ps1")

# Step 5-7: Terraform Apply
Write-Host "=== Running Terraform Infrastructure Deployment ===" -ForegroundColor Cyan
terraform -chdir="$tfDir" init
terraform -chdir="$tfDir" plan -var="lab_role_arn=$labRoleArn" -var="aws_region=$awsRegion"
terraform -chdir="$tfDir" apply -var="lab_role_arn=$labRoleArn" -var="aws_region=$awsRegion" -auto-approve

# Step 8-9: Generate frontend config
& (Join-Path $PSScriptRoot "generate_frontend_config.ps1")

$dashboardBucket = terraform -chdir="$tfDir" output -raw dashboard_bucket_name
$dashboardUrl = terraform -chdir="$tfDir" output -raw dashboard_url
$apiUrl = terraform -chdir="$tfDir" output -raw api_gateway_url

# Step 10: Upload Dashboard files to S3
Write-Host "=== Uploading Frontend Dashboard to S3 Bucket ($dashboardBucket) ===" -ForegroundColor Cyan
aws s3 cp (Join-Path $rootDir "frontend\index.html") "s3://$dashboardBucket/index.html"
aws s3 cp (Join-Path $rootDir "frontend\style.css") "s3://$dashboardBucket/style.css"
aws s3 cp (Join-Path $rootDir "frontend\app.js") "s3://$dashboardBucket/app.js"
aws s3 cp (Join-Path $rootDir "frontend\config.js") "s3://$dashboardBucket/config.js"

# Step 11-12: Summary
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Deployment Complete!                                   " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " S3 Dashboard URL:" -ForegroundColor Yellow
Write-Host "   $dashboardUrl" -ForegroundColor Yellow
Write-Host ""
Write-Host " API Gateway URL:" -ForegroundColor Yellow
Write-Host "   $apiUrl" -ForegroundColor Yellow
Write-Host ""
Write-Host " Sample Test Command:" -ForegroundColor Yellow
Write-Host "   .\scripts\publish_sample_aws_cli.ps1 A01 14.2" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
