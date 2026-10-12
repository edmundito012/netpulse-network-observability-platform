[CmdletBinding()]
param(
    [ValidatePattern("^[A-Za-z_][A-Za-z0-9_]*$")]
    [string]$DatabaseName = "netpulse_lab",

    [ValidateRange(10, 600)]
    [int]$HealthTimeoutSeconds = 120,

    [switch]$NoBuild
)

$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repositoryRoot

try {
    if (-not (Test-Path ".env")) {
        throw "Missing .env. Copy .env.example to .env and configure it first."
    }

    docker version | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not available."
    }

    docker compose --profile lab config --quiet

    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose configuration is invalid."
    }

    $resolvedCompose = docker compose --profile lab config | Out-String

    if ($resolvedCompose -notmatch "/$([regex]::Escape($DatabaseName))(?:\s|$)") {
        throw (
            "DATABASE_URL does not target $DatabaseName. " +
            "Update DATABASE_URL in .env before starting the laboratory."
        )
    }

    Write-Host "Starting PostgreSQL..."
    docker compose --profile lab up -d postgres

    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL could not be started."
    }

    $deadline = (Get-Date).AddSeconds($HealthTimeoutSeconds)

    do {
        Start-Sleep -Seconds 2

        $postgresHealth = docker inspect `
            --format="{{.State.Health.Status}}" `
            netpulse-postgres `
            2>$null
    } until (
        $postgresHealth -eq "healthy" `
        -or (Get-Date) -ge $deadline
    )

    if ($postgresHealth -ne "healthy") {
        throw "PostgreSQL did not become healthy before the timeout."
    }

    $databaseUser = (
        docker compose --profile lab exec -T postgres `
            printenv POSTGRES_USER
    ).Trim()

    if (-not $databaseUser) {
        throw "POSTGRES_USER is not available in the container."
    }

    $databaseExistsOutput = docker compose --profile lab exec -T postgres `
        psql `
        -U $databaseUser `
        -d postgres `
        -tA `
        -c "SELECT 1 FROM pg_database WHERE datname = '$DatabaseName';"

    $databaseExists = (
        $databaseExistsOutput |
            Out-String
    ).Trim()

    if ($databaseExists -ne "1") {
        Write-Host "Creating database $DatabaseName..."

        docker compose --profile lab exec -T postgres `
            psql `
            -U $databaseUser `
            -d postgres `
            -v ON_ERROR_STOP=1 `
            -c "CREATE DATABASE `"$DatabaseName`";"

        if ($LASTEXITCODE -ne 0) {
            throw "Database $DatabaseName could not be created."
        }
    }


    Write-Host "Starting SNMP simulator..."

    if ($NoBuild) {
        docker compose --profile lab up -d snmp-simulator
    }
    else {
        docker compose --profile lab up -d --build snmp-simulator
    }

    if ($LASTEXITCODE -ne 0) {
        throw "The SNMP simulator could not be started."
    }

    $deadline = (Get-Date).AddSeconds($HealthTimeoutSeconds)

    do {
        Start-Sleep -Seconds 3

        $snmpHealth = docker inspect `
            --format="{{.State.Health.Status}}" `
            netpulse-snmp-simulator `
            2>$null

        Write-Host "SNMP simulator: $snmpHealth"
    } until (
        $snmpHealth -eq "healthy" `
        -or (Get-Date) -ge $deadline
    )

    if ($snmpHealth -ne "healthy") {
        throw "The SNMP simulator did not become healthy before the timeout."
    }

    Write-Host "Starting NetPulse backend..."

    if ($NoBuild) {
        docker compose --profile lab up -d backend
    }
    else {
        docker compose --profile lab up -d --build backend
    }

    if ($LASTEXITCODE -ne 0) {
        throw "The backend could not be started."
    }

    $deadline = (Get-Date).AddSeconds($HealthTimeoutSeconds)

    do {
        Start-Sleep -Seconds 3

        $backendHealth = docker inspect `
            --format="{{.State.Health.Status}}" `
            netpulse-backend `
            2>$null

        Write-Host "Backend: $backendHealth"
    } until (
        $backendHealth -eq "healthy" `
        -or (Get-Date) -ge $deadline
    )

    if ($backendHealth -ne "healthy") {
        throw "The backend did not become healthy before the timeout."
    }

    $readiness = Invoke-RestMethod `
        -Uri "http://localhost:8000/health/ready" `
        -Method Get

    Write-Host ""
    Write-Host "NetPulse laboratory is ready."
    Write-Host "Database: $DatabaseName"
    Write-Host "Health: $($readiness.status)"
    Write-Host "Swagger: http://localhost:8000/docs"
    Write-Host "Dashboard: http://localhost:8000/portfolio"
}
finally {
    Pop-Location
}