#!/usr/bin/env python3
"""
Knowledge Base Visualization Configuration
Optimized for current scale: 49 nodes, 28 relationships, 38.8% embedding coverage
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class VisualizationConfig:
    """Configuration for knowledge base visualization optimized for current scale."""

    # Current KB Statistics (as of analysis)
    TOTAL_NODES = 49
    TOTAL_RELATIONSHIPS = 28
    EMBEDDING_COVERAGE = 0.388
    NODE_TYPES = {
        "WORKFLOW": 22,
        "CODE_PATTERN": 8,
        "ERROR_SOLUTION": 6,
        "USER_PREFERENCE": 2,
        "TOOL_USAGE": 2,
        "CONTEXT_PATTERN": 2,
        "TEST_*": 3,  # Various test types
        "NULL": 3,
    }

    # Visualization Performance Settings (optimized for 49 nodes)
    GRAPH_SETTINGS = {
        "layout": "force-directed",  # Best for <100 nodes
        "physics": {
            "enabled": True,  # Can handle physics with 49 nodes
            "solver": "barnesHut",
            "barnesHut": {
                "gravitationalConstant": -8000,
                "centralGravity": 0.3,
                "springLength": 95,
                "springConstant": 0.04,
                "damping": 0.09,
            },
        },
        "nodes": {
            "shape": "dot",
            "scaling": {
                "min": 10,
                "max": 30,
                "label": {
                    "enabled": True,  # Can show labels for 49 nodes
                    "min": 14,
                    "max": 30,
                },
            },
        },
        "edges": {
            "smooth": {"enabled": True, "type": "continuous"},
            "arrows": {"to": {"enabled": True, "scaleFactor": 0.5}},
        },
        "interaction": {
            "hover": True,
            "tooltipDelay": 200,
            "zoomView": True,
            "dragView": True,
        },
    }

    # Embedding Visualization Settings
    EMBEDDING_SETTINGS = {
        "dimension_reduction": {
            "method": "UMAP",  # Better for 49 points with 38.8% coverage
            "n_components": 2,
            "n_neighbors": 5,  # Lower for sparse embeddings
            "min_dist": 0.1,
            "metric": "cosine",
        },
        "clustering": {
            "method": "DBSCAN",  # Better for incomplete embeddings
            "eps": 0.5,
            "min_samples": 2,  # Lower threshold for 19 embedded nodes
        },
        "visualization": {
            "show_missing": True,  # Important with 61.2% missing
            "missing_position": "periphery",
            "missing_color": "#cccccc",
            "missing_opacity": 0.3,
        },
    }

    # Dashboard Metrics Configuration
    METRICS_CONFIG = {
        "key_metrics": [
            {
                "name": "Total Knowledge",
                "query": "MATCH (k:Knowledge) RETURN count(k) as value",
                "format": "number",
            },
            {
                "name": "Embedding Coverage",
                "query": """
                MATCH (k:Knowledge)
                WITH count(k) as total,
                     count(CASE WHEN k.embedding IS NOT NULL THEN 1 END) as embedded
                RETURN toFloat(embedded) / total as value
                """,
                "format": "percentage",
            },
            {
                "name": "Avg Confidence",
                "query": "MATCH (k:Knowledge) RETURN avg(k.confidence_score) as value",
                "format": "percentage",
            },
            {
                "name": "Active Relationships",
                "query": "MATCH ()-[r:RELATED_TO]->() RETURN count(r) as value",
                "format": "number",
            },
        ],
        "distribution_charts": [
            {
                "name": "Knowledge by Type",
                "query": """
                MATCH (k:Knowledge)
                RETURN k.knowledge_type as label, count(*) as value
                ORDER BY value DESC
                """,
                "chart_type": "pie",
            },
            {
                "name": "Confidence Distribution",
                "query": """
                MATCH (k:Knowledge)
                WHERE k.confidence_score IS NOT NULL
                RETURN CASE
                    WHEN k.confidence_score >= 0.95 THEN 'Excellent (≥95%)'
                    WHEN k.confidence_score >= 0.90 THEN 'Good (90-94%)'
                    WHEN k.confidence_score >= 0.85 THEN 'Fair (85-89%)'
                    ELSE 'Low (<85%)'
                END as label, count(*) as value
                """,
                "chart_type": "bar",
            },
        ],
        "time_series": [
            {
                "name": "Knowledge Growth",
                "query": """
                MATCH (k:Knowledge)
                WHERE k.created_at IS NOT NULL
                RETURN date(k.created_at) as date, count(*) as value
                ORDER BY date
                """,
                "chart_type": "line",
            }
        ],
    }

    # Color Schemes
    COLOR_SCHEMES = {
        "knowledge_types": {
            "WORKFLOW": "#4CAF50",
            "CODE_PATTERN": "#2196F3",
            "ERROR_SOLUTION": "#F44336",
            "CONTEXT_PATTERN": "#FF9800",
            "USER_PREFERENCE": "#9C27B0",
            "TOOL_USAGE": "#00BCD4",
            "TEST_VERIFICATION": "#8BC34A",
            "TEST_VALIDATION": "#8BC34A",
            "AUTO_EMBED_TEST": "#8BC34A",
            "TEST_SESSION_RESTART": "#8BC34A",
            "default": "#9E9E9E",
        },
        "confidence_gradient": {
            "high": "#4CAF50",  # >95%
            "good": "#8BC34A",  # 90-95%
            "medium": "#FFC107",  # 85-90%
            "low": "#FF5722",  # <85%
        },
        "embedding_status": {"embedded": "#2196F3", "missing": "#E0E0E0"},
    }

    # Federation Settings (if enabled)
    FEDERATION_CONFIG = {
        "enabled": False,  # Set to True when federation is active
        "sync_interval": 3600,  # 1 hour
        "max_sync_items": 100,
        "confidence_threshold": 0.85,
        "visualization": {
            "show_source": True,
            "source_colors": {
                "local": "#4CAF50",
                "federated": "#2196F3",
                "pending_sync": "#FFC107",
            },
        },
    }

    # Performance Optimization
    OPTIMIZATION = {
        "batch_size": 10,  # For embedding generation
        "cache_ttl": 3600,  # 1 hour cache
        "max_render_nodes": 100,  # Current 49 is well within limit
        "progressive_loading": False,  # Not needed for 49 nodes
        "use_webgl": False,  # Not needed for current scale
        "aggregation_threshold": 100,  # Start aggregating above this
    }

    @classmethod
    def get_graph_layout_for_scale(cls, node_count: int) -> str:
        """Determine optimal graph layout based on node count."""
        if node_count < 50:
            return "force-directed"
        elif node_count < 200:
            return "hierarchical"
        elif node_count < 500:
            return "circular"
        else:
            return "clustered"

    @classmethod
    def get_embedding_method_for_coverage(cls, coverage: float) -> str:
        """Determine best embedding visualization based on coverage."""
        if coverage < 0.5:
            return "hybrid"  # Mix embedded and graph-based positioning
        elif coverage < 0.8:
            return "UMAP"  # Good balance
        else:
            return "t-SNE"  # Better for complete embeddings

    @classmethod
    def should_enable_physics(cls, node_count: int) -> bool:
        """Determine if physics simulation should be enabled."""
        return node_count < 100

    @classmethod
    def get_optimization_strategy(cls) -> Dict:
        """Get optimization strategy for current scale."""
        return {
            "strategy": "full_render",  # Can render all 49 nodes
            "clustering": False,  # Not needed
            "sampling": False,  # Not needed
            "progressive": False,  # Not needed
            "recommendations": [
                "Generate embeddings for remaining 61.2% of nodes",
                "Consider adding more relationships (current density is low)",
                "Enable federation when ready for cross-project learning",
            ],
        }


class QueryOptimizer:
    """Optimize Cypher queries for visualization performance."""

    @staticmethod
    def get_graph_query(
        filter_type: Optional[str] = None, min_confidence: float = 0.0
    ) -> str:
        """Get optimized query for graph visualization."""
        base_query = """
        MATCH (k:Knowledge)
        WHERE k.confidence_score >= $min_confidence
        """

        if filter_type:
            base_query += " AND k.knowledge_type = $type"

        base_query += """
        WITH k LIMIT 100
        OPTIONAL MATCH (k)-[r:RELATED_TO]-(related:Knowledge)
        WHERE related.confidence_score >= $min_confidence
        RETURN k, collect(DISTINCT r) as relationships, collect(DISTINCT related) as related_nodes
        """

        return base_query

    @staticmethod
    def get_embedding_query(only_embedded: bool = False) -> str:
        """Get query for embedding visualization."""
        if only_embedded:
            return """
            MATCH (k:Knowledge)
            WHERE k.embedding IS NOT NULL
            RETURN k.knowledge_id as id,
                   k.knowledge_type as type,
                   k.content as content,
                   k.embedding as embedding,
                   k.confidence_score as confidence
            """
        else:
            return """
            MATCH (k:Knowledge)
            RETURN k.knowledge_id as id,
                   k.knowledge_type as type,
                   k.content as content,
                   k.embedding as embedding,
                   k.confidence_score as confidence,
                   CASE WHEN k.embedding IS NOT NULL THEN 'embedded' ELSE 'missing' END as status
            """

    @staticmethod
    def get_metrics_query(metric_type: str) -> str:
        """Get optimized query for specific metrics."""
        queries = {
            "overview": """
            MATCH (k:Knowledge)
            WITH count(k) as total_nodes,
                 avg(k.confidence_score) as avg_confidence,
                 count(CASE WHEN k.embedding IS NOT NULL THEN 1 END) as with_embeddings
            MATCH ()-[r:RELATED_TO]->()
            WITH total_nodes, avg_confidence, with_embeddings, count(r) as total_relationships
            RETURN {
                nodes: total_nodes,
                relationships: total_relationships,
                avg_confidence: avg_confidence,
                embedding_coverage: toFloat(with_embeddings) / total_nodes
            } as metrics
            """,
            "recent_activity": """
            MATCH (k:Knowledge)
            WHERE k.created_at > datetime() - duration('P7D')
            RETURN date(k.created_at) as date,
                   count(*) as additions,
                   collect(k.knowledge_type) as types
            ORDER BY date DESC
            """,
            "top_connected": """
            MATCH (k:Knowledge)
            OPTIONAL MATCH (k)-[r:RELATED_TO]-()
            WITH k, count(r) as connections
            WHERE connections > 0
            RETURN k.knowledge_id as id,
                   k.knowledge_type as type,
                   connections
            ORDER BY connections DESC
            LIMIT 10
            """,
        }

        return queries.get(metric_type, "RETURN 'Invalid metric type' as error")


# Export configuration instance
config = VisualizationConfig()
optimizer = QueryOptimizer()

if __name__ == "__main__":
    # Display current configuration
    print("Knowledge Base Visualization Configuration")
    print("=" * 50)
    print(f"Total Nodes: {config.TOTAL_NODES}")
    print(f"Total Relationships: {config.TOTAL_RELATIONSHIPS}")
    print(f"Embedding Coverage: {config.EMBEDDING_COVERAGE:.1%}")
    print("\nNode Type Distribution:")
    for type_name, count in config.NODE_TYPES.items():
        print(f"  {type_name}: {count}")
    print("\nRecommended Settings:")
    print(f"  Layout: {config.get_graph_layout_for_scale(config.TOTAL_NODES)}")
    print(f"  Physics: {config.should_enable_physics(config.TOTAL_NODES)}")
    print(
        f"  Embedding Method: {config.get_embedding_method_for_coverage(config.EMBEDDING_COVERAGE)}"
    )
    print("\nOptimization Strategy:")
    strategy = config.get_optimization_strategy()
    print(f"  Strategy: {strategy['strategy']}")
    print("  Recommendations:")
    for rec in strategy["recommendations"]:
        print(f"    - {rec}")
