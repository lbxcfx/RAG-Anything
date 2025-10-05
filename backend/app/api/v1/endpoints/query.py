"""Query and chat endpoints"""
import time
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.v1.deps import get_current_active_user
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.model_config import ModelConfig, ModelType
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import QueryRequest, QueryResponse, ChatSessionResponse, ChatMessageResponse
from app.services.rag_service import RAGService

router = APIRouter()


async def get_rag_service(kb_id: int, user_id: int, db: AsyncSession) -> RAGService:
    """Get RAG service for knowledge base"""
    # Get knowledge base
    kb_result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == user_id,
        )
    )
    kb = kb_result.scalar_one_or_none()

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    # Get model configurations
    model_configs = {}

    if kb.llm_model_id:
        llm_result = await db.execute(
            select(ModelConfig).where(ModelConfig.id == kb.llm_model_id)
        )
        llm_model = llm_result.scalar_one_or_none()
        if llm_model:
            model_configs["llm"] = llm_model.__dict__

    if kb.vlm_model_id:
        vlm_result = await db.execute(
            select(ModelConfig).where(ModelConfig.id == kb.vlm_model_id)
        )
        vlm_model = vlm_result.scalar_one_or_none()
        if vlm_model:
            model_configs["vlm"] = vlm_model.__dict__

    if kb.embedding_model_id:
        embed_result = await db.execute(
            select(ModelConfig).where(ModelConfig.id == kb.embedding_model_id)
        )
        embed_model = embed_result.scalar_one_or_none()
        if embed_model:
            model_configs["embedding"] = embed_model.__dict__

    # If no models configured, use default configurations
    if not model_configs.get("llm"):
        model_configs["llm"] = {
            "model_name": "gpt-4o-mini",
            "api_key": None,
            "api_base_url": None,
            "parameters": {},
        }

    if not model_configs.get("embedding"):
        model_configs["embedding"] = {
            "model_name": "text-embedding-3-large",
            "api_key": None,
            "api_base_url": None,
            "parameters": {"embedding_dim": 1024, "max_token_size": 8192},
        }

    # Create RAG service
    kb_config = kb.__dict__
    rag_service = RAGService(kb_config, model_configs)

    return rag_service


@router.post("/{kb_id}", response_model=QueryResponse)
async def query_knowledge_base(
    kb_id: int,
    query_request: QueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Query knowledge base"""
    start_time = time.time()

    # Get RAG service
    rag_service = await get_rag_service(kb_id, current_user.id, db)

    # Execute query
    answer = await rag_service.query(
        question=query_request.question,
        mode=query_request.mode.value,
        multimodal_content=query_request.multimodal_content,
        vlm_enhanced=query_request.vlm_enhanced,
    )

    response_time = int((time.time() - start_time) * 1000)  # milliseconds

    # Save to chat history if session_id provided
    if query_request.session_id:
        # Save user message
        user_msg = ChatMessage(
            session_id=query_request.session_id,
            role="user",
            content=query_request.question,
            multimodal_content=query_request.multimodal_content,
            query_mode=query_request.mode,
            vlm_enhanced=str(query_request.vlm_enhanced) if query_request.vlm_enhanced is not None else None,
        )
        db.add(user_msg)

        # Save assistant message
        assistant_msg = ChatMessage(
            session_id=query_request.session_id,
            role="assistant",
            content=answer,
            response_time=response_time,
        )
        db.add(assistant_msg)

        await db.commit()

    return QueryResponse(
        answer=answer,
        sources=[],  # Would extract from RAG response
        response_time=response_time,
        session_id=query_request.session_id,
    )


@router.post("/{kb_id}/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    kb_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new chat session"""
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

    # Create session
    session = ChatSession(
        knowledge_base_id=kb_id,
        user_id=current_user.id,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    response = ChatSessionResponse.from_orm(session)
    response.message_count = 0

    return response


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    kb_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's chat sessions"""
    query = select(ChatSession).where(ChatSession.user_id == current_user.id)
    
    if kb_id:
        query = query.where(ChatSession.knowledge_base_id == kb_id)
    
    query = query.order_by(ChatSession.created_at.desc())
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    # Convert to response format with message count
    response_sessions = []
    for session in sessions:
        response = ChatSessionResponse.from_orm(session)
        # Count messages for this session
        msg_count_result = await db.execute(
            select(ChatMessage).where(ChatMessage.session_id == session.id)
        )
        response.message_count = len(msg_count_result.scalars().all())
        response_sessions.append(response)
    
    return response_sessions


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific chat session with messages"""
    # Get session
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    
    # Get messages for this session
    messages_result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = messages_result.scalars().all()
    
    # Convert to response format
    response = ChatSessionResponse.from_orm(session)
    response.message_count = len(messages)
    
    # Add messages to response
    response.messages = [ChatMessageResponse.from_orm(msg) for msg in messages]
    
    return response


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            # Process chat message and stream response
            await websocket.send_json({"message": "Response", "data": data})
    except WebSocketDisconnect:
        print("Chat WebSocket disconnected")
