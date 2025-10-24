"""
Pydantic schemas for Knowledge Base API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    TEXT = "text"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"
    URL = "url"
    YOUTUBE = "youtube"


class ProcessingStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ContentIngestRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ContentIngestResponse(BaseModel):
    content_id: str
    status: ProcessingStatusEnum
    message: str


class SearchResult(BaseModel):
    id: str
    content: str
    source: Dict[str, Any]
    relevance_score: float
    timestamp: datetime
    content_type: ContentType
    metadata: Dict[str, Any] = {}


class KnowledgeQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    top_k: Optional[int] = Field(default=10, ge=1, le=50)
    content_types: Optional[List[ContentType]] = None
    date_range: Optional[Dict[str, str]] = None
    content_filters: Optional[Dict[str, Any]] = None


class KnowledgeQueryResponse(BaseModel):
    answer: str
    sources: List[SearchResult]
    query: str
    session_id: Optional[str] = None
    processing_time: float


class ContentItem(BaseModel):
    id: str
    content_id: str
    user_id: str
    content_type: ContentType
    title: str
    file_path: Optional[str] = None
    processing_status: ProcessingStatusEnum
    metadata: Dict[str, Any] = {}
    created_at: datetime
    processed_at: Optional[datetime] = None


class ProcessingStatus(BaseModel):
    content_id: str
    status: ProcessingStatusEnum
    progress: Optional[float] = None
    message: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class VectorSearchRequest(BaseModel):
    query: str
    user_id: str
    top_k: int = 10
    content_types: Optional[List[ContentType]] = None
    date_range: Optional[Dict[str, str]] = None


class EmbeddingRequest(BaseModel):
    texts: List[str]
    model: Optional[str] = "text-embedding-3-large"


class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    usage: Dict[str, int]


class ContentChunk(BaseModel):
    chunk_id: str
    content_id: str
    text: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}
    chunk_index: int
    start_char: Optional[int] = None
    end_char: Optional[int] = None


class BatchProcessRequest(BaseModel):
    content_ids: List[str]
    operation: str  # "reprocess", "delete", "export"
    parameters: Optional[Dict[str, Any]] = None


class BatchProcessResponse(BaseModel):
    job_id: str
    status: str
    total_items: int
    message: str


class ContentStats(BaseModel):
    total_items: int
    by_type: Dict[ContentType, int]
    by_status: Dict[ProcessingStatusEnum, int]
    total_size_bytes: int
    processing_queue_size: int


class RecommendationRequest(BaseModel):
    content_id: str
    recommendation_type: str  # "similar", "related", "follow_up"
    limit: int = 5


class RecommendationResponse(BaseModel):
    recommendations: List[SearchResult]
    recommendation_type: str
    confidence_scores: List[float]
