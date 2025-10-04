"""Model configuration models"""
from sqlalchemy import Column, String, Integer, JSON, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class ModelType(str, enum.Enum):
    """Model type enumeration"""
    LLM = "llm"
    VLM = "vlm"
    EMBEDDING = "embedding"
    RERANK = "rerank"


class ModelConfig(Base):
    """Model configuration database model"""

    __tablename__ = "model_configs"

    name = Column(String(255), nullable=False)
    model_type = Column(SQLEnum(ModelType), nullable=False)
    provider = Column(String(100), nullable=False)  # openai, anthropic, local, etc.
    model_name = Column(String(255), nullable=False)  # gpt-4o-mini, claude-3-opus, etc.
    api_key = Column(String(500))  # Encrypted
    api_base_url = Column(String(500))
    parameters = Column(JSON)  # temperature, top_p, max_tokens, etc.
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", backref="model_configs")
