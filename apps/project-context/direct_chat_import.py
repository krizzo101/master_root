#!/usr/bin/env python3
"""Direct Claude chat log import - bypass SQLite entirely"""

import asyncpg
import json
import glob
from datetime import datetime
from pathlib import Path

async def import_claude_logs():
    print("🚀 Direct Claude Chat Import")
    
    # Connect to PostgreSQL
    pg_conn = await asyncpg.connect('postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context')
    
    # Find Claude chat logs
    chat_files = glob.glob('/home/opsvi/.claude/projects/*/*.jsonl')
    print(f"📁 Found {len(chat_files)} chat files")
    
    imported = 0
    for chat_file in chat_files[:50]:  # Limit to first 50 for testing
        try:
            with open(chat_file, 'r') as f:
                for line_num, line in enumerate(f):
                    if not line.strip():
                        continue
                        
                    try:
                        data = json.loads(line)
                        
                        # Extract key info
                        msg_id = data.get('uuid', f"{Path(chat_file).stem}_{line_num}")
                        msg_type = data.get('type', 'unknown')
                        timestamp = datetime.now()
                        
                        if 'created_at' in data:
                            timestamp = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
                        
                        # Extract content
                        content = ""
                        if 'text' in data:
                            content = data['text']
                        elif 'content' in data:
                            if isinstance(data['content'], list):
                                content = " ".join(str(item.get('text', '')) for item in data['content'] if isinstance(item, dict))
                            else:
                                content = str(data['content'])
                        
                        # Insert with basic info only
                        await pg_conn.execute("""
                            INSERT INTO context_items (
                                source_type, source_id, entity_type, timestamp,
                                title, content, session_id, source_data
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                            ON CONFLICT (source_type, source_id) DO NOTHING
                        """, 
                        'claude_chat', msg_id, msg_type, timestamp,
                        f"{msg_type} {msg_id[:8]}", content, 
                        Path(chat_file).parent.name, json.dumps(data))
                        
                        imported += 1
                        
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            print(f"⚠️  Error with file {chat_file}: {e}")
    
    print(f"✅ Imported {imported} items")
    
    # Check final count
    final_count = await pg_conn.fetchval("SELECT COUNT(*) FROM context_items WHERE source_type='claude_chat'")
    print(f"📊 Total Claude chat items in PostgreSQL: {final_count}")
    
    await pg_conn.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(import_claude_logs())