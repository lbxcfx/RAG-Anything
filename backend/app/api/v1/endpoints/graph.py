"""Knowledge graph endpoints"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.v1.deps import get_current_active_user
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.services.graph_service import GraphService

router = APIRouter()


@router.get("/{kb_id}", response_model=Dict[str, Any])
async def get_knowledge_graph(
    kb_id: int,
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get knowledge graph for knowledge base"""
    # Verify KB exists and belongs to user
    kb_result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )
    kb = kb_result.scalar_one_or_none()

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    # Get graph data
    graph_service = GraphService()
    try:
        graph_data = await graph_service.query_graph(kb_id, limit=limit)
        stats = await graph_service.get_graph_stats(kb_id)

        return {
            **graph_data,
            "stats": stats,
        }
    finally:
        await graph_service.close()


@router.get("/{kb_id}/stats/", response_model=Dict[str, int])
async def get_graph_stats(
    kb_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get graph statistics"""
    # Verify KB exists
    kb_result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )
    kb = kb_result.scalar_one_or_none()

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    # Get stats
    graph_service = GraphService()
    try:
        stats = await graph_service.get_graph_stats(kb_id)
        return stats
    finally:
        await graph_service.close()
