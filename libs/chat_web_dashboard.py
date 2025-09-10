#!/usr/bin/env python3
"""
Simple Chat Analytics Web Dashboard
Serves both SQLite (existing) and PostgreSQL (new) data
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from threading import Thread

import asyncpg
from flask import Flask, jsonify, render_template_string, request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configurations
SQLITE_DB = "/home/opsvi/master_root/chat_logs.db"
POSTGRES_URL = "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context"


class DatabaseManager:
    def __init__(self):
        self.pg_pool = None

    async def init_postgres(self):
        """Initialize PostgreSQL connection pool."""
        try:
            self.pg_pool = await asyncpg.create_pool(
                POSTGRES_URL, min_size=2, max_size=5
            )
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")

    def get_sqlite_data(self):
        """Get data from SQLite database."""
        try:
            conn = sqlite3.connect(SQLITE_DB)
            conn.row_factory = sqlite3.Row

            # Get basic stats
            stats = conn.execute(
                """
                SELECT
                    COUNT(DISTINCT session_id) as sessions,
                    COUNT(*) as total_nodes,
                    COUNT(*) FILTER (WHERE node_type = 'user' OR node_type = 'assistant') as messages
                FROM nodes
            """
            ).fetchone()

            # Get recent sessions
            recent_sessions = conn.execute(
                """
                SELECT session_id, COUNT(*) as node_count,
                       MIN(timestamp) as start_time, MAX(timestamp) as end_time
                FROM nodes
                GROUP BY session_id
                ORDER BY MAX(timestamp) DESC
                LIMIT 10
            """
            ).fetchall()

            conn.close()

            return {
                "stats": dict(stats) if stats else {},
                "recent_sessions": [dict(row) for row in recent_sessions],
            }
        except Exception as e:
            logger.error(f"SQLite error: {e}")
            return {"stats": {}, "recent_sessions": []}

    async def get_postgres_data(self):
        """Get data from PostgreSQL database."""
        try:
            # Use a fresh connection each time to avoid pool issues
            conn = await asyncpg.connect(POSTGRES_URL)

            # Get basic stats
            stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_items,
                    COUNT(DISTINCT session_id) as sessions,
                    COUNT(*) FILTER (WHERE entity_type = 'message') as messages,
                    COUNT(*) FILTER (WHERE entity_type = 'tool_call') as tool_calls,
                    COUNT(DISTINCT file_path) FILTER (WHERE file_path IS NOT NULL) as unique_files,
                    MAX(ingested_at) as latest_ingestion
                FROM context_items
            """
            )

            # Get recent activity
            recent_items = await conn.fetch(
                """
                SELECT session_id, entity_type, title, timestamp, file_path
                FROM context_items
                ORDER BY timestamp DESC
                LIMIT 20
            """
            )

            await conn.close()

            return {
                "stats": dict(stats) if stats else {},
                "recent_items": [dict(item) for item in recent_items],
            }
        except Exception as e:
            logger.error(f"PostgreSQL error: {e}")
            return {"stats": {}, "recent_items": []}

    def search_sqlite(self, query: str, limit: int = 20):
        """Search SQLite database."""
        try:
            conn = sqlite3.connect(SQLITE_DB)
            conn.row_factory = sqlite3.Row

            # Search in nodes table (content stored in raw_json)
            results = conn.execute(
                """
                SELECT
                    uuid, session_id, node_type, timestamp,
                    substr(raw_json, 1, 200) as preview
                FROM nodes
                WHERE raw_json LIKE ?
                   OR session_id LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (f"%{query}%", f"%{query}%", limit),
            ).fetchall()

            conn.close()
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"SQLite search error: {e}")
            return []

    async def search_postgres(self, query: str, limit: int = 20):
        """Search PostgreSQL database."""
        try:
            conn = await asyncpg.connect(POSTGRES_URL)

            # Search in context_items with full-text search
            results = await conn.fetch(
                """
                SELECT
                    id, session_id, entity_type, title, timestamp, file_path,
                    substring(content, 1, 200) as preview
                FROM context_items
                WHERE content ILIKE $1
                   OR title ILIKE $1
                   OR session_id ILIKE $1
                   OR file_path ILIKE $1
                ORDER BY timestamp DESC
                LIMIT $2
            """,
                f"%{query}%",
                limit,
            )

            await conn.close()
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"PostgreSQL search error: {e}")
            return []

    def get_sqlite_details(self, uuid: str):
        """Get detailed information for a SQLite node."""
        try:
            conn = sqlite3.connect(SQLITE_DB)
            conn.row_factory = sqlite3.Row

            result = conn.execute(
                """
                SELECT * FROM nodes WHERE uuid = ?
            """,
                (uuid,),
            ).fetchone()

            conn.close()

            if result:
                details = dict(result)
                # Parse raw_json if it exists
                if details.get("raw_json"):
                    try:
                        details["parsed_content"] = json.loads(details["raw_json"])
                    except:
                        pass
                return details
            else:
                return {"error": "Item not found"}

        except Exception as e:
            logger.error(f"SQLite details error: {e}")
            return {"error": str(e)}

    async def get_postgres_details(self, item_id: str):
        """Get detailed information for a PostgreSQL item."""
        try:
            conn = await asyncpg.connect(POSTGRES_URL)

            result = await conn.fetchrow(
                """
                SELECT * FROM context_items WHERE id = $1
            """,
                item_id,
            )

            await conn.close()

            if result:
                details = dict(result)
                # Parse JSON fields if they exist
                for field in ["metrics", "source_data"]:
                    if details.get(field):
                        try:
                            details[f"parsed_{field}"] = json.loads(details[field])
                        except:
                            pass
                return details
            else:
                return {"error": "Item not found"}

        except Exception as e:
            logger.error(f"PostgreSQL details error: {e}")
            return {"error": str(e)}


# Global database manager
db_manager = DatabaseManager()

# HTML Template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Analytics Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .card { @apply bg-white rounded-lg shadow-md p-6 mb-6; }
        .stat-card { @apply bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg p-6; }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-4xl font-bold text-gray-800 mb-8">🚀 Chat Analytics Dashboard</h1>

        <!-- Search Section -->
        <div class="card mb-8">
            <h2 class="text-2xl font-semibold mb-4">🔍 Search Chat Logs</h2>
            <div class="flex flex-col md:flex-row gap-4">
                <input type="text" id="search-input" placeholder="Search messages, sessions, files..."
                       class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <select id="search-db" class="px-4 py-2 border border-gray-300 rounded-lg">
                    <option value="both">Both Databases</option>
                    <option value="sqlite">SQLite Only</option>
                    <option value="postgres">PostgreSQL Only</option>
                </select>
                <button onclick="performSearch()" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Search
                </button>
            </div>
            <div id="search-results" class="mt-4 hidden">
                <h3 class="text-lg font-semibold mb-2">Search Results</h3>
                <div id="search-content" class="space-y-2"></div>
            </div>
        </div>

        <!-- Details Modal -->
        <div id="details-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 hidden flex items-center justify-center p-4 z-50">
            <div class="bg-white rounded-lg max-w-4xl max-h-[80vh] w-full overflow-hidden">
                <div class="flex justify-between items-center p-6 border-b">
                    <h2 class="text-xl font-semibold" id="modal-title">Item Details</h2>
                    <button onclick="closeModal()" class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
                </div>
                <div class="p-6 overflow-y-auto max-h-[60vh]" id="modal-content">
                    Loading...
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div class="card">
                <h2 class="text-2xl font-semibold mb-4">📊 SQLite Data (Legacy)</h2>
                <div id="sqlite-stats" class="space-y-2">
                    <p>Loading...</p>
                </div>
            </div>

            <div class="card">
                <h2 class="text-2xl font-semibold mb-4">🐘 PostgreSQL Data (Real-time)</h2>
                <div id="postgres-stats" class="space-y-2">
                    <p>Loading...</p>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="card">
                <h3 class="text-xl font-semibold mb-4">📝 Recent SQLite Sessions</h3>
                <div id="sqlite-sessions" class="space-y-2">
                    <p>Loading...</p>
                </div>
            </div>

            <div class="card">
                <h3 class="text-xl font-semibold mb-4">⚡ Recent PostgreSQL Activity</h3>
                <div id="postgres-activity" class="space-y-2">
                    <p>Loading...</p>
                </div>
            </div>
        </div>

        <div class="card mt-6">
            <h3 class="text-xl font-semibold mb-4">🔧 Database Management</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="bg-blue-50 p-4 rounded">
                    <h4 class="font-semibold">SQLite Database</h4>
                    <p class="text-sm text-gray-600">Legacy chat analytics</p>
                    <p class="text-xs mt-2">File: chat_logs.db</p>
                </div>
                <div class="bg-green-50 p-4 rounded">
                    <h4 class="font-semibold">PostgreSQL</h4>
                    <p class="text-sm text-gray-600">Real-time ingestion</p>
                    <p class="text-xs mt-2">Port: 5432</p>
                </div>
                <div class="bg-purple-50 p-4 rounded">
                    <h4 class="font-semibold">pgAdmin</h4>
                    <p class="text-sm text-gray-600">Database management</p>
                    <a href="http://localhost:5433" class="text-xs text-blue-600 underline">Open pgAdmin</a>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function loadData() {
            try {
                // Load SQLite data
                const sqliteResponse = await fetch('/api/sqlite-stats');
                const sqliteData = await sqliteResponse.json();

                document.getElementById('sqlite-stats').innerHTML = `
                    <div class="grid grid-cols-3 gap-4">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-blue-600">${sqliteData.stats.sessions || 0}</div>
                            <div class="text-sm text-gray-600">Sessions</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-green-600">${sqliteData.stats.messages || 0}</div>
                            <div class="text-sm text-gray-600">Messages</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-purple-600">${sqliteData.stats.total_nodes || 0}</div>
                            <div class="text-sm text-gray-600">Total Nodes</div>
                        </div>
                    </div>
                `;

                document.getElementById('sqlite-sessions').innerHTML = sqliteData.recent_sessions.map(session => `
                    <div class="border-l-4 border-blue-500 pl-4 py-2">
                        <div class="font-medium">${session.session_id}</div>
                        <div class="text-sm text-gray-600">${session.node_count} nodes</div>
                    </div>
                `).join('');

                // Load PostgreSQL data
                const pgResponse = await fetch('/api/postgres-stats');
                const pgData = await pgResponse.json();

                document.getElementById('postgres-stats').innerHTML = `
                    <div class="grid grid-cols-2 gap-4">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-blue-600">${pgData.stats.total_items || 0}</div>
                            <div class="text-sm text-gray-600">Context Items</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-green-600">${pgData.stats.sessions || 0}</div>
                            <div class="text-sm text-gray-600">Sessions</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-purple-600">${pgData.stats.messages || 0}</div>
                            <div class="text-sm text-gray-600">Messages</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-red-600">${pgData.stats.tool_calls || 0}</div>
                            <div class="text-sm text-gray-600">Tool Calls</div>
                        </div>
                    </div>
                    <div class="mt-4 text-sm text-gray-600">
                        Last update: ${pgData.stats.latest_ingestion ? new Date(pgData.stats.latest_ingestion).toLocaleString() : 'Never'}
                    </div>
                `;

                document.getElementById('postgres-activity').innerHTML = pgData.recent_items.slice(0, 10).map(item => `
                    <div class="border-l-4 border-green-500 pl-4 py-2">
                        <div class="font-medium">${item.title}</div>
                        <div class="text-sm text-gray-600">${item.entity_type} • ${item.session_id}</div>
                        ${item.file_path ? `<div class="text-xs text-gray-500">${item.file_path}</div>` : ''}
                    </div>
                `).join('');

            } catch (error) {
                console.error('Error loading data:', error);
            }
        }

        // Load data on page load and refresh every 30 seconds
        loadData();
        setInterval(loadData, 30000);

        // Search functionality
        async function performSearch() {
            const query = document.getElementById('search-input').value.trim();
            const db = document.getElementById('search-db').value;
            const resultsDiv = document.getElementById('search-results');
            const contentDiv = document.getElementById('search-content');

            if (!query) {
                alert('Please enter a search term');
                return;
            }

            try {
                contentDiv.innerHTML = '<p class="text-gray-500">Searching...</p>';
                resultsDiv.classList.remove('hidden');

                const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&db=${db}&limit=20`);
                const data = await response.json();

                if (data.error) {
                    contentDiv.innerHTML = `<p class="text-red-500">Error: ${data.error}</p>`;
                    return;
                }

                let html = '';

                // SQLite results
                if (data.sqlite && data.sqlite.length > 0) {
                    html += `<div class="mb-6">
                        <h4 class="text-lg font-semibold text-blue-600 mb-2">SQLite Results (${data.sqlite.length})</h4>
                        <div class="space-y-2">`;

                    data.sqlite.forEach(result => {
                        html += `
                            <div class="border-l-4 border-blue-500 pl-4 py-2 bg-blue-50 cursor-pointer hover:bg-blue-100 transition-colors"
                                 onclick="showDetails('sqlite', '${result.uuid}')">
                                <div class="font-medium">${result.session_id || 'Unknown Session'}</div>
                                <div class="text-sm text-gray-600">${result.node_type} • ${new Date(result.timestamp).toLocaleString()}</div>
                                <div class="text-xs text-gray-500 mt-1">${result.preview || 'No preview available'}</div>
                                <div class="text-xs text-blue-600 mt-1">Click for details</div>
                            </div>`;
                    });

                    html += '</div></div>';
                }

                // PostgreSQL results
                if (data.postgres && data.postgres.length > 0) {
                    html += `<div class="mb-6">
                        <h4 class="text-lg font-semibold text-green-600 mb-2">PostgreSQL Results (${data.postgres.length})</h4>
                        <div class="space-y-2">`;

                    data.postgres.forEach(result => {
                        html += `
                            <div class="border-l-4 border-green-500 pl-4 py-2 bg-green-50 cursor-pointer hover:bg-green-100 transition-colors"
                                 onclick="showDetails('postgres', '${result.id}')">
                                <div class="font-medium">${result.title || result.session_id || 'Unknown'}</div>
                                <div class="text-sm text-gray-600">${result.entity_type} • ${new Date(result.timestamp).toLocaleString()}</div>
                                ${result.file_path ? `<div class="text-xs text-blue-600">${result.file_path}</div>` : ''}
                                <div class="text-xs text-gray-500 mt-1">${result.preview || 'No preview available'}</div>
                                <div class="text-xs text-green-600 mt-1">Click for details</div>
                            </div>`;
                    });

                    html += '</div></div>';
                }

                if (!html) {
                    html = '<p class="text-gray-500">No results found for your search query.</p>';
                }

                contentDiv.innerHTML = html;

            } catch (error) {
                console.error('Search error:', error);
                contentDiv.innerHTML = '<p class="text-red-500">Search failed. Please try again.</p>';
            }
        }

        // Allow Enter key to trigger search
        document.getElementById('search-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });

        // Modal functions
        async function showDetails(dbType, itemId) {
            const modal = document.getElementById('details-modal');
            const title = document.getElementById('modal-title');
            const content = document.getElementById('modal-content');

            // Show modal and loading state
            modal.classList.remove('hidden');
            title.textContent = `${dbType.toUpperCase()} Item Details`;
            content.innerHTML = '<p class="text-gray-500">Loading details...</p>';

            try {
                const response = await fetch(`/api/details/${dbType}/${itemId}`);
                const data = await response.json();

                if (data.error) {
                    content.innerHTML = `<p class="text-red-500">Error: ${data.error}</p>`;
                    return;
                }

                let html = '<div class="space-y-4">';

                // Basic info
                html += '<div class="bg-gray-50 p-4 rounded-lg">';
                html += '<h3 class="font-semibold mb-2">Basic Information</h3>';
                html += '<div class="grid grid-cols-2 gap-4 text-sm">';

                if (dbType === 'sqlite') {
                    html += `<div><strong>UUID:</strong> ${data.uuid}</div>`;
                    html += `<div><strong>Session:</strong> ${data.session_id}</div>`;
                    html += `<div><strong>Type:</strong> ${data.node_type}</div>`;
                    html += `<div><strong>Timestamp:</strong> ${new Date(data.timestamp).toLocaleString()}</div>`;
                } else {
                    html += `<div><strong>ID:</strong> ${data.id}</div>`;
                    html += `<div><strong>Session:</strong> ${data.session_id}</div>`;
                    html += `<div><strong>Type:</strong> ${data.entity_type}</div>`;
                    html += `<div><strong>Timestamp:</strong> ${new Date(data.timestamp).toLocaleString()}</div>`;
                    if (data.file_path) html += `<div class="col-span-2"><strong>File:</strong> <code>${data.file_path}</code></div>`;
                }

                html += '</div></div>';

                // Content
                if (data.content || data.raw_json) {
                    html += '<div>';
                    html += '<h3 class="font-semibold mb-2">Content</h3>';
                    html += '<div class="bg-gray-100 p-4 rounded max-h-60 overflow-y-auto text-sm">';
                    html += `<pre class="whitespace-pre-wrap">${data.content || data.raw_json}</pre>`;
                    html += '</div></div>';
                }

                // Parsed content (if available)
                if (data.parsed_content || data.parsed_source_data) {
                    html += '<div>';
                    html += '<h3 class="font-semibold mb-2">Structured Data</h3>';
                    html += '<div class="bg-blue-50 p-4 rounded max-h-60 overflow-y-auto text-sm">';
                    html += `<pre class="whitespace-pre-wrap">${JSON.stringify(data.parsed_content || data.parsed_source_data, null, 2)}</pre>`;
                    html += '</div></div>';
                }

                // Metrics (PostgreSQL only)
                if (data.metrics || data.parsed_metrics) {
                    html += '<div>';
                    html += '<h3 class="font-semibold mb-2">Metrics</h3>';
                    html += '<div class="bg-yellow-50 p-4 rounded text-sm">';
                    html += `<pre class="whitespace-pre-wrap">${JSON.stringify(data.parsed_metrics || JSON.parse(data.metrics || '{}'), null, 2)}</pre>`;
                    html += '</div></div>';
                }

                html += '</div>';
                content.innerHTML = html;

            } catch (error) {
                console.error('Details error:', error);
                content.innerHTML = '<p class="text-red-500">Failed to load details. Please try again.</p>';
            }
        }

        function closeModal() {
            document.getElementById('details-modal').classList.add('hidden');
        }

        // Close modal on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeModal();
            }
        });

        // Close modal on background click
        document.getElementById('details-modal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal();
            }
        });
    </script>
</body>
</html>
"""


@app.route("/")
def dashboard():
    """Serve the main dashboard."""
    return render_template_string(DASHBOARD_TEMPLATE)


@app.route("/api/sqlite-stats")
def sqlite_stats():
    """Get SQLite statistics."""
    return jsonify(db_manager.get_sqlite_data())


@app.route("/api/postgres-stats")
def postgres_stats():
    """Get PostgreSQL statistics."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        data = loop.run_until_complete(db_manager.get_postgres_data())
        return jsonify(data)
    finally:
        loop.close()


@app.route("/api/search")
def search():
    """Search across both databases."""
    query = request.args.get("q", "").strip()
    db_type = request.args.get("db", "both")  # 'sqlite', 'postgres', or 'both'
    limit = min(int(request.args.get("limit", 20)), 100)

    if not query:
        return jsonify({"error": "Query parameter required"}), 400

    results = {"sqlite": [], "postgres": []}

    if db_type in ["sqlite", "both"]:
        results["sqlite"] = db_manager.search_sqlite(query, limit)

    if db_type in ["postgres", "both"]:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results["postgres"] = loop.run_until_complete(
                db_manager.search_postgres(query, limit)
            )
        finally:
            loop.close()

    return jsonify(results)


@app.route("/api/details/<db_type>/<item_id>")
def get_details(db_type, item_id):
    """Get detailed information for a specific item."""
    if db_type == "sqlite":
        details = db_manager.get_sqlite_details(item_id)
    elif db_type == "postgres":
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            details = loop.run_until_complete(db_manager.get_postgres_details(item_id))
        finally:
            loop.close()
    else:
        return jsonify({"error": "Invalid database type"}), 400

    return jsonify(details)


def run_flask():
    """Run Flask application."""
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)


if __name__ == "__main__":
    # Initialize PostgreSQL connection
    async def init_async():
        await db_manager.init_postgres()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(init_async())
    except Exception as e:
        logger.error(f"Failed to initialize async components: {e}")
    finally:
        loop.close()

    logger.info("Starting Chat Analytics Dashboard on http://localhost:5000")
    run_flask()
