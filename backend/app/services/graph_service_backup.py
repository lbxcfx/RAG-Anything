"""Graph database service - Development stub for Neo4j"""
from typing import List, Dict, Any, Optional


class GraphService:
    """Neo4j graph database service stub (Neo4j not installed in dev mode)"""

    def __init__(self):
        self.driver = None
        print("[DEV MODE] GraphService initialized with stub implementation")

    async def close(self):
        """Close database connection (stub)"""
        print("[DEV MODE] GraphService.close() - stub implementation")

    async def store_entities(
        self, kb_id: int, entities: List[Dict[str, Any]], relations: List[Dict[str, Any]]
    ):
        """
        Store entities and relations in Neo4j (stub)

        Args:
            kb_id: Knowledge base ID
            entities: List of entities
            relations: List of relations
        """
        print(f"[DEV MODE] GraphService.store_entities() - would store {len(entities)} entities and {len(relations)} relations for KB {kb_id}")

    async def query_graph(
        self, kb_id: int, filters: Optional[Dict[str, Any]] = None, limit: int = 100
    ) -> Dict[str, Any]:
        """
        Query knowledge graph (stub)

        Args:
            kb_id: Knowledge base ID
            filters: Query filters
            limit: Maximum number of results

        Returns:
            Graph data with entities and relations
        """
        print(f"[DEV MODE] GraphService.query_graph() - stub implementation for KB {kb_id}")
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

    async def get_graph_stats(self, kb_id: int) -> Dict[str, int]:
        """Get graph statistics (stub)"""
        print(f"[DEV MODE] GraphService.get_graph_stats() - stub implementation for KB {kb_id}")
        return {"entity_count": 3, "relation_count": 2}

    async def delete_kb_graph(self, kb_id: int):
        """Delete all graph data for a knowledge base (stub)"""
        print(f"[DEV MODE] GraphService.delete_kb_graph() - would delete graph data for KB {kb_id}")
