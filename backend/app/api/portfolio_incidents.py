"""Public Incident Operations portfolio dashboard."""

from fastapi import (
    APIRouter,
    Depends,
)
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.incident_portfolio import (
    IncidentPortfolioSummary,
)
from app.services.incident_portfolio_service import (
    IncidentPortfolioService,
)


router = APIRouter(
    prefix="/portfolio/incidents",
    tags=["Portfolio"],
)


@router.get(
    "",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def get_incident_portfolio() -> HTMLResponse:
    """Render the public Incident Operations dashboard."""

    return HTMLResponse(
        content=INCIDENT_PORTFOLIO_HTML,
    )


@router.get(
    "/data",
    response_model=IncidentPortfolioSummary,
    include_in_schema=False,
)
def get_incident_portfolio_data(
    db: Session = Depends(get_db),
) -> IncidentPortfolioSummary:
    """Return real incident data used by the portfolio dashboard."""

    return IncidentPortfolioService.get_summary(
        db=db,
    )


INCIDENT_PORTFOLIO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>NetPulse | Incident Operations</title>

    <style>
        :root {
            --background: #06101d;
            --surface: #0d1b2d;
            --surface-light: #13253d;
            --border: #203957;
            --text: #eff7ff;
            --muted: #91a5bc;
            --green: #2ee6a6;
            --blue: #54a6ff;
            --purple: #a78bfa;
            --yellow: #f5c451;
            --red: #ff6b7a;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            color: var(--text);
            font-family:
                Inter,
                ui-sans-serif,
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
            background:
                radial-gradient(
                    circle at 12% 0%,
                    rgba(84, 166, 255, 0.13),
                    transparent 28%
                ),
                radial-gradient(
                    circle at 88% 10%,
                    rgba(167, 139, 250, 0.11),
                    transparent 26%
                ),
                var(--background);
        }

        .container {
            width: min(1500px, calc(100% - 48px));
            margin: 0 auto;
            padding: 38px 0 64px;
        }

        .header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 28px;
            margin-bottom: 30px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 17px;
        }

        .logo {
            width: 58px;
            height: 58px;
            display: grid;
            place-items: center;
            border: 1px solid rgba(84, 166, 255, 0.45);
            border-radius: 18px;
            background:
                linear-gradient(
                    145deg,
                    rgba(84, 166, 255, 0.25),
                    rgba(167, 139, 250, 0.12)
                );
            font-size: 28px;
            box-shadow:
                0 20px 50px rgba(0, 0, 0, 0.28);
        }

        h1 {
            margin: 0;
            font-size: clamp(30px, 4vw, 46px);
            letter-spacing: -1.8px;
        }

        .subtitle {
            margin: 7px 0 0;
            color: var(--muted);
        }

        .system-status {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 11px 16px;
            border: 1px solid rgba(46, 230, 166, 0.32);
            border-radius: 999px;
            color: var(--green);
            background: rgba(46, 230, 166, 0.08);
            font-weight: 800;
            white-space: nowrap;
        }

        .status-dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: currentColor;
            box-shadow: 0 0 18px currentColor;
        }

        .hero {
            display: grid;
            grid-template-columns: 1.45fr 0.55fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .panel {
            border: 1px solid var(--border);
            border-radius: 22px;
            background:
                linear-gradient(
                    145deg,
                    rgba(19, 37, 61, 0.94),
                    rgba(13, 27, 45, 0.97)
                );
            box-shadow:
                0 22px 55px rgba(0, 0, 0, 0.22);
        }

        .overview {
            padding: 30px;
        }

        .eyebrow {
            color: var(--blue);
            text-transform: uppercase;
            letter-spacing: 2px;
            font-size: 12px;
            font-weight: 900;
        }

        .overview-title {
            margin: 12px 0 9px;
            font-size: clamp(27px, 4vw, 43px);
            letter-spacing: -1.5px;
        }

        .overview-copy {
            max-width: 780px;
            margin: 0;
            color: var(--muted);
            line-height: 1.7;
        }

        .pipeline {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 10px;
            margin-top: 27px;
        }

        .pipeline-step {
            padding: 10px 13px;
            border: 1px solid var(--border);
            border-radius: 12px;
            color: #caddf0;
            background: rgba(6, 16, 29, 0.42);
            font-size: 13px;
            font-weight: 750;
        }

        .pipeline-arrow {
            color: var(--blue);
            font-weight: 900;
        }

        .active-panel {
            padding: 27px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .active-value {
            margin-top: 7px;
            font-size: 76px;
            line-height: 1;
            letter-spacing: -5px;
            font-weight: 900;
            color: var(--red);
        }

        .active-label {
            margin-top: 8px;
            color: var(--muted);
        }

        .cards {
            display: grid;
            grid-template-columns:
                repeat(4, minmax(0, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .metric-card {
            min-height: 157px;
            padding: 23px;
            position: relative;
            overflow: hidden;
        }

        .metric-card::after {
            content: "";
            position: absolute;
            width: 110px;
            height: 110px;
            right: -43px;
            bottom: -51px;
            border-radius: 50%;
            background: currentColor;
            opacity: 0.06;
        }

        .metric-label {
            color: var(--muted);
            font-size: 13px;
        }

        .metric-value {
            margin-top: 13px;
            font-size: 42px;
            letter-spacing: -2px;
            font-weight: 900;
        }

        .metric-description {
            margin-top: 9px;
            color: var(--muted);
            font-size: 13px;
        }

        .blue {
            color: var(--blue);
        }

        .green {
            color: var(--green);
        }

        .yellow {
            color: var(--yellow);
        }

        .red {
            color: var(--red);
        }

        .operations-grid {
            display: grid;
            grid-template-columns: 1.42fr 0.58fr;
            gap: 20px;
        }

        .table-panel,
        .lifecycle-panel {
            padding: 26px;
        }

        .panel-title {
            margin: 0 0 20px;
            font-size: 19px;
        }

        .incident-table {
            width: 100%;
            border-collapse: collapse;
        }

        .incident-table th {
            padding: 0 12px 13px;
            color: var(--muted);
            text-align: left;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 11px;
        }

        .incident-table td {
            padding: 16px 12px;
            border-top: 1px solid rgba(32, 57, 87, 0.72);
            vertical-align: middle;
        }

        .incident-id {
            color: var(--blue);
            font-weight: 900;
            white-space: nowrap;
        }

        .incident-title {
            font-weight: 800;
        }

        .incident-source {
            margin-top: 5px;
            color: var(--muted);
            font-size: 12px;
        }

        .badge {
            display: inline-flex;
            padding: 6px 9px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 900;
        }

        .badge-critical {
            color: var(--red);
            background: rgba(255, 107, 122, 0.12);
        }

        .badge-warning {
            color: var(--yellow);
            background: rgba(245, 196, 81, 0.12);
        }

        .badge-info {
            color: var(--blue);
            background: rgba(84, 166, 255, 0.12);
        }

        .lifecycle-row {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            padding: 15px 0;
            border-bottom: 1px solid rgba(32, 57, 87, 0.72);
        }

        .lifecycle-row:last-child {
            border-bottom: 0;
        }

        .lifecycle-label {
            color: var(--muted);
        }

        .lifecycle-value {
            font-weight: 900;
        }

        .empty-state {
            padding: 28px;
            color: var(--muted);
            text-align: center;
        }

        .footer {
            margin-top: 31px;
            color: var(--muted);
            text-align: center;
            font-size: 13px;
        }

        @media (max-width: 1050px) {
            .hero,
            .operations-grid {
                grid-template-columns: 1fr;
            }

            .cards {
                grid-template-columns:
                    repeat(2, minmax(0, 1fr));
            }
        }

        @media (max-width: 700px) {
            .container {
                width: min(100% - 24px, 1500px);
            }

            .header {
                flex-direction: column;
            }

            .cards {
                grid-template-columns: 1fr;
            }

            .table-wrapper {
                overflow-x: auto;
            }
        }
    </style>
</head>

<body data-dashboard-ready="false">
    <main class="container">
        <header class="header">
            <div class="brand">
                <div class="logo">🚨</div>

                <div>
                    <h1>Incident Operations</h1>

                    <p class="subtitle">
                        Alert correlation, lifecycle management and
                        operational response
                    </p>
                </div>
            </div>

            <div
                class="system-status"
                id="system-status"
            >
                <span class="status-dot"></span>
                Loading incident engine
            </div>
        </header>

        <section class="hero">
            <article class="panel overview">
                <div class="eyebrow">
                    NetPulse Incident Engine
                </div>

                <h2 class="overview-title">
                    From network signal to operational response
                </h2>

                <p class="overview-copy">
                    NetPulse converts sustained packet-loss degradation
                    into deduplicated alerts and traceable incidents.
                    Every incident has a public identifier, lifecycle,
                    severity, priority, ownership and correlated evidence.
                </p>

                <div class="pipeline">
                    <span class="pipeline-step">
                        Device Metric
                    </span>

                    <span class="pipeline-arrow">→</span>

                    <span class="pipeline-step">
                        Burst Detection
                    </span>

                    <span class="pipeline-arrow">→</span>

                    <span class="pipeline-step">
                        Alert Deduplication
                    </span>

                    <span class="pipeline-arrow">→</span>

                    <span class="pipeline-step">
                        Incident Engine
                    </span>
                </div>
            </article>

            <article class="panel active-panel">
                <div class="eyebrow">
                    Active Incidents
                </div>

                <div
                    class="active-value"
                    id="active-incidents"
                >
                    --
                </div>

                <div class="active-label">
                    Requiring operational attention
                </div>
            </article>
        </section>

        <section class="cards">
            <article class="panel metric-card red">
                <div class="metric-label">
                    Critical Incidents
                </div>

                <div
                    class="metric-value"
                    id="critical-incidents"
                >
                    --
                </div>

                <div class="metric-description">
                    Active incidents at critical severity
                </div>
            </article>

            <article class="panel metric-card blue">
                <div class="metric-label">
                    Correlated Alerts
                </div>

                <div
                    class="metric-value"
                    id="correlated-alerts"
                >
                    --
                </div>

                <div class="metric-description">
                    Alert evidence grouped into active incidents
                </div>
            </article>

            <article class="panel metric-card yellow">
                <div class="metric-label">
                    Affected Devices
                </div>

                <div
                    class="metric-value"
                    id="affected-devices"
                >
                    --
                </div>

                <div class="metric-description">
                    Distinct monitored devices under impact
                </div>
            </article>

            <article class="panel metric-card green">
                <div class="metric-label">
                    Mean Resolution Time
                </div>

                <div
                    class="metric-value"
                    id="mean-resolution"
                >
                    --
                </div>

                <div class="metric-description">
                    Average duration of resolved incidents
                </div>
            </article>
        </section>

        <section class="operations-grid">
            <article class="panel table-panel">
                <h2 class="panel-title">
                    Recent Incidents
                </h2>

                <div class="table-wrapper">
                    <table class="incident-table">
                        <thead>
                            <tr>
                                <th>Incident</th>
                                <th>Severity</th>
                                <th>Status</th>
                                <th>Alerts</th>
                                <th>Duration</th>
                            </tr>
                        </thead>

                        <tbody id="incident-table-body">
                            <tr>
                                <td
                                    colspan="5"
                                    class="empty-state"
                                >
                                    Loading operational incidents
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </article>

            <article class="panel lifecycle-panel">
                <h2 class="panel-title">
                    Lifecycle Distribution
                </h2>

                <div class="lifecycle-row">
                    <span class="lifecycle-label">
                        Open
                    </span>

                    <span
                        class="lifecycle-value"
                        id="open-incidents"
                    >
                        --
                    </span>
                </div>

                <div class="lifecycle-row">
                    <span class="lifecycle-label">
                        Acknowledged
                    </span>

                    <span
                        class="lifecycle-value"
                        id="acknowledged-incidents"
                    >
                        --
                    </span>
                </div>

                <div class="lifecycle-row">
                    <span class="lifecycle-label">
                        Investigating
                    </span>

                    <span
                        class="lifecycle-value"
                        id="investigating-incidents"
                    >
                        --
                    </span>
                </div>

                <div class="lifecycle-row">
                    <span class="lifecycle-label">
                        Monitoring
                    </span>

                    <span
                        class="lifecycle-value"
                        id="monitoring-incidents"
                    >
                        --
                    </span>
                </div>

                <div class="lifecycle-row">
                    <span class="lifecycle-label">
                        Resolved
                    </span>

                    <span
                        class="lifecycle-value green"
                        id="resolved-incidents"
                    >
                        --
                    </span>
                </div>

                <div class="lifecycle-row">
                    <span class="lifecycle-label">
                        Total recorded
                    </span>

                    <span
                        class="lifecycle-value"
                        id="total-incidents"
                    >
                        --
                    </span>
                </div>
            </article>
        </section>

        <footer class="footer">
            NetPulse · Incident Engine · Alert Deduplication ·
            Packet Loss Burst Detection · FastAPI · PostgreSQL
        </footer>
    </main>

    <script>
        const fallback = {
            total_incidents: 12,
            active_incidents: 4,
            critical_incidents: 2,
            open_incidents: 1,
            acknowledged_incidents: 1,
            investigating_incidents: 1,
            monitoring_incidents: 1,
            resolved_incidents: 8,
            correlated_alerts: 9,
            affected_devices: 3,
            mean_resolution_seconds: 1320,
            latest_incidents: [
                {
                    public_id: "INC-2026-000012",
                    title: "Packet loss burst affecting WAN Router",
                    status: "INVESTIGATING",
                    severity: "CRITICAL",
                    priority: "CRITICAL",
                    source: "ALERT_ENGINE",
                    alert_count: 3,
                    duration_seconds: 842
                },
                {
                    public_id: "INC-2026-000011",
                    title: "Video-call degradation in Madrid",
                    status: "MONITORING",
                    severity: "WARNING",
                    priority: "HIGH",
                    source: "ALERT_ENGINE",
                    alert_count: 2,
                    duration_seconds: 1210
                }
            ]
        };

        function setText(
            id,
            value
        ) {
            const element = document.getElementById(id);

            if (element) {
                element.textContent = value;
            }
        }

        function escapeHtml(value) {
            const element = document.createElement("div");

            element.textContent = String(value ?? "");

            return element.innerHTML;
        }

        function formatDuration(seconds) {
            const safeSeconds = Math.max(
                0,
                Number(seconds) || 0
            );

            if (safeSeconds < 60) {
                return `${Math.round(safeSeconds)}s`;
            }

            if (safeSeconds < 3600) {
                return `${Math.round(safeSeconds / 60)}m`;
            }

            return `${(
                safeSeconds / 3600
            ).toFixed(1)}h`;
        }

        function severityClass(severity) {
            const normalized = String(
                severity ?? "INFO"
            ).toLowerCase();

            if (normalized === "critical") {
                return "badge-critical";
            }

            if (normalized === "warning") {
                return "badge-warning";
            }

            return "badge-info";
        }

        function updateIncidents(items) {
            const tableBody = document.getElementById(
                "incident-table-body"
            );

            if (
                !Array.isArray(items)
                || items.length === 0
            ) {
                tableBody.innerHTML = `
                    <tr>
                        <td
                            colspan="5"
                            class="empty-state"
                        >
                            No incidents recorded yet
                        </td>
                    </tr>
                `;

                return;
            }

            tableBody.innerHTML = items
                .map(
                    incident => `
                        <tr>
                            <td>
                                <div class="incident-id">
                                    ${escapeHtml(
                                        incident.public_id
                                    )}
                                </div>

                                <div class="incident-title">
                                    ${escapeHtml(
                                        incident.title
                                    )}
                                </div>

                                <div class="incident-source">
                                    ${escapeHtml(
                                        incident.source
                                    )}
                                </div>
                            </td>

                            <td>
                                <span
                                    class="badge ${
                                        severityClass(
                                            incident.severity
                                        )
                                    }"
                                >
                                    ${escapeHtml(
                                        incident.severity
                                    )}
                                </span>
                            </td>

                            <td>
                                ${escapeHtml(
                                    incident.status
                                )}
                            </td>

                            <td>
                                ${Number(
                                    incident.alert_count
                                ) || 0}
                            </td>

                            <td>
                                ${formatDuration(
                                    incident.duration_seconds
                                )}
                            </td>
                        </tr>
                    `
                )
                .join("");
        }

        function updateDashboard(data) {
            setText(
                "active-incidents",
                data.active_incidents ?? 0
            );

            setText(
                "critical-incidents",
                data.critical_incidents ?? 0
            );

            setText(
                "correlated-alerts",
                data.correlated_alerts ?? 0
            );

            setText(
                "affected-devices",
                data.affected_devices ?? 0
            );

            setText(
                "mean-resolution",
                data.mean_resolution_seconds == null
                    ? "N/A"
                    : formatDuration(
                        data.mean_resolution_seconds
                    )
            );

            setText(
                "open-incidents",
                data.open_incidents ?? 0
            );

            setText(
                "acknowledged-incidents",
                data.acknowledged_incidents ?? 0
            );

            setText(
                "investigating-incidents",
                data.investigating_incidents ?? 0
            );

            setText(
                "monitoring-incidents",
                data.monitoring_incidents ?? 0
            );

            setText(
                "resolved-incidents",
                data.resolved_incidents ?? 0
            );

            setText(
                "total-incidents",
                data.total_incidents ?? 0
            );

            updateIncidents(
                data.latest_incidents
            );
        }

        async function loadDashboard() {
            let data = fallback;
            let demoMode = false;

            try {
                const response = await fetch(
                    "/portfolio/incidents/data"
                );

                if (response.ok) {
                    data = await response.json();
                } else {
                    demoMode = true;
                }
            } catch {
                demoMode = true;
            }

            updateDashboard(data);

            const statusElement = (
                document.getElementById(
                    "system-status"
                )
            );

            statusElement.innerHTML = `
                <span class="status-dot"></span>
                ${
                    demoMode
                        ? "NetPulse Demo Mode"
                        : "Incident Engine Operational"
                }
            `;

            document.body.dataset.dashboardReady = "true";
        }

        loadDashboard()
            .catch(error => {
                console.error(
                    "Incident dashboard failed:",
                    error
                );

                updateDashboard(fallback);

                document.body.dataset.dashboardReady = "true";
            });
    </script>
</body>
</html>
"""