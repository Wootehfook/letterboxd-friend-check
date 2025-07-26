# Quick Git Commit Script for Letterboxd Friend Check
# 
# Usage:
#   .\commit.ps1          # Safe automatic commit
#   .\commit.ps1 -Check   # Preview mode
#   .\commit.ps1 -Ask     # Interactive mode

param(
    [switch]$Check,
    [switch]$Ask,
    [string]$Message = ""
)

Write-Host "🚀 Quick Commit - Letterboxd Friend Check" -ForegroundColor Green
Write-Host "=========================================="

$pythonArgs = @("smart_git_automation.py")

if ($Check) {
    $pythonArgs += "--dry-run", "--interactive"
    Write-Host "🔍 Running in preview mode..." -ForegroundColor Yellow
}
elseif ($Ask) {
    $pythonArgs += "--interactive"
    Write-Host "❓ Running in interactive mode..." -ForegroundColor Cyan
}
else {
    Write-Host "⚡ Running automatic mode..." -ForegroundColor Green
}

# Run the Python automation script
python @pythonArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Success!" -ForegroundColor Green
}
else {
    Write-Host "`n❌ Failed!" -ForegroundColor Red
}
