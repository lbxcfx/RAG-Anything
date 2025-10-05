"""
LightRAG存储清理服务
负责清理LightRAG向量存储中的实体和关系数据
"""

import os
import shutil
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class LightRAGCleanupService:
    """LightRAG存储清理服务"""
    
    def __init__(self):
        """初始化清理服务"""
        self.vector_dir = Path(settings.VECTOR_DIR)
        logger.info(f"LightRAGCleanupService initialized with vector dir: {self.vector_dir}")
    
    def get_kb_directory(self, kb_id: int) -> Path:
        """获取knowledge base目录路径"""
        return self.vector_dir / f"kb_{kb_id}"
    
    def get_kb_directories(self) -> List[Path]:
        """获取所有knowledge base目录"""
        if not self.vector_dir.exists():
            return []
        
        kb_dirs = []
        for item in self.vector_dir.iterdir():
            if item.is_dir() and item.name.startswith("kb_"):
                kb_dirs.append(item)
        
        return kb_dirs
    
    def delete_document_from_lightrag(self, kb_id: int, document_path: str) -> Dict[str, int]:
        """
        从LightRAG存储中删除特定文档的实体和关系
        
        Args:
            kb_id: Knowledge base ID
            document_path: 文档路径
            
        Returns:
            删除统计信息
        """
        kb_dir = self.get_kb_directory(kb_id)
        if not kb_dir.exists():
            logger.warning(f"Knowledge base directory not found: {kb_dir}")
            return {"entities_deleted": 0, "relations_deleted": 0, "files_deleted": 0}
        
        logger.info(f"Deleting document from LightRAG: {document_path}")
        logger.info(f"Knowledge base directory: {kb_dir}")
        
        # 提取文件名用于匹配
        filename = os.path.basename(document_path)
        
        deleted_stats = {
            "entities_deleted": 0,
            "relations_deleted": 0,
            "files_deleted": 0
        }
        
        try:
            # 处理实体文件
            entity_files = list(kb_dir.glob("*entity*.json"))
            for entity_file in entity_files:
                deleted_count = self._clean_entities_file(entity_file, document_path, filename)
                deleted_stats["entities_deleted"] += deleted_count
                if deleted_count > 0:
                    logger.info(f"Deleted {deleted_count} entities from {entity_file.name}")
            
            # 处理关系文件
            relation_files = list(kb_dir.glob("*relation*.json"))
            for relation_file in relation_files:
                deleted_count = self._clean_relations_file(relation_file, document_path, filename)
                deleted_stats["relations_deleted"] += deleted_count
                if deleted_count > 0:
                    logger.info(f"Deleted {deleted_count} relations from {relation_file.name}")
            
            # 检查是否有空文件需要删除
            for file_path in kb_dir.glob("*.json"):
                if file_path.stat().st_size == 0:
                    file_path.unlink()
                    deleted_stats["files_deleted"] += 1
                    logger.info(f"Deleted empty file: {file_path.name}")
            
            logger.info(f"✓ LightRAG cleanup completed for {document_path}: "
                       f"{deleted_stats['entities_deleted']} entities, "
                       f"{deleted_stats['relations_deleted']} relations, "
                       f"{deleted_stats['files_deleted']} files removed")
            
        except Exception as e:
            logger.error(f"Error cleaning LightRAG storage for document {document_path}: {e}")
            raise
        
        return deleted_stats
    
    def _clean_entities_file(self, file_path: Path, document_path: str, filename: str) -> int:
        """清理实体文件中的特定文档数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            original_count = len(data)
            
            # 过滤掉与文档相关的实体
            filtered_data = []
            for item in data:
                # 检查实体是否与文档相关
                if self._is_document_related(item, document_path, filename):
                    continue
                filtered_data.append(item)
            
            deleted_count = original_count - len(filtered_data)
            
            # 如果数据有变化，写回文件
            if deleted_count > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(filtered_data, f, ensure_ascii=False, indent=2)
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning entities file {file_path}: {e}")
            return 0
    
    def _clean_relations_file(self, file_path: Path, document_path: str, filename: str) -> int:
        """清理关系文件中的特定文档数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            original_count = len(data)
            
            # 过滤掉与文档相关的关系
            filtered_data = []
            for item in data:
                # 检查关系是否与文档相关
                if self._is_document_related(item, document_path, filename):
                    continue
                filtered_data.append(item)
            
            deleted_count = original_count - len(filtered_data)
            
            # 如果数据有变化，写回文件
            if deleted_count > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(filtered_data, f, ensure_ascii=False, indent=2)
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning relations file {file_path}: {e}")
            return 0
    
    def _is_document_related(self, item: Dict[str, Any], document_path: str, filename: str) -> bool:
        """检查数据项是否与特定文档相关"""
        # 检查各种可能的文档标识字段
        doc_fields = ['file_path', 'source_file', 'document_path', 'filename', 'source']
        
        for field in doc_fields:
            if field in item:
                value = item[field]
                if isinstance(value, str):
                    # 精确匹配或文件名匹配
                    if value == document_path or value == filename or value.endswith(filename):
                        return True
        
        # 检查描述中是否包含文件名
        if 'description' in item and filename in str(item['description']):
            return True
        
        return False
    
    def delete_kb_storage(self, kb_id: int) -> bool:
        """
        删除整个knowledge base的存储目录
        
        Args:
            kb_id: Knowledge base ID
            
        Returns:
            是否成功删除
        """
        kb_dir = self.get_kb_directory(kb_id)
        
        if not kb_dir.exists():
            logger.warning(f"Knowledge base directory not found: {kb_dir}")
            return True
        
        try:
            shutil.rmtree(kb_dir)
            logger.info(f"✓ Deleted knowledge base storage directory: {kb_dir}")
            return True
        except Exception as e:
            logger.error(f"Error deleting knowledge base storage {kb_dir}: {e}")
            return False
    
    def cleanup_orphaned_storage(self, active_kb_ids: List[str]) -> Dict[str, int]:
        """
        清理孤立的存储目录
        
        Args:
            active_kb_ids: 活跃的knowledge base ID列表
            
        Returns:
            清理统计信息
        """
        logger.info("Starting orphaned storage cleanup...")
        
        kb_dirs = self.get_kb_directories()
        if not kb_dirs:
            logger.info("No knowledge base directories found")
            return {"orphaned_dirs": 0, "total_size": 0}
        
        orphaned_dirs = []
        total_size = 0
        
        for kb_dir in kb_dirs:
            kb_id = kb_dir.name.replace("kb_", "")
            if kb_id not in active_kb_ids:
                orphaned_dirs.append(kb_dir)
                # 计算目录大小
                try:
                    dir_size = sum(f.stat().st_size for f in kb_dir.rglob('*') if f.is_file())
                    total_size += dir_size
                except Exception as e:
                    logger.warning(f"Error calculating size for {kb_dir}: {e}")
        
        if not orphaned_dirs:
            logger.info("No orphaned directories found")
            return {"orphaned_dirs": 0, "total_size": 0}
        
        logger.info(f"Found {len(orphaned_dirs)} orphaned directories:")
        for orphaned_dir in orphaned_dirs:
            logger.info(f"  - {orphaned_dir.name}")
        
        # 删除孤立的目录
        deleted_count = 0
        for orphaned_dir in orphaned_dirs:
            try:
                shutil.rmtree(orphaned_dir)
                logger.info(f"✓ Deleted orphaned directory: {orphaned_dir.name}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting orphaned directory {orphaned_dir}: {e}")
        
        logger.info(f"✓ Orphaned storage cleanup completed: {deleted_count} directories removed")
        return {"orphaned_dirs": deleted_count, "total_size": total_size}
    
    def get_storage_stats(self, kb_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Args:
            kb_id: 特定knowledge base ID，None表示所有
            
        Returns:
            存储统计信息
        """
        stats = {
            "total_kb_dirs": 0,
            "total_size": 0,
            "kb_details": {}
        }
        
        if kb_id is not None:
            kb_dirs = [self.get_kb_directory(kb_id)]
        else:
            kb_dirs = self.get_kb_directories()
        
        stats["total_kb_dirs"] = len(kb_dirs)
        
        for kb_dir in kb_dirs:
            if not kb_dir.exists():
                continue
            
            kb_id_str = kb_dir.name.replace("kb_", "")
            kb_stats = {
                "size": 0,
                "file_count": 0,
                "entity_files": 0,
                "relation_files": 0
            }
            
            try:
                # 计算目录大小和文件数量
                for file_path in kb_dir.rglob('*'):
                    if file_path.is_file():
                        kb_stats["size"] += file_path.stat().st_size
                        kb_stats["file_count"] += 1
                        
                        # 统计特定类型的文件
                        if 'entity' in file_path.name.lower():
                            kb_stats["entity_files"] += 1
                        elif 'relation' in file_path.name.lower():
                            kb_stats["relation_files"] += 1
                
                stats["total_size"] += kb_stats["size"]
                stats["kb_details"][kb_id_str] = kb_stats
                
            except Exception as e:
                logger.warning(f"Error getting stats for {kb_dir}: {e}")
        
        return stats


