"""
Pydantic schemas for Podcast Generation API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PodcastStatus(str, Enum):
    PENDING = "pending"
    GENERATING_SCRIPT = "generating_script"
    GENERATING_AUDIO = "generating_audio"
    COMPLETED = "completed"
    FAILED = "failed"


class VoiceSettings(BaseModel):
    voice_id: Optional[str] = "default"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)
    emotion: Optional[str] = "neutral"  # neutral, happy, sad, excited, etc.


class PodcastSettings(BaseModel):
    duration_minutes: int = Field(default=10, ge=1, le=60)
    voice_settings: VoiceSettings = VoiceSettings()
    include_intro: bool = True
    include_outro: bool = True
    background_music: bool = False
    format: str = "conversational"  # conversational, interview, narrative
    language: str = "en"


class PodcastGenerationRequest(BaseModel):
    title: str
    topic: str
    knowledge_query: Optional[str] = None
    content_ids: Optional[List[str]] = None
    settings: Optional[PodcastSettings] = None


class PodcastGenerationResponse(BaseModel):
    podcast_id: str
    status: PodcastStatus
    message: str
    estimated_duration: Optional[int] = None


class PodcastScript(BaseModel):
    podcast_id: str
    content: str
    segments: List[Dict[str, Any]]  # Each segment has speaker, text, timing, etc.
    word_count: int
    estimated_duration: float
    created_at: datetime
    updated_at: Optional[datetime] = None


class PodcastItem(BaseModel):
    id: str
    podcast_id: str
    user_id: str
    title: str
    topic: str
    status: PodcastStatus
    audio_file_path: Optional[str] = None
    script_content: Optional[str] = None
    duration_seconds: Optional[int] = None
    file_size_bytes: Optional[int] = None
    settings: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class PodcastListResponse(BaseModel):
    podcasts: List[PodcastItem]
    total_count: int
    skip: int
    limit: int


class ScriptSegment(BaseModel):
    segment_id: str
    speaker: str  # host, guest, narrator
    text: str
    start_time: float
    end_time: float
    voice_settings: Optional[VoiceSettings] = None
    metadata: Dict[str, Any] = {}


class AudioGenerationRequest(BaseModel):
    script_segments: List[ScriptSegment]
    global_settings: PodcastSettings
    output_format: str = "mp3"


class AudioGenerationResponse(BaseModel):
    audio_file_path: str
    duration_seconds: float
    file_size_bytes: int
    format: str


class PodcastShare(BaseModel):
    share_token: str
    podcast_id: str
    public: bool
    expires_at: Optional[datetime] = None
    created_at: datetime


class ScriptPreviewRequest(BaseModel):
    topic: str
    knowledge_query: str
    content_ids: Optional[List[str]] = None
    settings: Optional[PodcastSettings] = None


class ScriptPreviewResponse(BaseModel):
    script_preview: str
    estimated_duration: float
    word_count: int
    segments_count: int
    topics_covered: List[str]


class PodcastAnalytics(BaseModel):
    podcast_id: str
    play_count: int
    download_count: int
    share_count: int
    average_listen_duration: float
    completion_rate: float
    listener_feedback: Dict[str, Any]
    geographic_data: Dict[str, int]
    device_data: Dict[str, int]


class RegenerationRequest(BaseModel):
    regenerate_script: bool = False
    regenerate_audio: bool = True
    new_settings: Optional[PodcastSettings] = None
    script_modifications: Optional[str] = None
