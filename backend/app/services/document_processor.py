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
import hashlib

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

    async def _get_or_create_rag_instance(
        self,
        kb_id: int,
        model_configs: Optional[Dict[str, Dict[str, str]]] = None
    ) -> RAGAnything:
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

        # Get model configurations (use config or fallback to defaults)
        llm_config = model_configs.get("llm", {}) if model_configs else {}
        vlm_config = model_configs.get("vlm", {}) if model_configs else {}
        embedding_config = model_configs.get("embedding", {}) if model_configs else {}

        # LLM settings
        llm_model_name = llm_config.get("model_name", settings.DEFAULT_LLM_MODEL)
        llm_api_key = llm_config.get("api_key") or settings.OPENAI_API_KEY or settings.DASHSCOPE_API_KEY
        llm_base_url = llm_config.get("api_base_url") or (
            settings.OPENAI_BASE_URL if settings.OPENAI_API_KEY else settings.DASHSCOPE_BASE_URL
        )

        # VLM settings
        vlm_model_name = vlm_config.get("model_name", settings.DEFAULT_VLM_MODEL)
        vlm_api_key = vlm_config.get("api_key") or settings.OPENAI_API_KEY or settings.DASHSCOPE_API_KEY
        vlm_base_url = vlm_config.get("api_base_url") or (
            settings.OPENAI_BASE_URL if settings.OPENAI_API_KEY else settings.DASHSCOPE_BASE_URL
        )

        # Embedding settings
        # If no embedding model is configured, fallback to LLM settings
        embedding_model_name = embedding_config.get("model_name", settings.DEFAULT_EMBEDDING_MODEL)
        embedding_api_key = (
            embedding_config.get("api_key") or
            llm_api_key or  # Fallback to LLM API key
            settings.OPENAI_API_KEY or
            settings.DASHSCOPE_API_KEY
        )
        embedding_base_url = (
            embedding_config.get("api_base_url") or
            llm_base_url or  # Fallback to LLM base URL
            (settings.OPENAI_BASE_URL if settings.OPENAI_API_KEY else settings.DASHSCOPE_BASE_URL)
        )

        logger.info(f"Configuring models - LLM: {llm_model_name}, VLM: {vlm_model_name}, Embedding: {embedding_model_name}")

        # Create embedding function
        async def embedding_func(texts: List[str]) -> List[List[float]]:
            """Embedding function supporting both OpenAI and DashScope APIs"""
            import openai

            client = openai.AsyncOpenAI(
                api_key=embedding_api_key,
                base_url=embedding_base_url,
            )

            # Check if using DashScope API
            is_dashscope = "dashscope" in embedding_base_url.lower()
            
            if is_dashscope:
                # DashScope embedding API call
                response = await client.embeddings.create(
                    model=embedding_model_name,
                    input=texts,
                    encoding_format="float"
                )
            else:
                # OpenAI embedding API call
                response = await client.embeddings.create(
                    model=embedding_model_name,
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
                api_key=llm_api_key,
                base_url=llm_base_url,
            )

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.extend(history_messages)
            messages.append({"role": "user", "content": prompt})

            # Filter out unsupported parameters (hashing_kv is used by LightRAG internally)
            supported_params = ['temperature', 'top_p', 'max_tokens', 'frequency_penalty', 
                              'presence_penalty', 'stop', 'n', 'stream', 'logit_bias', 'user']
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_params}

            response = await client.chat.completions.create(
                model=llm_model_name,
                messages=messages,
                **filtered_kwargs
            )

            return response.choices[0].message.content

        # Create vision model function for multimodal analysis
        async def vision_model_func(
            prompt, image_url=None, system_prompt=None, **kwargs
        ) -> str:
            """Vision model function using OpenAI API"""
            import openai

            client = openai.AsyncOpenAI(
                api_key=vlm_api_key,
                base_url=vlm_base_url,
            )

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            content = [{"type": "text", "text": prompt}]
            if image_url:
                content.append({"type": "image_url", "image_url": {"url": image_url}})

            messages.append({"role": "user", "content": content})

            response = await client.chat.completions.create(
                model=vlm_model_name,
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

        # Configure Chinese language for entity extraction IMMEDIATELY after LightRAG initialization
        self._configure_chinese_language()
        
        # Verify configuration was applied
        self._verify_chinese_configuration()

        logger.info(f"Created and initialized RAGAnything instance for KB {kb_id} at {working_dir}")
        return self.rag_instance

    def _configure_chinese_language(self):
        """Configure LightRAG to use Chinese language for entity extraction with optimized prompts"""
        try:
            import lightrag
            
            # Method 1: Try to set language via addon_params
            if hasattr(self, 'rag_instance') and self.rag_instance and hasattr(self.rag_instance, 'lightrag'):
                if hasattr(self.rag_instance.lightrag, 'addon_params'):
                    self.rag_instance.lightrag.addon_params['language'] = 'Chinese'
                    logger.info("✓ Configured Chinese language via addon_params")
            
            # Method 2: Create optimized Chinese prompts for better entity extraction
            self._create_optimized_chinese_prompts()
            
            logger.info("✓ Configured Chinese language with optimized prompts")
            logger.info("✓ Entity extraction will now use Chinese language by default")
            
        except Exception as e:
            logger.warning(f"⚠ Failed to configure Chinese language: {e}")
            logger.warning("⚠ Entity extraction may still use English")

    def _create_optimized_chinese_prompts(self):
        """Create optimized Chinese prompts for better entity and relation extraction"""
        import lightrag
        
        # Enhanced Chinese system prompt for better entity extraction
        chinese_system_prompt = """---角色---
您是一位专业的知识图谱专家，负责从各种类型的中文文档中提取实体和关系。

---指令---
1.  **实体提取与输出：**
    *   **识别：** 识别输入文本中明确定义且有意义的实体，包括：
        - 人名、机构名称、地理位置
        - 专业术语、概念、理论
        - 时间、数量、测量单位
        - 工具、方法、技术
        - 事件、过程、状态
        - 抽象概念、原则、规则
    *   **实体详情：** 对于每个识别的实体，提取以下信息：
        *   `entity_name`: 实体的名称。如果是中文实体，保持原始中文名称。确保在整个提取过程中**命名一致**。
        *   `entity_type`: 使用以下类型之一对实体进行分类：`{entity_types}`。如果提供的实体类型都不适用，不要添加新的实体类型，将其分类为`Other`。
        *   `entity_description`: 基于输入文本中*仅*存在的信息，提供实体属性和活动的简洁而全面的描述。
    *   **输出格式 - 实体：** 为每个实体输出总共4个字段，用`{tuple_delimiter}`分隔，在一行上。第一个字段*必须*是字面字符串`entity`。
        *   格式：`entity{tuple_delimiter}entity_name{tuple_delimiter}entity_type{tuple_delimiter}entity_description`

2.  **关系提取与输出：**
    *   **识别：** 识别先前提取的实体之间直接、明确陈述且有意义的关系，包括：
        - 因果关系：A导致B、A引起B
        - 包含关系：A包含B、A属于B
        - 时间关系：A在B之前、A在B之后
        - 空间关系：A位于B、A在B中
        - 功能关系：A用于B、A作用于B
        - 比较关系：A优于B、A与B相似
        - 从属关系：A属于B、A隶属于B
        - 协作关系：A与B合作、A协助B
    *   **N元关系分解：** 如果单个语句描述涉及两个以上实体的关系（N元关系），将其分解为多个二元（两实体）关系对进行单独描述。
        *   **示例：** 对于"张三、李四和王五合作完成项目X"，提取二元关系如"张三与项目X合作"、"李四与项目X合作"和"王五与项目X合作"，或"张三与李四合作"，基于最合理的二元解释。
    *   **关系详情：** 对于每个二元关系，提取以下字段：
        *   `source_entity`: 源实体的名称。确保与实体提取**命名一致**。如果是中文实体，保持原始中文名称。
        *   `target_entity`: 目标实体的名称。确保与实体提取**命名一致**。如果是中文实体，保持原始中文名称。
        *   `relationship_keywords`: 总结关系总体性质、概念或主题的一个或多个高级关键词。此字段内的多个关键词必须用逗号`,`分隔。**不要在此字段内使用`{tuple_delimiter}`来分隔多个关键词。**
        *   `relationship_description`: 源实体和目标实体之间关系性质的简洁解释，提供它们连接的清晰理由。
    *   **输出格式 - 关系：** 为每个关系输出总共5个字段，用`{tuple_delimiter}`分隔，在一行上。第一个字段*必须*是字面字符串`relation`。
        *   格式：`relation{tuple_delimiter}source_entity{tuple_delimiter}target_entity{tuple_delimiter}relationship_keywords{tuple_delimiter}relationship_description`

3.  **分隔符使用协议：**
    *   `{tuple_delimiter}`是一个完整的原子标记，**不得填充内容**。它严格用作字段分隔符。
    *   **错误示例：** `entity{tuple_delimiter}北京<|location|>北京是中国的首都。`
    *   **正确示例：** `entity{tuple_delimiter}北京{tuple_delimiter}location{tuple_delimiter}北京是中国的首都。`

4.  **关系方向与重复：**
    *   除非明确说明，否则将所有关系视为**无向**。交换无向关系的源实体和目标实体不构成新关系。
    *   避免输出重复关系。

5.  **输出顺序与优先级：**
    *   首先输出所有提取的实体，然后输出所有提取的关系。
    *   在关系列表中，优先输出对输入文本核心意义**最重要**的关系。

6.  **上下文与客观性：**
    *   确保所有实体名称和描述都用**第三人称**书写。
    *   明确命名主语或宾语；**避免使用代词**，如`本文`、`本论文`、`我们公司`、`我`、`你`和`他/她`。

7.  **语言与专有名词：**
    *   整个输出（实体名称、关键词和描述）必须用中文书写。
    *   专有名词（如人名、地名、组织名称）应保持其原始语言，如果没有适当、广泛接受的翻译或会造成歧义。
    *   专业术语应使用标准的中文术语，保持专业性和准确性。

8.  **通用文档处理：**
    *   适用于各种类型的文档，包括学术论文、技术文档、商业报告、新闻文章等。
    *   根据文档内容自动调整实体和关系的识别重点。
    *   保持提取结果的客观性和准确性。

9.  **完成信号：** 只有在所有实体和关系按照所有标准完全提取和输出后，才输出字面字符串`{completion_delimiter}`。

---示例---
{examples}

---要处理的真实数据---
<输入>
实体类型：[{entity_types}]
文本：
```
{input_text}
```
</输入>"""

        # Enhanced Chinese user prompt
        chinese_user_prompt = """---任务---
从要处理的输入文本中提取实体和关系。

---指令---
1.  **严格遵循格式：** 严格遵循实体和关系列表的所有格式要求，包括输出顺序、字段分隔符和专有名词处理，如系统提示中指定的。
2.  **仅输出内容：** 仅输出提取的实体和关系列表。不要在列表前后包含任何介绍性或结论性评论、解释或附加文本。
3.  **完成信号：** 在所有相关实体和关系提取并呈现后，输出`{completion_delimiter}`作为最后一行。
4.  **输出语言：** 确保输出语言是中文。专有名词（如人名、地名、组织名称）必须保持其原始语言，不要翻译。

<输出>"""

        # Update the prompts
        lightrag.prompt.PROMPTS['entity_extraction_system_prompt'] = chinese_system_prompt
        lightrag.prompt.PROMPTS['entity_extraction_user_prompt'] = chinese_user_prompt
        
        logger.info("✓ Created optimized Chinese prompts for better entity extraction")

    def _verify_chinese_configuration(self):
        """Verify that Chinese configuration was applied correctly"""
        try:
            import lightrag
            
            # Check if prompts are correctly configured
            prompts = lightrag.prompt.PROMPTS
            
            system_prompt = prompts.get('entity_extraction_system_prompt', '')
            user_prompt = prompts.get('entity_extraction_user_prompt', '')
            
            # Verify Chinese configuration
            has_chinese_system = '专业的知识图谱专家' in system_prompt
            has_chinese_user = '中文' in user_prompt
            no_language_placeholder = '{language}' not in system_prompt and '{language}' not in user_prompt
            
            if has_chinese_system and has_chinese_user and no_language_placeholder:
                logger.info("✅ Chinese language configuration verified successfully")
                logger.info(f"   System prompt length: {len(system_prompt)} characters")
                logger.info(f"   User prompt length: {len(user_prompt)} characters")
                return True
            else:
                logger.error("❌ Chinese language configuration verification failed!")
                logger.error(f"   Has Chinese system prompt: {has_chinese_system}")
                logger.error(f"   Has Chinese user prompt: {has_chinese_user}")
                logger.error(f"   No language placeholder: {no_language_placeholder}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to verify Chinese configuration: {e}")
            return False

    async def process_document(
        self,
        kb_id: int,
        file_path: str,
        filename: str,
        progress_callback: Optional[Callable[[int, str], Any]] = None,
        model_configs: Optional[Dict[str, Dict[str, str]]] = None
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
            rag = await self._get_or_create_rag_instance(kb_id, model_configs)

            # Process document with RAGAnything
            # This will:
            # 1. Parse the document using MinerU/Docling
            # 2. Extract text, images, tables, equations
            # 3. Use LLM to extract entities and relations
            # 4. Build knowledge graph in LightRAG's internal storage
            if progress_callback:
                await progress_callback(25, "Parsing document...")
            logger.info(f"========== Processing document {filename} with RAGAnything ==========")
            logger.info(f"RAG instance: {rag}")
            logger.info(f"RAG lightrag: {rag.lightrag}")
            logger.info(f"RAG lightrag type: {type(rag.lightrag)}")

            logger.info(f"========== Step 1: Starting document parsing ==========")
            await rag.process_document_complete(file_path)
            logger.info(f"========== Step 1 Completed: Document parsed ==========")

            # Check if LightRAG processing failed
            logger.info(f"========== Checking LightRAG document status ==========")
            doc_id = f"doc-{hashlib.md5(file_path.encode()).hexdigest()}"
            try:
                doc_status = await rag.lightrag.doc_status.get_by_id(doc_id)
                if doc_status:
                    status = doc_status.get("status", "unknown")
                    logger.info(f"  → LightRAG document status: {status}")

                    if status == "failed":
                        error_msg = f"LightRAG processing failed for {filename}"
                        logger.error(f"  ✗ {error_msg}")
                        logger.error(f"  → Document status details: {doc_status}")
                        return {
                            "success": False,
                            "entity_count": 0,
                            "relation_count": 0,
                            "message": f"{error_msg} - LightRAG returned failed status"
                        }
                    elif status != "processed":
                        logger.warning(f"  ⚠ Unexpected status: {status}")
                else:
                    logger.warning(f"  ⚠ Could not find document status for {doc_id}")
            except Exception as e:
                logger.warning(f"  ⚠ Error checking document status: {e}")

            if progress_callback:
                await progress_callback(70, "Extracting knowledge graph...")
            logger.info(f"========== Step 2: Starting knowledge graph extraction (LLM-based entity & relation extraction) ==========")

            # Extract entities and relations from LightRAG's graph storage
            # Pass file_path to tag all extracted entities and relations with their source document
            entities, relations = await self._extract_graph_data(rag, kb_id, file_path)
            logger.info(f"========== Step 2 Completed: Extracted {len(entities)} entities and {len(relations)} relations ==========")

            if progress_callback:
                await progress_callback(85, "Storing in graph database...")
            logger.info(f"========== Step 3: Storing graph data in Neo4j ==========")

            # Store in Neo4j for visualization
            if entities or relations:
                logger.info(f"Storing {len(entities)} entities and {len(relations)} relations in Neo4j...")
                await self.graph_service.store_entities(kb_id, entities, relations)
                logger.info(f"========== Step 3 Completed: Graph data stored in Neo4j ==========")
            else:
                logger.warning(f"========== Step 3 Skipped: No entities or relations to store ==========")

            if progress_callback:
                await progress_callback(100, "Processing completed successfully")

            logger.info(f"========== Document {filename} processed successfully ==========")
            logger.info(f"========== SUMMARY: {len(entities)} entities, {len(relations)} relations ==========")

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
        kb_id: int,
        file_path: str
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract entities and relations from LightRAG's graph storage

        Args:
            rag: RAGAnything instance
            kb_id: Knowledge base ID
            file_path: Source document file path (for tracking entity origins)

        Returns:
            Tuple of (entities, relations)
        """
        logger.info(f"  → Checking LightRAG graph storage for document: {file_path}...")
        entities = []
        relations = []

        try:
            # Access LightRAG's graph storage
            if not hasattr(rag, 'lightrag') or rag.lightrag is None:
                logger.warning("  ✗ RAGAnything has no LightRAG instance")
                return entities, relations
            logger.info(f"  ✓ RAGAnything has LightRAG instance")

            lightrag = rag.lightrag

            # Get graph storage
            if not hasattr(lightrag, 'chunk_entity_relation_graph'):
                logger.warning("  ✗ LightRAG has no graph storage")
                return entities, relations
            logger.info(f"  ✓ LightRAG has graph storage")

            graph_storage = lightrag.chunk_entity_relation_graph

            # Check LightRAG's entity and relation storage first
            logger.info(f"  → Checking LightRAG's full_entities storage...")
            try:
                all_entity_keys = await lightrag.full_entities.get_all()
                if all_entity_keys:
                    logger.info(f"  ✓ Found {len(all_entity_keys)} entities in full_entities storage")
                else:
                    logger.warning(f"  ⚠ full_entities storage is EMPTY - LLM extraction may not have run!")
            except Exception as e:
                logger.warning(f"  ✗ Could not check full_entities: {e}")

            logger.info(f"  → Checking LightRAG's full_relations storage...")
            try:
                all_relation_keys = await lightrag.full_relations.get_all()
                if all_relation_keys:
                    logger.info(f"  ✓ Found {len(all_relation_keys)} relations in full_relations storage")
                else:
                    logger.warning(f"  ⚠ full_relations storage is EMPTY - LLM extraction may not have run!")
            except Exception as e:
                logger.warning(f"  ✗ Could not check full_relations: {e}")

            # Extract all nodes (entities)
            logger.info(f"  → Extracting entities from graph storage...")
            if hasattr(graph_storage, 'get_all_nodes'):
                nodes = await graph_storage.get_all_nodes()
                logger.info(f"  ✓ Found {len(nodes)} nodes in graph storage")
                if len(nodes) == 0:
                    logger.warning(f"  ⚠ WARNING: Graph storage has 0 nodes! This means:")
                    logger.warning(f"      - Either LLM extraction was skipped (document cached)")
                    logger.warning(f"      - Or LLM failed to extract any entities")
                    logger.warning(f"      - Or graph storage was not updated after extraction")
                
                # Handle both dict and list return types
                if isinstance(nodes, dict):
                    nodes_items = nodes.items()
                elif isinstance(nodes, list):
                    nodes_items = enumerate(nodes)
                else:
                    logger.warning(f"  ✗ Unexpected nodes type: {type(nodes)}")
                    nodes_items = []

                for node_id, node_data in nodes_items:
                    # Skip if node_data is None or not a dict
                    if not isinstance(node_data, dict):
                        logger.debug(f"  ⚠ Skipping non-dict node: id={node_id}, type={type(node_data)}, value={node_data}")
                        continue

                    # Try to get entity name from different possible fields
                    entity_name = (
                        node_data.get("entity_id") or  # LightRAG uses entity_id
                        node_data.get("entity_name") or
                        node_data.get("name") or
                        node_data.get("label") or
                        node_data.get("id") or
                        str(node_id)
                    )
                    # Get file_path from node_data, or use the provided file_path as fallback
                    entity_file_path = node_data.get("file_path") or node_data.get("source_id") or file_path

                    entity = {
                        "name": entity_name,
                        "type": node_data.get("entity_type", node_data.get("type", "unknown")),
                        "description": node_data.get("description", ""),
                        "file_path": entity_file_path,  # Always set file_path for deletion tracking
                    }
                    entities.append(entity)
                    logger.debug(f"    - Entity: {entity['name']} ({entity['type']}) [from: {entity_file_path}]")
            else:
                logger.warning(f"  ✗ Graph storage has no get_all_nodes method")

            # Extract relations from LightRAG's graph storage (more detailed info)
            logger.info(f"  → Extracting relations from graph storage...")
            if hasattr(graph_storage, 'get_all_edges'):
                edges = await graph_storage.get_all_edges()
                logger.info(f"  ✓ Found {len(edges)} edges in graph storage")
                
                # Handle both dict and list return types
                if isinstance(edges, dict):
                    edges_items = edges.items()
                elif isinstance(edges, list):
                    edges_items = enumerate(edges)
                else:
                    logger.warning(f"  ✗ Unexpected edges type: {type(edges)}")
                    edges_items = []

                for edge_id, edge_data in edges_items:
                    # Skip if edge_data is None or not a dict
                    if not isinstance(edge_data, dict):
                        logger.debug(f"  ⚠ Skipping non-dict edge: id={edge_id}, type={type(edge_data)}, value={edge_data}")
                        continue

                    # Extract relation type from description/keywords
                    relation_type = self._infer_relation_type(
                        edge_data.get("description", ""),
                        edge_data.get("keywords", ""),
                        edge_data.get("source", ""),
                        edge_data.get("target", "")
                    )

                    # Get file_path from edge_data, or use the provided file_path as fallback
                    relation_file_path = edge_data.get("file_path") or edge_data.get("source_id") or file_path

                    relation = {
                        "source": edge_data.get("source", ""),
                        "target": edge_data.get("target", ""),
                        "type": relation_type,
                        "weight": edge_data.get("weight", 1.0),
                        "description": edge_data.get("description", ""),
                        "keywords": edge_data.get("keywords", ""),
                        "file_path": relation_file_path,  # Always set file_path for deletion tracking
                    }
                    relations.append(relation)
                    logger.debug(f"    - Relation: {relation['source']} --[{relation['type']}]--> {relation['target']} [from: {relation_file_path}]")
            else:
                logger.warning(f"  ✗ Graph storage has no get_all_edges method")
                
                # Fallback: try to extract from full_relations storage
                logger.info(f"  → Fallback: Extracting relations from full_relations storage...")
                try:
                    all_relation_keys = await lightrag.full_relations.get_all()
                    if all_relation_keys:
                        logger.info(f"  ✓ Found {len(all_relation_keys)} relations in full_relations storage")
                        
                        # Extract each relation
                        for relation_key in all_relation_keys:
                            try:
                                # Use the correct method to get data from JsonKVStorage
                                relation_data = await lightrag.full_relations.get(relation_key)
                                if relation_data and isinstance(relation_data, dict):
                                    # Extract relation pairs from the stored data
                                    relation_pairs = relation_data.get('relation_pairs', [])
                                    for pair in relation_pairs:
                                        if isinstance(pair, list) and len(pair) >= 2:
                                            relation = {
                                                "source": pair[0],
                                                "target": pair[1],
                                                "type": "RELATED",  # Default type
                                                "weight": 1.0,
                                                "file_path": file_path,  # Use provided file_path
                                            }
                                            relations.append(relation)
                                            logger.debug(f"    - Relation: {relation['source']} --[{relation['type']}]--> {relation['target']} [from: {file_path}]")
                            except Exception as e:
                                logger.warning(f"  ✗ Error extracting relation {relation_key}: {e}")
                                
                                # Fallback: try to read directly from storage file
                                try:
                                    import json
                                    import os
                                    storage_file = os.path.join(lightrag.working_dir, "kv_store_full_relations.json")
                                    if os.path.exists(storage_file):
                                        with open(storage_file, 'r', encoding='utf-8') as f:
                                            storage_data = json.load(f)
                                        
                                        if relation_key in storage_data:
                                            relation_data = storage_data[relation_key]
                                            relation_pairs = relation_data.get('relation_pairs', [])
                                            for pair in relation_pairs:
                                                if isinstance(pair, list) and len(pair) >= 2:
                                                    relation = {
                                                        "source": pair[0],
                                                        "target": pair[1],
                                                        "type": "RELATED",
                                                        "weight": 1.0,
                                                        "file_path": file_path,  # Use provided file_path
                                                    }
                                                    relations.append(relation)
                                                    logger.debug(f"    - Relation (fallback): {relation['source']} --[{relation['type']}]--> {relation['target']} [from: {file_path}]")
                                except Exception as fallback_e:
                                    logger.warning(f"  ✗ Fallback also failed: {fallback_e}")
                    else:
                        logger.warning(f"  ⚠ No relations found in full_relations storage")
                except Exception as e:
                    logger.warning(f"  ✗ Error accessing full_relations storage: {e}")

            logger.info(f"  ✓ Successfully extracted {len(entities)} entities and {len(relations)} relations from LightRAG")

        except Exception as e:
            logger.error(f"  ✗ Error extracting graph data: {e}", exc_info=True)

        return entities, relations

    def _infer_relation_type(self, description: str, keywords: str, source: str, target: str) -> str:
        """
        Infer relation type from description, keywords, and entity names
        
        Args:
            description: Relation description
            keywords: Relation keywords
            source: Source entity name
            target: Target entity name
            
        Returns:
            Inferred relation type
        """
        text = f"{description} {keywords} {source} {target}".lower()
        
        # Time-related relations
        if any(word in text for word in ['time', 'period', 'date', 'year', 'month', '年', '月', '时间', '期间']):
            return "TEMPORAL"
        
        # Location-related relations
        if any(word in text for word in ['location', 'place', 'address', '位置', '地点', '地址']):
            return "SPATIAL"
        
        # Part-whole relations
        if any(word in text for word in ['part', 'component', 'include', 'contain', '部分', '包含', '组成']):
            return "PART_OF"
        
        # Cause-effect relations
        if any(word in text for word in ['cause', 'effect', 'result', 'lead to', '导致', '引起', '结果']):
            return "CAUSES"
        
        # Method-application relations
        if any(word in text for word in ['method', 'technique', 'approach', '方法', '技术', '手段']):
            return "USES_METHOD"
        
        # Person-organization relations
        if any(word in text for word in ['researcher', 'author', 'team', 'organization', '研究者', '作者', '团队', '组织']):
            return "AFFILIATED_WITH"
        
        # Data-source relations
        if any(word in text for word in ['database', 'library', 'source', '数据库', '文献库', '来源']):
            return "STORED_IN"
        
        # Language relations
        if any(word in text for word in ['language', 'chinese', 'english', '语言', '中文', '英文']):
            return "WRITTEN_IN"
        
        # Criteria relations
        if any(word in text for word in ['criteria', 'condition', 'requirement', '标准', '条件', '要求']):
            return "SATISFIES"
        
        # Default relation type
        return "RELATED"

    async def query_knowledge_base(
        self,
        kb_id: int,
        query: str,
        mode: str = "hybrid",
        model_configs: Optional[Dict[str, Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Query knowledge base using RAGAnything

        Args:
            kb_id: Knowledge base ID
            query: Query text
            mode: Query mode (naive/local/global/hybrid)
            model_configs: Optional model configurations

        Returns:
            Query results
        """
        try:
            rag = await self._get_or_create_rag_instance(kb_id, model_configs)

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
