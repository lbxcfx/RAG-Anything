"""Document management endpoints with RAGAnything processing"""
from typing import List
import os
import shutil
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.v1.deps import get_current_active_user
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.schemas.document import DocumentResponse
from app.core.config import settings
from app.services.document_processor import DocumentProcessor

router = APIRouter()
logger = logging.getLogger(__name__)

# Global document processor instance
document_processor = DocumentProcessor()


def process_document_background(doc_id: int, kb_id: int, file_path: str, filename: str):
    """Background task to process document with RAGAnything"""
    import asyncio

    async def async_process():
        try:
            # Import here to avoid circular imports
            from app.db.session import async_session_maker

            # Progress callback to update database
            async def progress_callback(progress: int, status_msg: str):
                """Update document progress in database"""
                async with async_session_maker() as db:
                    result = await db.execute(select(Document).where(Document.id == doc_id))
                    document = result.scalar_one_or_none()
                    if document:
                        document.progress = progress
                        # Map progress to status
                        if progress < 25:
                            document.status = DocumentStatus.PARSING
                        elif progress < 70:
                            document.status = DocumentStatus.ANALYZING
                        elif progress < 85:
                            document.status = DocumentStatus.BUILDING_GRAPH
                        elif progress < 100:
                            document.status = DocumentStatus.EMBEDDING
                        else:
                            document.status = DocumentStatus.COMPLETED
                        await db.commit()
                        logger.info(f"Document {doc_id} progress: {progress}% - {status_msg}")

            # Set initial status
            async with async_session_maker() as db:
                result = await db.execute(select(Document).where(Document.id == doc_id))
                document = result.scalar_one_or_none()
                if document:
                    document.status = DocumentStatus.PARSING
                    document.progress = 10
                    await db.commit()
                    logger.info(f"Document {doc_id} status updated to PARSING")

            # Process document with RAGAnything
            #  Create a fresh DocumentProcessor instance to avoid caching issues
            from app.services.document_processor import DocumentProcessor
            from app.models.model_config import ModelConfig

            # Get knowledge base with model configs
            async with async_session_maker() as db:
                result = await db.execute(
                    select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
                )
                kb = result.scalar_one_or_none()

                # Fetch model configurations
                model_configs = {}
                if kb and kb.llm_model_id:
                    llm_result = await db.execute(
                        select(ModelConfig).where(ModelConfig.id == kb.llm_model_id)
                    )
                    llm_model = llm_result.scalar_one_or_none()
                    if llm_model:
                        model_configs["llm"] = {
                            "model_name": llm_model.model_name,
                            "api_key": llm_model.api_key,
                            "api_base_url": llm_model.api_base_url,
                            "provider": llm_model.provider,
                        }

                if kb and kb.vlm_model_id:
                    vlm_result = await db.execute(
                        select(ModelConfig).where(ModelConfig.id == kb.vlm_model_id)
                    )
                    vlm_model = vlm_result.scalar_one_or_none()
                    if vlm_model:
                        model_configs["vlm"] = {
                            "model_name": vlm_model.model_name,
                            "api_key": vlm_model.api_key,
                            "api_base_url": vlm_model.api_base_url,
                            "provider": vlm_model.provider,
                        }

                if kb and kb.embedding_model_id:
                    embed_result = await db.execute(
                        select(ModelConfig).where(ModelConfig.id == kb.embedding_model_id)
                    )
                    embed_model = embed_result.scalar_one_or_none()
                    if embed_model:
                        model_configs["embedding"] = {
                            "model_name": embed_model.model_name,
                            "api_key": embed_model.api_key,
                            "api_base_url": embed_model.api_base_url,
                            "provider": embed_model.provider,
                        }

            processor = DocumentProcessor()
            logger.info(f"Starting RAGAnything processing for document {doc_id}")
            logger.info(f"Using model configs: LLM={model_configs.get('llm', {}).get('model_name', 'default')}, "
                       f"VLM={model_configs.get('vlm', {}).get('model_name', 'default')}, "
                       f"Embedding={model_configs.get('embedding', {}).get('model_name', 'default')}")
            process_result = await processor.process_document(
                kb_id, file_path, filename,
                progress_callback=progress_callback,
                model_configs=model_configs
            )

            # Update document with processing results
            async with async_session_maker() as db:
                result = await db.execute(select(Document).where(Document.id == doc_id))
                document = result.scalar_one_or_none()
                if document:
                    if process_result["success"]:
                        document.status = DocumentStatus.COMPLETED
                        document.progress = 100
                        document.entity_count = process_result.get("entity_count", 0)
                        document.relation_count = process_result.get("relation_count", 0)
                        logger.info(f"Document {doc_id} processed successfully: {process_result['message']}")
                    else:
                        document.status = DocumentStatus.FAILED
                        document.error_message = process_result.get("message", "Processing failed")
                        logger.error(f"Document {doc_id} processing failed: {process_result['message']}")

                    await db.commit()

        except Exception as e:
            logger.error(f"Error in background processing for document {doc_id}: {e}", exc_info=True)
            # Try to mark as failed
            try:
                from app.db.session import async_session_maker
                async with async_session_maker() as db:
                    result = await db.execute(select(Document).where(Document.id == doc_id))
                    document = result.scalar_one_or_none()
                    if document:
                        document.status = DocumentStatus.FAILED
                        document.error_message = str(e)
                        await db.commit()
            except:
                pass

    # Run the async function in the event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a task
            asyncio.create_task(async_process())
        else:
            # If no loop is running, run it
            loop.run_until_complete(async_process())
    except RuntimeError:
        # Create a new event loop if needed
        asyncio.run(async_process())


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    knowledge_base_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document to knowledge base and process with RAGAnything"""
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

    # Save uploaded file
    content = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    file_size = os.path.getsize(file_path)
    file_type = file.filename.split(".")[-1] if "." in file.filename else "unknown"

    # Create document record with PENDING status
    document = Document(
        filename=file.filename,
        original_path=file_path,
        file_size=file_size,
        file_type=file_type,
        status=DocumentStatus.PENDING,  # Will be processed in background
        progress=0,
        knowledge_base_id=kb.id,
        user_id=current_user.id,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Add background task to process document
    background_tasks.add_task(
        process_document_background,
        document.id,
        kb.id,
        file_path,
        file.filename
    )

    logger.info(f"Document {document.id} uploaded, scheduled for background processing")

    return document


async def auto_process_pending_documents():
    """自动处理所有待处理的文档"""
    from app.db.session import async_session_maker
    
    async with async_session_maker() as db:
        # 查找所有待处理的文档
        result = await db.execute(
            select(Document).where(
                Document.status == DocumentStatus.PENDING
            ).order_by(Document.created_at)
        )
        pending_docs = result.scalars().all()
        
        if not pending_docs:
            logger.info("No pending documents found")
            return
        
        logger.info(f"Found {len(pending_docs)} pending documents to process")
        
        for doc in pending_docs:
            try:
                # 获取知识库
                kb_result = await db.execute(
                    select(KnowledgeBase).where(KnowledgeBase.id == doc.knowledge_base_id)
                )
                kb = kb_result.scalar_one_or_none()
                
                if not kb:
                    logger.error(f"Knowledge base not found for document {doc.id}")
                    continue
                
                # 触发处理
                logger.info(f"Auto-processing document {doc.id}: {doc.filename}")
                
                # 使用asyncio.create_task来异步处理
                import asyncio
                asyncio.create_task(
                    process_document_background_async(
                        doc.id, kb.id, doc.original_path, doc.filename
                    )
                )
                
            except Exception as e:
                logger.error(f"Error auto-processing document {doc.id}: {e}")


async def process_document_background_async(doc_id: int, kb_id: int, file_path: str, filename: str):
    """异步处理文档的包装函数"""
    try:
        # 调用原有的处理函数
        process_document_background(doc_id, kb_id, file_path, filename)
    except Exception as e:
        logger.error(f"Error processing document {doc_id}: {e}")


@router.post("/auto-process")
async def trigger_auto_process(
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_active_user),
):
    """触发自动处理所有待处理文档"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can trigger auto-processing",
        )
    
    # 添加后台任务
    background_tasks.add_task(auto_process_pending_documents)
    
    logger.info("Auto-processing of pending documents triggered")
    
    return {"message": "Auto-processing triggered for all pending documents"}


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
        logger.info(f"Deleted file: {document.original_path}")

    # Delete associated entities and relations from Neo4j
    logger.info(f"Starting Neo4j cleanup for document {doc_id}, KB {document.knowledge_base_id}, path: {document.original_path}")
    try:
        from app.services.graph_service import GraphService
        graph_service = GraphService()
        await graph_service.delete_document_entities(document.knowledge_base_id, document.original_path)
        await graph_service.close()
        logger.info(f"Completed Neo4j cleanup for document {doc_id}")
    except Exception as e:
        logger.error(f"Error deleting Neo4j entities for document {doc_id}: {e}", exc_info=True)
        # Continue with database deletion even if Neo4j cleanup fails

    # Delete associated entities and relations from LightRAG storage
    logger.info(f"Starting LightRAG cleanup for document {doc_id}, KB {document.knowledge_base_id}, path: {document.original_path}")
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
    logger.info(f"Document {doc_id} deleted from database")
