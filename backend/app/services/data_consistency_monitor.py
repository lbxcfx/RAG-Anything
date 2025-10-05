"""
数据一致性监控服务
检查数据库和存储目录的同步状态
"""

import os
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from app.core.config import settings
from app.services.lightrag_cleanup_service import LightRAGCleanupService

logger = logging.getLogger(__name__)


@dataclass
class ConsistencyIssue:
    """数据一致性问题"""
    type: str  # 'orphaned_storage', 'missing_storage', 'size_mismatch'
    kb_id: str
    description: str
    severity: str  # 'low', 'medium', 'high'
    suggested_action: str


class DataConsistencyMonitor:
    """数据一致性监控服务"""
    
    def __init__(self):
        """初始化监控服务"""
        self.db_path = "rag_anything_dev.db"
        self.cleanup_service = LightRAGCleanupService()
        logger.info("DataConsistencyMonitor initialized")
    
    def check_consistency(self) -> Dict[str, Any]:
        """
        检查数据一致性
        
        Returns:
            一致性检查结果
        """
        logger.info("Starting data consistency check...")
        
        result = {
            "timestamp": self._get_timestamp(),
            "overall_status": "healthy",
            "issues": [],
            "statistics": {},
            "recommendations": []
        }
        
        try:
            # 获取数据库中的活跃knowledge base
            active_kb_ids = self._get_active_kb_ids()
            result["statistics"]["active_kb_count"] = len(active_kb_ids)
            
            # 获取存储目录中的knowledge base
            storage_kb_ids = self._get_storage_kb_ids()
            result["statistics"]["storage_kb_count"] = len(storage_kb_ids)
            
            # 检查孤立存储
            orphaned_issues = self._check_orphaned_storage(active_kb_ids, storage_kb_ids)
            result["issues"].extend(orphaned_issues)
            
            # 检查缺失存储
            missing_issues = self._check_missing_storage(active_kb_ids, storage_kb_ids)
            result["issues"].extend(missing_issues)
            
            # 检查存储大小
            size_issues = self._check_storage_sizes(active_kb_ids)
            result["issues"].extend(size_issues)
            
            # 检查文档数量一致性
            doc_issues = self._check_document_consistency(active_kb_ids)
            result["issues"].extend(doc_issues)
            
            # 确定整体状态
            if any(issue.severity == "high" for issue in result["issues"]):
                result["overall_status"] = "critical"
            elif any(issue.severity == "medium" for issue in result["issues"]):
                result["overall_status"] = "warning"
            elif result["issues"]:
                result["overall_status"] = "info"
            
            # 生成建议
            result["recommendations"] = self._generate_recommendations(result["issues"])
            
            logger.info(f"Consistency check completed. Status: {result['overall_status']}, "
                       f"Issues: {len(result['issues'])}")
            
        except Exception as e:
            logger.error(f"Error during consistency check: {e}")
            result["overall_status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def _get_active_kb_ids(self) -> List[str]:
        """获取数据库中的活跃knowledge base ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT knowledge_base_id 
                FROM documents 
                WHERE knowledge_base_id IS NOT NULL
            """)
            
            active_ids = [str(row[0]) for row in cursor.fetchall()]
            conn.close()
            
            return active_ids
        except Exception as e:
            logger.error(f"Error getting active KB IDs: {e}")
            return []
    
    def _get_storage_kb_ids(self) -> List[str]:
        """获取存储目录中的knowledge base ID"""
        kb_dirs = self.cleanup_service.get_kb_directories()
        storage_ids = []
        for kb_dir in kb_dirs:
            kb_id_str = kb_dir.name.replace("kb_", "")
            # 只保留数字部分，忽略其他字符
            try:
                # 提取数字部分
                kb_id_numeric = ''.join(filter(str.isdigit, kb_id_str))
                if kb_id_numeric:
                    storage_ids.append(kb_id_numeric)
            except Exception as e:
                logger.warning(f"Error parsing KB ID from {kb_dir.name}: {e}")
        return storage_ids
    
    def _check_orphaned_storage(self, active_ids: List[str], storage_ids: List[str]) -> List[ConsistencyIssue]:
        """检查孤立的存储目录"""
        issues = []
        orphaned_ids = [kb_id for kb_id in storage_ids if kb_id not in active_ids]
        
        for orphaned_id in orphaned_ids:
            # 获取存储大小
            kb_dir = self.cleanup_service.get_kb_directory(int(orphaned_id))
            size_mb = self._get_directory_size_mb(kb_dir)
            
            issue = ConsistencyIssue(
                type="orphaned_storage",
                kb_id=orphaned_id,
                description=f"Knowledge base {orphaned_id} has storage directory but no active documents. "
                           f"Storage size: {size_mb:.2f} MB",
                severity="medium" if size_mb > 10 else "low",
                suggested_action=f"Run cleanup script to remove orphaned storage for KB {orphaned_id}"
            )
            issues.append(issue)
        
        return issues
    
    def _check_missing_storage(self, active_ids: List[str], storage_ids: List[str]) -> List[ConsistencyIssue]:
        """检查缺失的存储目录"""
        issues = []
        missing_ids = [kb_id for kb_id in active_ids if kb_id not in storage_ids]
        
        for missing_id in missing_ids:
            # 检查是否有文档
            doc_count = self._get_document_count(missing_id)
            
            if doc_count > 0:
                issue = ConsistencyIssue(
                    type="missing_storage",
                    kb_id=missing_id,
                    description=f"Knowledge base {missing_id} has {doc_count} documents but no storage directory",
                    severity="high",
                    suggested_action=f"Check if documents for KB {missing_id} were processed correctly"
                )
                issues.append(issue)
        
        return issues
    
    def _check_storage_sizes(self, active_ids: List[str]) -> List[ConsistencyIssue]:
        """检查存储大小异常"""
        issues = []
        
        for kb_id in active_ids:
            kb_dir = self.cleanup_service.get_kb_directory(int(kb_id))
            if not kb_dir.exists():
                continue
            
            size_mb = self._get_directory_size_mb(kb_dir)
            doc_count = self._get_document_count(kb_id)
            
            # 检查存储大小是否异常
            if doc_count > 0:
                avg_size_per_doc = size_mb / doc_count
                
                if avg_size_per_doc > 100:  # 每个文档超过100MB
                    issue = ConsistencyIssue(
                        type="size_mismatch",
                        kb_id=kb_id,
                        description=f"Knowledge base {kb_id} has unusually large storage: "
                                   f"{size_mb:.2f} MB for {doc_count} documents "
                                   f"(avg: {avg_size_per_doc:.2f} MB/doc)",
                        severity="medium",
                        suggested_action=f"Review storage usage for KB {kb_id}, consider cleanup"
                    )
                    issues.append(issue)
                elif avg_size_per_doc < 0.1:  # 每个文档小于0.1MB
                    issue = ConsistencyIssue(
                        type="size_mismatch",
                        kb_id=kb_id,
                        description=f"Knowledge base {kb_id} has unusually small storage: "
                                   f"{size_mb:.2f} MB for {doc_count} documents "
                                   f"(avg: {avg_size_per_doc:.2f} MB/doc)",
                        severity="low",
                        suggested_action=f"Check if documents for KB {kb_id} were processed correctly"
                    )
                    issues.append(issue)
        
        return issues
    
    def _check_document_consistency(self, active_ids: List[str]) -> List[ConsistencyIssue]:
        """检查文档一致性"""
        issues = []
        
        for kb_id in active_ids:
            # 检查文档状态分布
            status_dist = self._get_document_status_distribution(kb_id)
            
            # 检查是否有大量失败或卡住的文档
            failed_count = status_dist.get("failed", 0)
            processing_count = status_dist.get("parsing", 0) + status_dist.get("analyzing", 0)
            
            if failed_count > 0:
                issue = ConsistencyIssue(
                    type="document_consistency",
                    kb_id=kb_id,
                    description=f"Knowledge base {kb_id} has {failed_count} failed documents",
                    severity="medium",
                    suggested_action=f"Review and retry failed documents in KB {kb_id}"
                )
                issues.append(issue)
            
            if processing_count > 5:  # 超过5个文档在处理中
                issue = ConsistencyIssue(
                    type="document_consistency",
                    kb_id=kb_id,
                    description=f"Knowledge base {kb_id} has {processing_count} documents stuck in processing",
                    severity="high",
                    suggested_action=f"Check processing pipeline for KB {kb_id}"
                )
                issues.append(issue)
        
        return issues
    
    def _get_directory_size_mb(self, directory: Path) -> float:
        """获取目录大小（MB）"""
        if not directory.exists():
            return 0.0
        
        total_size = 0
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.warning(f"Error calculating directory size for {directory}: {e}")
        
        return total_size / (1024 * 1024)  # 转换为MB
    
    def _get_document_count(self, kb_id: str) -> int:
        """获取knowledge base的文档数量"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM documents 
                WHERE knowledge_base_id = ?
            """, (kb_id,))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
        except Exception as e:
            logger.error(f"Error getting document count for KB {kb_id}: {e}")
            return 0
    
    def _get_document_status_distribution(self, kb_id: str) -> Dict[str, int]:
        """获取文档状态分布"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT status, COUNT(*) FROM documents 
                WHERE knowledge_base_id = ?
                GROUP BY status
            """, (kb_id,))
            
            distribution = dict(cursor.fetchall())
            conn.close()
            
            return distribution
        except Exception as e:
            logger.error(f"Error getting document status distribution for KB {kb_id}: {e}")
            return {}
    
    def _generate_recommendations(self, issues: List[ConsistencyIssue]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 按类型分组问题
        orphaned_storage = [issue for issue in issues if issue.type == "orphaned_storage"]
        missing_storage = [issue for issue in issues if issue.type == "missing_storage"]
        size_mismatch = [issue for issue in issues if issue.type == "size_mismatch"]
        
        if orphaned_storage:
            recommendations.append(
                f"Run cleanup script to remove {len(orphaned_storage)} orphaned storage directories"
            )
        
        if missing_storage:
            recommendations.append(
                f"Investigate {len(missing_storage)} knowledge bases with missing storage directories"
            )
        
        if size_mismatch:
            recommendations.append(
                f"Review storage usage for {len(size_mismatch)} knowledge bases with size anomalies"
            )
        
        if not issues:
            recommendations.append("Data consistency is healthy. No issues found.")
        
        return recommendations
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_detailed_report(self) -> str:
        """获取详细的一致性报告"""
        result = self.check_consistency()
        
        report = f"""
# 数据一致性报告

**检查时间**: {result['timestamp']}
**整体状态**: {result['overall_status'].upper()}

## 统计信息
- 活跃知识库数量: {result['statistics'].get('active_kb_count', 0)}
- 存储目录数量: {result['statistics'].get('storage_kb_count', 0)}

## 发现的问题
"""
        
        if not result['issues']:
            report += "\n✅ 未发现数据一致性问题\n"
        else:
            for i, issue in enumerate(result['issues'], 1):
                report += f"""
### {i}. {issue.type.upper()} - KB {issue.kb_id}
**严重程度**: {issue.severity.upper()}
**描述**: {issue.description}
**建议操作**: {issue.suggested_action}
"""
        
        report += f"""
## 建议
"""
        for i, recommendation in enumerate(result['recommendations'], 1):
            report += f"{i}. {recommendation}\n"
        
        return report
    
    def auto_fix_issues(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        自动修复发现的问题
        
        Args:
            dry_run: 是否为试运行模式
            
        Returns:
            修复结果
        """
        logger.info(f"Starting auto-fix (dry_run={dry_run})...")
        
        result = {
            "dry_run": dry_run,
            "issues_found": 0,
            "issues_fixed": 0,
            "actions_taken": [],
            "errors": []
        }
        
        try:
            consistency_result = self.check_consistency()
            result["issues_found"] = len(consistency_result["issues"])
            
            # 处理孤立存储
            orphaned_issues = [issue for issue in consistency_result["issues"] 
                             if issue.type == "orphaned_storage"]
            
            for issue in orphaned_issues:
                try:
                    if not dry_run:
                        # 删除孤立存储
                        success = self.cleanup_service.delete_kb_storage(int(issue.kb_id))
                        if success:
                            result["issues_fixed"] += 1
                            result["actions_taken"].append(f"Deleted orphaned storage for KB {issue.kb_id}")
                        else:
                            result["errors"].append(f"Failed to delete storage for KB {issue.kb_id}")
                    else:
                        result["actions_taken"].append(f"[DRY RUN] Would delete orphaned storage for KB {issue.kb_id}")
                        result["issues_fixed"] += 1
                        
                except Exception as e:
                    result["errors"].append(f"Error fixing issue for KB {issue.kb_id}: {e}")
            
            logger.info(f"Auto-fix completed. Fixed {result['issues_fixed']} issues")
            
        except Exception as e:
            logger.error(f"Error during auto-fix: {e}")
            result["errors"].append(str(e))
        
        return result
