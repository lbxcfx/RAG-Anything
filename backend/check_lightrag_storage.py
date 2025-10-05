#!/usr/bin/env python3
"""
Check LightRAG storage for entities and relations
"""

import os
import json
import sqlite3

def check_lightrag_storage(kb_id=4):
    """Check LightRAG storage for entities and relations"""
    try:
        kb_dir = f'./storage/vectors/kb_{kb_id}'
        print(f"📁 Checking LightRAG storage in: {kb_dir}")
        print(f"Directory exists: {os.path.exists(kb_dir)}")
        
        if not os.path.exists(kb_dir):
            print("❌ Knowledge base directory not found")
            return
        
        # List files in the directory
        files = os.listdir(kb_dir)
        print(f"\n📋 Files in kb_{kb_id}:")
        for file in files:
            file_path = os.path.join(kb_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"  {file} ({file_size} bytes)")
        
        # Check for entity and relation storage files
        entity_files = [f for f in files if 'entity' in f.lower()]
        relation_files = [f for f in files if 'relation' in f.lower()]
        
        print(f"\n🔍 Entity files: {entity_files}")
        print(f"🔍 Relation files: {relation_files}")
        
        # Try to read entity data
        for entity_file in entity_files:
            if entity_file.endswith('.json'):
                try:
                    with open(os.path.join(kb_dir, entity_file), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    print(f"\n📊 Entity file {entity_file} contains {len(data)} entries")
                    
                    # Show sample entities
                    if data:
                        print("Sample entities:")
                        count = 0
                        for key, value in data.items():
                            if count < 5:  # Show first 5 entities
                                if isinstance(value, dict):
                                    entity_name = value.get('entity_id', value.get('name', key))
                                    entity_type = value.get('entity_type', value.get('type', 'unknown'))
                                    print(f"  {entity_name} ({entity_type})")
                                else:
                                    print(f"  {key}: {value}")
                                count += 1
                            else:
                                break
                                
                except Exception as e:
                    print(f"❌ Error reading {entity_file}: {e}")
        
        # Try to read relation data
        for relation_file in relation_files:
            if relation_file.endswith('.json'):
                try:
                    with open(os.path.join(kb_dir, relation_file), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    print(f"\n📊 Relation file {relation_file} contains {len(data)} entries")
                    
                    # Show sample relations
                    if data:
                        print("Sample relations:")
                        count = 0
                        for key, value in data.items():
                            if count < 5:  # Show first 5 relations
                                if isinstance(value, dict):
                                    source = value.get('source', 'unknown')
                                    target = value.get('target', 'unknown')
                                    rel_type = value.get('type', 'unknown')
                                    print(f"  {source} --[{rel_type}]--> {target}")
                                else:
                                    print(f"  {key}: {value}")
                                count += 1
                            else:
                                break
                                
                except Exception as e:
                    print(f"❌ Error reading {relation_file}: {e}")
        
    except Exception as e:
        print(f"❌ Error checking LightRAG storage: {e}")

def check_document_info(doc_id=21):
    """Check document information"""
    try:
        conn = sqlite3.connect('rag_anything_dev.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, filename, status, progress, entity_count, relation_count, knowledge_base_id
            FROM documents WHERE id = ?
        ''', (doc_id,))
        
        row = cursor.fetchone()
        if row:
            doc_id, filename, status, progress, entity_count, relation_count, kb_id = row
            print(f"\n📄 Document Information:")
            print(f"  ID: {doc_id}")
            print(f"  Filename: {filename}")
            print(f"  Status: {status}")
            print(f"  Progress: {progress}%")
            print(f"  Entity Count: {entity_count}")
            print(f"  Relation Count: {relation_count}")
            print(f"  Knowledge Base ID: {kb_id}")
            
            return kb_id
        else:
            print(f"❌ Document {doc_id} not found")
            return None
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking document info: {e}")
        return None

if __name__ == "__main__":
    print("🔍 LightRAG Storage Analysis")
    print("=" * 35)
    
    kb_id = check_document_info(21)
    if kb_id:
        check_lightrag_storage(kb_id)


