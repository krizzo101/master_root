#!/usr/bin/env python3
"""Direct SQLite to PostgreSQL migration - no orchestration nonsense"""

import asyncio
import json
import sqlite3
from datetime import datetime

import asyncpg


async def migrate():
    print("🚀 Direct SQLite → PostgreSQL Migration")

    # Connect to SQLite
    sqlite_conn = sqlite3.connect("/home/opsvi/master_root/chat_logs.db")
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    # Connect to PostgreSQL
    pg_conn = await asyncpg.connect(
        "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context"
    )

    # Get sessions and nodes
    cursor.execute(
        """
        SELECT s.session_id, s.cwd, s.git_branch, s.created_at,
               COUNT(n.uuid) as node_count
        FROM sessions s
        LEFT JOIN nodes n ON s.session_id = n.session_id
        GROUP BY s.session_id
        ORDER BY s.created_at DESC
        LIMIT 10
    """
    )

    sessions = cursor.fetchall()
    migrated = 0

    for session in sessions:
        print(
            f"📂 Session: {session['session_id'][:8]}... ({session['node_count']} nodes)"
        )

        # Get nodes for this session
        cursor.execute(
            """
            SELECT uuid, node_type, timestamp, raw_json
            FROM nodes
            WHERE session_id = ?
            ORDER BY timestamp
        """,
            (session["session_id"],),
        )

        nodes = cursor.fetchall()

        for node in nodes:
            try:
                raw_data = json.loads(node["raw_json"]) if node["raw_json"] else {}

                # Extract content
                content = ""
                if "content" in raw_data:
                    if isinstance(raw_data["content"], list):
                        content = " ".join(
                            str(item.get("text", ""))
                            for item in raw_data["content"]
                            if isinstance(item, dict)
                        )
                    else:
                        content = str(raw_data["content"])

                # Insert into PostgreSQL
                await pg_conn.execute(
                    """
                    INSERT INTO context_items (
                        source_type, source_id, entity_type, timestamp,
                        title, content, session_id, source_data
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (source_type, source_id) DO NOTHING
                """,
                    "chat",
                    node["uuid"],
                    node["node_type"],
                    datetime.fromisoformat(node["timestamp"].replace("Z", "+00:00")),
                    f"{node['node_type']} {node['uuid'][:8]}",
                    content,
                    session["session_id"],
                    json.dumps(raw_data),
                )

                migrated += 1

            except Exception as e:
                print(f"⚠️  Error with node {node['uuid']}: {e}")

    print(f"✅ Migrated {migrated} items")

    # Check final count
    final_count = await pg_conn.fetchval(
        "SELECT COUNT(*) FROM context_items WHERE source_type='chat'"
    )
    print(f"📊 Total chat items in PostgreSQL: {final_count}")

    await pg_conn.close()
    sqlite_conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
