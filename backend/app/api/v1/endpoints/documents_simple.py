"""Simplified document management endpoints without Celery"""
from typing import List
import os
import shutil
import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.v1.deps import get_current_active_user
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.schemas.document import DocumentResponse
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    knowledge_base_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document to knowledge base (simplified without processing)"""
    # Verify knowledge base exists and belongs to user
    kb_result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == knowledge_base_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )
    kb = kb_result.scalar_one_or_none()

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    # Save file
    upload_dir = os.path.join(settings.UPLOAD_DIR, f"kb_{kb.id}")
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)

    # Save uploaded file asynchronously
    async with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    file_size = os.path.getsize(file_path)
    file_type = file.filename.split(".")[-1] if "." in file.filename else "unknown"

    # Create document record with COMPLETED status (no processing)
    document = Document(
        filename=file.filename,
        original_path=file_path,
        file_size=file_size,
        file_type=file_type,
        status=DocumentStatus.COMPLETED,  # Mark as completed immediately
        progress=100,
        knowledge_base_id=kb.id,
        user_id=current_user.id,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    return document


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    knowledge_base_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's documents"""
    query = select(Document).where(Document.user_id == current_user.id)

    if knowledge_base_id:
        query = query.where(Document.knowledge_base_id == knowledge_base_id)

    result = await db.execute(query)
    documents = result.scalars().all()

    return documents


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document details"""
    result = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.user_id == current_user.id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete document"""
    result = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.user_id == current_user.id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete file
    if os.path.exists(document.original_path):
        os.remove(document.original_path)

    # Delete associated entities and relations from Neo4j
    from app.services.graph_service import GraphService
    graph_service = GraphService()
    await graph_service.delete_document_entities(document.knowledge_base_id, document.original_path)
    await graph_service.close()

    # Delete associated entities and relations from LightRAG storage
    try:
        from app.services.lightrag_cleanup_service import LightRAGCleanupService
        cleanup_service = LightRAGCleanupService()
        cleanup_stats = cleanup_service.delete_document_from_lightrag(document.knowledge_base_id, document.original_path)
        logger.info(f"Completed LightRAG cleanup for document {doc_id}: {cleanup_stats}")
    except Exception as e:
        logger.error(f"Error deleting LightRAG entities for document {doc_id}: {e}", exc_info=True)
        # Continue with database deletion even if LightRAG cleanup fails

    # Delete from database
    await db.delete(document)
    await db.commit()
