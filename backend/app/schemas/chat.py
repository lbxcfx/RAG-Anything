"""Chat schemas"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.chat import QueryMode


class ChatSessionBase(BaseModel):
    """Chat session base schema"""
    title: Optional[str] = None
    knowledge_base_id: int


class ChatSessionCreate(ChatSessionBase):
    """Chat session creation schema"""
    pass


class ChatSessionInDB(ChatSessionBase):
    """Chat session in database schema"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(ChatSessionInDB):
    """Chat session response schema"""
    message_count: Optional[int] = 0
    messages: Optional[List[ChatMessageResponse]] = None


class ChatMessageBase(BaseModel):
    """Chat message base schema"""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str
    multimodal_content: Optional[List[Dict[str, Any]]] = None
    query_mode: Optional[QueryMode] = QueryMode.HYBRID
    vlm_enhanced: Optional[str] = None


class ChatMessageCreate(ChatMessageBase):
    """Chat message creation schema"""
    session_id: int


class ChatMessageInDB(ChatMessageBase):
    """Chat message in database schema"""
    id: int
    session_id: int
    sources: Optional[List[Dict[str, Any]]] = None
    response_time: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageResponse(ChatMessageInDB):
    """Chat message response schema"""
    pass


class QueryRequest(BaseModel):
    """Query request schema"""
    question: str
    mode: QueryMode = QueryMode.HYBRID
    multimodal_content: Optional[List[Dict[str, Any]]] = None
    vlm_enhanced: Optional[bool] = None
    session_id: Optional[int] = None


class QueryResponse(BaseModel):
    """Query response schema"""
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None
    response_time: int
    session_id: Optional[int] = None
