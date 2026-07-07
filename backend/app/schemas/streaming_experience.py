from pydantic import BaseModel


class StreamingExperienceResponse(BaseModel):
    streaming_score: int

    quality: str

    recommended_resolution: str

    buffering_risk: str

    live_stream_ready: bool

    recommended_platforms: list[str]

    recommendation: str