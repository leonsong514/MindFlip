#!/usr/bin/env pwsh
# Run Ruff lint and format-check on the Python backend.
# This script honours the project's pyproject.toml configuration and
# is the same command contributors run locally. CI reuses it.

$ErrorActionPreference = "Stop"

$python = & conda run -n mindflip python -c "import sys; print(sys.executable)" 2>$null |
    Select-Object -Last 1
if (-not $python) {
    Write-Error "conda environment 'mindflip' is not available."
    exit 1
}

$backendRoot = Resolve-Path (Join-Path $PSScriptRoot ".." | Join-Path -ChildPath "apps" | Join-Path -ChildPath "backend")
Push-Location $backendRoot
try {
    & $python -m ruff check .
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python -m ruff format --check .
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}