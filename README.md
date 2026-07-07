# NetPulse Network Observability Platform

<p align="center">
  <h1 align="center">🚀 NetPulse</h1>
  <p align="center">
    Modern Network Observability Platform built with FastAPI, React and PostgreSQL.
  </p>
</p>

## Overview

NetPulse is a modern network observability platform designed to monitor, analyze and visualize network infrastructure in real time.

### Main Features

- 🔐 JWT Authentication & Role Based Access
- 🌐 Device Management
- 📡 SNMP Monitoring
- 📈 Prometheus Metrics
- 📊 Real-time Dashboard
- 🔔 Alert Engine
- 📬 Notifications
- ⚡ WebSockets
- 🐳 Docker Support
- 🔄 GitHub Actions CI
- 🛡️ CodeQL Security Analysis

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

# License

Choose your preferred open-source license (MIT recommended).

---

Made with ❤️ using FastAPI, React and Docker.
