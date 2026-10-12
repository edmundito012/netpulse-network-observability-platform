# NetPulse Real-Device Laboratory

This guide describes how to run NetPulse as a reproducible local network
observability laboratory using Docker Compose and authorized real devices.

## Laboratory topology

The basic laboratory contains:

- a Windows computer running Docker Desktop;
- a domestic router;
- one or more Wi-Fi or Ethernet devices;
- the NetPulse backend;
- a dedicated PostgreSQL laboratory database.

All monitored devices must be reachable from the computer running NetPulse.

## Safety boundaries

Only monitor devices and networks that you own or are authorized to test.
Do not expose the router administration interface, PostgreSQL, Swagger, or
the development API to the public internet. Never commit `.env` files,
passwords, secret keys, public IP addresses, or device MAC addresses.

## Requirements

- Windows PowerShell 5.1 or PowerShell 7
- Docker Desktop with Docker Compose
- Git
- a configured `.env` file
- devices connected to the same local network
- DHCP reservations or otherwise stable private IP addresses

Verify the local tooling:

```powershell
docker version
docker compose version
docker compose config --services
```

The expected services are `postgres` and `backend`.

## Environment configuration

Create `.env` from `.env.example` when necessary. Configure a dedicated
database, for example `netpulse_lab`. The database name selected through
`-DatabaseName` must match the final database name in `DATABASE_URL`.

Do not reuse the test database for persistent real-device measurements.

## Start the laboratory

From the repository root:

```powershell
.\scripts\lab-start.ps1
```

Skip the backend image rebuild when it is already current:

```powershell
.\scripts\lab-start.ps1 -NoBuild
```

The start script validates Docker, Compose, and `DATABASE_URL`; starts
PostgreSQL; creates the selected database when needed; starts the backend;
and waits for its health check.

Useful endpoints:

- Swagger: http://localhost:8000/docs
- Portfolio: http://localhost:8000/portfolio
- Readiness: http://localhost:8000/health/ready

## Prepare real devices

Use the router administration interface to create a DHCP reservation for
each laboratory device. This prevents its private IP address from changing.
Keep every MAC address private.

Reconnect the device after reserving its address and verify reachability:

```powershell
ping.exe -n 4 DEVICE_IP
```

Replace `DEVICE_IP` with the device's reserved private address.

## Register devices

Open Swagger at http://localhost:8000/docs, authenticate with a laboratory
account, and register each authorized device through the device API. Use a
descriptive name, reserved private IP address, device type, and location.

## Inspect status and measurements

```powershell
.\scripts\lab-status.ps1
.\scripts\lab-status.ps1 -MetricLimit 10
```

The report includes service health, backend readiness, registered devices,
recent latency, packet loss, jitter, and active alerts.

To inspect metrics directly:

```powershell
docker compose exec postgres `
    psql -U netpulse -d netpulse_lab -tA `
    -F " | " `
    -c "SELECT id, status, response_time_ms, packet_loss_percent, jitter_ms, checked_at FROM device_metrics WHERE device_id = DEVICE_ID ORDER BY id DESC LIMIT 10;"
```

Replace `DEVICE_ID` with the registered device identifier.

## Validate outage and recovery

NetPulse confirms status transitions over consecutive monitoring cycles to
avoid incidents caused by a single missed response.

1. Confirm that the test device is `ONLINE`.
2. Disconnect only that device from Wi-Fi.
3. Wait for the configured offline confirmation cycles.
4. Verify the `OFFLINE` status and one `DEVICE_OFFLINE` alert.
5. Reconnect the device.
6. Wait for the configured online confirmation cycles.
7. Verify the `ONLINE` status and resolution of the availability alert.
8. Confirm that no alert remains active after full recovery.

Do not disconnect the router or the computer running Docker during the test.
Some mobile devices stop answering while asleep, so keep the test device
awake during controlled validation.

## Inspect alerts and events

```powershell
docker compose exec postgres `
    psql -U netpulse -d netpulse_lab -tA `
    -F " | " `
    -c "SELECT id, device_id, alert_type, severity, status, message FROM alerts WHERE status IN ('OPEN', 'ACKNOWLEDGED') ORDER BY id;"
```

```powershell
docker compose exec postgres `
    psql -U netpulse -d netpulse_lab -tA `
    -F " | " `
    -c "SELECT id, device_id, event_type, message, created_at FROM device_events ORDER BY id DESC LIMIT 20;"
```

## Stop the laboratory

Stop the containers while retaining them:

```powershell
.\scripts\lab-stop.ps1
```

Remove containers and the Compose network while preserving database data:

```powershell
.\scripts\lab-stop.ps1 -RemoveContainers
```

Do not run `docker compose down -v` unless permanent deletion of the
laboratory database is intentional.

## Troubleshooting

Inspect backend logs when it does not become healthy:

```powershell
docker compose logs backend --tail 200
docker compose ps
```

If `DATABASE_URL` does not target the selected database, update `.env` so
its final database name matches `-DatabaseName` and start again.

If a device does not answer ping, confirm that it is powered on, connected
to the same network, using its reserved address, and allowed to answer ICMP.

SNMP is optional for this laboratory. Domestic routers and mobile devices
may not expose it; ping, latency, loss, jitter, availability, and recovery
can still be validated.

## Evidence checklist

A completed run should demonstrate:

- healthy Docker services and backend readiness;
- real router and device reachability;
- persisted latency, loss, and jitter measurements;
- confirmed offline and online transitions;
- deduplicated availability alerts;
- independent packet-loss alert resolution;
- device event history;
- no active alerts after full recovery.
