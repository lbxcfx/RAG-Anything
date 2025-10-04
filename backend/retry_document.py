"""Script to manually retry processing a stuck document"""
import asyncio
import sys
sys.path.insert(0, "/e/RAG-Anything/backend")

from app.db.session import async_session_maker
from app.models.document import Document, DocumentStatus
from app.services.document_processor import DocumentProcessor
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def retry_document(doc_id: int):
    """Retry processing a document"""
    processor = DocumentProcessor()

    async with async_session_maker() as db:
        # Get document
        result = await db.execute(select(Document).where(Document.id == doc_id))
        document = result.scalar_one_or_none()

        if not document:
            logger.error(f"Document {doc_id} not found")
            return

        logger.info(f"Found document: {document.filename}")
        logger.info(f"Current status: {document.status}, progress: {document.progress}%")

        # Update to PARSING
        document.status = DocumentStatus.PARSING
        document.progress = 10
        document.error_message = None
        await db.commit()
        logger.info(f"Updated status to PARSING")

        # Process document
        logger.info(f"Starting processing for KB {document.knowledge_base_id}")
        result = await processor.process_document(
            document.knowledge_base_id,
            document.original_path,
            document.filename
        )

        # Update with results
        if result["success"]:
            document.status = DocumentStatus.COMPLETED
            document.progress = 100
            document.entity_count = result.get("entity_count", 0)
            document.relation_count = result.get("relation_count", 0)
            logger.info(f"Processing completed: {result['message']}")
        else:
            document.status = DocumentStatus.FAILED
            document.error_message = result.get("message", "Processing failed")
            logger.error(f"Processing failed: {result['message']}")

        await db.commit()
        logger.info(f"Final status: {document.status}, progress: {document.progress}%")


if __name__ == "__main__":
    doc_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    asyncio.run(retry_document(doc_id))
