"""Chat models"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class QueryMode(str, enum.Enum):
    """Query mode enumeration"""
    HYBRID = "hybrid"
    LOCAL = "local"
    GLOBAL = "global"
    NAIVE = "naive"


class ChatSession(Base):
    """Chat session database model"""

    __tablename__ = "chat_sessions"

    title = Column(String(500))
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    knowledge_base = relationship("KnowledgeBase", backref="chat_sessions")
    user = relationship("User", backref="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Chat message database model"""

    __tablename__ = "chat_messages"

    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)

    # Multimodal content
    multimodal_content = Column(JSON)  # images, tables, equations

    # Query parameters
    query_mode = Column(SQLEnum(QueryMode))
    vlm_enhanced = Column(String(10))  # "true", "false", null

    # Response metadata
    sources = Column(JSON)  # citation sources
    response_time = Column(Integer)  # in milliseconds

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
