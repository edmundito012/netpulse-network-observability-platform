# NetPulse Network Observability Platform

<p align="center">
  <h1 align="center">ðŸš€ NetPulse</h1>
  <p align="center">
    Modern Network Observability Platform built with FastAPI, React and PostgreSQL.
  </p>
</p>

## Overview

NetPulse is a modern network observability platform designed to monitor, analyze and visualize network infrastructure in real time.

### Main Features

- ðŸ” JWT Authentication & Role Based Access
- ðŸŒ Device Management
- ðŸ“¡ SNMP Monitoring
- ðŸ“ˆ Prometheus Metrics
- ðŸ“Š Real-time Dashboard
- ðŸ”” Alert Engine
- ðŸ“¬ Notifications
- âš¡ WebSockets
- ðŸ³ Docker Support
- ðŸ”„ GitHub Actions CI
- ðŸ›¡ï¸ CodeQL Security Analysis

---

# Architecture

```mermaid
flowchart TD

User[User]

Frontend[React Frontend]

Backend[FastAPI Backend]

DB[(PostgreSQL)]

SNMP[SNMP Collector]

Prom[Prometheus]

Devices[(Network Devices)]

User --> Frontend
Frontend --> Backend
Backend --> DB
Backend --> SNMP
Backend --> Prom
SNMP --> Devices
```

---

# Tech Stack

## Backend

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Pydantic
- Uvicorn

## Frontend

- React
- TypeScript

## DevOps

- Docker
- Docker Compose
- GitHub Actions
- GitHub Container Registry
- Dependabot
- CodeQL

---

# Project Structure

```text
backend/
frontend/
docs/
infra/
scripts/
.github/
```

---

# Quick Start

## Docker

```bash
git clone https://github.com/edmundito012/netpulse-network-observability-platform.git

cd netpulse-network-observability-platform

docker compose up --build
```

Backend:

http://localhost:8000

API Docs:

http://localhost:8000/docs

ReDoc:

http://localhost:8000/redoc

---

# Development

Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend

```bash
cd frontend
npm install
npm run dev
```

---

# GitHub Automation

This repository includes:

- Backend CI
- Docker Image publishing to GHCR
- CodeQL
- Dependabot
- Pull Request Template
- Issue Templates
- Branch Protection Rules

---

# Roadmap

- Device Discovery
- SNMPv3
- Alert Escalation
- Email Notifications
- Microsoft Teams Integration
- Custom Dashboards
- Helm Chart
- Kubernetes Deployment
- Grafana Integration
- OpenTelemetry

---

# Contributing

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Open a Pull Request.

---

# Security

Please report vulnerabilities privately.

See `SECURITY.md` for details.

---
# Screenshots

![Swagger](docs/screenshots/swagger.png)

![ReDoc](docs/screenshots/redoc.png)

## Project Status

<!-- NETPULSE:AUTO:START -->

Generated automatically from tests, commits, and screenshots.

_Last automation run: 2026-08-03 14:19 UTC_

### ✅ Automated Quality

- **Tests:** 354 passed
- **Warnings:** 1
- **CI:** GitHub Actions
- **Security:** CodeQL
- **Workflow:** Feature branch → Pull Request → CI → Merge

### 🧠 Recent Engineering Milestones

- ✨ **portfolio** — add correlation intelligence dashboard
- 📝 **portfolio** — update automated evidence [skip readme-sync]
- ✨ **correlation** — add correlation analytics API
- 📝 **portfolio** — update automated evidence [skip readme-sync]
- ✨ **correlation** — add PostgreSQL advisory worker lock
- 📝 **portfolio** — update automated evidence [skip readme-sync]
- 🐛 **correlation** — add worker metrics and idempotent selection
- 📝 **portfolio** — update automated evidence [skip readme-sync]
- ✨ **correlation** — add background correlation worker

### 📸 Automated Screenshots

#### Incident Operations Dashboard

![Incident Operations Dashboard](docs/screenshots/incident-operations-dashboard.png)

#### Portfolio Dashboard

![Portfolio Dashboard](docs/screenshots/portfolio-dashboard.png)

#### Redoc Api

![Redoc Api](docs/screenshots/redoc-api.png)

#### Redoc

![Redoc](docs/screenshots/redoc.png)

#### Swagger Api

![Swagger Api](docs/screenshots/swagger-api.png)

#### Swagger

![Swagger](docs/screenshots/swagger.png)

<!-- NETPULSE:AUTO:END -->
# License

Choose your preferred open-source license (MIT recommended).

---

Made with â¤ï¸ using FastAPI, React and Docker.

<!-- correlation-intelligence:start -->
## Correlation Intelligence

NetPulse includes an explainable Correlation Engine that groups related
network alerts into operational incidents using deterministic scoring,
idempotent persistence and PostgreSQL concurrency protection.

Highlights:

- deterministic correlation scoring;
- existing-incident matching;
- automatic incident creation;
- background batch processing;
- PostgreSQL advisory locking;
- Prometheus metrics;
- correlation analytics API;
- public correlation intelligence dashboard.

Dashboard:

```text
http://localhost:8000/portfolio/correlations
```

Technical documentation:

```text
docs/correlation-engine.md
```

![Correlation Intelligence dashboard](docs/screenshots/correlation-intelligence-dashboard.png)
<!-- correlation-intelligence:end -->
