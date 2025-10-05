#!/usr/bin/env python3
"""
数据一致性管理命令行工具
提供数据一致性检查、清理和监控功能
"""

import argparse
import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.data_consistency_monitor import DataConsistencyMonitor
from app.services.lightrag_cleanup_service import LightRAGCleanupService


def check_consistency():
    """检查数据一致性"""
    print("🔍 检查数据一致性...")
    
    monitor = DataConsistencyMonitor()
    result = monitor.check_consistency()
    
    print(f"\n📊 检查结果:")
    print(f"   整体状态: {result['overall_status'].upper()}")
    print(f"   发现问题: {len(result['issues'])}")
    print(f"   活跃知识库: {result['statistics'].get('active_kb_count', 0)}")
    print(f"   存储目录: {result['statistics'].get('storage_kb_count', 0)}")
    
    if result['issues']:
        print(f"\n⚠️  发现的问题:")
        for i, issue in enumerate(result['issues'], 1):
            print(f"   {i}. [{issue.severity.upper()}] KB {issue.kb_id}: {issue.description}")
    
    if result['recommendations']:
        print(f"\n💡 建议:")
        for i, recommendation in enumerate(result['recommendations'], 1):
            print(f"   {i}. {recommendation}")
    
    return result


def generate_report():
    """生成详细报告"""
    print("📋 生成详细一致性报告...")
    
    monitor = DataConsistencyMonitor()
    report = monitor.get_detailed_report()
    
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    # 保存报告到文件
    report_file = "consistency_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 报告已保存到: {report_file}")


def auto_fix(dry_run=True):
    """自动修复问题"""
    print(f"🔧 自动修复数据一致性问题 (试运行: {dry_run})...")
    
    monitor = DataConsistencyMonitor()
    result = monitor.auto_fix_issues(dry_run=dry_run)
    
    print(f"\n📊 修复结果:")
    print(f"   发现问题: {result['issues_found']}")
    print(f"   修复问题: {result['issues_fixed']}")
    print(f"   执行操作: {len(result['actions_taken'])}")
    
    if result['actions_taken']:
        print(f"\n✅ 执行的操作:")
        for i, action in enumerate(result['actions_taken'], 1):
            print(f"   {i}. {action}")
    
    if result['errors']:
        print(f"\n❌ 错误:")
        for i, error in enumerate(result['errors'], 1):
            print(f"   {i}. {error}")
    
    return result


def cleanup_orphaned():
    """清理孤立存储"""
    print("🗑️  清理孤立的存储目录...")
    
    cleanup_service = LightRAGCleanupService()
    
    # 获取活跃的knowledge base ID
    import sqlite3
    try:
        conn = sqlite3.connect("rag_anything_dev.db")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT knowledge_base_id FROM documents WHERE knowledge_base_id IS NOT NULL")
        active_ids = [str(row[0]) for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        print(f"❌ 无法从数据库获取活跃的KB ID: {e}")
        return
    
    print(f"📊 数据库中有 {len(active_ids)} 个活跃的知识库")
    
    result = cleanup_service.cleanup_orphaned_storage(active_ids)
    
    print(f"\n📊 清理结果:")
    print(f"   清理目录: {result['orphaned_dirs']}")
    print(f"   释放空间: {result['total_size'] / (1024*1024):.2f} MB")


def show_storage_stats(kb_id=None):
    """显示存储统计"""
    print(f"📊 显示存储统计信息 (KB: {kb_id or '全部'})...")
    
    cleanup_service = LightRAGCleanupService()
    stats = cleanup_service.get_storage_stats(kb_id)
    
    print(f"\n📊 存储统计:")
    print(f"   知识库目录数: {stats['total_kb_dirs']}")
    print(f"   总存储大小: {stats['total_size'] / (1024*1024):.2f} MB")
    
    if stats['kb_details']:
        print(f"\n📁 各知识库详情:")
        for kb_id_str, kb_stats in stats['kb_details'].items():
            print(f"   KB {kb_id_str}:")
            print(f"     大小: {kb_stats['size'] / (1024*1024):.2f} MB")
            print(f"     文件数: {kb_stats['file_count']}")
            print(f"     实体文件: {kb_stats['entity_files']}")
            print(f"     关系文件: {kb_stats['relation_files']}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据一致性管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 检查一致性
    subparsers.add_parser('check', help='检查数据一致性')
    
    # 生成报告
    subparsers.add_parser('report', help='生成详细一致性报告')
    
    # 自动修复
    fix_parser = subparsers.add_parser('fix', help='自动修复数据一致性问题')
    fix_parser.add_argument('--dry-run', action='store_true', default=True,
                          help='试运行模式（默认）')
    fix_parser.add_argument('--execute', action='store_true',
                          help='执行修复（非试运行）')
    
    # 清理孤立存储
    subparsers.add_parser('cleanup', help='清理孤立的存储目录')
    
    # 显示存储统计
    stats_parser = subparsers.add_parser('stats', help='显示存储统计信息')
    stats_parser.add_argument('--kb-id', type=int, help='特定知识库ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'check':
            check_consistency()
        elif args.command == 'report':
            generate_report()
        elif args.command == 'fix':
            dry_run = not args.execute
            auto_fix(dry_run)
        elif args.command == 'cleanup':
            cleanup_orphaned()
        elif args.command == 'stats':
            show_storage_stats(args.kb_id)
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"❌ 执行命令时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


