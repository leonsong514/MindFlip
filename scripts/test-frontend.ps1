#!/usr/bin/env pwsh
# Run format-check and tests on the frontend. Same command CI uses.

$ErrorActionPreference = "Stop"

$frontendRoot = Resolve-Path (Join-Path $PSScriptRoot ".." | Join-Path -ChildPath "apps" | Join-Path -ChildPath "desktop")
Push-Location $frontendRoot
try {
    npm run format:check
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    npm run test
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}