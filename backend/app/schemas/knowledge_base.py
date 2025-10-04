"""Knowledge base schemas"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.knowledge_base import ParserType


class KnowledgeBaseBase(BaseModel):
    """Knowledge base base schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    parser_type: ParserType = ParserType.MINERU
    parse_method: str = Field(default="auto", pattern="^(auto|ocr|txt)$")
    enable_image_processing: bool = True
    enable_table_processing: bool = True
    enable_equation_processing: bool = True
    llm_model_id: Optional[int] = None
    vlm_model_id: Optional[int] = None
    embedding_model_id: Optional[int] = None


class KnowledgeBaseCreate(KnowledgeBaseBase):
    """Knowledge base creation schema"""
    pass


class KnowledgeBaseUpdate(BaseModel):
    """Knowledge base update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    parser_type: Optional[ParserType] = None
    parse_method: Optional[str] = Field(None, pattern="^(auto|ocr|txt)$")
    enable_image_processing: Optional[bool] = None
    enable_table_processing: Optional[bool] = None
    enable_equation_processing: Optional[bool] = None
    llm_model_id: Optional[int] = None
    vlm_model_id: Optional[int] = None
    embedding_model_id: Optional[int] = None
    is_active: Optional[bool] = None


class KnowledgeBaseInDB(KnowledgeBaseBase):
    """Knowledge base in database schema"""
    id: int
    working_dir: Optional[str] = None
    vector_collection_name: Optional[str] = None
    is_active: bool
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBaseResponse(KnowledgeBaseInDB):
    """Knowledge base response schema"""
    document_count: Optional[int] = 0
    entity_count: Optional[int] = 0
    relation_count: Optional[int] = 0
