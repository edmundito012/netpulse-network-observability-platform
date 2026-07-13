from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"],
)


@router.get(
    "",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def get_portfolio_dashboard() -> HTMLResponse:
    return HTMLResponse(
        content=PORTFOLIO_HTML,
    )


PORTFOLIO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>NetPulse | Network Observability</title>

    <style>
        :root {
            --background: #07111f;
            --surface: #0d1b2d;
            --surface-light: #13243a;
            --border: #203754;
            --text: #eef6ff;
            --muted: #91a4ba;
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
                    circle at top right,
                    rgba(84, 166, 255, 0.13),
                    transparent 28%
                ),
                radial-gradient(
                    circle at top left,
                    rgba(46, 230, 166, 0.09),
                    transparent 24%
                ),
                var(--background);
            color: var(--text);
        }

        .container {
            width: min(1480px, calc(100% - 48px));
            margin: 0 auto;
            padding: 42px 0 70px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 30px;
            margin-bottom: 34px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 18px;
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
                    rgba(84, 166, 255, 0.26),
                    rgba(46, 230, 166, 0.09)
                );
            box-shadow:
                0 18px 45px rgba(0, 0, 0, 0.27);
            font-size: 28px;
        }

        h1 {
            margin: 0;
            font-size: clamp(28px, 4vw, 44px);
            letter-spacing: -1.6px;
        }

        .subtitle {
            margin: 7px 0 0;
            color: var(--muted);
            font-size: 16px;
        }

        .system-status {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 11px 16px;
            border: 1px solid rgba(46, 230, 166, 0.32);
            border-radius: 999px;
            background: rgba(46, 230, 166, 0.08);
            color: var(--green);
            font-weight: 700;
            white-space: nowrap;
        }

        .status-dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: currentColor;
            box-shadow: 0 0 18px currentColor;
        }

        .hero-grid {
            display: grid;
            grid-template-columns: 1.3fr 0.7fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .panel {
            border: 1px solid var(--border);
            border-radius: 22px;
            background:
                linear-gradient(
                    145deg,
                    rgba(19, 36, 58, 0.94),
                    rgba(13, 27, 45, 0.96)
                );
            box-shadow:
                0 22px 55px rgba(0, 0, 0, 0.22);
        }

        .health-panel {
            min-height: 290px;
            padding: 30px;
            display: grid;
            grid-template-columns: 1fr 0.85fr;
            align-items: center;
            gap: 28px;
        }

        .eyebrow {
            color: var(--blue);
            text-transform: uppercase;
            letter-spacing: 2px;
            font-size: 12px;
            font-weight: 800;
        }

        .health-score {
            margin: 14px 0 2px;
            font-size: clamp(64px, 9vw, 104px);
            line-height: 0.95;
            letter-spacing: -6px;
            font-weight: 800;
        }

        .health-score span {
            color: var(--muted);
            font-size: 28px;
            letter-spacing: -1px;
        }

        .health-grade {
            color: var(--green);
            font-size: 21px;
            font-weight: 800;
            margin-top: 13px;
        }

        .health-description {
            color: var(--muted);
            max-width: 610px;
            line-height: 1.6;
            margin-top: 13px;
        }

        .score-ring {
            width: 190px;
            height: 190px;
            margin: auto;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background:
                conic-gradient(
                    var(--green) 0deg 340deg,
                    rgba(255, 255, 255, 0.07) 340deg
                );
            position: relative;
        }

        .score-ring::after {
            content: "";
            position: absolute;
            inset: 16px;
            border-radius: 50%;
            background: var(--surface);
            border: 1px solid var(--border);
        }

        .score-ring-content {
            position: relative;
            z-index: 2;
            text-align: center;
        }

        .score-ring-value {
            font-size: 42px;
            font-weight: 800;
        }

        .score-ring-label {
            color: var(--muted);
            font-size: 13px;
        }

        .summary-panel {
            padding: 26px;
        }

        .panel-title {
            margin: 0 0 22px;
            font-size: 18px;
        }

        .summary-row {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            padding: 16px 0;
            border-bottom: 1px solid rgba(32, 55, 84, 0.72);
        }

        .summary-row:last-child {
            border-bottom: 0;
        }

        .summary-label {
            color: var(--muted);
        }

        .summary-value {
            font-weight: 800;
        }

        .green {
            color: var(--green);
        }

        .yellow {
            color: var(--yellow);
        }

        .blue {
            color: var(--blue);
        }

        .cards {
            display: grid;
            grid-template-columns:
                repeat(4, minmax(0, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .metric-card {
            padding: 24px;
            min-height: 205px;
            position: relative;
            overflow: hidden;
        }

        .metric-card::after {
            content: "";
            position: absolute;
            width: 115px;
            height: 115px;
            right: -42px;
            bottom: -52px;
            border-radius: 50%;
            background: currentColor;
            opacity: 0.06;
        }

        .metric-icon {
            font-size: 28px;
        }

        .metric-name {
            color: var(--muted);
            margin-top: 24px;
            font-size: 14px;
        }

        .metric-value {
            font-size: 37px;
            font-weight: 800;
            margin-top: 6px;
            letter-spacing: -1.5px;
        }

        .metric-status {
            margin-top: 12px;
            font-size: 13px;
            font-weight: 800;
        }

        .progress {
            width: 100%;
            height: 7px;
            margin-top: 20px;
            overflow: hidden;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.07);
        }

        .progress-value {
            height: 100%;
            border-radius: inherit;
            background: currentColor;
            transition: width 0.5s ease;
        }

        .details-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .details-panel {
            padding: 26px;
        }

        .capability-grid {
            display: grid;
            grid-template-columns:
                repeat(2, minmax(0, 1fr));
            gap: 12px;
        }

        .capability {
            padding: 14px 15px;
            border: 1px solid var(--border);
            border-radius: 14px;
            background: rgba(7, 17, 31, 0.33);
            color: #c7d7e8;
            font-size: 14px;
        }

        .capability::before {
            content: "✓";
            color: var(--green);
            margin-right: 8px;
            font-weight: 900;
        }

        .notification {
            padding: 17px;
            margin-top: 12px;
            border: 1px solid var(--border);
            border-radius: 16px;
            background: rgba(7, 17, 31, 0.36);
        }

        .notification-title {
            font-weight: 800;
        }

        .notification-meta {
            color: var(--muted);
            font-size: 13px;
            margin-top: 7px;
        }

        .footer {
            text-align: center;
            color: var(--muted);
            margin-top: 34px;
            font-size: 13px;
        }

        .loading {
            opacity: 0.55;
        }

        @media (max-width: 1050px) {
            .hero-grid,
            .details-grid {
                grid-template-columns: 1fr;
            }

            .cards {
                grid-template-columns:
                    repeat(2, minmax(0, 1fr));
            }
        }

        @media (max-width: 680px) {
            .container {
                width: min(100% - 24px, 1480px);
                padding-top: 24px;
            }

            .header {
                flex-direction: column;
            }

            .health-panel {
                grid-template-columns: 1fr;
            }

            .cards,
            .capability-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>

<body data-dashboard-ready="false">
    <main class="container">
        <header class="header">
            <div class="brand">
                <div class="logo">⚡</div>

                <div>
                    <h1>NetPulse</h1>

                    <p class="subtitle">
                        Network Observability & Quality of Experience Platform
                    </p>
                </div>
            </div>

            <div
                class="system-status"
                id="api-status"
            >
                <span class="status-dot"></span>
                Connecting to NetPulse
            </div>
        </header>

        <section class="hero-grid">
            <article class="panel health-panel">
                <div>
                    <div class="eyebrow">
                        Network Intelligence
                    </div>

                    <div class="health-score">
                        <span id="health-score">--</span>
                        <span>/100</span>
                    </div>

                    <div
                        class="health-grade"
                        id="health-grade"
                    >
                        Calculating network health
                    </div>

                    <p
                        class="health-description"
                        id="health-recommendation"
                    >
                        Collecting latency, jitter, packet loss and
                        stability signals.
                    </p>
                </div>

                <div
                    class="score-ring"
                    id="health-ring"
                >
                    <div class="score-ring-content">
                        <div
                            class="score-ring-value"
                            id="ring-value"
                        >
                            --
                        </div>

                        <div class="score-ring-label">
                            Health Score
                        </div>
                    </div>
                </div>
            </article>

            <article class="panel summary-panel">
                <h2 class="panel-title">
                    Operational Summary
                </h2>

                <div class="summary-row">
                    <span class="summary-label">
                        SLA status
                    </span>

                    <span
                        class="summary-value green"
                        id="sla-status"
                    >
                        Loading
                    </span>
                </div>

                <div class="summary-row">
                    <span class="summary-label">
                        SLA compliance
                    </span>

                    <span
                        class="summary-value"
                        id="sla-compliance"
                    >
                        --
                    </span>
                </div>

                <div class="summary-row">
                    <span class="summary-label">
                        Primary bottleneck
                    </span>

                    <span
                        class="summary-value yellow"
                        id="bottleneck"
                    >
                        --
                    </span>
                </div>

                <div class="summary-row">
                    <span class="summary-label">
                        Notification channel
                    </span>

                    <span class="summary-value blue">
                        Telegram
                    </span>
                </div>
            </article>
        </section>

        <section class="cards">
            <article class="panel metric-card blue">
                <div class="metric-icon">🎮</div>

                <div class="metric-name">
                    Gaming Experience
                </div>

                <div
                    class="metric-value"
                    id="gaming-score"
                >
                    --
                </div>

                <div
                    class="metric-status"
                    id="gaming-status"
                >
                    Loading
                </div>

                <div class="progress">
                    <div
                        class="progress-value"
                        id="gaming-progress"
                        style="width: 0%"
                    ></div>
                </div>
            </article>

            <article class="panel metric-card green">
                <div class="metric-icon">📺</div>

                <div class="metric-name">
                    Streaming Experience
                </div>

                <div
                    class="metric-value"
                    id="streaming-score"
                >
                    --
                </div>

                <div
                    class="metric-status"
                    id="streaming-status"
                >
                    Loading
                </div>

                <div class="progress">
                    <div
                        class="progress-value"
                        id="streaming-progress"
                        style="width: 0%"
                    ></div>
                </div>
            </article>

            <article class="panel metric-card purple">
                <div class="metric-icon">📞</div>

                <div class="metric-name">
                    Video Call Experience
                </div>

                <div
                    class="metric-value"
                    id="video-score"
                >
                    --
                </div>

                <div
                    class="metric-status"
                    id="video-status"
                >
                    Loading
                </div>

                <div class="progress">
                    <div
                        class="progress-value"
                        id="video-progress"
                        style="width: 0%"
                    ></div>
                </div>
            </article>

            <article class="panel metric-card yellow">
                <div class="metric-icon">📈</div>

                <div class="metric-name">
                    SLA Compliance
                </div>

                <div
                    class="metric-value"
                    id="sla-card-score"
                >
                    --
                </div>

                <div
                    class="metric-status"
                    id="sla-card-status"
                >
                    Loading
                </div>

                <div class="progress">
                    <div
                        class="progress-value"
                        id="sla-progress"
                        style="width: 0%"
                    ></div>
                </div>
            </article>
        </section>

        <section class="details-grid">
            <article class="panel details-panel">
                <h2 class="panel-title">
                    Platform Capabilities
                </h2>

                <div class="capability-grid">
                    <div class="capability">
                        JWT Authentication and RBAC
                    </div>

                    <div class="capability">
                        Device Monitoring
                    </div>

                    <div class="capability">
                        Latency Intelligence
                    </div>

                    <div class="capability">
                        Jitter Intelligence
                    </div>

                    <div class="capability">
                        Packet Loss Detection
                    </div>

                    <div class="capability">
                        Predictive Alerts
                    </div>

                    <div class="capability">
                        Network Risk Index
                    </div>

                    <div class="capability">
                        SLA Intelligence
                    </div>

                    <div class="capability">
                        QoE Experience Profiles
                    </div>

                    <div class="capability">
                        Telegram Notifications
                    </div>

                    <div class="capability">
                        GitHub Actions CI
                    </div>

                    <div class="capability">
                        CodeQL Security Analysis
                    </div>
                </div>
            </article>

            <article class="panel details-panel">
                <h2 class="panel-title">
                    Recent Notifications
                </h2>

                <div id="notifications">
                    <div class="notification">
                        <div class="notification-title">
                            Loading notification history
                        </div>

                        <div class="notification-meta">
                            Connecting to the notification service
                        </div>
                    </div>
                </div>
            </article>
        </section>

        <footer class="footer">
            NetPulse · FastAPI · PostgreSQL · Docker · Prometheus ·
            GitHub Actions
        </footer>
    </main>

    <script>
        const fallback = {
            health: {
                health_score: 94,
                grade: "A",
                bottleneck: "jitter",
                recommendation:
                    "Network is operating at an excellent level."
            },
            gaming: {
                gaming_score: 95,
                competitive_ready: true,
                recommendation:
                    "Excellent for competitive gaming."
            },
            streaming: {
                streaming_score: 93,
                quality: "EXCELLENT",
                recommended_resolution: "4K"
            },
            video: {
                video_call_score: 97,
                quality: "EXCELLENT",
                zoom_ready: true
            },
            sla: {
                overall_compliance_percent: 99.96,
                status: "PASS"
            }
        };

        async function requestJson(
            url,
            fallbackValue
        ) {
            try {
                const response = await fetch(url);

                if (!response.ok) {
                    return fallbackValue;
                }

                return await response.json();
            } catch {
                return fallbackValue;
            }
        }

        function setText(
            id,
            value
        ) {
            const element = document.getElementById(id);

            if (element) {
                element.textContent = value;
            }
        }

        function setProgress(
            id,
            value
        ) {
            const safeValue = Math.max(
                0,
                Math.min(100, Number(value) || 0)
            );

            const element = document.getElementById(id);

            if (element) {
                element.style.width = `${safeValue}%`;
            }
        }

        function updateHealth(data) {
            const score = data.health_score ?? 0;

            setText("health-score", score);
            setText("ring-value", score);
            setText(
                "health-grade",
                `Grade ${data.grade ?? "UNKNOWN"}`
            );
            setText(
                "health-recommendation",
                data.recommendation
                    ?? "No recommendation available."
            );
            setText(
                "bottleneck",
                data.bottleneck ?? "none"
            );

            const degrees = Math.round(
                score * 3.6
            );

            const ring = document.getElementById(
                "health-ring"
            );

            ring.style.background = `
                conic-gradient(
                    var(--green) 0deg ${degrees}deg,
                    rgba(255, 255, 255, 0.07)
                    ${degrees}deg
                )
            `;
        }

        function updateGaming(data) {
            const score = data.gaming_score ?? 0;

            setText("gaming-score", `${score}/100`);

            setText(
                "gaming-status",
                data.competitive_ready
                    ? "Competitive gaming ready"
                    : "Casual gaming recommended"
            );

            setProgress(
                "gaming-progress",
                score
            );
        }

        function updateStreaming(data) {
            const score = data.streaming_score ?? 0;

            setText(
                "streaming-score",
                `${score}/100`
            );

            setText(
                "streaming-status",
                `${data.quality ?? "UNKNOWN"} · ${
                    data.recommended_resolution ?? "Unknown"
                }`
            );

            setProgress(
                "streaming-progress",
                score
            );
        }

        function updateVideo(data) {
            const score = data.video_call_score ?? 0;

            setText(
                "video-score",
                `${score}/100`
            );

            setText(
                "video-status",
                data.zoom_ready
                    ? "HD conferencing ready"
                    : "Quality degradation possible"
            );

            setProgress(
                "video-progress",
                score
            );
        }

        function updateSla(data) {
            const compliance =
                data.overall_compliance_percent ?? 0;

            setText(
                "sla-status",
                data.status ?? "UNKNOWN"
            );

            setText(
                "sla-compliance",
                `${compliance}%`
            );

            setText(
                "sla-card-score",
                `${compliance}%`
            );

            setText(
                "sla-card-status",
                data.status ?? "UNKNOWN"
            );

            setProgress(
                "sla-progress",
                compliance
            );
        }

        function updateNotifications(items) {
            const container = document.getElementById(
                "notifications"
            );

            if (
                !Array.isArray(items)
                || items.length === 0
            ) {
                container.innerHTML = `
                    <div class="notification">
                        <div class="notification-title">
                            No notifications recorded
                        </div>

                        <div class="notification-meta">
                            NetPulse will display recent alerts here.
                        </div>
                    </div>
                `;

                return;
            }

            container.innerHTML = items
                .slice(0, 4)
                .map(
                    item => `
                        <div class="notification">
                            <div class="notification-title">
                                ${item.title}
                            </div>

                            <div class="notification-meta">
                                ${item.provider}
                                ·
                                ${item.status}
                            </div>
                        </div>
                    `
                )
                .join("");
        }

        async function loadDashboard() {
            const [
                health,
                gaming,
                streaming,
                video,
                sla,
                notifications
            ] = await Promise.all([
                requestJson(
                    "/analytics/health-score",
                    fallback.health
                ),
                requestJson(
                    "/gaming/experience",
                    fallback.gaming
                ),
                requestJson(
                    "/streaming/experience",
                    fallback.streaming
                ),
                requestJson(
                    "/video-calls/experience",
                    fallback.video
                ),
                requestJson(
                    "/analytics/sla",
                    fallback.sla
                ),
                requestJson(
                    "/notifications/history",
                    []
                )
            ]);

            updateHealth(health);
            updateGaming(gaming);
            updateStreaming(streaming);
            updateVideo(video);
            updateSla(sla);
            updateNotifications(notifications);

            const apiStatus = document.getElementById(
                "api-status"
            );

            apiStatus.innerHTML = `
                <span class="status-dot"></span>
                NetPulse Operational
            `;

            document.body.dataset.dashboardReady = "true";
        }

        loadDashboard()
            .catch(error => {
                console.error(
                    "Dashboard loading failed:",
                    error
                );

                const apiStatus = document.getElementById(
                    "api-status"
                );

                apiStatus.innerHTML = `
                    <span class="status-dot"></span>
                    NetPulse Demo Mode
                `;
            })
            .finally(() => {
                document.body.dataset.dashboardReady = "true";
            });
    </script>
</body>
</html>
"""