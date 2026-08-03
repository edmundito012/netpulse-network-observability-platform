"""Public Correlation Engine portfolio dashboard."""

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.correlation_analytics import (
    CorrelationAnalyticsSummary,
)
from app.services.correlation_analytics_service import (
    CorrelationAnalyticsService,
)


router = APIRouter(
    prefix="/portfolio/correlations",
    tags=["Portfolio"],
)


@router.get(
    "",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def get_correlation_portfolio() -> HTMLResponse:
    """Render the public Correlation Engine dashboard."""

    return HTMLResponse(
        content=CORRELATION_PORTFOLIO_HTML,
    )


@router.get(
    "/data",
    response_model=CorrelationAnalyticsSummary,
    include_in_schema=False,
)
def get_correlation_portfolio_data(
    window_hours: int = Query(
        default=24,
        ge=1,
        le=720,
    ),
    recent_limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
) -> CorrelationAnalyticsSummary:
    """Return real data for the public correlation dashboard."""

    return (
        CorrelationAnalyticsService
        .get_summary(
            db=db,
            window_hours=window_hours,
            recent_limit=recent_limit,
        )
    )


CORRELATION_PORTFOLIO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>NetPulse | Correlation Intelligence</title>

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
                    circle at 10% 0%,
                    rgba(84, 166, 255, 0.15),
                    transparent 30%
                ),
                radial-gradient(
                    circle at 90% 8%,
                    rgba(167, 139, 250, 0.13),
                    transparent 28%
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
            border: 1px solid rgba(167, 139, 250, 0.45);
            border-radius: 18px;
            background:
                linear-gradient(
                    145deg,
                    rgba(84, 166, 255, 0.22),
                    rgba(167, 139, 250, 0.18)
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

        .status {
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

        .panel {
            border: 1px solid var(--border);
            border-radius: 22px;
            background:
                linear-gradient(
                    145deg,
                    rgba(19, 37, 61, 0.95),
                    rgba(13, 27, 45, 0.98)
                );
            box-shadow:
                0 22px 55px rgba(0, 0, 0, 0.22);
        }

        .hero {
            display: grid;
            grid-template-columns: 1.45fr 0.55fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .overview {
            padding: 30px;
        }

        .eyebrow {
            color: var(--purple);
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
            max-width: 820px;
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
            color: var(--purple);
            font-weight: 900;
        }

        .score-panel {
            padding: 27px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .score-value {
            margin-top: 8px;
            font-size: 72px;
            line-height: 1;
            letter-spacing: -5px;
            font-weight: 900;
            color: var(--purple);
        }

        .score-label {
            margin-top: 9px;
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
            min-height: 160px;
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

        .purple {
            color: var(--purple);
        }

        .yellow {
            color: var(--yellow);
        }

        .red {
            color: var(--red);
        }

        .analytics-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .distribution-panel {
            padding: 26px;
        }

        .panel-title {
            margin: 0 0 20px;
            font-size: 19px;
        }

        .distribution-row {
            margin-bottom: 18px;
        }

        .distribution-header {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 8px;
        }

        .distribution-name {
            font-weight: 800;
        }

        .distribution-count {
            color: var(--muted);
        }

        .bar-track {
            height: 10px;
            overflow: hidden;
            border-radius: 999px;
            background: rgba(6, 16, 29, 0.72);
        }

        .bar-value {
            width: 0;
            height: 100%;
            border-radius: inherit;
            background:
                linear-gradient(
                    90deg,
                    var(--blue),
                    var(--purple)
                );
            transition: width 500ms ease;
        }

        .table-panel {
            padding: 26px;
        }

        .table-wrapper {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            padding: 0 12px 13px;
            color: var(--muted);
            text-align: left;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 11px;
        }

        td {
            padding: 16px 12px;
            border-top: 1px solid rgba(32, 57, 87, 0.72);
            vertical-align: middle;
        }

        .correlation-id {
            color: var(--purple);
            font-weight: 900;
            white-space: nowrap;
        }

        .badge {
            display: inline-flex;
            padding: 6px 9px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 900;
        }

        .badge-create {
            color: var(--blue);
            background: rgba(84, 166, 255, 0.12);
        }

        .badge-match {
            color: var(--green);
            background: rgba(46, 230, 166, 0.12);
        }

        .badge-none {
            color: var(--yellow);
            background: rgba(245, 196, 81, 0.12);
        }

        .badge-failed {
            color: var(--red);
            background: rgba(255, 107, 122, 0.12);
        }

        .badge-applied {
            color: var(--green);
            background: rgba(46, 230, 166, 0.12);
        }

        .badge-evaluated {
            color: var(--yellow);
            background: rgba(245, 196, 81, 0.12);
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
            .analytics-grid {
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
        }
    </style>
</head>

<body data-dashboard-ready="false">
    <main class="container">
        <header class="header">
            <div class="brand">
                <div class="logo">🧠</div>

                <div>
                    <h1>Correlation Intelligence</h1>

                    <p class="subtitle">
                        Explainable alert grouping and automated
                        incident decision analytics
                    </p>
                </div>
            </div>

            <div
                class="status"
                id="system-status"
            >
                <span class="status-dot"></span>
                Loading correlation engine
            </div>
        </header>

        <section class="hero">
            <article class="panel overview">
                <div class="eyebrow">
                    NetPulse Correlation Engine
                </div>

                <h2 class="overview-title">
                    From isolated alerts to explainable incidents
                </h2>

                <p class="overview-copy">
                    NetPulse evaluates alert context, temporal proximity,
                    signal compatibility, severity and active incident
                    evidence to determine whether an alert should create
                    a new incident, join an existing one or require no
                    action.
                </p>

                <div class="pipeline">
                    <span class="pipeline-step">
                        Alert Signal
                    </span>

                    <span class="pipeline-arrow">→</span>

                    <span class="pipeline-step">
                        Candidate Search
                    </span>

                    <span class="pipeline-arrow">→</span>

                    <span class="pipeline-step">
                        Explainable Scoring
                    </span>

                    <span class="pipeline-arrow">→</span>

                    <span class="pipeline-step">
                        Incident Decision
                    </span>
                </div>
            </article>

            <article class="panel score-panel">
                <div class="eyebrow">
                    Average Score
                </div>

                <div
                    class="score-value"
                    id="average-score"
                >
                    --
                </div>

                <div class="score-label">
                    Mean confidence across evaluated alerts
                </div>
            </article>
        </section>

        <section class="cards">
            <article class="panel metric-card blue">
                <div class="metric-label">
                    Total Evaluations
                </div>

                <div
                    class="metric-value"
                    id="total-evaluations"
                >
                    --
                </div>

                <div class="metric-description">
                    Correlation decisions in the selected window
                </div>
            </article>

            <article class="panel metric-card green">
                <div class="metric-label">
                    Application Success
                </div>

                <div
                    class="metric-value"
                    id="success-rate"
                >
                    --
                </div>

                <div class="metric-description">
                    Successfully applied correlation decisions
                </div>
            </article>

            <article class="panel metric-card purple">
                <div class="metric-label">
                    Incident Reuse
                </div>

                <div
                    class="metric-value"
                    id="reuse-rate"
                >
                    --
                </div>

                <div class="metric-description">
                    Alerts matched to existing incidents
                </div>
            </article>

            <article class="panel metric-card yellow">
                <div class="metric-label">
                    Incidents Avoided
                </div>

                <div
                    class="metric-value"
                    id="incidents-avoided"
                >
                    --
                </div>

                <div class="metric-description">
                    Estimated duplicate incidents prevented
                </div>
            </article>
        </section>

        <section class="analytics-grid">
            <article class="panel distribution-panel">
                <h2 class="panel-title">
                    Decision Outcomes
                </h2>

                <div id="outcome-distribution">
                    <div class="empty-state">
                        Loading outcome distribution
                    </div>
                </div>
            </article>

            <article class="panel distribution-panel">
                <h2 class="panel-title">
                    Signal Families
                </h2>

                <div id="family-distribution">
                    <div class="empty-state">
                        Loading signal family distribution
                    </div>
                </div>
            </article>
        </section>

        <section class="panel table-panel">
            <h2 class="panel-title">
                Recent Correlation Decisions
            </h2>

            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Correlation</th>
                            <th>Alert</th>
                            <th>Incident</th>
                            <th>Outcome</th>
                            <th>Status</th>
                            <th>Family</th>
                            <th>Score</th>
                            <th>Evaluated</th>
                        </tr>
                    </thead>

                    <tbody id="recent-table">
                        <tr>
                            <td
                                colspan="8"
                                class="empty-state"
                            >
                                Loading recent correlations
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>

        <footer class="footer">
            NetPulse Network Observability Platform ·
            Explainable Correlation Intelligence
        </footer>
    </main>

    <script>
        const DATA_URL = (
            "/portfolio/correlations/data"
            + "?window_hours=168"
            + "&recent_limit=20"
        );

        function escapeHtml(value) {
            return String(value)
                .replaceAll("&", "&amp;")
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;")
                .replaceAll('"', "&quot;")
                .replaceAll("'", "&#039;");
        }

        function formatScore(value) {
            if (
                value === null
                || value === undefined
            ) {
                return "--";
            }

            return Number(value).toFixed(2);
        }

        function formatDate(value) {
            if (!value) {
                return "--";
            }

            return new Intl.DateTimeFormat(
                undefined,
                {
                    dateStyle: "medium",
                    timeStyle: "short",
                },
            ).format(
                new Date(value),
            );
        }

        function outcomeBadge(outcome) {
            const classes = {
                CREATE_NEW: "badge-create",
                MATCHED_EXISTING: "badge-match",
                NO_ACTION: "badge-none",
            };

            const badgeClass = (
                classes[outcome]
                || "badge-none"
            );

            return (
                `<span class="badge ${badgeClass}">`
                + `${escapeHtml(outcome)}`
                + "</span>"
            );
        }

        function statusBadge(status) {
            const classes = {
                APPLIED: "badge-applied",
                FAILED: "badge-failed",
                EVALUATED: "badge-evaluated",
            };

            const badgeClass = (
                classes[status]
                || "badge-evaluated"
            );

            return (
                `<span class="badge ${badgeClass}">`
                + `${escapeHtml(status)}`
                + "</span>"
            );
        }

        function renderDistribution(
            containerId,
            items,
        ) {
            const container = document.getElementById(
                containerId,
            );

            if (!items || items.length === 0) {
                container.innerHTML = (
                    '<div class="empty-state">'
                    + "No data in this time window"
                    + "</div>"
                );

                return;
            }

            const maximum = Math.max(
                ...items.map(
                    item => Number(item.count),
                ),
                1,
            );

            container.innerHTML = items.map(
                item => {
                    const percentage = (
                        Number(item.count)
                        / maximum
                    ) * 100;

                    return `
                        <div class="distribution-row">
                            <div class="distribution-header">
                                <span class="distribution-name">
                                    ${escapeHtml(item.name)}
                                </span>

                                <span class="distribution-count">
                                    ${Number(item.count)}
                                </span>
                            </div>

                            <div class="bar-track">
                                <div
                                    class="bar-value"
                                    style="width: ${percentage}%"
                                ></div>
                            </div>
                        </div>
                    `;
                },
            ).join("");
        }

        function renderRecent(items) {
            const table = document.getElementById(
                "recent-table",
            );

            if (!items || items.length === 0) {
                table.innerHTML = `
                    <tr>
                        <td
                            colspan="8"
                            class="empty-state"
                        >
                            No correlations in this time window
                        </td>
                    </tr>
                `;

                return;
            }

            table.innerHTML = items.map(
                item => `
                    <tr>
                        <td class="correlation-id">
                            COR-${String(
                                item.correlation_id,
                            ).padStart(6, "0")}
                        </td>

                        <td>
                            #${Number(item.source_alert_id)}
                        </td>

                        <td>
                            ${
                                item.target_incident_id
                                ? `#${Number(
                                    item.target_incident_id,
                                )}`
                                : "--"
                            }
                        </td>

                        <td>
                            ${outcomeBadge(item.outcome)}
                        </td>

                        <td>
                            ${
                                statusBadge(
                                    item.application_status,
                                )
                            }
                        </td>

                        <td>
                            ${escapeHtml(item.signal_family)}
                        </td>

                        <td>
                            ${formatScore(item.score)}
                        </td>

                        <td>
                            ${formatDate(item.evaluated_at)}
                        </td>
                    </tr>
                `,
            ).join("");
        }

        async function loadDashboard() {
            const status = document.getElementById(
                "system-status",
            );

            try {
                const response = await fetch(
                    DATA_URL,
                    {
                        cache: "no-store",
                    },
                );

                if (!response.ok) {
                    throw new Error(
                        `HTTP ${response.status}`,
                    );
                }

                const data = await response.json();

                document.getElementById(
                    "average-score",
                ).textContent = formatScore(
                    data.average_score,
                );

                document.getElementById(
                    "total-evaluations",
                ).textContent = Number(
                    data.total_evaluations,
                );

                document.getElementById(
                    "success-rate",
                ).textContent = (
                    `${Number(
                        data.application_success_rate,
                    ).toFixed(1)}%`
                );

                document.getElementById(
                    "reuse-rate",
                ).textContent = (
                    `${Number(
                        data.incident_reuse_rate,
                    ).toFixed(1)}%`
                );

                document.getElementById(
                    "incidents-avoided",
                ).textContent = Number(
                    data.estimated_incidents_avoided,
                );

                renderDistribution(
                    "outcome-distribution",
                    data.outcomes,
                );

                renderDistribution(
                    "family-distribution",
                    data.signal_families,
                );

                renderRecent(
                    data.recent_correlations,
                );

                status.innerHTML = (
                    '<span class="status-dot"></span>'
                    + "Correlation engine operational"
                );

                document.body.dataset.dashboardReady = (
                    "true"
                );

            } catch (error) {
                console.error(
                    "Correlation dashboard error:",
                    error,
                );

                status.innerHTML = (
                    '<span class="status-dot"></span>'
                    + "Correlation data unavailable"
                );

                status.style.color = "var(--red)";
                status.style.borderColor = (
                    "rgba(255, 107, 122, 0.34)"
                );

                status.style.background = (
                    "rgba(255, 107, 122, 0.08)"
                );
            }
        }

        loadDashboard();

        window.setInterval(
            loadDashboard,
            30000,
        );
    </script>
</body>
</html>
"""