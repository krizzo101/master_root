#!/usr/bin/env python3
"""
Ingestion script for Claude chat logs
Parses and stores all JSONL files from the master_root project
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from tqdm import tqdm

# Add libs directory to path
sys.path.append("/home/opsvi/master_root/libs")

from chat_report_generator import ChatReportGenerator
from chat_taxonomy_parser import ChatLogParser, ChatLogStorage

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "database": os.environ.get("DB_NAME", "chat_logs"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "postgres"),
}


def setup_database():
    """Create database if it doesn't exist"""
    # Connect to postgres database to create our database
    admin_config = DB_CONFIG.copy()
    admin_config["database"] = "postgres"

    try:
        conn = psycopg2.connect(**admin_config)
        conn.autocommit = True
        cur = conn.cursor()

        # Check if database exists
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG["database"],)
        )

        if not cur.fetchone():
            logger.info(f"Creating database {DB_CONFIG['database']}")
            cur.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
        else:
            logger.info(f"Database {DB_CONFIG['database']} already exists")

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        logger.error(f"Error setting up database: {e}")
        return False

    # Now create schema in our database
    try:
        storage = ChatLogStorage(DB_CONFIG)
        storage.connect()
        storage.create_schema()
        storage.close()
        logger.info("Database schema created/verified")
        return True

    except psycopg2.Error as e:
        logger.error(f"Error creating schema: {e}")
        return False


def get_jsonl_files():
    """Get all JSONL files from the project directory"""
    project_dir = Path.home() / ".claude" / "projects" / "-home-opsvi-master-root"

    if not project_dir.exists():
        logger.error(f"Project directory not found: {project_dir}")
        return []

    jsonl_files = list(project_dir.glob("*.jsonl"))
    logger.info(f"Found {len(jsonl_files)} JSONL files")
    return sorted(jsonl_files)


def process_batch(files_batch, storage, batch_num, total_batches):
    """Process a batch of files"""
    logger.info(
        f"Processing batch {batch_num}/{total_batches} ({len(files_batch)} files)"
    )

    parser = ChatLogParser()

    for file_path in tqdm(files_batch, desc=f"Batch {batch_num}"):
        try:
            # Parse the file
            parser.parse_jsonl_file(file_path)

        except Exception as e:
            logger.error(f"Error parsing {file_path.name}: {e}")
            continue

    # Store all parsed data
    try:
        storage.store_parsed_data(parser)
        logger.info(
            f"Stored batch {batch_num}: {len(parser.nodes)} nodes, "
            f"{len(parser.tool_calls)} tool calls, "
            f"{len(parser.file_operations)} file operations"
        )
        return True

    except Exception as e:
        logger.error(f"Error storing batch {batch_num}: {e}")
        return False


def main():
    """Main ingestion process"""
    logger.info("Starting chat log ingestion")

    # Setup database
    if not setup_database():
        logger.error("Failed to setup database")
        return 1

    # Get all JSONL files
    jsonl_files = get_jsonl_files()
    if not jsonl_files:
        logger.error("No JSONL files found")
        return 1

    # Connect to storage
    storage = ChatLogStorage(DB_CONFIG)
    storage.connect()

    # Process files in batches to manage memory
    batch_size = 20  # Process 20 files at a time
    total_batches = (len(jsonl_files) + batch_size - 1) // batch_size

    success_count = 0
    for i in range(0, len(jsonl_files), batch_size):
        batch_num = (i // batch_size) + 1
        files_batch = jsonl_files[i : i + batch_size]

        if process_batch(files_batch, storage, batch_num, total_batches):
            success_count += 1

    storage.close()

    logger.info(
        f"Ingestion complete: {success_count}/{total_batches} batches processed successfully"
    )

    # Generate summary report
    if success_count > 0:
        generate_summary_report()

    return 0


def generate_summary_report():
    """Generate a summary report after ingestion"""
    logger.info("Generating summary report")

    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Get overall statistics
        stats_query = """
        SELECT
            COUNT(DISTINCT session_id) as total_sessions,
            COUNT(DISTINCT uuid) as total_nodes,
            COUNT(DISTINCT CASE WHEN node_type = 'user' THEN uuid END) as user_messages,
            COUNT(DISTINCT CASE WHEN node_type = 'assistant' THEN uuid END) as assistant_messages,
            MIN(timestamp) as earliest_timestamp,
            MAX(timestamp) as latest_timestamp
        FROM nodes
        """
        cur.execute(stats_query)
        stats = cur.fetchone()

        # Get tool usage statistics
        tool_query = """
        SELECT
            tool_name,
            COUNT(*) as usage_count
        FROM tool_calls
        GROUP BY tool_name
        ORDER BY usage_count DESC
        LIMIT 10
        """
        cur.execute(tool_query)
        top_tools = cur.fetchall()

        # Get file statistics
        file_query = """
        SELECT
            COUNT(DISTINCT file_path) as unique_files,
            COUNT(*) as total_operations,
            COUNT(CASE WHEN operation = 'read' THEN 1 END) as reads,
            COUNT(CASE WHEN operation = 'write' THEN 1 END) as writes,
            COUNT(CASE WHEN operation = 'edit' THEN 1 END) as edits
        FROM file_operations
        """
        cur.execute(file_query)
        file_stats = cur.fetchone()

        cur.close()
        conn.close()

        # Print summary
        print("\n" + "=" * 60)
        print("CHAT LOG INGESTION SUMMARY")
        print("=" * 60)
        print(f"Total Sessions:        {stats[0]:,}")
        print(f"Total Nodes:           {stats[1]:,}")
        print(f"User Messages:         {stats[2]:,}")
        print(f"Assistant Messages:    {stats[3]:,}")
        print(f"Date Range:            {stats[4]} to {stats[5]}")
        print("\nTOP TOOLS USED:")
        for tool_name, count in top_tools:
            print(f"  {tool_name:30} {count:,}")
        print(f"\nFILE OPERATIONS:")
        print(f"  Unique Files:        {file_stats[0]:,}")
        print(f"  Total Operations:    {file_stats[1]:,}")
        print(f"  Reads:               {file_stats[2]:,}")
        print(f"  Writes:              {file_stats[3]:,}")
        print(f"  Edits:               {file_stats[4]:,}")
        print("=" * 60)

        # Save summary to file
        summary_path = Path("/tmp/chat_ingestion_summary.txt")
        with open(summary_path, "w") as f:
            f.write(f"Chat Log Ingestion Summary\n")
            f.write(f"Generated: {datetime.now()}\n\n")
            f.write(f"Total Sessions: {stats[0]}\n")
            f.write(f"Total Nodes: {stats[1]}\n")
            f.write(f"User Messages: {stats[2]}\n")
            f.write(f"Assistant Messages: {stats[3]}\n")
            f.write(f"Date Range: {stats[4]} to {stats[5]}\n")

        logger.info(f"Summary saved to {summary_path}")

    except Exception as e:
        logger.error(f"Error generating summary: {e}")


if __name__ == "__main__":
    sys.exit(main())
