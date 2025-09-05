#!/usr/bin/env python3
"""Realtime chat log pipeline - continuous processing from file system events"""

import asyncpg
import asyncio
import json
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

class ChatLogHandler(FileSystemEventHandler):
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.processing = set()  # Track files being processed
        
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith('.jsonl'):
            return
        asyncio.create_task(self.process_file(event.src_path))
        
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith('.jsonl'):
            return
        asyncio.create_task(self.process_file(event.src_path))
    
    async def process_file(self, filepath):
        if filepath in self.processing:
            return
            
        self.processing.add(filepath)
        try:
            await self.import_jsonl_file(filepath)
        finally:
            self.processing.discard(filepath)
    
    async def import_jsonl_file(self, filepath):
        """Import single JSONL file"""
        async with self.db_pool.acquire() as conn:
            try:
                with open(filepath, 'r') as f:
                    for line_num, line in enumerate(f):
                        if not line.strip():
                            continue
                            
                        try:
                            data = json.loads(line)
                            
                            # Create unique ID
                            file_stem = Path(filepath).stem
                            msg_id = data.get('uuid', f"{file_stem}_{line_num}")
                            
                            # Extract basic info
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
                            
                            # Insert (ignore conflicts for already processed)
                            await conn.execute("""
                                INSERT INTO context_items (
                                    source_type, source_id, entity_type, timestamp,
                                    title, content, session_id, source_data
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                                ON CONFLICT (source_type, source_id) DO NOTHING
                            """, 
                            'claude_realtime', msg_id, msg_type, timestamp,
                            f"{msg_type} {msg_id[:8]}", content[:1000], 
                            file_stem, json.dumps(data))
                            
                        except json.JSONDecodeError:
                            continue
                            
                print(f"✅ Processed {filepath}")
                            
            except Exception as e:
                print(f"⚠️  Error processing {filepath}: {e}")

async def bootstrap_existing_logs(db_pool):
    """Process all existing logs first"""
    print("🔄 Bootstrap: Processing existing logs...")
    
    claude_dir = Path("/home/opsvi/.claude/projects")
    jsonl_files = list(claude_dir.glob("*/*.jsonl"))
    
    handler = ChatLogHandler(db_pool)
    
    for i, filepath in enumerate(jsonl_files):
        await handler.import_jsonl_file(str(filepath))
        if i % 100 == 0:
            print(f"   Processed {i}/{len(jsonl_files)} files")
    
    print(f"✅ Bootstrap complete: {len(jsonl_files)} files processed")

async def start_realtime_monitoring(db_pool):
    """Start file system monitoring"""
    print("👁️  Starting realtime monitoring...")
    
    handler = ChatLogHandler(db_pool)
    observer = Observer()
    observer.schedule(handler, "/home/opsvi/.claude/projects", recursive=True)
    observer.start()
    
    try:
        while True:
            await asyncio.sleep(10)
            # Periodic stats
            async with db_pool.acquire() as conn:
                count = await conn.fetchval("SELECT COUNT(*) FROM context_items WHERE source_type='claude_realtime'")
                print(f"📊 Total messages: {count}")
                
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

async def main():
    print("🚀 Realtime Chat Pipeline Starting")
    
    # Create connection pool
    db_pool = await asyncpg.create_pool(
        'postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context',
        min_size=2, max_size=10
    )
    
    try:
        # Bootstrap existing logs
        await bootstrap_existing_logs(db_pool)
        
        # Start realtime monitoring 
        await start_realtime_monitoring(db_pool)
        
    finally:
        await db_pool.close()

if __name__ == "__main__":
    asyncio.run(main())