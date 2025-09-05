#!/usr/bin/env python3
"""Simple, working chat import - no complexity"""

import asyncpg
import asyncio
import json
import glob
from datetime import datetime
import hashlib

async def main():
    # Connect to PostgreSQL
    conn = await asyncpg.connect('postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context')
    
    # Find all chat files
    files = glob.glob('/home/opsvi/.claude/projects/*/*.jsonl')
    print(f"📁 Found {len(files)} chat files")
    
    imported = 0
    errors = 0
    
    for filepath in files:
        try:
            with open(filepath, 'r') as f:
                for line_num, line in enumerate(f):
                    if not line.strip():
                        continue
                        
                    try:
                        data = json.loads(line)
                        
                        # Create unique ID
                        unique_str = f"{filepath}:{line_num}:{data.get('uuid', '')}"
                        item_id = hashlib.sha256(unique_str.encode()).hexdigest()[:16]
                        
                        # Extract content
                        content = ""
                        if 'content' in data and data['content']:
                            if isinstance(data['content'], list):
                                content = ' '.join([str(c.get('text', '')) for c in data['content']])
                            else:
                                content = str(data['content'])
                        
                        # Skip empty content
                        if not content.strip():
                            continue
                            
                        # Insert with conflict handling
                        await conn.execute('''
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
                        'claude_chat',
                        f"{filepath}:{line_num}",
                        'message',
                        datetime.now(),
                        content[:10000],  # Limit content length
                        data.get('sessionId'),
                        json.dumps(data)
                        )
                        imported += 1
                        
                        if imported % 100 == 0:
                            print(f"✅ Imported {imported} items")
                            
                    except json.JSONDecodeError:
                        errors += 1
                        continue
                        
        except Exception as e:
            print(f"❌ Error with file {filepath}: {e}")
            errors += 1
    
    # Final count
    total = await conn.fetchval("SELECT COUNT(*) FROM context_items WHERE source_type='claude_chat'")
    print(f"🎯 Import complete: {imported} processed, {errors} errors")
    print(f"📊 Total Claude chat items in database: {total}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())