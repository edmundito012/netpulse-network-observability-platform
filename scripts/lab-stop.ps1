[CmdletBinding()]
param(
    [switch]$RemoveContainers
)

$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repositoryRoot

try {
    if ($RemoveContainers) {
        docker compose down
    }
    else {
        docker compose stop
    }

    if ($LASTEXITCODE -ne 0) {
        throw "The laboratory could not be stopped."
    }

    Write-Host ""
    Write-Host "NetPulse laboratory stopped."
    Write-Host "PostgreSQL data volume was preserved."
}
finally {
    Pop-Location
}