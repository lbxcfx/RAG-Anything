"""Real GraphService implementation with Neo4j"""
from typing import List, Dict, Any, Optional
from neo4j import AsyncGraphDatabase
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class GraphService:
    """Neo4j graph database service"""

    def __init__(self):
        """Initialize Neo4j connection"""
        logger.info(f"Initializing GraphService...")
        logger.info(f"Neo4j URL: {settings.NEO4J_URL}")
        logger.info(f"Neo4j User: {settings.NEO4J_USER}")
        logger.info(f"Neo4j Password: {settings.NEO4J_PASSWORD[:5]}..." if settings.NEO4J_PASSWORD else "None")
        try:
            self.driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URL,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            logger.info(f"GraphService initialized with Neo4j at {settings.NEO4J_URL}")
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}. Running in stub mode.")
            self.driver = None

    async def close(self):
        """Close database connection"""
        if self.driver:
            await self.driver.close()
            logger.debug("GraphService connection closed")

    async def store_entities(
        self, kb_id: int, entities: List[Dict[str, Any]], relations: List[Dict[str, Any]]
    ):
        """
        Store entities and relations in Neo4j

        Args:
            kb_id: Knowledge base ID
            entities: List of entities [{"name": str, "type": str, "description": str}, ...]
            relations: List of relations [{"source": str, "target": str, "type": str}, ...]
        """
        if not self.driver:
            logger.warning(f"Neo4j not available. Would store {len(entities)} entities and {len(relations)} relations for KB {kb_id}")
            return

        async with self.driver.session() as session:
            # Create entities
            for entity in entities:
                await session.run(
                    """
                    MERGE (e:Entity {name: $name, kb_id: $kb_id})
                    SET e.type = $type, e.description = $description, e.file_path = $file_path
                    """,
                    name=entity["name"],
                    kb_id=kb_id,
                    type=entity.get("type", "unknown"),
                    description=entity.get("description", ""),
                    file_path=entity.get("file_path", "")
                )

            # Create relations
            for relation in relations:
                relation_type = relation.get("type", "RELATED")
                # Use dynamic relationship type instead of hardcoded RELATES_TO
                await session.run(
                    f"""
                    MATCH (source:Entity {{name: $source, kb_id: $kb_id}})
                    MATCH (target:Entity {{name: $target, kb_id: $kb_id}})
                    MERGE (source)-[r:{relation_type}]->(target)
                    SET r.weight = $weight, r.description = $description, r.keywords = $keywords, r.file_path = $file_path
                    """,
                    source=relation["source"],
                    target=relation["target"],
                    kb_id=kb_id,
                    weight=relation.get("weight", 1.0),
                    description=relation.get("description", ""),
                    keywords=relation.get("keywords", ""),
                    file_path=relation.get("file_path", "")
                )

        logger.info(f"Stored {len(entities)} entities and {len(relations)} relations for KB {kb_id}")

    async def query_graph(
        self, kb_id: int, filters: Optional[Dict[str, Any]] = None, limit: int = 100
    ) -> Dict[str, Any]:
        """
        Query knowledge graph

        Args:
            kb_id: Knowledge base ID
            filters: Query filters
            limit: Maximum number of results

        Returns:
            Graph data with entities and relations
        """
        if not self.driver:
            logger.warning(f"Neo4j not available. Returning stub data for KB {kb_id}")
            return {
                "entities": [
                    {"id": "entity_1", "name": "Concept A", "type": "concept", "description": "First concept"},
                    {"id": "entity_2", "name": "Concept B", "type": "concept", "description": "Second concept"},
                    {"id": "entity_3", "name": "Concept C", "type": "concept", "description": "Third concept"},
                ],
                "relations": [
                    {"source": "entity_1", "target": "entity_2", "type": "RELATED_TO", "weight": 0.8},
                    {"source": "entity_2", "target": "entity_3", "type": "DEPENDS_ON", "weight": 0.9},
                ],
            }

        async with self.driver.session() as session:
            # Get entities
            entity_result = await session.run(
                """
                MATCH (e:Entity {kb_id: $kb_id})
                RETURN e.name AS name, e.type AS type, e.description AS description
                LIMIT $limit
                """,
                kb_id=kb_id,
                limit=limit
            )

            entities = []
            async for record in entity_result:
                entities.append({
                    "id": record["name"].replace(" ", "_"),
                    "name": record["name"],
                    "type": record["type"],
                    "description": record["description"]
                })

            # Get relations (all types, not just RELATES_TO)
            relation_result = await session.run(
                """
                MATCH (source:Entity {kb_id: $kb_id})-[r]->(target:Entity {kb_id: $kb_id})
                RETURN source.name AS source, target.name AS target, type(r) AS relation_type, 
                       r.weight AS weight, r.description AS description, r.keywords AS keywords
                LIMIT $limit
                """,
                kb_id=kb_id,
                limit=limit
            )

            relations = []
            async for record in relation_result:
                relations.append({
                    "source": record["source"].replace(" ", "_"),
                    "target": record["target"].replace(" ", "_"),
                    "type": record["relation_type"],
                    "weight": record["weight"],
                    "description": record["description"] or "",
                    "keywords": record["keywords"] or ""
                })

        return {
            "entities": entities,
            "relations": relations,
        }

    async def get_graph_stats(self, kb_id: int) -> Dict[str, int]:
        """Get graph statistics"""
        logger.info(f"Getting graph stats for KB {kb_id}")
        logger.info(f"Driver available: {self.driver is not None}")

        if not self.driver:
            logger.warning(f"Neo4j not available. Returning stub stats for KB {kb_id}")
            return {"entity_count": 0, "relation_count": 0}

        try:
            async with self.driver.session() as session:
                # Count entities
                entity_count_result = await session.run(
                    "MATCH (e:Entity {kb_id: $kb_id}) RETURN count(e) AS count",
                    kb_id=kb_id
                )
                entity_count_record = await entity_count_result.single()
                entity_count = entity_count_record["count"] if entity_count_record else 0

                # Count relations (all types, not just RELATES_TO)
                relation_count_result = await session.run(
                    "MATCH (:Entity {kb_id: $kb_id})-[r]->(:Entity {kb_id: $kb_id}) RETURN count(r) AS count",
                    kb_id=kb_id
                )
                relation_count_record = await relation_count_result.single()
                relation_count = relation_count_record["count"] if relation_count_record else 0

            logger.info(f"Graph stats for KB {kb_id}: entities={entity_count}, relations={relation_count}")
            return {
                "entity_count": entity_count,
                "relation_count": relation_count
            }
        except Exception as e:
            logger.error(f"Error getting graph stats for KB {kb_id}: {e}")
            raise

    async def delete_document_entities(self, kb_id: int, document_path: str):
        """Delete entities and relations associated with a specific document

        Note: Since LightRAG may not consistently store file_path in entities/relations,
        we use a multi-strategy approach:
        1. Try to delete by exact file_path match
        2. Try to delete by filename match (extract filename from path)
        3. Clean up orphaned entities
        """
        if not self.driver:
            logger.warning(f"Neo4j not available. Would delete entities for document {document_path}")
            return

        async with self.driver.session() as session:
            # Extract filename from path for fallback matching
            import os
            filename = os.path.basename(document_path)

            logger.info(f"Deleting entities for document: {document_path}")
            logger.info(f"  Filename: {filename}")

            # Strategy 1: Try exact path match
            result = await session.run(
                """
                MATCH (e:Entity {kb_id: $kb_id})
                WHERE e.file_path = $document_path
                RETURN count(e) as count
                """,
                kb_id=kb_id,
                document_path=document_path
            )
            exact_match_count = (await result.single())["count"] if result else 0
            logger.info(f"  Exact path matches: {exact_match_count}")

            # Strategy 2: Try filename match
            result = await session.run(
                """
                MATCH (e:Entity {kb_id: $kb_id})
                WHERE e.file_path = $filename OR e.file_path ENDS WITH $filename
                RETURN count(e) as count
                """,
                kb_id=kb_id,
                filename=filename
            )
            filename_match_count = (await result.single())["count"] if result else 0
            logger.info(f"  Filename matches: {filename_match_count}")

            # Delete relations first (by both strategies)
            result = await session.run(
                """
                MATCH (s:Entity {kb_id: $kb_id})-[r]->(t:Entity {kb_id: $kb_id})
                WHERE r.file_path = $document_path
                   OR r.file_path = $filename
                   OR r.file_path ENDS WITH $filename
                DELETE r
                RETURN count(r) as deleted_count
                """,
                kb_id=kb_id,
                document_path=document_path,
                filename=filename
            )
            deleted_relations = (await result.single())["deleted_count"] if result else 0
            logger.info(f"  Deleted {deleted_relations} relations")

            # Delete entities (by both strategies)
            result = await session.run(
                """
                MATCH (e:Entity {kb_id: $kb_id})
                WHERE e.file_path = $document_path
                   OR e.file_path = $filename
                   OR e.file_path ENDS WITH $filename
                DETACH DELETE e
                RETURN count(e) as deleted_count
                """,
                kb_id=kb_id,
                document_path=document_path,
                filename=filename
            )
            deleted_entities = (await result.single())["deleted_count"] if result else 0
            logger.info(f"  Deleted {deleted_entities} entities")

            # Clean up orphaned entities (no relations)
            result = await session.run(
                """
                MATCH (e:Entity {kb_id: $kb_id})
                WHERE NOT (e)--()
                DELETE e
                RETURN count(e) as deleted_count
                """,
                kb_id=kb_id
            )
            orphan_deleted = (await result.single())["deleted_count"] if result else 0
            if orphan_deleted > 0:
                logger.info(f"  Deleted {orphan_deleted} orphaned entities")

            total_deleted = deleted_entities + orphan_deleted
            logger.info(f"✓ Completed deletion for {document_path}: "
                       f"{total_deleted} entities, {deleted_relations} relations removed")

    async def delete_kb_graph(self, kb_id: int):
        """Delete all graph data for a knowledge base, including LightRAG cache"""
        if not self.driver:
            logger.warning(f"Neo4j not available. Would delete graph data for KB {kb_id}")
            return

        # Delete from Neo4j
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (e:Entity {kb_id: $kb_id}) DETACH DELETE e RETURN count(e) as deleted_count",
                kb_id=kb_id
            )
            record = await result.single()
            deleted_count = record["deleted_count"] if record else 0
            logger.info(f"Deleted {deleted_count} entities from Neo4j for KB {kb_id}")

        # Delete LightRAG cache files
        import os
        import shutil
        from app.core.config import settings

        vector_dir = os.path.join(settings.VECTOR_DIR, f"kb_{kb_id}")
        if os.path.exists(vector_dir):
            try:
                shutil.rmtree(vector_dir)
                logger.info(f"Deleted LightRAG cache directory: {vector_dir}")
            except Exception as e:
                logger.error(f"Error deleting LightRAG cache for KB {kb_id}: {e}")

        logger.info(f"✓ Completed deletion of all graph data for KB {kb_id}")
