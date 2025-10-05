"""
数据一致性监控API端点
提供数据一致性检查、报告和自动修复功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from typing import Dict, Any, Optional
from app.api.v1.deps import get_current_active_user
from app.models.user import User
from app.services.data_consistency_monitor import DataConsistencyMonitor
from app.services.lightrag_cleanup_service import LightRAGCleanupService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/consistency/check")
async def check_data_consistency(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """检查数据一致性"""
    try:
        monitor = DataConsistencyMonitor()
        result = monitor.check_consistency()
        return result
    except Exception as e:
        logger.error(f"Error checking data consistency: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check data consistency: {str(e)}"
        )


@router.get("/consistency/report", response_class=PlainTextResponse)
async def get_consistency_report(
    current_user: User = Depends(get_current_active_user),
) -> str:
    """获取详细的一致性报告"""
    try:
        monitor = DataConsistencyMonitor()
        report = monitor.get_detailed_report()
        return report
    except Exception as e:
        logger.error(f"Error generating consistency report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate consistency report: {str(e)}"
        )


@router.post("/consistency/auto-fix")
async def auto_fix_consistency_issues(
    dry_run: bool = True,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """自动修复数据一致性问题"""
    try:
        monitor = DataConsistencyMonitor()
        result = monitor.auto_fix_issues(dry_run=dry_run)
        return result
    except Exception as e:
        logger.error(f"Error auto-fixing consistency issues: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to auto-fix consistency issues: {str(e)}"
        )


@router.get("/storage/stats")
async def get_storage_stats(
    kb_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """获取存储统计信息"""
    try:
        cleanup_service = LightRAGCleanupService()
        stats = cleanup_service.get_storage_stats(kb_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage stats: {str(e)}"
        )


@router.post("/storage/cleanup-orphaned")
async def cleanup_orphaned_storage(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """清理孤立的存储目录"""
    try:
        cleanup_service = LightRAGCleanupService()
        
        # 获取活跃的knowledge base ID
        import sqlite3
        conn = sqlite3.connect("rag_anything_dev.db")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT knowledge_base_id FROM documents WHERE knowledge_base_id IS NOT NULL")
        active_ids = [str(row[0]) for row in cursor.fetchall()]
        conn.close()
        
        result = cleanup_service.cleanup_orphaned_storage(active_ids)
        return result
    except Exception as e:
        logger.error(f"Error cleaning up orphaned storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup orphaned storage: {str(e)}"
        )


@router.delete("/storage/kb/{kb_id}")
async def delete_kb_storage(
    kb_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """删除特定knowledge base的存储目录"""
    try:
        cleanup_service = LightRAGCleanupService()
        success = cleanup_service.delete_kb_storage(kb_id)
        
        if success:
            return {"message": f"Successfully deleted storage for knowledge base {kb_id}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete storage for knowledge base {kb_id}"
            )
    except Exception as e:
        logger.error(f"Error deleting KB storage {kb_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete storage for knowledge base {kb_id}: {str(e)}"
        )


