#!/usr/bin/env pwsh
# Run pytest on the Python backend and the CI workflow tests.
# Same command CI uses.

$ErrorActionPreference = "Stop"

$python = & conda run -n mindflip python -c "import sys; print(sys.executable)" 2>$null |
    Select-Object -Last 1
if (-not $python) {
    Write-Error "conda environment 'mindflip' is not available."
    exit 1
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$backendRoot = Resolve-Path (Join-Path $PSScriptRoot ".." | Join-Path -ChildPath "apps" | Join-Path -ChildPath "backend")
Push-Location $backendRoot
try {
    & $python -m pytest tests -q
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Pop-Location
    Push-Location $backendRoot
    & $python -m pytest (Join-Path $repoRoot "tests/ci") -q
}
finally {
    Pop-Location
}