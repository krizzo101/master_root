#!/usr/bin/env python3
"""Initialize dashboard database connection and test integration."""

import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.append("/home/opsvi/master_root/apps/project-context/src")
sys.path.append("/home/opsvi/master_root/apps/project-context/dashboard/backend")

from database_integration import dashboard_db


async def main():
    """Initialize and test dashboard database."""
    
    print("🚀 Initializing Dashboard Database Integration")
    print("=" * 50)
    
    # Initialize database connections
    success = await dashboard_db.initialize()
    if not success:
        print("❌ Failed to initialize database connections")
        return False
    
    # Test database status
    print("\n📊 Testing Database Status:")
    status = await dashboard_db.get_status()
    print(f"Connected: {status.get('connected', False)}")
    if status.get('connected'):
        print(f"PostgreSQL: {status.get('postgres', False)}")
        print(f"Redis: {status.get('redis', False)}")
        print(f"Neo4j: {status.get('neo4j', False)}")
        print(f"Ingestion Pool: {status.get('ingestion_pool', False)}")
    else:
        print(f"Error: {status.get('error')}")
        return False
    
    # Test project stats
    print("\n📈 Testing Project Stats:")
    stats = await dashboard_db.get_project_stats()
    if 'error' in stats:
        print(f"Error: {stats['error']}")
    else:
        print(f"Total Items: {stats.get('total_items', 0)}")
        print(f"Unique Projects: {stats.get('unique_projects', 0)}")
        if stats.get('breakdown'):
            print(f"Data Types: {len(stats['breakdown'])}")
    
    # Test search functionality
    print("\n🔍 Testing Search:")
    search_results = await dashboard_db.search_context("test", limit=3)
    if 'error' in search_results:
        print(f"Error: {search_results['error']}")
    else:
        print(f"Found {search_results.get('count', 0)} results")
        
    print("\n✅ Dashboard database integration initialized successfully!")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)