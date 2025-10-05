#!/usr/bin/env python3
"""
清理孤立的 knowledge base 目录
当文档从数据库中删除后，清理对应的 LightRAG 存储目录
"""

import os
import shutil
import sqlite3
import json
from pathlib import Path

def get_kb_directories():
    """获取所有 knowledge base 目录"""
    storage_path = Path("./storage/vectors")
    if not storage_path.exists():
        return []
    
    kb_dirs = []
    for item in storage_path.iterdir():
        if item.is_dir() and item.name.startswith("kb_"):
            kb_dirs.append(item)
    
    return kb_dirs

def get_active_kb_ids():
    """从数据库获取活跃的 knowledge base ID"""
    try:
        conn = sqlite3.connect("rag_anything_dev.db")
        cursor = conn.cursor()
        
        # 查询所有文档的 knowledge_base_id
        cursor.execute("SELECT DISTINCT knowledge_base_id FROM documents WHERE knowledge_base_id IS NOT NULL")
        active_ids = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return active_ids
    except Exception as e:
        print(f"❌ 无法从数据库获取活跃的 KB ID: {e}")
        return []

def cleanup_orphaned_kb():
    """清理孤立的 knowledge base 目录"""
    print("🔍 检查孤立的 knowledge base 目录...")
    
    # 获取所有 KB 目录
    kb_dirs = get_kb_directories()
    if not kb_dirs:
        print("✅ 没有找到 knowledge base 目录")
        return
    
    print(f"📁 找到 {len(kb_dirs)} 个 knowledge base 目录:")
    for kb_dir in kb_dirs:
        print(f"   - {kb_dir.name}")
    
    # 获取活跃的 KB ID
    active_ids = get_active_kb_ids()
    print(f"📊 数据库中有 {len(active_ids)} 个活跃的 knowledge base")
    
    # 找出孤立的目录
    orphaned_dirs = []
    for kb_dir in kb_dirs:
        kb_id = kb_dir.name.replace("kb_", "")
        if kb_id not in active_ids:
            orphaned_dirs.append(kb_dir)
    
    if not orphaned_dirs:
        print("✅ 没有找到孤立的 knowledge base 目录")
        return
    
    print(f"🗑️  找到 {len(orphaned_dirs)} 个孤立的目录:")
    for orphaned_dir in orphaned_dirs:
        print(f"   - {orphaned_dir.name}")
    
    # 确认删除
    print("\n⚠️  这些目录将被永久删除，包括其中的所有实体和关系数据！")
    confirm = input("确认删除吗？(y/N): ").strip().lower()
    
    if confirm != 'y':
        print("❌ 操作已取消")
        return
    
    # 执行删除
    deleted_count = 0
    for orphaned_dir in orphaned_dirs:
        try:
            shutil.rmtree(orphaned_dir)
            print(f"✅ 已删除: {orphaned_dir.name}")
            deleted_count += 1
        except Exception as e:
            print(f"❌ 删除失败 {orphaned_dir.name}: {e}")
    
    print(f"\n🎉 清理完成！删除了 {deleted_count} 个孤立的目录")
    print("📊 现在知识图谱中应该只包含活跃文档的实体和关系")

if __name__ == "__main__":
    cleanup_orphaned_kb()


