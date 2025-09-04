#!/usr/bin/env python3
"""
Simple Chat Data Quality Check
Basic validation of chat data import status
"""

import json
import os
import subprocess
import sys
from datetime import datetime


def check_database_connection():
    """Check if PostgreSQL database is accessible."""
    try:
        result = subprocess.run(
            [
                "psql",
                "-h",
                "localhost",
                "-U",
                "opsvi",
                "-d",
                "unified_context",
                "-c",
                "SELECT 1;",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        return result.returncode == 0, result.stderr if result.returncode != 0 else "OK"
    except Exception as e:
        return False, str(e)


def get_basic_stats():
    """Get basic statistics from the database."""
    queries = {
        "total_items": "SELECT COUNT(*) as count FROM context_items;",
        "chat_items": "SELECT COUNT(*) as count FROM context_items WHERE adapter_id LIKE '%chat%' OR source_type = 'chat';",
        "unique_sessions": "SELECT COUNT(DISTINCT session_id) as count FROM context_items WHERE session_id IS NOT NULL;",
        "recent_items": "SELECT COUNT(*) as count FROM context_items WHERE timestamp > NOW() - INTERVAL '7 days';",
        "embedding_coverage": "SELECT COUNT(*) as with_embeddings, (SELECT COUNT(*) FROM context_items) as total FROM context_items WHERE embedding IS NOT NULL;",
    }

    stats = {}

    for stat_name, query in queries.items():
        try:
            result = subprocess.run(
                [
                    "psql",
                    "-h",
                    "localhost",
                    "-U",
                    "opsvi",
                    "-d",
                    "unified_context",
                    "-c",
                    query,
                    "-t",
                    "--csv",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                if "," in output and stat_name == "embedding_coverage":
                    # Handle embedding coverage special case
                    with_emb, total = output.split(",")
                    stats[stat_name] = {
                        "with_embeddings": int(with_emb),
                        "total": int(total),
                        "percentage": round(
                            (int(with_emb) / max(1, int(total))) * 100, 2
                        ),
                    }
                else:
                    stats[stat_name] = int(output) if output.isdigit() else 0
            else:
                stats[stat_name] = f"Error: {result.stderr}"

        except Exception as e:
            stats[stat_name] = f"Error: {str(e)}"

    return stats


def check_entity_extraction():
    """Check entity extraction statistics."""
    query = """
    SELECT entity_type, COUNT(*) as count
    FROM context_item_entities cie
    JOIN context_items ci ON cie.item_id = ci.id
    WHERE ci.adapter_id LIKE '%chat%' OR ci.source_type = 'chat'
    GROUP BY entity_type
    ORDER BY count DESC;
    """

    try:
        result = subprocess.run(
            [
                "psql",
                "-h",
                "localhost",
                "-U",
                "opsvi",
                "-d",
                "unified_context",
                "-c",
                query,
                "--csv",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")[1:]  # Skip header
            entity_stats = {}
            for line in lines:
                if "," in line:
                    entity_type, count = line.split(",", 1)
                    entity_stats[entity_type] = int(count)
            return entity_stats
        else:
            return {"error": result.stderr}

    except Exception as e:
        return {"error": str(e)}


def generate_quality_assessment(stats, entities):
    """Generate overall quality assessment."""
    assessment = {
        "timestamp": datetime.now().isoformat(),
        "status": "UNKNOWN",
        "quality_score": 0,
        "findings": [],
        "recommendations": [],
    }

    # Check if chat data exists
    chat_items = stats.get("chat_items", 0)
    if chat_items == 0:
        assessment["status"] = "NO_DATA"
        assessment["findings"].append("No chat data found in database")
        assessment["recommendations"].append("Execute chat import process")
        return assessment

    # Calculate quality indicators
    scores = []

    # Data presence score
    if chat_items > 1000:
        scores.append(100)
        assessment["findings"].append(f"Good data volume: {chat_items:,} chat items")
    elif chat_items > 100:
        scores.append(80)
        assessment["findings"].append(
            f"Moderate data volume: {chat_items:,} chat items"
        )
    else:
        scores.append(40)
        assessment["findings"].append(f"Low data volume: {chat_items:,} chat items")
        assessment["recommendations"].append("Consider importing more chat data")

    # Session diversity score
    unique_sessions = stats.get("unique_sessions", 0)
    if unique_sessions > 100:
        scores.append(100)
        assessment["findings"].append(
            f"Good session diversity: {unique_sessions} unique sessions"
        )
    elif unique_sessions > 10:
        scores.append(70)
        assessment["findings"].append(
            f"Moderate session diversity: {unique_sessions} unique sessions"
        )
    else:
        scores.append(30)
        assessment["findings"].append(
            f"Low session diversity: {unique_sessions} unique sessions"
        )

    # Embedding coverage score
    embedding_data = stats.get("embedding_coverage", {})
    if isinstance(embedding_data, dict):
        coverage = embedding_data.get("percentage", 0)
        if coverage >= 95:
            scores.append(100)
            assessment["findings"].append(f"Excellent embedding coverage: {coverage}%")
        elif coverage >= 80:
            scores.append(80)
            assessment["findings"].append(f"Good embedding coverage: {coverage}%")
        elif coverage >= 50:
            scores.append(60)
            assessment["findings"].append(f"Moderate embedding coverage: {coverage}%")
            assessment["recommendations"].append(
                "Improve embedding generation coverage"
            )
        else:
            scores.append(20)
            assessment["findings"].append(f"Low embedding coverage: {coverage}%")
            assessment["recommendations"].append("Fix embedding generation issues")
    else:
        scores.append(0)
        assessment["findings"].append("Unable to assess embedding coverage")

    # Entity extraction score
    if isinstance(entities, dict) and not entities.get("error"):
        total_entities = sum(entities.values())
        entity_types = len(entities)

        if total_entities > 5000 and entity_types >= 5:
            scores.append(100)
            assessment["findings"].append(
                f"Excellent entity extraction: {total_entities:,} entities, {entity_types} types"
            )
        elif total_entities > 1000 and entity_types >= 3:
            scores.append(80)
            assessment["findings"].append(
                f"Good entity extraction: {total_entities:,} entities, {entity_types} types"
            )
        elif total_entities > 100:
            scores.append(60)
            assessment["findings"].append(
                f"Moderate entity extraction: {total_entities:,} entities, {entity_types} types"
            )
            assessment["recommendations"].append("Optimize entity extraction patterns")
        else:
            scores.append(30)
            assessment["findings"].append(
                f"Low entity extraction: {total_entities:,} entities"
            )
            assessment["recommendations"].append(
                "Review entity extraction configuration"
            )
    else:
        scores.append(0)
        assessment["findings"].append("Entity extraction data unavailable")

    # Calculate overall score
    assessment["quality_score"] = round(sum(scores) / len(scores), 1) if scores else 0

    # Determine status
    if assessment["quality_score"] >= 90:
        assessment["status"] = "EXCELLENT"
    elif assessment["quality_score"] >= 80:
        assessment["status"] = "GOOD"
    elif assessment["quality_score"] >= 70:
        assessment["status"] = "ACCEPTABLE"
    elif assessment["quality_score"] >= 50:
        assessment["status"] = "NEEDS_IMPROVEMENT"
    else:
        assessment["status"] = "POOR"

    return assessment


def main():
    """Main validation execution."""
    print("🔍 Simple Chat Data Quality Check")
    print("=" * 50)

    # Check database connection
    print("📊 Checking database connection...")
    db_ok, db_msg = check_database_connection()

    if not db_ok:
        print(f"❌ Database connection failed: {db_msg}")
        print("\nRecommendation: Ensure PostgreSQL is running and accessible")
        return

    print("✅ Database connection successful")

    # Get basic statistics
    print("\n📈 Gathering statistics...")
    stats = get_basic_stats()

    # Check entity extraction
    print("🔍 Checking entity extraction...")
    entities = check_entity_extraction()

    # Generate assessment
    assessment = generate_quality_assessment(stats, entities)

    # Print results
    print(f"\n📋 QUALITY ASSESSMENT")
    print(f"Status: {assessment['status']}")
    print(f"Quality Score: {assessment['quality_score']}/100")

    print(f"\n📊 DATA STATISTICS")
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"{key}: {value}")
        else:
            print(f"{key}: {value:,}" if isinstance(value, int) else f"{key}: {value}")

    if isinstance(entities, dict) and not entities.get("error"):
        print(f"\n🏷️ ENTITY TYPES FOUND ({len(entities)} types)")
        for entity_type, count in sorted(
            entities.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {entity_type}: {count:,}")

    print(f"\n🔍 KEY FINDINGS")
    for finding in assessment["findings"]:
        print(f"  • {finding}")

    if assessment["recommendations"]:
        print(f"\n💡 RECOMMENDATIONS")
        for rec in assessment["recommendations"]:
            print(f"  • {rec}")

    # Save detailed report
    report = {"assessment": assessment, "statistics": stats, "entities": entities}

    report_file = (
        f"chat_data_quality_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n📄 Report saved to: {report_file}")
    print("✅ Quality check complete!")


if __name__ == "__main__":
    main()
