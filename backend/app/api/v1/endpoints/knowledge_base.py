"""Knowledge base endpoints"""
from typing import List
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.api.v1.deps import get_current_active_user
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
)
from app.core.config import settings

router = APIRouter()


@router.post("/", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    kb_in: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new knowledge base"""
    # Create working directory
    working_dir = os.path.join(
        settings.UPLOAD_DIR, f"kb_{current_user.id}_{kb_in.name.replace(' ', '_')}"
    )
    os.makedirs(working_dir, exist_ok=True)

    # Create vector collection name
    vector_collection_name = f"kb_{current_user.id}_{kb_in.name.replace(' ', '_').lower()}"

    # Create knowledge base
    kb = KnowledgeBase(
        **kb_in.model_dump(),
        user_id=current_user.id,
        working_dir=working_dir,
        vector_collection_name=vector_collection_name,
    )

    db.add(kb)
    await db.commit()
    await db.refresh(kb)

    response = KnowledgeBaseResponse.from_orm(kb)
    response.document_count = 0

    return response


@router.get("/", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's knowledge bases"""
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.user_id == current_user.id)
    )
    kbs = result.scalars().all()

    response_list = []
    for kb in kbs:
        # Get document count
        doc_count_result = await db.execute(
            select(func.count(Document.id)).where(Document.knowledge_base_id == kb.id)
        )
        doc_count = doc_count_result.scalar() or 0

        kb_response = KnowledgeBaseResponse.from_orm(kb)
        kb_response.document_count = doc_count
        response_list.append(kb_response)

    return response_list


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get knowledge base"""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id, KnowledgeBase.user_id == current_user.id
        )
    )
    kb = result.scalar_one_or_none()

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    # Get document count
    doc_count_result = await db.execute(
        select(func.count(Document.id)).where(Document.knowledge_base_id == kb.id)
    )
    doc_count = doc_count_result.scalar() or 0

    kb_response = KnowledgeBaseResponse.from_orm(kb)
    kb_response.document_count = doc_count

    return kb_response


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: int,
    kb_update: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update knowledge base"""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id, KnowledgeBase.user_id == current_user.id
        )
    )
    kb = result.scalar_one_or_none()

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    update_data = kb_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(kb, field, value)

    await db.commit()
    await db.refresh(kb)

    return KnowledgeBaseResponse.from_orm(kb)


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete knowledge base"""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id, KnowledgeBase.user_id == current_user.id
        )
    )
    kb = result.scalar_one_or_none()

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    # Delete from Neo4j
    from app.services.graph_service import GraphService

    graph_service = GraphService()
    await graph_service.delete_kb_graph(kb_id)
    await graph_service.close()

    # Delete from database (will cascade delete documents)
    await db.delete(kb)
    await db.commit()
