"""Model configuration schemas"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.model_config import ModelType


class ModelConfigBase(BaseModel):
    """Model config base schema"""
    name: str = Field(..., min_length=1, max_length=255)
    model_type: ModelType
    provider: str = Field(..., min_length=1, max_length=100)
    model_name: str = Field(..., min_length=1, max_length=255)
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_default: bool = False
    is_active: bool = True


class ModelConfigCreate(ModelConfigBase):
    """Model config creation schema"""
    pass


class ModelConfigUpdate(BaseModel):
    """Model config update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    model_type: Optional[ModelType] = None
    provider: Optional[str] = Field(None, min_length=1, max_length=100)
    model_name: Optional[str] = Field(None, min_length=1, max_length=255)
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class ModelConfigInDB(ModelConfigBase):
    """Model config in database schema"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelConfigResponse(ModelConfigInDB):
    """Model config response schema (without API key)"""
    api_key: Optional[str] = Field(None, description="Hidden for security")

    @classmethod
    def from_orm(cls, obj):
        data = obj.__dict__.copy()
        if 'api_key' in data and data['api_key']:
            data['api_key'] = "***"  # Mask API key
        return cls(**data)
