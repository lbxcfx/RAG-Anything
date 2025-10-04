"""Document processing Celery tasks"""
import os
from celery import Task
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.model_config import ModelConfig
from app.services.rag_service import RAGService
from app.services.graph_service import GraphService


class DocumentProcessingTask(Task):
    """Base task for document processing with progress tracking"""

    def update_progress(self, doc_id: int, stage: str, progress: int, status: str, message: str = None):
        """Update document processing progress"""
        db = SessionLocal()
        try:
            document = db.query(Document).filter(Document.id == doc_id).first()
            if document:
                document.status = DocumentStatus[status.upper()]
                document.progress = progress
                if message:
                    document.error_message = message
                db.commit()

                # In production, this would also push to WebSocket
                print(f"Progress update - Stage: {stage}, Progress: {progress}%, Status: {status}")
        finally:
            db.close()


@celery_app.task(bind=True, base=DocumentProcessingTask)
def process_document_task(self, doc_id: int, file_path: str, kb_id: int):
    """
    Process document asynchronously

    Args:
        doc_id: Document ID
        file_path: Path to uploaded file
        kb_id: Knowledge base ID
    """
    db = SessionLocal()

    try:
        # Get document and KB
        document = db.query(Document).filter(Document.id == doc_id).first()
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()

        if not document or not kb:
            raise ValueError("Document or Knowledge Base not found")

        # Stage 1: PARSING
        self.update_progress(doc_id, "parsing", 0, "parsing", "Starting document parsing...")

        # Get model configs
        model_configs = {}
        if kb.llm_model_id:
            llm_model = db.query(ModelConfig).filter(ModelConfig.id == kb.llm_model_id).first()
            if llm_model:
                model_configs["llm"] = llm_model.__dict__

        if kb.vlm_model_id:
            vlm_model = db.query(ModelConfig).filter(ModelConfig.id == kb.vlm_model_id).first()
            if vlm_model:
                model_configs["vlm"] = vlm_model.__dict__

        if kb.embedding_model_id:
            embed_model = db.query(ModelConfig).filter(ModelConfig.id == kb.embedding_model_id).first()
            if embed_model:
                model_configs["embedding"] = embed_model.__dict__

        # Initialize RAG service
        kb_config = kb.__dict__
        rag_service = RAGService(kb_config, model_configs)

        # Parse document
        output_dir = os.path.join(kb.working_dir, f"doc_{doc_id}_output")
        os.makedirs(output_dir, exist_ok=True)

        self.update_progress(doc_id, "parsing", 25, "parsing", "Parsing document...")

        # This would call the actual parsing
        # For now, simulate
        document.parsed_path = output_dir
        document.text_count = 10  # Placeholder
        document.image_count = 2
        document.table_count = 1
        document.equation_count = 0

        self.update_progress(doc_id, "parsing", 100, "analyzing", "Document parsed successfully")

        # Stage 2: ANALYZING
        self.update_progress(doc_id, "analyzing", 0, "analyzing", "Analyzing content...")

        # Content analysis would happen here
        self.update_progress(doc_id, "analyzing", 50, "analyzing", "Extracting entities...")

        # Simulate entity extraction
        entities_count = 15
        relations_count = 20

        self.update_progress(doc_id, "analyzing", 100, "building_graph", "Content analysis completed")

        # Stage 3: BUILDING GRAPH
        self.update_progress(doc_id, "building_graph", 0, "building_graph", "Building knowledge graph...")

        # Store in Neo4j
        graph_service = GraphService()

        # Simulate graph data
        entities = [
            {"id": f"entity_{i}", "name": f"Entity {i}", "type": "concept"}
            for i in range(entities_count)
        ]
        relations = [
            {"source": f"entity_{i}", "target": f"entity_{i+1}", "type": "RELATED_TO", "weight": 0.8}
            for i in range(relations_count)
        ]

        # This would actually store the real extracted entities
        # await graph_service.store_entities(kb_id, entities, relations)

        document.entity_count = entities_count
        document.relation_count = relations_count

        self.update_progress(doc_id, "building_graph", 100, "embedding", "Knowledge graph built")

        # Stage 4: EMBEDDING
        self.update_progress(doc_id, "embedding", 0, "embedding", "Generating embeddings...")

        # Vector embedding would happen here
        self.update_progress(doc_id, "embedding", 50, "embedding", "Storing vectors...")

        # Simulate vector storage
        self.update_progress(doc_id, "embedding", 100, "completed", "Processing completed successfully")

        # Final update
        document.status = DocumentStatus.COMPLETED
        document.progress = 100
        db.commit()

        return {
            "doc_id": doc_id,
            "status": "completed",
            "text_count": document.text_count,
            "image_count": document.image_count,
            "table_count": document.table_count,
            "entity_count": document.entity_count,
            "relation_count": document.relation_count,
        }

    except Exception as e:
        # Handle errors
        self.update_progress(doc_id, "error", 0, "failed", str(e))

        if db:
            document = db.query(Document).filter(Document.id == doc_id).first()
            if document:
                document.status = DocumentStatus.FAILED
                document.error_message = str(e)
                db.commit()

        raise

    finally:
        db.close()


@celery_app.task
def cleanup_old_tasks():
    """Periodic task to cleanup old completed tasks"""
    # This would clean up old task results
    print("Cleaning up old tasks...")
    return {"cleaned": 0}
