"""Document models"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Enum as SQLEnum, BigInteger
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class DocumentStatus(str, enum.Enum):
    """Document processing status"""
    PENDING = "pending"
    PARSING = "parsing"
    ANALYZING = "analyzing"
    BUILDING_GRAPH = "building_graph"
    EMBEDDING = "embedding"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    """Document database model"""

    __tablename__ = "documents"

    filename = Column(String(500), nullable=False)
    original_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger)  # in bytes
    file_type = Column(String(100))  # pdf, docx, etc.

    # Processing status
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text)

    # Processing results
    parsed_path = Column(String(1000))
    text_count = Column(Integer, default=0)
    image_count = Column(Integer, default=0)
    table_count = Column(Integer, default=0)
    equation_count = Column(Integer, default=0)

    # Knowledge graph stats
    entity_count = Column(Integer, default=0)
    relation_count = Column(Integer, default=0)

    # Task reference
    task_id = Column(String(255))  # Celery task ID

    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    user = relationship("User", backref="documents")
