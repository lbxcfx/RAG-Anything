"""RAG service - Development stub for RAGAnything"""
import os
from typing import Optional, List, Dict, Any


class RAGService:
    """RAG service stub for development (RAGAnything dependencies not installed)"""

    def __init__(self, kb_config: dict, model_configs: dict):
        """
        Initialize RAG service

        Args:
            kb_config: Knowledge base configuration
            model_configs: Model configurations (llm, vlm, embedding)
        """
        self.kb_config = kb_config
        self.model_configs = model_configs
        self.rag_instance: Optional[Any] = None
        print("[DEV MODE] RAGService initialized with stub implementation")

    async def initialize(self):
        """Initialize RAGAnything instance (stub)"""
        print("[DEV MODE] RAGService.initialize() - stub implementation")
        return None

    async def process_document(
        self, file_path: str, output_dir: str, parse_method: str = "auto"
    ) -> Dict[str, Any]:
        """
        Process a document (stub)

        Args:
            file_path: Path to the document
            output_dir: Output directory for parsed content
            parse_method: Parsing method (auto, ocr, txt)

        Returns:
            Processing result
        """
        print(f"[DEV MODE] RAGService.process_document() - stub implementation for {file_path}")
        return {
            "file_path": file_path,
            "output_dir": output_dir,
            "status": "simulated",
            "text_count": 10,
            "image_count": 2,
            "table_count": 1,
        }

    async def query(
        self,
        question: str,
        mode: str = "hybrid",
        multimodal_content: Optional[List[Dict[str, Any]]] = None,
        vlm_enhanced: Optional[bool] = None,
    ) -> str:
        """
        Query the knowledge base (stub)

        Args:
            question: User question
            mode: Query mode (hybrid, local, global, naive)
            multimodal_content: Optional multimodal content
            vlm_enhanced: Enable VLM enhancement

        Returns:
            Answer string
        """
        print(f"[DEV MODE] RAGService.query() - stub implementation for question: {question}")
        return f"[DEV MODE] This is a stub response. The real RAG engine is not installed. Question was: {question}"

    async def get_knowledge_graph(self) -> Dict[str, Any]:
        """
        Get knowledge graph data (stub)

        Returns:
            Graph data with entities and relations
        """
        print("[DEV MODE] RAGService.get_knowledge_graph() - stub implementation")
        return {
            "entities": [
                {"id": "entity_1", "name": "Concept A", "type": "concept"},
                {"id": "entity_2", "name": "Concept B", "type": "concept"},
            ],
            "relations": [
                {"source": "entity_1", "target": "entity_2", "type": "RELATED_TO", "weight": 0.8}
            ],
        }

    async def insert_content_list(
        self, content_list: List[Dict[str, Any]], file_path: str, doc_id: Optional[str] = None
    ):
        """Insert pre-parsed content list (stub)"""
        print(f"[DEV MODE] RAGService.insert_content_list() - stub implementation for {len(content_list)} items")
