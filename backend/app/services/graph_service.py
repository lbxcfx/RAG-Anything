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
        try:
            self.driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URL,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            logger.info(f"GraphService initialized with Neo4j at {settings.NEO4J_URL}")
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}. Running in stub mode.")
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
                    SET e.type = $type, e.description = $description
                    """,
                    name=entity["name"],
                    kb_id=kb_id,
                    type=entity.get("type", "unknown"),
                    description=entity.get("description", "")
                )

            # Create relations
            for relation in relations:
                await session.run(
                    """
                    MATCH (source:Entity {name: $source, kb_id: $kb_id})
                    MATCH (target:Entity {name: $target, kb_id: $kb_id})
                    MERGE (source)-[r:RELATES_TO {type: $type}]->(target)
                    SET r.weight = $weight
                    """,
                    source=relation["source"],
                    target=relation["target"],
                    kb_id=kb_id,
                    type=relation.get("type", "RELATED"),
                    weight=relation.get("weight", 1.0)
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

            # Get relations
            relation_result = await session.run(
                """
                MATCH (source:Entity {kb_id: $kb_id})-[r:RELATES_TO]->(target:Entity {kb_id: $kb_id})
                RETURN source.name AS source, target.name AS target, r.type AS type, r.weight AS weight
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
                    "type": record["type"],
                    "weight": record["weight"]
                })

        return {
            "entities": entities,
            "relations": relations,
        }

    async def get_graph_stats(self, kb_id: int) -> Dict[str, int]:
        """Get graph statistics"""
        if not self.driver:
            logger.warning(f"Neo4j not available. Returning stub stats for KB {kb_id}")
            return {"entity_count": 0, "relation_count": 0}

        async with self.driver.session() as session:
            # Count entities
            entity_count_result = await session.run(
                "MATCH (e:Entity {kb_id: $kb_id}) RETURN count(e) AS count",
                kb_id=kb_id
            )
            entity_count_record = await entity_count_result.single()
            entity_count = entity_count_record["count"] if entity_count_record else 0

            # Count relations
            relation_count_result = await session.run(
                "MATCH (:Entity {kb_id: $kb_id})-[r:RELATES_TO]->(:Entity {kb_id: $kb_id}) RETURN count(r) AS count",
                kb_id=kb_id
            )
            relation_count_record = await relation_count_result.single()
            relation_count = relation_count_record["count"] if relation_count_record else 0

        return {
            "entity_count": entity_count,
            "relation_count": relation_count
        }

    async def delete_kb_graph(self, kb_id: int):
        """Delete all graph data for a knowledge base"""
        if not self.driver:
            logger.warning(f"Neo4j not available. Would delete graph data for KB {kb_id}")
            return

        async with self.driver.session() as session:
            await session.run(
                "MATCH (e:Entity {kb_id: $kb_id}) DETACH DELETE e",
                kb_id=kb_id
            )

        logger.info(f"Deleted all graph data for KB {kb_id}")
