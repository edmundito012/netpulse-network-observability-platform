from pydantic import BaseModel


class VideoCallExperienceResponse(BaseModel):
    video_call_score: int

    quality: str

    zoom_ready: bool

    teams_ready: bool

    meet_ready: bool

    discord_ready: bool

    audio_drop_risk: str

    video_freeze_risk: str

    recommendation: str