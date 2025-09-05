#!/usr/bin/env python3
"""SQLite to PostgreSQL migration - direct and simple"""

import sqlite3
import asyncpg
import asyncio
import json
from datetime import datetime
import hashlib

async def main():
    # Connect to both databases
    sqlite_conn = sqlite3.connect('/home/opsvi/master_root/chat_logs.db')
    sqlite_conn.row_factory = sqlite3.Row
    
    pg_conn = await asyncpg.connect('postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context')
    
    # Get all nodes from SQLite
    cursor = sqlite_conn.cursor()
    cursor.execute('''
        SELECT n.*, s.session_id as session_uuid
        FROM nodes n 
        JOIN sessions s ON n.session_id = s.session_id
        ORDER BY n.timestamp
    ''')
    
    imported = 0
    errors = 0
    
    print(f"🚀 Migrating SQLite chat data to PostgreSQL")
    
    for row in cursor:
        try:
            # Create unique source_id
            source_id = f"sqlite:{row['session_id']}:{row['uuid']}"
            
            # Map node_type to entity_type  
            entity_type = row['node_type'] or 'message'
            
            # Extract content from raw_json
            content = ''
            if row['raw_json']:
                try:
                    raw_data = json.loads(row['raw_json'])
                    if 'content' in raw_data:
                        if isinstance(raw_data['content'], list):
                            content = ' '.join([str(c.get('text', '') if isinstance(c, dict) else c) for c in raw_data['content']])
                        else:
                            content = str(raw_data['content'])
                    elif 'summary' in raw_data:
                        content = str(raw_data['summary'])
                except:
                    content = row['raw_json'][:1000]  # Fallback
            
            if len(content) > 10000:
                content = content[:10000]
                
            # Create source data
            source_data = {
                'uuid': row['uuid'],
                'node_type': row['node_type'],
                'session_id': row['session_id'],
                'session_uuid': row['session_uuid'],
                'timestamp': row['timestamp'],
                'parent_uuid': row['parent_uuid'],
                'original_source': 'sqlite_chat_logs'
            }
            
            # Insert to PostgreSQL
            await pg_conn.execute('''
                INSERT INTO context_items (
                    source_type,
                    source_id,
                    entity_type,
                    timestamp,
                    content,
                    session_id,
                    source_data
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (source_type, source_id) DO NOTHING
            ''',
            'sqlite_chat',
            source_id,
            entity_type,
            datetime.fromisoformat(row['timestamp']) if row['timestamp'] else datetime.now(),
            content,
            row['session_uuid'],
            json.dumps(source_data)
            )
            
            imported += 1
            if imported % 1000 == 0:
                print(f"✅ Migrated {imported} nodes")
                
        except Exception as e:
            errors += 1
            if errors < 5:  # Only show first few errors
                print(f"❌ Error with node {row['uuid'] if 'uuid' in row.keys() else 'unknown'}: {e}")
    
    # Final counts
    total = await pg_conn.fetchval("SELECT COUNT(*) FROM context_items WHERE source_type='sqlite_chat'")
    print(f"🎯 Migration complete: {imported} processed, {errors} errors")
    print(f"📊 Total SQLite chat items in database: {total}")
    
    sqlite_conn.close()
    await pg_conn.close()

if __name__ == "__main__":
    asyncio.run(main())