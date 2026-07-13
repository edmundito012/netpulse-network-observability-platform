"""Packet loss burst analytics API."""

from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.packet_loss_burst import (
    PacketLossBurstRead,
    PacketLossBurstResponse,
)
from app.services.packet_loss_burst_application_service import (
    PacketLossBurstApplicationService,
)


router = APIRouter(
    prefix="/analytics",
    tags=["Network Analytics"],
)


@router.get(
    "/packet-loss-bursts",
    response_model=PacketLossBurstResponse,
    summary="Detect sustained packet loss bursts",
)
def get_packet_loss_bursts(
    device_id: int | None = Query(
        default=None,
        ge=1,
        description=(
            "Device whose packet loss history will be analyzed. "
            "When omitted, the latest measured device is used."
        ),
    ),
    start_at: datetime | None = Query(
        default=None,
        description="Inclusive UTC start of the analysis window.",
    ),
    end_at: datetime | None = Query(
        default=None,
        description="Inclusive UTC end of the analysis window.",
    ),
    limit: int = Query(
        default=100,
        ge=2,
        le=10_000,
    ),
    warning_threshold_percent: float = Query(
        default=5.0,
        ge=0,
        le=100,
    ),
    critical_threshold_percent: float = Query(
        default=20.0,
        ge=0,
        le=100,
    ),
    minimum_consecutive_samples: int = Query(
        default=3,
        ge=2,
        le=100,
    ),
    maximum_gap_seconds: int = Query(
        default=120,
        ge=1,
        le=86_400,
    ),
    db: Session = Depends(get_db),
) -> PacketLossBurstResponse:
    """Analyze sustained packet loss using real historical samples."""

    try:
        result = (
            PacketLossBurstApplicationService
            .analyze(
                db=db,
                device_id=device_id,
                start_at=start_at,
                end_at=end_at,
                limit=limit,
                warning_threshold_percent=(
                    warning_threshold_percent
                ),
                critical_threshold_percent=(
                    critical_threshold_percent
                ),
                minimum_consecutive_samples=(
                    minimum_consecutive_samples
                ),
                maximum_gap_seconds=maximum_gap_seconds,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    analysis = result.analysis

    return PacketLossBurstResponse(
        device_id=result.device_id,
        start_at=(
            result.series.start_at
            if result.series is not None
            else start_at
        ),
        end_at=(
            result.series.end_at
            if result.series is not None
            else end_at
        ),
        burst_detected=analysis.burst_detected,
        current_burst_active=(
            analysis.current_burst_active
        ),
        severity=analysis.severity,
        samples_analyzed=analysis.samples_analyzed,
        measured_samples=analysis.measured_samples,
        missing_samples=analysis.missing_samples,
        burst_count=analysis.burst_count,
        longest_burst_samples=(
            analysis.longest_burst_samples
        ),
        peak_packet_loss_percent=(
            analysis.peak_packet_loss_percent
        ),
        average_packet_loss_percent=(
            analysis.average_packet_loss_percent
        ),
        warning_threshold_percent=(
            analysis.warning_threshold_percent
        ),
        critical_threshold_percent=(
            analysis.critical_threshold_percent
        ),
        minimum_consecutive_samples=(
            analysis.minimum_consecutive_samples
        ),
        maximum_gap_seconds=(
            analysis.maximum_gap_seconds
        ),
        bursts=[
            PacketLossBurstRead(
                start_at=burst.start_at,
                end_at=burst.end_at,
                duration_seconds=(
                    burst.duration_seconds
                ),
                sample_count=burst.sample_count,
                average_packet_loss_percent=(
                    burst.average_packet_loss_percent
                ),
                peak_packet_loss_percent=(
                    burst.peak_packet_loss_percent
                ),
                severity=burst.severity,
                status=burst.status,
            )
            for burst in analysis.bursts
        ],
    )