[CmdletBinding()]
param(
    [ValidatePattern("^[A-Za-z_][A-Za-z0-9_]*$")]
    [string]$DatabaseName = "netpulse_lab",

    [ValidateRange(1, 100)]
    [int]$MetricLimit = 5
)

$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repositoryRoot

try {
    docker compose --profile lab ps

    $readiness = Invoke-RestMethod `
        -Uri "http://localhost:8000/health/ready" `
        -Method Get

    Write-Host ""
    Write-Host "Readiness: $($readiness.status)"
    Write-Host "Database health: $($readiness.database)"

    $databaseUser = (
        docker compose --profile lab exec -T postgres `
            printenv POSTGRES_USER
    ).Trim()

    if (-not $databaseUser) {
        throw "POSTGRES_USER is not available in the container."
    }

    Write-Host ""
    Write-Host "===== DEVICES ====="

    docker compose --profile lab exec -T postgres `
        psql `
        -U $databaseUser `
        -d $DatabaseName `
        -P pager=off `
        -c @"
SELECT
    id,
    name,
    ip_address,
    status,
    updated_at
FROM devices
ORDER BY id;
"@

    if ($LASTEXITCODE -ne 0) {
        throw "The device query failed."
    }

    Write-Host ""
    Write-Host "===== RECENT METRICS PER DEVICE ====="

    docker compose --profile lab exec -T postgres `
        psql `
        -U $databaseUser `
        -d $DatabaseName `
        -P pager=off `
        -c @"
WITH ranked_metrics AS (
    SELECT
        device_id,
        id,
        status,
        response_time_ms,
        packet_loss_percent,
        jitter_ms,
        checked_at,
        ROW_NUMBER() OVER (
            PARTITION BY device_id
            ORDER BY checked_at DESC, id DESC
        ) AS row_number
    FROM device_metrics
)
SELECT
    device_id,
    id,
    status,
    response_time_ms,
    packet_loss_percent,
    jitter_ms,
    checked_at
FROM ranked_metrics
WHERE row_number <= $MetricLimit
ORDER BY device_id, checked_at DESC, id DESC;
"@

    if ($LASTEXITCODE -ne 0) {
        throw "The metric query failed."
    }

    Write-Host ""
    Write-Host "===== RECENT SNMP SNAPSHOTS PER DEVICE ====="

    docker compose --profile lab exec -T postgres `
        psql `
        -U $databaseUser `
        -d $DatabaseName `
        -P pager=off `
        -c @"
WITH ranked_snapshots AS (
    SELECT
        device_id,
        id,
        sysdescr,
        sysuptime,
        syscontact,
        sysname,
        syslocation,
        collected_at,
        ROW_NUMBER() OVER (
            PARTITION BY device_id
            ORDER BY collected_at DESC, id DESC
        ) AS row_number
    FROM device_snmp_system_snapshots
)
SELECT
    device_id,
    id,
    sysdescr,
    sysuptime,
    syscontact,
    sysname,
    syslocation,
    collected_at
FROM ranked_snapshots
WHERE row_number <= $MetricLimit
ORDER BY device_id, collected_at DESC, id DESC;
"@

    if ($LASTEXITCODE -ne 0) {
        throw "The SNMP snapshot query failed."
    }

    Write-Host ""
    Write-Host "===== ACTIVE ALERTS ====="

    docker compose --profile lab exec -T postgres `
        psql `
        -U $databaseUser `
        -d $DatabaseName `
        -P pager=off `
        -c @"
SELECT
    id,
    device_id,
    alert_type,
    severity,
    status,
    occurrence_count,
    message
FROM alerts
WHERE status IN ('OPEN', 'ACKNOWLEDGED')
ORDER BY device_id, id;
"@

    if ($LASTEXITCODE -ne 0) {
        throw "The alert query failed."
    }
}
finally {
    Pop-Location
}