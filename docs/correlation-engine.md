# NetPulse Correlation Engine

## Overview

The NetPulse Correlation Engine converts isolated network alerts into
explainable operational decisions.

For each source alert, the engine determines whether to:

- attach the alert to an existing active incident;
- create a new incident;
- take no operational action.

Every decision is persisted with its score, threshold, reasons, candidate
count, signal family, application status and timestamps.

## Architecture

```text
Alert
  |
  v
Signal classification
  |
  v
Active incident candidate search
  |
  v
Deterministic correlation scoring
  |
  v
Correlation decision
  |
  +--> MATCHED_EXISTING
  |
  +--> CREATE_NEW
  |
  +--> NO_ACTION
  |
  v
Incident application
  |
  v
Persisted correlation history
```

## Deterministic scoring

Correlation decisions use weighted operational signals:

- same device;
- temporal proximity;
- compatible signal family;
- severity alignment;
- availability of an active incident;
- recent incident detection.

```env
CORRELATION_WINDOW_SECONDS=900
CORRELATION_THRESHOLD=0.65
CORRELATION_MAX_CANDIDATES=25
```

## Background worker

The worker processes eligible open and acknowledged alerts in bounded batches.

```env
CORRELATION_WORKER_ENABLED=false
CORRELATION_WORKER_INTERVAL_SECONDS=30
CORRELATION_WORKER_BATCH_SIZE=25
```

The worker excludes alerts that:

- already have a persisted correlation;
- are resolved;
- are already attached to an incident.

## Idempotency and concurrency

Deterministic correlation keys provide persistence idempotency.

A PostgreSQL advisory lock prevents multiple backend instances from
processing a correlation batch simultaneously.

## Prometheus metrics

Metrics are exposed through `/metrics`.

```text
netpulse_correlation_worker_runs_total
netpulse_correlation_worker_duration_seconds
netpulse_correlation_worker_pending_alerts
netpulse_correlation_worker_processed_alerts_total
netpulse_correlation_evaluations_total
netpulse_correlation_applications_total
netpulse_correlation_failures_total
netpulse_correlation_incidents_created_total
netpulse_correlation_existing_incidents_matched_total
netpulse_correlation_no_action_total
```

## API endpoints

### Correlation operations

```text
GET  /incident-correlations
GET  /incident-correlations/{correlation_id}
POST /incident-correlations/evaluate/{alert_id}
POST /incident-correlations/apply/{alert_id}
```

### Analytics

```text
GET /analytics/correlations
```

Supported query parameters:

```text
window_hours
recent_limit
```

The response includes totals, application success rate, incident reuse,
average score, distributions and recent decisions.

## Portfolio dashboard

Dashboard:

```text
/portfolio/correlations
```

JSON source:

```text
/portfolio/correlations/data
```

![Correlation Intelligence dashboard](screenshots/correlation-intelligence-dashboard.png)

## Testing

```powershell
docker compose exec `
  -e TEST_DATABASE_URL=postgresql+psycopg2://admin:admin@postgres:5432/netpulse_test `
  -e DATABASE_URL=postgresql+psycopg2://admin:admin@postgres:5432/netpulse_test `
  -e CORRELATION_WORKER_ENABLED=false `
  backend python -m pytest
```

Current verified result:

```text
354 passed
```
