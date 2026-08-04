# PowerShell Find AWS Academy LabRole Script
$ErrorActionPreference = "SilentlyContinue"

$roleArn = aws iam get-role --role-name LabRole --query "Role.Arn" --output text
if (-not $roleArn -or $roleArn -eq "None") {
    $roleArn = aws iam get-role --role-name VocLabs --query "Role.Arn" --output text
}

if ($roleArn -and $roleArn -ne "None") {
    Write-Output $roleArn
} else {
    Write-Error "ERROR: Unable to detect 'LabRole' or 'VocLabs' IAM role."
    exit 1
}
