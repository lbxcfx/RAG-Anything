"""Document schemas"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.document import DocumentStatus


class DocumentBase(BaseModel):
    """Document base schema"""
    filename: str
    file_type: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Document creation schema"""
    knowledge_base_id: int


class DocumentUpdate(BaseModel):
    """Document update schema"""
    status: Optional[DocumentStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    error_message: Optional[str] = None


class DocumentInDB(DocumentBase):
    """Document in database schema"""
    id: int
    original_path: str
    file_size: Optional[int] = None
    status: DocumentStatus
    progress: int
    error_message: Optional[str] = None
    parsed_path: Optional[str] = None
    text_count: int
    image_count: int
    table_count: int
    equation_count: int
    entity_count: int
    relation_count: int
    task_id: Optional[str] = None
    knowledge_base_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(DocumentInDB):
    """Document response schema"""
    pass


class DocumentProgress(BaseModel):
    """Document processing progress"""
    stage: str
    progress: int
    status: str
    message: Optional[str] = None
    result: Optional[dict] = None
