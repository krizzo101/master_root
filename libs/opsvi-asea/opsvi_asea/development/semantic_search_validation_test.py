#!/usr/bin/env python3
"""
Comprehensive Semantic Search Validation Test
Tests all implemented semantic search capabilities in the cognitive database architecture
"""

import requests
from arango import ArangoClient
from datetime import datetime

# Database configuration
ARANGO_HOST = "http://127.0.0.1:8531"
DATABASE = "asea_prod_db"
USERNAME = "root"
PASSWORD = "arango_production_password"


def test_database_connection():
    """Test basic database connectivity"""
    print("=" * 60)
    print("1. TESTING DATABASE CONNECTION")
    print("=" * 60)

    try:
        client = ArangoClient(hosts=ARANGO_HOST)
        db = client.db(DATABASE, username=USERNAME, password=PASSWORD)

        # Test collections
        collections = db.collections()
        collection_names = [
            col["name"] for col in collections if not col["name"].startswith("_")
        ]

        print(f"✓ Connected to ArangoDB at {ARANGO_HOST}")
        print(f"✓ Database: {DATABASE}")
        print(f"✓ Collections found: {len(collection_names)}")
        print(
            f"  Core collections: {[name for name in collection_names if name in ['agent_memory', 'cognitive_concepts', 'semantic_relationships']]}"
        )

        return db
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return None


def test_analyzers(db):
    """Test custom analyzers"""
    print("\n" + "=" * 60)
    print("2. TESTING CUSTOM ANALYZERS")
    print("=" * 60)

    try:
        # Test analyzer existence
        analyzers_query = "FOR analyzer IN _analyzers FILTER analyzer.name LIKE '%asea_prod_db::%' RETURN analyzer.name"
        cursor = db.aql.execute(analyzers_query)
        analyzers = list(cursor)

        expected_analyzers = [
            "asea_prod_db::agent_memory_analyzer",
            "asea_prod_db::operational_knowledge_analyzer",
            "asea_prod_db::semantic_concepts_analyzer",
        ]

        print(f"✓ Found {len(analyzers)} custom analyzers:")
        for analyzer in analyzers:
            status = "✓" if analyzer in expected_analyzers else "?"
            print(f"  {status} {analyzer}")

        # Test analyzer functionality
        test_query = """
        RETURN TOKENS("autonomous behavioral validation", "asea_prod_db::agent_memory_analyzer")
        """
        cursor = db.aql.execute(test_query)
        tokens = list(cursor)[0]
        print(
            f"✓ Analyzer test - tokenized 'autonomous behavioral validation': {tokens}"
        )

        return len(analyzers) >= 3
    except Exception as e:
        print(f"✗ Analyzer test failed: {e}")
        return False


def test_arangosearch_view(db):
    """Test ArangoSearch view"""
    print("\n" + "=" * 60)
    print("3. TESTING ARANGOSEARCH VIEW")
    print("=" * 60)

    try:
        # Check view existence
        views_query = "FOR view IN _views RETURN view.name"
        cursor = db.aql.execute(views_query)
        views = list(cursor)

        if "cognitive_search" in views:
            print("✓ cognitive_search view exists")

            # Test view search
            search_query = """
            FOR doc IN cognitive_search
              SEARCH "autonomous" IN doc.tags OR "behavioral" IN doc.tags
              LIMIT 3
              RETURN {
                collection: PARSE_IDENTIFIER(doc._id).collection,
                title: doc.title,
                tags: doc.tags
              }
            """
            cursor = db.aql.execute(search_query)
            results = list(cursor)

            print(f"✓ View search returned {len(results)} results")
            for result in results:
                print(f"  - {result['collection']}: {result['title'][:50]}...")

            return True
        else:
            print("✗ cognitive_search view not found")
            return False

    except Exception as e:
        print(f"✗ ArangoSearch view test failed: {e}")
        return False


def test_semantic_relationships(db):
    """Test semantic relationships and compound learning"""
    print("\n" + "=" * 60)
    print("4. TESTING SEMANTIC RELATIONSHIPS")
    print("=" * 60)

    try:
        # Count relationships
        count_query = "RETURN LENGTH(FOR rel IN semantic_relationships RETURN rel)"
        cursor = db.aql.execute(count_query)
        total_relationships = list(cursor)[0]

        # High compound learning relationships
        high_potential_query = """
        FOR rel IN semantic_relationships
          FILTER rel.compound_learning_potential >= 0.8
          RETURN {
            from: DOCUMENT(rel._from).knowledge_content.title,
            to: DOCUMENT(rel._to).knowledge_content.title,
            type: rel.relationship_type,
            potential: rel.compound_learning_potential
          }
        """
        cursor = db.aql.execute(high_potential_query)
        high_potential = list(cursor)

        print(f"✓ Total semantic relationships: {total_relationships}")
        print(f"✓ High compound learning potential (≥0.8): {len(high_potential)}")

        if high_potential:
            print("  Top compound learning relationships:")
            for rel in high_potential[:3]:
                print(
                    f"    {rel['from'][:30]}... → {rel['to'][:30]}... ({rel['potential']:.2f})"
                )

        return len(high_potential) > 0
    except Exception as e:
        print(f"✗ Semantic relationships test failed: {e}")
        return False


def test_foxx_service():
    """Test Foxx service endpoints"""
    print("\n" + "=" * 60)
    print("5. TESTING FOXX SERVICE API")
    print("=" * 60)

    base_url = f"{ARANGO_HOST}/_db/{DATABASE}/agent_memory_api"
    auth = (USERNAME, PASSWORD)

    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/health", auth=auth, timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"✓ Health check: {health['status']}")
            print(f"✓ Service version: {health['version']}")
            print(f"✓ Features: {', '.join(health['features'])}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False

        # Test semantic search
        response = requests.get(
            f"{base_url}/search/semantic/autonomous", auth=auth, timeout=10
        )
        if response.status_code == 200:
            search_results = response.json()
            print(
                f"✓ Semantic search: {search_results['results']['total_count']} results"
            )
            print(f"  - Memories: {len(search_results['results']['memories'])}")
            print(f"  - Concepts: {len(search_results['results']['concepts'])}")
        else:
            print(f"✗ Semantic search failed: {response.status_code}")

        # Test cognitive analytics
        response = requests.get(
            f"{base_url}/analytics/cognitive-overview", auth=auth, timeout=10
        )
        if response.status_code == 200:
            analytics = response.json()
            print("✓ Cognitive analytics available")
            print(
                f"  - Cognitive maturity score: {analytics['analysis_summary']['cognitive_maturity_score']:.3f}"
            )
            print(
                f"  - Knowledge validation rate: {analytics['analysis_summary']['knowledge_validation_rate']:.3f}"
            )
        else:
            print(f"✗ Cognitive analytics failed: {response.status_code}")

        return True
    except Exception as e:
        print(f"✗ Foxx service test failed: {e}")
        return False


def test_compound_learning_discovery(db):
    """Test compound learning discovery capabilities"""
    print("\n" + "=" * 60)
    print("6. TESTING COMPOUND LEARNING DISCOVERY")
    print("=" * 60)

    try:
        # Behavioral domain compound learning
        behavioral_query = """
        FOR concept IN cognitive_concepts
          FILTER concept.knowledge_domain == "behavioral"
          FOR rel IN semantic_relationships
            FILTER rel._from == concept._id AND rel.compound_learning_potential >= 0.8
            LET target = DOCUMENT(rel._to)
            RETURN {
              source: concept.knowledge_content.title,
              target: target.knowledge_content.title,
              learning_potential: rel.compound_learning_potential,
              relationship_type: rel.relationship_type
            }
        """
        cursor = db.aql.execute(behavioral_query)
        behavioral_learning = list(cursor)

        print(
            f"✓ Behavioral domain compound learning opportunities: {len(behavioral_learning)}"
        )

        if behavioral_learning:
            avg_potential = sum(
                rel["learning_potential"] for rel in behavioral_learning
            ) / len(behavioral_learning)
            print(f"✓ Average learning potential: {avg_potential:.3f}")

            print("  Top learning opportunities:")
            for rel in behavioral_learning[:3]:
                print(
                    f"    {rel['source'][:25]}... → {rel['target'][:25]}... ({rel['learning_potential']:.2f})"
                )

        # Cross-domain analysis
        domain_query = """
        FOR domain IN ["behavioral", "infrastructure", "research", "operational", "technical"]
          LET domain_concepts = LENGTH(FOR c IN cognitive_concepts FILTER c.knowledge_domain == domain RETURN c)
          LET domain_relationships = LENGTH(
            FOR rel IN semantic_relationships
              LET from_concept = DOCUMENT(rel._from)
              FILTER from_concept.knowledge_domain == domain
              RETURN rel
          )
          RETURN {
            domain: domain,
            concepts: domain_concepts,
            relationships: domain_relationships,
            connectivity: domain_concepts > 0 ? domain_relationships / domain_concepts : 0
          }
        """
        cursor = db.aql.execute(domain_query)
        domain_analysis = list(cursor)

        print("✓ Domain connectivity analysis:")
        for domain in domain_analysis:
            if domain["concepts"] > 0:
                print(
                    f"    {domain['domain']}: {domain['concepts']} concepts, {domain['relationships']} relationships ({domain['connectivity']:.2f} ratio)"
                )

        return len(behavioral_learning) > 0
    except Exception as e:
        print(f"✗ Compound learning discovery test failed: {e}")
        return False


def run_comprehensive_test():
    """Run all semantic search validation tests"""
    print("COGNITIVE DATABASE SEMANTIC SEARCH VALIDATION")
    print("=" * 60)
    print(f"Test started at: {datetime.now().isoformat()}")

    test_results = []

    # Run tests
    db = test_database_connection()
    test_results.append(("Database Connection", db is not None))

    if db:
        test_results.append(("Custom Analyzers", test_analyzers(db)))
        test_results.append(("ArangoSearch View", test_arangosearch_view(db)))
        test_results.append(("Semantic Relationships", test_semantic_relationships(db)))
        test_results.append(
            ("Compound Learning Discovery", test_compound_learning_discovery(db))
        )

    test_results.append(("Foxx Service API", test_foxx_service()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 ALL SEMANTIC SEARCH CAPABILITIES VALIDATED!")
    else:
        print("⚠️  Some tests failed - check implementation")

    print(f"\nTest completed at: {datetime.now().isoformat()}")

    return passed == total


if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)
