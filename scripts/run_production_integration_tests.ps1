# scripts/run_production_integration_tests.ps1
# Helper script to set up and run production-ready live integration tests.

# Exit on error
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  BengalBound HUB - Production Integration Test Runner    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Load from .env if it exists
if (Test-Path ".env") {
    Write-Host "Loading environment variables from .env file..." -ForegroundColor Gray
    Get-Content .env | Where-Object { $_ -and -not $_.StartsWith("#") } | ForEach-Object {
        $parts = $_.Split('=', 2)
        if ($parts.Count -eq 2) {
            $name = $parts[0].Trim()
            $value = $parts[1].Trim()
            if ($name -and $value) {
                [System.Environment]::SetEnvironmentVariable($name, $value)
                Write-Host "  Loaded $name" -ForegroundColor Gray
            }
        }
    }
}

# 1. Check/Prompt for LITELLM_MASTER_KEY
if (-not $env:LITELLM_MASTER_KEY) {
    Write-Host "LITELLM_MASTER_KEY is not set in the environment." -ForegroundColor Yellow
    $keyInput = Read-Host "Please enter your LITELLM_MASTER_KEY (or press Enter to skip live LLM tests)"
    if ($keyInput) {
        $env:LITELLM_MASTER_KEY = $keyInput.Trim()
    }
}

# 2. Check/Prompt for LITELLM_BASE_URL
if ($env:LITELLM_MASTER_KEY -and -not $env:LITELLM_BASE_URL) {
    $urlInput = Read-Host "Please enter LITELLM_BASE_URL [Default: http://localhost:4000]"
    if ($urlInput) {
        $env:LITELLM_BASE_URL = $urlInput.Trim()
    } else {
        $env:LITELLM_BASE_URL = "http://localhost:4000"
    }
}

# 3. Check/Prompt for CLOUDRUN_URL
if (-not $env:CLOUDRUN_URL) {
    Write-Host "CLOUDRUN_URL is not set." -ForegroundColor Yellow
    $urlInput = Read-Host "Please enter the target CLOUDRUN_URL [Default: https://bengal-bound-hub-u5i67kezxa-vp.a.run.app]"
    if ($urlInput) {
        $env:CLOUDRUN_URL = $urlInput.Trim()
    }
}

# Set flag to run Cloud Run Playwright tests
$env:RUN_CLOUDRUN_TESTS = "true"

Write-Host ""
Write-Host "Installing Playwright chromium browser binaries..." -ForegroundColor Cyan
& .venv\Scripts\playwright install chromium

Write-Host ""
Write-Host "Running production integration tests..." -ForegroundColor Cyan
Write-Host "Executing: pytest tests/serea/test_serea.py::TestSereaBrainLive tests/test_cloudrun_full_flow.py -v" -ForegroundColor Gray
Write-Host ""

& .venv\Scripts\pytest tests/serea/test_serea.py::TestSereaBrainLive tests/test_cloudrun_full_flow.py -v
