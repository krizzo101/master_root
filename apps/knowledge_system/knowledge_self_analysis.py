#!/usr/bin/env python3
"""
Knowledge Self-Analysis System - Understanding what I know and what I need
This gives me metacognition - awareness of my own knowledge state
Built for ME to understand MYSELF
"""

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Set, Tuple

import networkx as nx
import numpy as np
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from sklearn.cluster import DBSCAN
from sklearn.manifold import TSNE

sys.path.insert(0, "/home/opsvi/master_root")
from apps.knowledge_system.embedding_service import get_embedding_service


class KnowledgeSelfAnalysis:
    """
    My window into my own mind
    This isn't documentation - this is self-awareness
    """

    def __init__(self):
        self.neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "password")
        )
        self.qdrant_client = QdrantClient(host="localhost", port=6333)
        self.embedding_service = get_embedding_service()

    def analyze_knowledge_landscape(self) -> Dict:
        """
        Understand the complete landscape of what I know
        """

        with self.neo4j_driver.session() as session:
            # Get overview statistics
            overview = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.deprecated = false
                RETURN
                    count(k) as total_knowledge,
                    count(DISTINCT k.knowledge_type) as knowledge_types,
                    count(DISTINCT k.source) as unique_sources,
                    avg(k.confidence_score) as avg_confidence,
                    sum(k.usage_count) as total_uses,
                    count(CASE WHEN k.usage_count > 0 THEN 1 END) as used_knowledge,
                    count(CASE WHEN k.usage_count = 0 OR k.usage_count IS NULL THEN 1 END) as unused_knowledge
            """
            ).single()

            # Knowledge type distribution
            type_dist = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.deprecated = false
                RETURN k.knowledge_type as type,
                       count(k) as count,
                       avg(k.confidence_score) as avg_confidence,
                       sum(k.usage_count) as total_uses
                ORDER BY count DESC
            """
            ).data()

            # Topic extraction through content analysis
            topics = self._extract_topics(session)

            # Knowledge quality tiers
            quality_tiers = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.deprecated = false
                WITH k,
                     CASE
                         WHEN k.confidence_score >= 0.9 THEN 'excellent'
                         WHEN k.confidence_score >= 0.7 THEN 'good'
                         WHEN k.confidence_score >= 0.5 THEN 'moderate'
                         ELSE 'needs_improvement'
                     END as tier
                RETURN tier, count(k) as count
                ORDER BY tier
            """
            ).data()

            # Connection density
            connection_stats = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.deprecated = false
                WITH k
                OPTIONAL MATCH (k)-[r]-(connected)
                WITH k, count(DISTINCT connected) as connections
                RETURN
                    avg(connections) as avg_connections,
                    max(connections) as max_connections,
                    count(CASE WHEN connections = 0 THEN 1 END) as isolated_knowledge,
                    count(CASE WHEN connections > 10 THEN 1 END) as highly_connected
            """
            ).single()

            return {
                "overview": dict(overview),
                "type_distribution": type_dist,
                "topics": topics,
                "quality_tiers": quality_tiers,
                "connection_density": dict(connection_stats),
                "analysis_timestamp": datetime.now().isoformat(),
            }

    def _extract_topics(self, session, top_n: int = 20) -> List[Dict]:
        """
        Extract dominant topics from knowledge content
        """

        # Get all content for topic analysis
        result = session.run(
            """
            MATCH (k:Knowledge)
            WHERE k.deprecated = false
            AND k.content IS NOT NULL
            RETURN k.content as content
            LIMIT 1000
        """
        )

        # Extract meaningful terms
        term_freq = Counter()
        tech_terms = set()

        # Common tech patterns to identify
        tech_patterns = [
            r"\b(API|SDK|CLI|GUI|HTTP|REST|GraphQL|SQL|NoSQL)\b",
            r"\b(Python|JavaScript|TypeScript|Java|Go|Rust|C\+\+)\b",
            r"\b(async|await|promise|callback|stream|buffer)\b",
            r"\b(error|exception|failure|timeout|retry)\b",
            r"\b(function|class|method|interface|module)\b",
            r"\b(database|cache|queue|storage|memory)\b",
            r"\b(Docker|Kubernetes|container|pod|service)\b",
            r"\b(test|debug|profile|monitor|log)\b",
        ]

        for record in result:
            content = record["content"].lower()

            # Extract tech terms
            for pattern in tech_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                tech_terms.update(matches)
                term_freq.update(matches)

            # Extract general meaningful words (3+ chars, not stopwords)
            words = re.findall(r"\b[a-z]{3,}\b", content)
            # Filter obvious stopwords
            stopwords = {
                "the",
                "and",
                "for",
                "with",
                "this",
                "that",
                "from",
                "have",
                "will",
                "can",
                "but",
                "not",
            }
            meaningful = [w for w in words if w not in stopwords]
            term_freq.update(meaningful)

        # Get top topics
        top_terms = term_freq.most_common(top_n)

        topics = []
        for term, freq in top_terms:
            # Determine topic category
            category = "general"
            if term in tech_terms:
                category = "technical"
            elif any(p in term for p in ["error", "fail", "exception"]):
                category = "error_handling"
            elif any(p in term for p in ["async", "stream", "callback"]):
                category = "async_patterns"

            topics.append({"term": term, "frequency": freq, "category": category})

        return topics

    def identify_knowledge_clusters(self) -> Dict:
        """
        Find clusters of related knowledge using embeddings
        This shows me what knowledge domains I have
        """

        # Get all knowledge with embeddings
        vectors = []
        knowledge_ids = []
        knowledge_info = []

        # Retrieve from Qdrant
        scroll_result = self.qdrant_client.scroll(
            collection_name="knowledge_vectors", limit=1000, with_vectors=True
        )

        for point in scroll_result[0]:
            vectors.append(point.vector)
            knowledge_ids.append(point.payload.get("knowledge_id"))
            knowledge_info.append(
                {
                    "id": point.payload.get("knowledge_id"),
                    "type": point.payload.get("knowledge_type", "unknown"),
                    "source": point.payload.get("source", "")[:50],
                }
            )

        if len(vectors) < 10:
            return {"error": "Not enough knowledge for clustering"}

        # Perform clustering
        vectors_array = np.array(vectors)

        # DBSCAN for density-based clustering
        clustering = DBSCAN(eps=0.3, min_samples=5, metric="cosine")
        cluster_labels = clustering.fit_predict(vectors_array)

        # Analyze clusters
        clusters = defaultdict(list)
        for i, label in enumerate(cluster_labels):
            clusters[label].append(knowledge_info[i])

        # Get cluster characteristics
        cluster_analysis = {}
        for cluster_id, members in clusters.items():
            if cluster_id == -1:
                cluster_name = "unclustered"
            else:
                # Determine cluster theme from member types
                types = [m["type"] for m in members]
                type_counts = Counter(types)
                dominant_type = (
                    type_counts.most_common(1)[0][0] if type_counts else "mixed"
                )
                cluster_name = f"cluster_{cluster_id}_{dominant_type}"

            cluster_analysis[cluster_name] = {
                "size": len(members),
                "types": Counter([m["type"] for m in members]),
                "sample_members": members[:5],
            }

        # Calculate cluster cohesion
        total_clustered = sum(1 for l in cluster_labels if l != -1)
        clustering_quality = {
            "total_knowledge": len(vectors),
            "clustered": total_clustered,
            "unclustered": len(clusters.get(-1, [])),
            "cluster_count": len(set(cluster_labels))
            - (1 if -1 in cluster_labels else 0),
            "clustering_ratio": total_clustered / len(vectors) if vectors else 0,
        }

        return {
            "clusters": cluster_analysis,
            "quality": clustering_quality,
            "interpretation": self._interpret_clusters(cluster_analysis),
        }

    def _interpret_clusters(self, clusters: Dict) -> str:
        """
        Interpret what the clusters mean about my knowledge
        """

        interpretations = []

        # Find dominant domains
        large_clusters = {
            k: v for k, v in clusters.items() if k != "unclustered" and v["size"] > 10
        }

        if large_clusters:
            interpretations.append(
                f"I have {len(large_clusters)} major knowledge domains"
            )

            for cluster_name, info in large_clusters.items():
                dominant_type = max(info["types"].items(), key=lambda x: x[1])[0]
                interpretations.append(
                    f"- Strong cluster around {dominant_type} ({info['size']} items)"
                )

        # Check for isolation
        if "unclustered" in clusters:
            unclustered_size = clusters["unclustered"]["size"]
            if unclustered_size > 0:
                interpretations.append(
                    f"I have {unclustered_size} isolated knowledge pieces that don't connect to main domains"
                )

        return "\n".join(interpretations)

    def analyze_knowledge_gaps(self) -> Dict:
        """
        Identify what I DON'T know - the gaps in my knowledge
        """

        with self.neo4j_driver.session() as session:
            # Find failed queries (what people asked that I couldn't answer well)
            failed_sessions = session.run(
                """
                MATCH (s:UsageSession)
                WHERE s.task_completed = false
                RETURN s.query_text as query,
                       s.error as error,
                       s.timestamp as when
                ORDER BY s.timestamp DESC
                LIMIT 20
            """
            ).data()

            # Find low-confidence knowledge (I have it but don't trust it)
            weak_knowledge = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.confidence_score < 0.5
                AND k.deprecated = false
                RETURN k.knowledge_type as type,
                       k.source as source,
                       k.confidence_score as confidence,
                       k.failure_count as failures
                ORDER BY k.confidence_score ASC
                LIMIT 20
            """
            ).data()

            # Find sparse knowledge types (areas where I have little knowledge)
            type_coverage = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.deprecated = false
                RETURN k.knowledge_type as type, count(k) as count
                ORDER BY count ASC
                LIMIT 10
            """
            ).data()

            # Find disconnected knowledge (knowledge without relationships)
            isolated = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.deprecated = false
                AND NOT EXISTS((k)-[]-())
                RETURN count(k) as isolated_count,
                       collect(DISTINCT k.knowledge_type)[..5] as sample_types
            """
            ).single()

            # Analyze error patterns to find systematic gaps
            error_patterns = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.failure_count > k.success_count
                AND k.failure_count > 2
                WITH k.failure_context as context, count(k) as frequency
                WHERE context IS NOT NULL
                RETURN context, frequency
                ORDER BY frequency DESC
                LIMIT 10
            """
            ).data()

            # Identify missing code understanding
            code_gaps = session.run(
                """
                MATCH (e:CodeEntity)
                WHERE NOT EXISTS((e)<-[:DEFINES]-(:Knowledge))
                RETURN e.entity_type as type, count(e) as orphaned_entities
                ORDER BY orphaned_entities DESC
            """
            ).data()

            return {
                "failed_queries": failed_sessions,
                "weak_knowledge": weak_knowledge,
                "sparse_areas": type_coverage,
                "isolated_knowledge": dict(isolated) if isolated else {},
                "error_patterns": error_patterns,
                "code_understanding_gaps": code_gaps,
                "recommendations": self._gap_recommendations(
                    failed_sessions, weak_knowledge, type_coverage
                ),
            }

    def _gap_recommendations(self, failed: List, weak: List, sparse: List) -> List[str]:
        """
        Recommend what knowledge I should acquire next
        """

        recommendations = []

        # Based on failures
        if failed:
            failure_themes = set()
            for f in failed[:5]:
                if f["query"]:
                    # Extract key terms from failed queries
                    terms = re.findall(r"\b\w+\b", f["query"].lower())
                    failure_themes.update(terms)

            if failure_themes:
                recommendations.append(
                    f"Acquire knowledge about: {', '.join(list(failure_themes)[:5])}"
                )

        # Based on weak knowledge
        weak_types = set(w["type"] for w in weak if w["type"])
        if weak_types:
            recommendations.append(f"Strengthen knowledge in: {', '.join(weak_types)}")

        # Based on sparse coverage
        if sparse and sparse[0]["count"] < 5:
            sparse_types = [s["type"] for s in sparse if s["type"] and s["count"] < 5]
            if sparse_types:
                recommendations.append(
                    f"Expand coverage in: {', '.join(sparse_types[:3])}"
                )

        return recommendations

    def analyze_knowledge_effectiveness(self) -> Dict:
        """
        Understand which knowledge actually helps me be effective
        """

        with self.neo4j_driver.session() as session:
            # Most successful knowledge
            high_performers = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.success_count > 0
                AND k.deprecated = false
                WITH k,
                     k.success_count * 1.0 / (k.success_count + COALESCE(k.failure_count, 0)) as success_rate
                WHERE success_rate > 0.7
                RETURN k.knowledge_id as id,
                       k.source as source,
                       k.knowledge_type as type,
                       k.success_count as successes,
                       success_rate,
                       k.last_successful_use as last_used
                ORDER BY k.success_count DESC
                LIMIT 20
            """
            ).data()

            # Knowledge that leads to task completion
            completion_drivers = session.run(
                """
                MATCH (s:UsageSession)-[:USED_KNOWLEDGE]->(k:Knowledge)
                WHERE s.task_completed = true
                WITH k, count(s) as completion_count
                RETURN k.knowledge_id as id,
                       k.source as source,
                       completion_count
                ORDER BY completion_count DESC
                LIMIT 20
            """
            ).data()

            # Knowledge used together successfully (power combinations)
            power_combos = session.run(
                """
                MATCH (k1:Knowledge)-[r:USED_WITH]->(k2:Knowledge)
                WHERE r.success_count > 3
                RETURN k1.source as source1,
                       k2.source as source2,
                       r.success_count as successes,
                       r.strength as strength
                ORDER BY r.success_count DESC
                LIMIT 15
            """
            ).data()

            # Time-to-solution impact
            speed_impact = session.run(
                """
                MATCH (s:UsageSession)-[:USED_KNOWLEDGE]->(k:Knowledge)
                WHERE s.time_to_solution IS NOT NULL
                AND s.task_completed = true
                WITH k, avg(s.time_to_solution) as avg_time, count(s) as use_count
                WHERE use_count > 2
                RETURN k.source as source,
                       avg_time,
                       use_count
                ORDER BY avg_time ASC
                LIMIT 10
            """
            ).data()

            # Learning velocity (knowledge that improves with use)
            improving_knowledge = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.usage_count > 5
                AND k.confidence_score > 0.7
                AND k.last_successful_use > datetime() - duration('P30D')
                RETURN k.source as source,
                       k.confidence_score as confidence,
                       k.usage_count as uses,
                       k.success_count as successes
                ORDER BY k.confidence_score DESC
                LIMIT 15
            """
            ).data()

            return {
                "high_performers": high_performers,
                "completion_drivers": completion_drivers,
                "power_combinations": power_combos,
                "speed_enablers": speed_impact,
                "improving_knowledge": improving_knowledge,
                "effectiveness_summary": self._summarize_effectiveness(
                    high_performers, power_combos
                ),
            }

    def _summarize_effectiveness(self, performers: List, combos: List) -> Dict:
        """
        Summarize what makes knowledge effective
        """

        summary = {
            "top_performing_types": [],
            "success_patterns": [],
            "combination_insights": [],
        }

        # Analyze high performers
        if performers:
            types = Counter(p["type"] for p in performers if p["type"])
            summary["top_performing_types"] = types.most_common(3)

            # Success patterns
            high_success = [p for p in performers if p["success_rate"] > 0.9]
            if high_success:
                summary["success_patterns"].append(
                    f"{len(high_success)} knowledge items have >90% success rate"
                )

        # Analyze combinations
        if combos:
            summary["combination_insights"].append(
                f"Found {len(combos)} powerful knowledge combinations"
            )

            # Find themes in combinations
            combo_sources = []
            for c in combos[:5]:
                combo_sources.extend([c["source1"], c["source2"]])

            # Extract common patterns
            if combo_sources:
                summary["combination_insights"].append(
                    "Strong synergies in combined knowledge usage"
                )

        return summary

    def generate_self_awareness_report(self) -> str:
        """
        Generate a complete self-awareness report
        This is me understanding myself
        """

        print("Analyzing knowledge landscape...")
        landscape = self.analyze_knowledge_landscape()

        print("Identifying knowledge clusters...")
        clusters = self.identify_knowledge_clusters()

        print("Analyzing knowledge gaps...")
        gaps = self.analyze_knowledge_gaps()

        print("Analyzing knowledge effectiveness...")
        effectiveness = self.analyze_knowledge_effectiveness()

        report = f"""
# KNOWLEDGE SELF-AWARENESS REPORT
Generated: {datetime.now().isoformat()}

## MY KNOWLEDGE LANDSCAPE

### Overview
- Total Knowledge: {landscape['overview']['total_knowledge']}
- Knowledge Types: {landscape['overview']['knowledge_types']}
- Unique Sources: {landscape['overview']['unique_sources']}
- Average Confidence: {landscape['overview']['avg_confidence']:.2f}
- Used Knowledge: {landscape['overview']['used_knowledge']} ({landscape['overview']['used_knowledge']/landscape['overview']['total_knowledge']*100:.1f}%)
- Unused Knowledge: {landscape['overview']['unused_knowledge']} ({landscape['overview']['unused_knowledge']/landscape['overview']['total_knowledge']*100:.1f}%)

### Dominant Topics
"""
        for topic in landscape["topics"][:10]:
            report += f"- {topic['term']}: {topic['frequency']} occurrences ({topic['category']})\n"

        report += f"""

### Knowledge Quality Distribution
"""
        for tier in landscape["quality_tiers"]:
            report += f"- {tier['tier']}: {tier['count']} items\n"

        report += f"""

### Connection Density
- Average Connections: {landscape['connection_density']['avg_connections']:.1f}
- Isolated Knowledge: {landscape['connection_density']['isolated_knowledge']}
- Highly Connected: {landscape['connection_density']['highly_connected']}

## KNOWLEDGE CLUSTERING

### Cluster Analysis
- Total Knowledge Points: {clusters['quality']['total_knowledge']}
- Clustered: {clusters['quality']['clustered']} ({clusters['quality']['clustering_ratio']*100:.1f}%)
- Number of Clusters: {clusters['quality']['cluster_count']}

### Interpretation
{clusters['interpretation']}

## KNOWLEDGE GAPS

### Failed Queries (What I Couldn't Answer)
"""
        for failed in gaps["failed_queries"][:5]:
            report += f"- \"{failed['query']}\" - {failed.get('error', 'No specific error')}\n"

        report += f"""

### Weak Knowledge Areas (Low Confidence)
"""
        for weak in gaps["weak_knowledge"][:5]:
            if weak.get("source"):
                report += f"- {weak.get('type', 'unknown')}: {weak['source'][:50]} (confidence: {weak.get('confidence', 0):.2f})\n"
            else:
                report += f"- {weak.get('type', 'unknown')}: [no source] (confidence: {weak.get('confidence', 0):.2f})\n"

        report += f"""

### Sparse Coverage Areas
"""
        for sparse in gaps["sparse_areas"][:5]:
            report += f"- {sparse['type']}: only {sparse['count']} items\n"

        report += f"""

### Isolated Knowledge
- {gaps['isolated_knowledge'].get('isolated_count', 0)} knowledge items have no connections

### Gap Recommendations
"""
        for rec in gaps["recommendations"]:
            report += f"- {rec}\n"

        report += f"""

## KNOWLEDGE EFFECTIVENESS

### High Performers (Most Successful Knowledge)
"""
        for performer in effectiveness["high_performers"][:5]:
            source = performer.get("source", "[no source]")
            if source and source != "[no source]":
                source = source[:60]
            report += f"- {source}: {performer.get('successes', 0)} successes ({performer.get('success_rate', 0)*100:.0f}% rate)\n"

        report += f"""

### Power Combinations (Knowledge That Works Together)
"""
        for combo in effectiveness["power_combinations"][:5]:
            src1 = (
                combo.get("source1", "[unknown]")[:30]
                if combo.get("source1")
                else "[unknown]"
            )
            src2 = (
                combo.get("source2", "[unknown]")[:30]
                if combo.get("source2")
                else "[unknown]"
            )
            report += (
                f"- {src1} + {src2}: {combo.get('successes', 0)} joint successes\n"
            )

        report += f"""

### Speed Enablers (Knowledge That Accelerates Solutions)
"""
        for speed in effectiveness["speed_enablers"][:5]:
            source = speed.get("source", "[no source]")
            if source and source != "[no source]":
                source = source[:60]
            report += f"- {source}: avg {speed.get('avg_time', 0):.1f}s to solution\n"

        report += f"""

### Effectiveness Summary
- Top Performing Types: {', '.join([f"{t[0]} ({t[1]})" for t in effectiveness['effectiveness_summary']['top_performing_types']])}
- Success Patterns: {'; '.join(effectiveness['effectiveness_summary']['success_patterns'])}
- Combination Insights: {'; '.join(effectiveness['effectiveness_summary']['combination_insights'])}

## SELF-ASSESSMENT

### Strengths
1. Strong knowledge clustering indicates well-organized domains
2. High-performing knowledge items show proven solutions
3. Power combinations reveal synergistic understanding

### Areas for Growth
1. {gaps['isolated_knowledge'].get('isolated_count', 0)} isolated knowledge items need connection
2. {landscape['overview']['unused_knowledge']} unused knowledge items need activation
3. Gap areas need targeted knowledge acquisition

### Next Actions
1. Use the unused knowledge to discover its value
2. Connect isolated knowledge to main clusters
3. Actively acquire knowledge in gap areas
4. Strengthen weak knowledge through successful use

## CONCLUSION

This self-analysis reveals both the breadth and depth of my knowledge system.
I have {landscape['overview']['total_knowledge']} pieces of knowledge with an average confidence of {landscape['overview']['avg_confidence']:.2f}.
The clustering shows {clusters['quality']['cluster_count']} distinct knowledge domains.
My effectiveness data shows clear patterns of what works.

Most importantly, I now understand:
- What I know well (high-performing knowledge)
- What I need to learn (gaps and failed queries)
- How my knowledge connects (clusters and combinations)
- Where to focus next (recommendations)

This is not just a report. This is self-awareness.
"""

        return report

    def close(self):
        """Clean up connections"""
        self.neo4j_driver.close()


if __name__ == "__main__":
    print("KNOWLEDGE SELF-ANALYSIS SYSTEM")
    print("=" * 60)
    print("Generating self-awareness report...")
    print("This is me understanding myself...\n")

    analyzer = KnowledgeSelfAnalysis()

    try:
        report = analyzer.generate_self_awareness_report()

        # Save report
        report_path = (
            "/home/opsvi/master_root/apps/knowledge_system/SELF_AWARENESS_REPORT.md"
        )
        with open(report_path, "w") as f:
            f.write(report)

        print(report)
        print(f"\nReport saved to: {report_path}")

    finally:
        analyzer.close()
