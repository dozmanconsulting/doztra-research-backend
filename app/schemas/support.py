from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SupportChatStatus(str, Enum):
    WAITING = "waiting"
    CONNECTED = "connected" 
    ENDED = "ended"
    DISCONNECTED = "disconnected"


class RepresentativeStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    AWAY = "away"


class SupportChatRequest(BaseModel):
    user_email: Optional[EmailStr] = None
    user_name: Optional[str] = None
    initial_message: Optional[str] = None
    priority: Optional[str] = "normal"  # normal, high, urgent

    class Config:
        json_schema_extra = {
            "example": {
                "user_email": "user@example.com",
                "user_name": "John Doe",
                "initial_message": "I need help with my account",
                "priority": "normal"
            }
        }


class SupportChatResponse(BaseModel):
    chat_id: str
    status: SupportChatStatus
    estimated_wait_time: Optional[int] = None  # in minutes
    message: str
    representative_name: Optional[str] = None
    queue_position: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "chat_id": "chat_123456789",
                "status": "waiting",
                "estimated_wait_time": 5,
                "message": "You are in the queue. Estimated wait time: 5 minutes",
                "queue_position": 3
            }
        }


class SupportMessageRequest(BaseModel):
    message: str
    sender_type: str = "user"  # user or representative

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hello, I need help with my subscription",
                "sender_type": "user"
            }
        }


class SupportMessageResponse(BaseModel):
    message_id: str
    chat_id: str
    message: str
    sender_type: str
    sender_name: Optional[str] = None
    timestamp: datetime
    delivered: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_123456789",
                "chat_id": "chat_123456789", 
                "message": "Hello! How can I help you today?",
                "sender_type": "representative",
                "sender_name": "Sarah Johnson",
                "timestamp": "2024-01-01T12:00:00Z",
                "delivered": True
            }
        }


class SupportChatHistory(BaseModel):
    chat_id: str
    messages: List[SupportMessageResponse]
    status: SupportChatStatus
    created_at: datetime
    ended_at: Optional[datetime] = None
    representative_name: Optional[str] = None
    user_rating: Optional[int] = None


class RepresentativeInfo(BaseModel):
    id: str
    name: str
    email: str
    status: RepresentativeStatus
    current_chats: int
    max_concurrent_chats: int
    is_online: bool
    last_seen: Optional[datetime] = None


class SupportStatusResponse(BaseModel):
    representatives_online: int
    total_representatives: int
    current_queue_length: int
    average_wait_time: int  # in minutes
    is_available: bool

    class Config:
        json_schema_extra = {
            "example": {
                "representatives_online": 3,
                "total_representatives": 5,
                "current_queue_length": 2,
                "average_wait_time": 4,
                "is_available": True
            }
        }