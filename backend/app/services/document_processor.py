"""Document processing service with RAGAnything integration

This service processes uploaded documents using RAGAnything for:
- Document parsing (MinerU/Docling)
- Multimodal content analysis (images, tables, equations)
- LLM-based entity extraction
- Knowledge graph construction
"""

import os
import sys
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import logging

# Add raganything to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from raganything import RAGAnything, RAGAnythingConfig
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from app.core.config import settings
from app.services.graph_service import GraphService

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process documents and build knowledge graphs using RAGAnything"""

    def __init__(self):
        """Initialize document processor with RAGAnything"""
        self.graph_service = GraphService()
        self.rag_instance: Optional[RAGAnything] = None
        logger.info("DocumentProcessor initialized")

    async def _get_or_create_rag_instance(self, kb_id: int) -> RAGAnything:
        """Get or create RAGAnything instance for knowledge base"""
        # Always create a fresh instance instead of caching
        # This ensures proper initialization with LightRAG

        # Create working directory for this KB
        working_dir = os.path.join(settings.VECTOR_DIR, f"kb_{kb_id}")
        os.makedirs(working_dir, exist_ok=True)

        # Configure RAGAnything
        config = RAGAnythingConfig(
            working_dir=working_dir,
            parser=settings.DEFAULT_PARSER,  # mineru or docling
            parse_method=settings.DEFAULT_PARSE_METHOD,  # auto
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
            # MinerU API settings
            mineru_use_api=settings.MINERU_USE_API,
            mineru_api_url=settings.MINERU_API_URL,
            mineru_api_key=settings.MINERU_API_KEY,
        )

        # Create embedding function
        async def embedding_func(texts: List[str]) -> List[List[float]]:
            """Embedding function using OpenAI API"""
            import openai

            client = openai.AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY or settings.DASHSCOPE_API_KEY,
                base_url=settings.OPENAI_BASE_URL if settings.OPENAI_API_KEY
                         else settings.DASHSCOPE_BASE_URL,
            )

            response = await client.embeddings.create(
                model=settings.DEFAULT_EMBEDDING_MODEL,
                input=texts,
                encoding_format="float"
            )

            return [item.embedding for item in response.data]

        # Create LLM function
        async def llm_model_func(
            prompt, system_prompt=None, history_messages=[], **kwargs
        ) -> str:
            """LLM function using OpenAI API"""
            import openai

            client = openai.AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY or settings.DASHSCOPE_API_KEY,
                base_url=settings.OPENAI_BASE_URL if settings.OPENAI_API_KEY
                         else settings.DASHSCOPE_BASE_URL,
            )

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.extend(history_messages)
            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=settings.DEFAULT_LLM_MODEL,
                messages=messages,
                **kwargs
            )

            return response.choices[0].message.content

        # Create vision model function for multimodal analysis
        async def vision_model_func(
            prompt, image_url=None, system_prompt=None, **kwargs
        ) -> str:
            """Vision model function using OpenAI API"""
            import openai

            client = openai.AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY or settings.DASHSCOPE_API_KEY,
                base_url=settings.OPENAI_BASE_URL if settings.OPENAI_API_KEY
                         else settings.DASHSCOPE_BASE_URL,
            )

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            content = [{"type": "text", "text": prompt}]
            if image_url:
                content.append({"type": "image_url", "image_url": {"url": image_url}})

            messages.append({"role": "user", "content": content})

            response = await client.chat.completions.create(
                model=settings.DEFAULT_VLM_MODEL,
                messages=messages,
                **kwargs
            )

            return response.choices[0].message.content

        # Initialize RAGAnything with LightRAG
        self.rag_instance = RAGAnything(
            config=config,
            llm_model_func=llm_model_func,
            vision_model_func=vision_model_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=settings.DEFAULT_EMBEDDING_DIM,
                max_token_size=8192,
                func=embedding_func
            ),
        )

        # Skip MinerU installation check - set flag manually to avoid subprocess PATH issues
        # This prevents check_installation() from failing when mineru is in venv but not system PATH
        self.rag_instance._parser_installation_checked = True

        # Initialize LightRAG storages
        init_result = await self.rag_instance._ensure_lightrag_initialized()
        if not init_result.get("success"):
            error_msg = init_result.get("error", "Unknown error initializing LightRAG")
            logger.error(f"Failed to initialize LightRAG: {error_msg}")
            raise RuntimeError(f"LightRAG initialization failed: {error_msg}")

        logger.info(f"Created and initialized RAGAnything instance for KB {kb_id} at {working_dir}")
        return self.rag_instance

    async def process_document(
        self,
        kb_id: int,
        file_path: str,
        filename: str,
        progress_callback: Optional[Callable[[int, str], Any]] = None
    ) -> Dict[str, Any]:
        """
        Process document and extract entities for knowledge graph

        Args:
            kb_id: Knowledge base ID
            file_path: Path to uploaded document
            filename: Original filename
            progress_callback: Optional callback for progress updates (progress%, status)

        Returns:
            Processing results with entity and relation counts
        """
        logger.info(f"Processing document {filename} for KB {kb_id}")

        try:
            # Get RAGAnything instance
            if progress_callback:
                await progress_callback(15, "Initializing RAG engine...")
            rag = await self._get_or_create_rag_instance(kb_id)

            # Process document with RAGAnything
            # This will:
            # 1. Parse the document using MinerU/Docling
            # 2. Extract text, images, tables, equations
            # 3. Use LLM to extract entities and relations
            # 4. Build knowledge graph in LightRAG's internal storage
            if progress_callback:
                await progress_callback(25, "Parsing document...")
            logger.info(f"Processing document {filename} with RAGAnything...")
            logger.info(f"RAG instance: {rag}")
            logger.info(f"RAG lightrag: {rag.lightrag}")
            logger.info(f"RAG lightrag type: {type(rag.lightrag)}")

            await rag.process_document_complete(file_path)

            if progress_callback:
                await progress_callback(70, "Extracting knowledge graph...")

            # Extract entities and relations from LightRAG's graph storage
            entities, relations = await self._extract_graph_data(rag, kb_id)

            if progress_callback:
                await progress_callback(85, "Storing in graph database...")

            # Store in Neo4j for visualization
            if entities or relations:
                logger.info(f"Storing {len(entities)} entities and {len(relations)} relations in Neo4j...")
                await self.graph_service.store_entities(kb_id, entities, relations)

            if progress_callback:
                await progress_callback(100, "Processing completed successfully")

            logger.info(f"Document {filename} processed successfully")

            return {
                "success": True,
                "entity_count": len(entities),
                "relation_count": len(relations),
                "message": f"Processed {filename}: extracted {len(entities)} entities and {len(relations)} relations"
            }

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Error processing document {filename}: {e}")
            logger.error(f"Full traceback:\n{error_trace}")
            return {
                "success": False,
                "entity_count": 0,
                "relation_count": 0,
                "message": f"Error processing {filename}: {str(e)}\nTraceback: {error_trace}"
            }

    async def _extract_graph_data(
        self,
        rag: RAGAnything,
        kb_id: int
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract entities and relations from LightRAG's graph storage

        Args:
            rag: RAGAnything instance
            kb_id: Knowledge base ID

        Returns:
            Tuple of (entities, relations)
        """
        entities = []
        relations = []

        try:
            # Access LightRAG's graph storage
            if not hasattr(rag, 'lightrag') or rag.lightrag is None:
                logger.warning("RAGAnything has no LightRAG instance")
                return entities, relations

            lightrag = rag.lightrag

            # Get graph storage
            if not hasattr(lightrag, 'chunk_entity_relation_graph'):
                logger.warning("LightRAG has no graph storage")
                return entities, relations

            graph_storage = lightrag.chunk_entity_relation_graph

            # Extract all nodes (entities)
            if hasattr(graph_storage, 'get_all_nodes'):
                nodes = await graph_storage.get_all_nodes()
                for node_id, node_data in nodes.items():
                    entities.append({
                        "name": node_data.get("entity_name", node_id),
                        "type": node_data.get("entity_type", "unknown"),
                        "description": node_data.get("description", ""),
                    })

            # Extract all edges (relations)
            if hasattr(graph_storage, 'get_all_edges'):
                edges = await graph_storage.get_all_edges()
                for edge_id, edge_data in edges.items():
                    relations.append({
                        "source": edge_data.get("src_id", ""),
                        "target": edge_data.get("tgt_id", ""),
                        "type": edge_data.get("relation_type", "RELATED"),
                        "weight": edge_data.get("weight", 1.0),
                    })

            logger.info(f"Extracted {len(entities)} entities and {len(relations)} relations from LightRAG")

        except Exception as e:
            logger.error(f"Error extracting graph data: {e}", exc_info=True)

        return entities, relations

    async def query_knowledge_base(
        self,
        kb_id: int,
        query: str,
        mode: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        Query knowledge base using RAGAnything

        Args:
            kb_id: Knowledge base ID
            query: Query text
            mode: Query mode (naive/local/global/hybrid)

        Returns:
            Query results
        """
        try:
            rag = await self._get_or_create_rag_instance(kb_id)

            # Query using RAGAnything
            result = await rag.query(query, param=QueryParam(mode=mode))

            return {
                "success": True,
                "result": result,
                "message": "Query completed successfully"
            }

        except Exception as e:
            logger.error(f"Error querying KB {kb_id}: {e}", exc_info=True)
            return {
                "success": False,
                "result": None,
                "message": f"Query failed: {str(e)}"
            }

    async def close(self):
        """Cleanup resources"""
        if self.rag_instance:
            self.rag_instance.close()
        await self.graph_service.close()
