from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Enum, Table, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.base_class import Base
import uuid


class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"


class ModelTier(str, enum.Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    EXPIRED = "expired"
    PENDING = "pending"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    role = Column(String, default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # OAuth fields
    oauth_provider = Column(String, nullable=True)  # e.g., 'google', 'facebook'
    oauth_user_id = Column(String, nullable=True)  # Provider's user ID
    oauth_access_token = Column(String, nullable=True)
    oauth_refresh_token = Column(String, nullable=True)
    oauth_token_expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete")
    token_usage = relationship("TokenUsage", back_populates="user", cascade="all, delete")
    token_usage_summary = relationship("TokenUsageSummary", back_populates="user", cascade="all, delete")
    user_preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete")
    usage_statistics = relationship("UsageStatistics", back_populates="user", uselist=False, cascade="all, delete")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete")
    research_projects = relationship("ResearchProject", back_populates="user", cascade="all, delete")
    documents = relationship("Document", back_populates="user", cascade="all, delete")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan = Column(Enum(SubscriptionPlan), default=SubscriptionPlan.FREE, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    auto_renew = Column(Boolean, default=False)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    payment_method_id = Column(String, nullable=True)
    token_limit = Column(Integer, nullable=True)
    max_model_tier = Column(String, default=ModelTier.GPT_3_5_TURBO, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subscription")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
