# Git Safe - PowerShell Wrapper
# =============================
# Safe git operations with pre-commit checks
#
# Usage:
#   .\git-safe.ps1 add .
#   .\git-safe.ps1 commit -m "message"  
#   .\git-safe.ps1 push

param(
    [Parameter(Mandatory=$true)]
    [string]$Command,
    
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Error "❌ Not in a git repository"
    exit 1
}

# Check if pre_commit_check.py exists
if (-not (Test-Path "pre_commit_check.py")) {
    Write-Error "❌ pre_commit_check.py not found in current directory"
    exit 1
}

# Commands that should trigger pre-commit checks
$checkCommands = @('add', 'commit', 'push')

if ($Command -in $checkCommands) {
    Write-Host "🛡️  Running pre-commit safety checks..." -ForegroundColor Cyan
    
    # Special handling for 'add .' - offer to fix issues automatically
    $fixMode = ($Command -eq 'add') -and ('.' -in $Arguments)
    
    $checkArgs = @()
    if ($fixMode) {
        $checkArgs += '--fix'
    }
    
    # Run pre-commit checks
    & python pre_commit_check.py @checkArgs
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host "✅ Pre-commit checks passed - proceeding with git operation" -ForegroundColor Green
    }
    elseif ($exitCode -eq 1) {
        Write-Host "`n⚠️  Warnings found." -ForegroundColor Yellow
        $response = Read-Host "Continue anyway? (y/N)"
        if ($response -notmatch "^[Yy]([Ee][Ss])?$") {
            Write-Host "🛑 Operation cancelled" -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "`n❌ Critical issues found. Aborting git operation." -ForegroundColor Red
        Write-Host "Run 'python pre_commit_check.py --fix' to auto-fix issues" -ForegroundColor Yellow
        exit 1
    }
}

# Execute the git command
$gitArgs = @($Command) + $Arguments
$cmdString = "git " + ($gitArgs -join " ")
Write-Host "🔧 Executing: $cmdString" -ForegroundColor Blue

try {
    & git @gitArgs
    exit $LASTEXITCODE
}
catch {
    Write-Error "❌ Error executing git command: $_"
    exit 1
}
