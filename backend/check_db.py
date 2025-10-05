#!/usr/bin/env python3
"""Check database status and user data"""

import sqlite3
import os

def check_database():
    db_path = "rag_anything_dev.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file does not exist!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📊 Tables: {[table[0] for table in tables]}")
        
        # Check users table
        if ('users',) in tables:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"👥 Users count: {user_count}")
            
            if user_count > 0:
                cursor.execute("SELECT id, username, email, is_active FROM users LIMIT 5")
                users = cursor.fetchall()
                print("👤 Sample users:")
                for user in users:
                    print(f"  - ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Active: {user[3]}")
        else:
            print("❌ Users table does not exist!")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    check_database()

