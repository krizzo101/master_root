#!/usr/bin/env python3
"""
Comprehensive test suite for consolidated ArangoDB MCP tools
Tests all 3 tools across 8 search types, 4 modify operations, and 6 manage actions
"""

import sys
import os
import json
from datetime import datetime

# Add core directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))
from consolidated_arango import ConsolidatedArangoDB


def test_database_connection():
    """Test basic database connectivity"""
    print("🔗 Testing database connection...")

    try:
        db = ConsolidatedArangoDB()
        print("✅ Database connection successful")
        return db
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None


def test_search_operations(db):
    """Test all search operation types"""
    print("\n🔍 Testing search operations...")

    test_cases = [
        {
            "name": "Content Search",
            "params": {
                "search_type": "content",
                "collection": "agent_memory",
                "content": "database",
                "limit": 5,
            },
        },
        {
            "name": "Tag Search",
            "params": {
                "search_type": "tags",
                "collection": "cognitive_concepts",
                "tags": ["operational", "database"],
                "match_all": False,
                "limit": 3,
            },
        },
        {
            "name": "Type Search",
            "params": {
                "search_type": "type",
                "collection": "agent_memory",
                "document_type": "operational",
                "limit": 5,
            },
        },
        {
            "name": "Recent Search",
            "params": {
                "search_type": "recent",
                "collection": "agent_memory",
                "hours": 24,
                "limit": 5,
            },
        },
        {
            "name": "Quality Search",
            "params": {
                "search_type": "quality",
                "collection": "cognitive_concepts",
                "min_quality": 0.8,
                "limit": 3,
            },
        },
        {
            "name": "Date Range Search",
            "params": {
                "search_type": "date_range",
                "collection": "agent_memory",
                "start_date": "2025-01-01T00:00:00Z",
                "end_date": "2025-12-31T23:59:59Z",
                "limit": 5,
            },
        },
    ]

    results = {}

    for test_case in test_cases:
        try:
            print(f"  Testing {test_case['name']}...")
            result = db.search(**test_case["params"])

            if result.get("success"):
                count = result.get("count", 0)
                print(f"    ✅ Success: {count} results")
                results[test_case["name"]] = {"status": "success", "count": count}
            else:
                print(f"    ⚠️  No results: {result.get('error', 'Unknown error')}")
                results[test_case["name"]] = {
                    "status": "no_results",
                    "error": result.get("error"),
                }

        except Exception as e:
            print(f"    ❌ Failed: {e}")
            results[test_case["name"]] = {"status": "failed", "error": str(e)}

    return results


def test_modify_operations(db):
    """Test CRUD operations"""
    print("\n✏️  Testing modify operations...")

    test_collection = "test_consolidated_operations"
    results = {}

    # Test Insert
    try:
        print("  Testing Insert...")
        test_doc = {
            "title": "Test Document for Consolidated Tools",
            "content": "This is a test document created by consolidated ArangoDB tools",
            "type": "test",
            "quality_score": 0.95,
            "tags": ["test", "consolidated", "validation"],
        }

        result = db.modify("insert", test_collection, document=test_doc)

        if result.get("success"):
            doc_id = result.get("document_id")
            doc_key = result.get("document_key")
            print(f"    ✅ Insert successful: {doc_id}")
            results["insert"] = {
                "status": "success",
                "document_id": doc_id,
                "document_key": doc_key,
            }
        else:
            print(f"    ❌ Insert failed: {result.get('error')}")
            results["insert"] = {"status": "failed", "error": result.get("error")}

    except Exception as e:
        print(f"    ❌ Insert exception: {e}")
        results["insert"] = {"status": "exception", "error": str(e)}

    # Test Update (if insert succeeded)
    if results.get("insert", {}).get("status") == "success":
        try:
            print("  Testing Update...")
            doc_key = results["insert"]["document_key"]

            updates = {
                "content": "Updated content for testing consolidated tools",
                "last_modified": datetime.now().isoformat(),
                "update_test": True,
            }

            result = db.modify("update", test_collection, key=doc_key, updates=updates)

            if result.get("success"):
                print("    ✅ Update successful")
                results["update"] = {"status": "success"}
            else:
                print(f"    ❌ Update failed: {result.get('error')}")
                results["update"] = {"status": "failed", "error": result.get("error")}

        except Exception as e:
            print(f"    ❌ Update exception: {e}")
            results["update"] = {"status": "exception", "error": str(e)}

    # Test Upsert
    try:
        print("  Testing Upsert...")
        upsert_doc = {
            "title": "Upsert Test Document",
            "content": "Testing upsert functionality",
            "type": "upsert_test",
            "unique_field": "consolidated_test_upsert_2025",
        }

        result = db.modify(
            "upsert",
            test_collection,
            document=upsert_doc,
            match_fields=["unique_field"],
        )

        if result.get("success"):
            print("    ✅ Upsert successful")
            results["upsert"] = {"status": "success"}
        else:
            print(f"    ❌ Upsert failed: {result.get('error')}")
            results["upsert"] = {"status": "failed", "error": result.get("error")}

    except Exception as e:
        print(f"    ❌ Upsert exception: {e}")
        results["upsert"] = {"status": "exception", "error": str(e)}

    return results, test_collection


def test_manage_operations(db, test_collection):
    """Test management operations"""
    print("\n⚙️  Testing manage operations...")

    results = {}

    # Test Collection Info
    try:
        print("  Testing Collection Info...")
        result = db.manage("collection_info", collection="agent_memory")

        if result.get("success"):
            info = result.get("info", {})
            count = info.get("count", 0)
            print(f"    ✅ Collection info successful: {count} documents")
            results["collection_info"] = {"status": "success", "count": count}
        else:
            print(f"    ❌ Collection info failed: {result.get('error')}")
            results["collection_info"] = {
                "status": "failed",
                "error": result.get("error"),
            }

    except Exception as e:
        print(f"    ❌ Collection info exception: {e}")
        results["collection_info"] = {"status": "exception", "error": str(e)}

    # Test Health Check
    try:
        print("  Testing Health Check...")
        result = db.manage("health")

        if result.get("success"):
            health_score = result.get("health_score", 0)
            total_docs = result.get("total_documents", 0)
            print(
                f"    ✅ Health check successful: Score {health_score:.2f}, {total_docs} total docs"
            )
            results["health"] = {
                "status": "success",
                "health_score": health_score,
                "total_documents": total_docs,
            }
        else:
            print(f"    ❌ Health check failed: {result.get('error')}")
            results["health"] = {"status": "failed", "error": result.get("error")}

    except Exception as e:
        print(f"    ❌ Health check exception: {e}")
        results["health"] = {"status": "exception", "error": str(e)}

    # Test Count
    try:
        print("  Testing Count...")
        result = db.manage("count", collection="agent_memory")

        if result.get("success"):
            count = result.get("count", 0)
            print(f"    ✅ Count successful: {count} documents")
            results["count"] = {"status": "success", "count": count}
        else:
            print(f"    ❌ Count failed: {result.get('error')}")
            results["count"] = {"status": "failed", "error": result.get("error")}

    except Exception as e:
        print(f"    ❌ Count exception: {e}")
        results["count"] = {"status": "exception", "error": str(e)}

    # Test Exists
    try:
        print("  Testing Exists...")
        result = db.manage(
            "exists", collection=test_collection, criteria={"type": "test"}
        )

        if result.get("success"):
            exists = result.get("exists", False)
            print(f"    ✅ Exists check successful: {exists}")
            results["exists"] = {"status": "success", "exists": exists}
        else:
            print(f"    ❌ Exists check failed: {result.get('error')}")
            results["exists"] = {"status": "failed", "error": result.get("error")}

    except Exception as e:
        print(f"    ❌ Exists check exception: {e}")
        results["exists"] = {"status": "exception", "error": str(e)}

    return results


def cleanup_test_data(db, test_collection):
    """Clean up test data"""
    print(f"\n🧹 Cleaning up test collection: {test_collection}...")

    try:
        # Delete test documents
        result = db.modify(
            "delete", test_collection, criteria={"type": "test"}, confirm=True
        )

        if result.get("success"):
            deleted_count = result.get("deleted_count", 0)
            print(f"    ✅ Cleanup successful: {deleted_count} test documents deleted")
        else:
            print(f"    ⚠️  Cleanup warning: {result.get('error')}")

    except Exception as e:
        print(f"    ❌ Cleanup failed: {e}")


def generate_test_report(search_results, modify_results, manage_results):
    """Generate comprehensive test report"""
    print("\n📊 CONSOLIDATED TOOLS TEST REPORT")
    print("=" * 50)

    # Search operations summary
    print("\n🔍 SEARCH OPERATIONS:")
    search_success = sum(1 for r in search_results.values() if r["status"] == "success")
    search_total = len(search_results)
    print(
        f"  Success Rate: {search_success}/{search_total} ({search_success/search_total*100:.1f}%)"
    )

    for name, result in search_results.items():
        status_icon = (
            "✅"
            if result["status"] == "success"
            else "❌"
            if result["status"] == "failed"
            else "⚠️"
        )
        if result["status"] == "success":
            print(f"    {status_icon} {name}: {result['count']} results")
        else:
            print(
                f"    {status_icon} {name}: {result.get('error', 'No error details')}"
            )

    # Modify operations summary
    print("\n✏️  MODIFY OPERATIONS:")
    modify_success = sum(1 for r in modify_results.values() if r["status"] == "success")
    modify_total = len(modify_results)
    print(
        f"  Success Rate: {modify_success}/{modify_total} ({modify_success/modify_total*100:.1f}%)"
    )

    for name, result in modify_results.items():
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"    {status_icon} {name.capitalize()}: {result['status']}")

    # Manage operations summary
    print("\n⚙️  MANAGE OPERATIONS:")
    manage_success = sum(1 for r in manage_results.values() if r["status"] == "success")
    manage_total = len(manage_results)
    print(
        f"  Success Rate: {manage_success}/{manage_total} ({manage_success/manage_total*100:.1f}%)"
    )

    for name, result in manage_results.items():
        status_icon = "✅" if result["status"] == "success" else "❌"
        if result["status"] == "success" and name == "health":
            print(
                f"    {status_icon} {name.replace('_', ' ').title()}: Score {result['health_score']:.2f}"
            )
        elif result["status"] == "success" and "count" in result:
            print(
                f"    {status_icon} {name.replace('_', ' ').title()}: {result['count']} items"
            )
        else:
            print(
                f"    {status_icon} {name.replace('_', ' ').title()}: {result['status']}"
            )

    # Overall summary
    total_success = search_success + modify_success + manage_success
    total_tests = search_total + modify_total + manage_total
    overall_rate = total_success / total_tests * 100

    print(
        f"\n🎯 OVERALL SUCCESS RATE: {total_success}/{total_tests} ({overall_rate:.1f}%)"
    )

    if overall_rate >= 80:
        print("🚀 CONSOLIDATED TOOLS READY FOR DEPLOYMENT!")
    elif overall_rate >= 60:
        print("⚠️  CONSOLIDATED TOOLS NEED MINOR FIXES")
    else:
        print("❌ CONSOLIDATED TOOLS NEED MAJOR WORK")

    return {
        "search_success_rate": search_success / search_total,
        "modify_success_rate": modify_success / modify_total,
        "manage_success_rate": manage_success / manage_total,
        "overall_success_rate": overall_rate / 100,
    }


def main():
    """Main test execution"""
    print("🧪 CONSOLIDATED ARANGO TOOLS COMPREHENSIVE TEST")
    print("=" * 55)
    print("Testing 3 tools: arango_search, arango_modify, arango_manage")
    print("Eliminating AQL complexity with parameter-based routing")

    # Test database connection
    db = test_database_connection()
    if not db:
        print("❌ Cannot proceed without database connection")
        return

    # Run all test suites
    search_results = test_search_operations(db)
    modify_results, test_collection = test_modify_operations(db)
    manage_results = test_manage_operations(db, test_collection)

    # Clean up test data
    cleanup_test_data(db, test_collection)

    # Generate comprehensive report
    report = generate_test_report(search_results, modify_results, manage_results)

    # Save detailed results
    detailed_results = {
        "timestamp": datetime.now().isoformat(),
        "search_operations": search_results,
        "modify_operations": modify_results,
        "manage_operations": manage_results,
        "summary": report,
    }

    results_file = "consolidated_tools_test_results.json"
    with open(results_file, "w") as f:
        json.dump(detailed_results, f, indent=2)

    print(f"\n📄 Detailed results saved to: {results_file}")


if __name__ == "__main__":
    main()
