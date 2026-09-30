#!/usr/bin/env pwsh
# Run lint and typecheck on the frontend. Same command CI uses.

$ErrorActionPreference = "Stop"

$frontendRoot = Resolve-Path (Join-Path $PSScriptRoot ".." | Join-Path -ChildPath "apps" | Join-Path -ChildPath "desktop")
Push-Location $frontendRoot
try {
    npm run lint
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}