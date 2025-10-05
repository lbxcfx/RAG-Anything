#!/usr/bin/env python3
"""
Check knowledge base and LightRAG storage status
"""

import os
import json
import sqlite3

def check_knowledge_base_status():
    """Check knowledge base and storage status"""
    print("🔍 Knowledge Base and Storage Analysis")
    print("=" * 50)
    
    # Check database documents
    try:
        conn = sqlite3.connect('rag_anything_dev.db')
        cursor = conn.cursor()
        
        # Get document counts by knowledge base
        cursor.execute('SELECT knowledge_base_id, COUNT(*) as doc_count FROM documents GROUP BY knowledge_base_id')
        kb_docs = cursor.fetchall()
        
        print("📄 Documents in database:")
        for kb_id, doc_count in kb_docs:
            print(f"  KB {kb_id}: {doc_count} documents")
        
        # Get all documents
        cursor.execute('SELECT id, filename, knowledge_base_id, status FROM documents ORDER BY created_at DESC')
        all_docs = cursor.fetchall()
        
        print(f"\n📋 All documents ({len(all_docs)} total):")
        for doc_id, filename, kb_id, status in all_docs:
            print(f"  ID: {doc_id:2d} | KB: {kb_id} | Status: {status:<12} | {filename[:50]}...")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    
    # Check LightRAG storage
    print(f"\n🗄️ LightRAG Storage Analysis:")
    print("-" * 30)
    
    vectors_dir = './storage/vectors'
    if os.path.exists(vectors_dir):
        kb_dirs = [d for d in os.listdir(vectors_dir) if d.startswith('kb_')]
        print(f"Found knowledge base directories: {kb_dirs}")
        
        for kb_dir in kb_dirs:
            kb_path = os.path.join(vectors_dir, kb_dir)
            print(f"\n📁 {kb_dir}:")
            
            if os.path.exists(kb_path):
                files = os.listdir(kb_path)
                json_files = [f for f in files if f.endswith('.json')]
                
                print(f"  Total files: {len(files)}")
                print(f"  JSON files: {len(json_files)}")
                
                # Check specific files
                for json_file in json_files:
                    file_path = os.path.join(kb_path, json_file)
                    file_size = os.path.getsize(file_path)
                    print(f"    {json_file}: {file_size} bytes")
                    
                    # Check entity and relationship files
                    if 'entity' in json_file.lower() or 'relation' in json_file.lower():
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            if isinstance(data, dict):
                                count = len(data)
                                print(f"      -> Contains {count} items")
                                
                                # Show sample items
                                if count > 0:
                                    sample_keys = list(data.keys())[:3]
                                    print(f"      -> Sample keys: {sample_keys}")
                                    
                                    # Check if items have Chinese content
                                    chinese_count = 0
                                    for key, value in data.items():
                                        if isinstance(value, dict):
                                            name = value.get('entity_id', value.get('name', key))
                                            if any('\u4e00' <= char <= '\u9fff' for char in str(name)):
                                                chinese_count += 1
                                    
                                    print(f"      -> Chinese items: {chinese_count}/{count}")
                            
                        except Exception as e:
                            print(f"      -> Error reading file: {e}")
            else:
                print(f"  Directory not found: {kb_path}")
    else:
        print(f"❌ Vectors directory not found: {vectors_dir}")

def check_specific_kb(kb_id):
    """Check specific knowledge base in detail"""
    print(f"\n🔍 Detailed Analysis of KB {kb_id}")
    print("-" * 40)
    
    kb_dir = f'./storage/vectors/kb_{kb_id}'
    if not os.path.exists(kb_dir):
        print(f"❌ Knowledge base directory not found: {kb_dir}")
        return
    
    # Check entities
    entities_file = os.path.join(kb_dir, 'vdb_entities.json')
    if os.path.exists(entities_file):
        try:
            with open(entities_file, 'r', encoding='utf-8') as f:
                entities = json.load(f)
            
            print(f"📊 Entities in KB {kb_id}: {len(entities)}")
            
            if len(entities) > 0:
                print("Sample entities:")
                count = 0
                for key, value in entities.items():
                    if count < 10:  # Show first 10
                        if isinstance(value, dict):
                            name = value.get('entity_id', value.get('name', key))
                            entity_type = value.get('entity_type', value.get('type', 'unknown'))
                            print(f"  {count+1:2d}. {name} ({entity_type})")
                        else:
                            print(f"  {count+1:2d}. {key}: {value}")
                        count += 1
                    else:
                        break
                
                if len(entities) > 10:
                    print(f"  ... and {len(entities) - 10} more entities")
        
        except Exception as e:
            print(f"❌ Error reading entities: {e}")
    else:
        print(f"❌ Entities file not found: {entities_file}")
    
    # Check relationships
    relations_file = os.path.join(kb_dir, 'vdb_relationships.json')
    if os.path.exists(relations_file):
        try:
            with open(relations_file, 'r', encoding='utf-8') as f:
                relations = json.load(f)
            
            print(f"📊 Relationships in KB {kb_id}: {len(relations)}")
            
            if len(relations) > 0:
                print("Sample relationships:")
                count = 0
                for key, value in relations.items():
                    if count < 10:  # Show first 10
                        if isinstance(value, dict):
                            src = value.get('src_id', value.get('source', 'unknown'))
                            tgt = value.get('tgt_id', value.get('target', 'unknown'))
                            rel_type = value.get('relation_type', value.get('type', 'unknown'))
                            print(f"  {count+1:2d}. {src} -> {tgt} ({rel_type})")
                        else:
                            print(f"  {count+1:2d}. {key}: {value}")
                        count += 1
                    else:
                        break
                
                if len(relations) > 10:
                    print(f"  ... and {len(relations) - 10} more relationships")
        
        except Exception as e:
            print(f"❌ Error reading relationships: {e}")
    else:
        print(f"❌ Relationships file not found: {relations_file}")

def main():
    check_knowledge_base_status()
    
    # Check specific knowledge bases
    for kb_id in [2, 3, 4]:
        check_specific_kb(kb_id)

if __name__ == "__main__":
    main()


