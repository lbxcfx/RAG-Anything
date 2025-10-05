"""
清理Neo4j中的孤立实体

这个脚本会:
1. 显示所有知识库中的实体和关系数量
2. 清理所有没有关系的孤立实体
3. 清理所有file_path为空的实体和关系
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.graph_service import GraphService
from app.core.config import settings

async def main():
    print("=== Neo4j 数据清理工具 ===\n")

    graph_service = GraphService()

    if not graph_service.driver:
        print("❌ 无法连接到 Neo4j")
        return

    try:
        async with graph_service.driver.session() as session:
            # 1. 统计所有知识库的数据
            print("📊 当前数据统计:")
            result = await session.run(
                """
                MATCH (e:Entity)
                RETURN e.kb_id as kb_id, count(e) as entity_count
                ORDER BY kb_id
                """
            )
            kb_stats = {}
            async for record in result:
                kb_id = record["kb_id"]
                entity_count = record["entity_count"]
                kb_stats[kb_id] = {"entities": entity_count}
                print(f"  知识库 {kb_id}: {entity_count} 个实体")

            # 统计关系数量
            for kb_id in kb_stats.keys():
                result = await session.run(
                    """
                    MATCH (:Entity {kb_id: $kb_id})-[r]->(:Entity {kb_id: $kb_id})
                    RETURN count(r) as relation_count
                    """,
                    kb_id=kb_id
                )
                record = await result.single()
                relation_count = record["relation_count"] if record else 0
                kb_stats[kb_id]["relations"] = relation_count
                print(f"  知识库 {kb_id}: {relation_count} 个关系")

            print()

            # 2. 检查孤立实体 (没有任何关系的实体)
            print("🔍 检查孤立实体...")
            result = await session.run(
                """
                MATCH (e:Entity)
                WHERE NOT (e)--()
                RETURN e.kb_id as kb_id, e.name as name, e.file_path as file_path
                """
            )
            orphaned_entities = []
            async for record in result:
                orphaned_entities.append({
                    "kb_id": record["kb_id"],
                    "name": record["name"],
                    "file_path": record["file_path"]
                })

            if orphaned_entities:
                print(f"  发现 {len(orphaned_entities)} 个孤立实体:")
                for entity in orphaned_entities[:10]:  # 只显示前10个
                    file_path = entity["file_path"] or "(无file_path)"
                    print(f"    - KB{entity['kb_id']}: {entity['name']} [{file_path}]")
                if len(orphaned_entities) > 10:
                    print(f"    ... 还有 {len(orphaned_entities) - 10} 个")
            else:
                print("  ✓ 没有发现孤立实体")

            print()

            # 3. 检查缺少file_path的实体
            print("🔍 检查缺少file_path的实体...")
            result = await session.run(
                """
                MATCH (e:Entity)
                WHERE e.file_path IS NULL OR e.file_path = ''
                RETURN e.kb_id as kb_id, count(e) as count
                """
            )
            missing_path_count = {}
            async for record in result:
                kb_id = record["kb_id"]
                count = record["count"]
                missing_path_count[kb_id] = count
                if count > 0:
                    print(f"  知识库 {kb_id}: {count} 个实体缺少file_path")

            if not missing_path_count:
                print("  ✓ 所有实体都有file_path")

            print()

            # 4. 询问是否清理
            if orphaned_entities:
                response = input(f"是否删除 {len(orphaned_entities)} 个孤立实体? (y/N): ")
                if response.lower() == 'y':
                    await session.run(
                        """
                        MATCH (e:Entity)
                        WHERE NOT (e)--()
                        DELETE e
                        """
                    )
                    print(f"✅ 已删除 {len(orphaned_entities)} 个孤立实体")
                else:
                    print("⏭️  跳过删除孤立实体")

            # 5. 最终统计
            print("\n📊 清理后的数据统计:")
            for kb_id in kb_stats.keys():
                result = await session.run(
                    """
                    MATCH (e:Entity {kb_id: $kb_id})
                    RETURN count(e) as entity_count
                    """,
                    kb_id=kb_id
                )
                record = await result.single()
                entity_count = record["entity_count"] if record else 0

                result = await session.run(
                    """
                    MATCH (:Entity {kb_id: $kb_id})-[r]->(:Entity {kb_id: $kb_id})
                    RETURN count(r) as relation_count
                    """,
                    kb_id=kb_id
                )
                record = await result.single()
                relation_count = record["relation_count"] if record else 0

                print(f"  知识库 {kb_id}: {entity_count} 个实体, {relation_count} 个关系")

    finally:
        await graph_service.close()
        print("\n✅ 完成")

if __name__ == "__main__":
    asyncio.run(main())
