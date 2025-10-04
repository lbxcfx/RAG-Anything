"""Knowledge base models"""
from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class ParserType(str, enum.Enum):
    """Parser type enumeration"""
    MINERU = "mineru"
    DOCLING = "docling"


class KnowledgeBase(Base):
    """Knowledge base database model"""

    __tablename__ = "knowledge_bases"

    name = Column(String(255), nullable=False)
    description = Column(Text)
    parser_type = Column(SQLEnum(ParserType), default=ParserType.MINERU)
    parse_method = Column(String(50), default="auto")  # auto, ocr, txt
    enable_image_processing = Column(Boolean, default=True)
    enable_table_processing = Column(Boolean, default=True)
    enable_equation_processing = Column(Boolean, default=True)

    # Model configurations (reference to ModelConfig IDs)
    llm_model_id = Column(Integer, ForeignKey("model_configs.id"))
    vlm_model_id = Column(Integer, ForeignKey("model_configs.id"))
    embedding_model_id = Column(Integer, ForeignKey("model_configs.id"))

    # Storage paths
    working_dir = Column(String(500))
    vector_collection_name = Column(String(255))

    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", backref="knowledge_bases")
    llm_model = relationship("ModelConfig", foreign_keys=[llm_model_id])
    vlm_model = relationship("ModelConfig", foreign_keys=[vlm_model_id])
    embedding_model = relationship("ModelConfig", foreign_keys=[embedding_model_id])
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
