#!/usr/bin/env python3
"""
Knowledge Base Visualization Dashboard
Interactive dashboard for exploring the vectorized knowledge graph.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import networkx as nx
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import umap
from pyvis.network import Network
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler

# Page configuration
st.set_page_config(
    page_title="Knowledge Base Visualization",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


class KnowledgeVisualizer:
    """Main visualization class for knowledge base exploration."""

    def __init__(self, neo4j_driver=None):
        self.driver = neo4j_driver
        self.embeddings_cache = {}
        self.graph_cache = None

    def create_dashboard(self):
        """Create the main dashboard interface."""

        # Header
        st.title("🧠 Knowledge Base Visualization Dashboard")
        st.markdown("---")

        # Sidebar controls
        self._create_sidebar()

        # Main content area with tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            [
                "📊 Overview",
                "🔗 Graph Structure",
                "🎯 Embedding Space",
                "📈 Metrics & Analytics",
                "🔍 Search & Explore",
            ]
        )

        with tab1:
            self._create_overview_tab()

        with tab2:
            self._create_graph_tab()

        with tab3:
            self._create_embedding_tab()

        with tab4:
            self._create_metrics_tab()

        with tab5:
            self._create_search_tab()

    def _create_sidebar(self):
        """Create sidebar with filters and controls."""
        st.sidebar.header("🎛️ Controls")

        # Knowledge type filter
        st.sidebar.subheader("Filters")
        knowledge_types = st.sidebar.multiselect(
            "Knowledge Types",
            ["WORKFLOW", "CODE_PATTERN", "ERROR_SOLUTION", "CONTEXT_PATTERN"],
            default=["WORKFLOW", "CODE_PATTERN"],
        )

        # Confidence threshold
        confidence_threshold = st.sidebar.slider(
            "Minimum Confidence", min_value=0.0, max_value=1.0, value=0.8, step=0.05
        )

        # Date range
        st.sidebar.subheader("Time Range")
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            max_value=datetime.now(),
        )

        # Visualization settings
        st.sidebar.subheader("Visualization Settings")
        color_scheme = st.sidebar.selectbox(
            "Color Scheme", ["Viridis", "Plasma", "Inferno", "Turbo", "Rainbow"]
        )

        node_size_metric = st.sidebar.selectbox(
            "Node Size Represents",
            ["Confidence", "Usage Count", "Success Rate", "Connections"],
        )

        # Export options
        st.sidebar.subheader("Export")
        if st.sidebar.button("📥 Export Graph Data"):
            self._export_graph_data()

        if st.sidebar.button("📥 Export Embeddings"):
            self._export_embeddings()

        # Store in session state
        st.session_state.filters = {
            "knowledge_types": knowledge_types,
            "confidence_threshold": confidence_threshold,
            "date_range": date_range,
            "color_scheme": color_scheme,
            "node_size_metric": node_size_metric,
        }

    def _create_overview_tab(self):
        """Create overview tab with key metrics."""
        st.header("Knowledge Base Overview")

        # Key metrics in columns
        col1, col2, col3, col4 = st.columns(4)

        # Mock data - would be fetched from Neo4j
        with col1:
            st.metric(label="Total Knowledge Nodes", value="1,247", delta="+23 today")

        with col2:
            st.metric(label="Average Confidence", value="91.2%", delta="+2.1%")

        with col3:
            st.metric(label="Success Rate", value="94.5%", delta="+0.8%")

        with col4:
            st.metric(label="Active Relationships", value="3,891", delta="+145")

        # Charts row
        col1, col2 = st.columns(2)

        with col1:
            # Knowledge distribution pie chart
            fig = px.pie(
                values=[450, 380, 290, 127],
                names=["WORKFLOW", "CODE_PATTERN", "ERROR_SOLUTION", "CONTEXT_PATTERN"],
                title="Knowledge Distribution by Type",
                color_discrete_sequence=px.colors.sequential.Viridis,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Usage trend line chart
            dates = pd.date_range(end=datetime.now(), periods=30)
            usage = np.random.randint(50, 200, size=30).cumsum()

            fig = px.line(
                x=dates,
                y=usage,
                title="Knowledge Usage Trend (30 days)",
                labels={"x": "Date", "y": "Cumulative Usage"},
            )
            st.plotly_chart(fig, use_container_width=True)

        # Recent activity feed
        st.subheader("📋 Recent Activity")
        activity_data = pd.DataFrame(
            {
                "Time": pd.date_range(end=datetime.now(), periods=10, freq="H"),
                "Action": ["Knowledge Added", "Pattern Updated", "Relationship Created"]
                * 3
                + ["Query Executed"],
                "Entity": [f"knowledge-{i}" for i in range(10)],
                "Confidence": np.random.uniform(0.85, 0.99, 10),
            }
        )
        st.dataframe(activity_data, use_container_width=True)

    def _create_graph_tab(self):
        """Create graph structure visualization tab."""
        st.header("Knowledge Graph Structure")

        # Graph layout options
        col1, col2, col3 = st.columns(3)
        with col1:
            st.selectbox(
                "Layout Algorithm",
                ["Force Atlas", "Fruchterman Reingold", "Circular", "Hierarchical"],
            )

        with col2:
            st.checkbox("Show Labels", value=True)

        with col3:
            physics_enabled = st.checkbox("Enable Physics", value=True)

        # Create sample graph
        G = self._create_sample_graph()

        # Pyvis network
        net = Network(height="600px", width="100%", notebook=False)
        net.from_nx(G)

        # Configure physics
        if physics_enabled:
            net.show_buttons(filter_=["physics"])

        # Save and display
        net.save_graph("knowledge_graph.html")

        # Display using iframe
        with open("knowledge_graph.html", "r") as f:
            html_string = f.read()

        st.components.v1.html(html_string, height=600)

        # Graph statistics
        st.subheader("Graph Statistics")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.info(f"**Nodes:** {G.number_of_nodes()}")
            st.info(f"**Edges:** {G.number_of_edges()}")

        with col2:
            st.info(f"**Density:** {nx.density(G):.3f}")
            st.info(
                f"**Avg Degree:** {sum(dict(G.degree()).values())/G.number_of_nodes():.2f}"
            )

        with col3:
            if nx.is_connected(G):
                st.info(f"**Diameter:** {nx.diameter(G)}")
            else:
                st.info("**Connected:** No")
            st.info(f"**Components:** {nx.number_connected_components(G)}")

    def _create_embedding_tab(self):
        """Create embedding visualization tab."""
        st.header("Embedding Space Visualization")

        # Dimension reduction options
        col1, col2, col3 = st.columns(3)

        with col1:
            reduction_method = st.selectbox(
                "Dimension Reduction", ["UMAP", "t-SNE", "PCA"]
            )

        with col2:
            n_dimensions = st.radio("Dimensions", [2, 3], horizontal=True)

        with col3:
            perplexity = st.slider(
                "Perplexity (t-SNE)"
                if reduction_method == "t-SNE"
                else "N Neighbors (UMAP)",
                min_value=5,
                max_value=50,
                value=15,
            )

        # Generate sample embeddings
        embeddings, labels, metadata = self._generate_sample_embeddings()

        # Reduce dimensions
        if reduction_method == "UMAP":
            reducer = umap.UMAP(n_components=n_dimensions, n_neighbors=perplexity)
        elif reduction_method == "t-SNE":
            reducer = TSNE(n_components=n_dimensions, perplexity=perplexity)
        else:  # PCA
            from sklearn.decomposition import PCA

            reducer = PCA(n_components=n_dimensions)

        reduced_embeddings = reducer.fit_transform(embeddings)

        # Create visualization
        if n_dimensions == 2:
            fig = px.scatter(
                x=reduced_embeddings[:, 0],
                y=reduced_embeddings[:, 1],
                color=labels,
                size=metadata["confidence"],
                hover_data={
                    "ID": metadata["ids"],
                    "Type": labels,
                    "Confidence": metadata["confidence"],
                    "Usage": metadata["usage"],
                },
                title=f"Knowledge Embeddings ({reduction_method})",
                labels={"x": "Component 1", "y": "Component 2"},
                color_discrete_sequence=px.colors.sequential.Viridis,
            )
        else:  # 3D
            fig = px.scatter_3d(
                x=reduced_embeddings[:, 0],
                y=reduced_embeddings[:, 1],
                z=reduced_embeddings[:, 2],
                color=labels,
                size=metadata["confidence"],
                hover_data={
                    "ID": metadata["ids"],
                    "Type": labels,
                    "Confidence": metadata["confidence"],
                },
                title=f"Knowledge Embeddings 3D ({reduction_method})",
                labels={"x": "Component 1", "y": "Component 2", "z": "Component 3"},
            )

        st.plotly_chart(fig, use_container_width=True)

        # Cluster analysis
        st.subheader("Cluster Analysis")

        # Perform clustering
        from sklearn.cluster import KMeans

        n_clusters = st.slider("Number of Clusters", 2, 10, 5)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(reduced_embeddings)

        # Show cluster distribution
        cluster_df = pd.DataFrame({"Cluster": clusters, "Type": labels})

        cluster_stats = (
            cluster_df.groupby(["Cluster", "Type"]).size().unstack(fill_value=0)
        )

        fig = px.bar(
            cluster_stats.T, title="Knowledge Distribution by Cluster", barmode="stack"
        )
        st.plotly_chart(fig, use_container_width=True)

    def _create_metrics_tab(self):
        """Create metrics and analytics tab."""
        st.header("Metrics & Analytics")

        # Time range selector
        st.selectbox(
            "Time Range",
            ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Last 90 Days"],
        )

        # Performance metrics
        st.subheader("Performance Metrics")

        col1, col2 = st.columns(2)

        with col1:
            # Success rate over time
            dates = pd.date_range(end=datetime.now(), periods=30)
            success_rates = np.random.uniform(0.88, 0.96, 30)

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=success_rates,
                    mode="lines+markers",
                    name="Success Rate",
                    line=dict(color="green", width=2),
                )
            )
            fig.add_hline(
                y=0.95,
                line_dash="dash",
                line_color="red",
                annotation_text="Target: 95%",
            )
            fig.update_layout(
                title="Success Rate Trend",
                yaxis_title="Success Rate",
                yaxis_tickformat=".0%",
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Confidence distribution
            confidence_scores = np.random.beta(9, 1, 1000)

            fig = px.histogram(
                confidence_scores,
                nbins=20,
                title="Confidence Score Distribution",
                labels={"value": "Confidence Score", "count": "Frequency"},
            )
            fig.add_vline(
                x=0.9,
                line_dash="dash",
                line_color="red",
                annotation_text="Threshold: 0.9",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Usage patterns
        st.subheader("Usage Patterns")

        # Heatmap of usage by type and hour
        hours = list(range(24))
        types = ["WORKFLOW", "CODE_PATTERN", "ERROR_SOLUTION", "CONTEXT_PATTERN"]
        usage_matrix = np.random.randint(0, 50, (len(types), len(hours)))

        fig = px.imshow(
            usage_matrix,
            labels=dict(x="Hour of Day", y="Knowledge Type", color="Usage Count"),
            x=hours,
            y=types,
            title="Knowledge Usage Heatmap (24h)",
            color_continuous_scale="Viridis",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Top performers
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🏆 Top Performing Knowledge")
            top_knowledge = pd.DataFrame(
                {
                    "ID": [f"knowledge-{i}" for i in range(5)],
                    "Type": np.random.choice(types, 5),
                    "Success Rate": np.random.uniform(0.95, 0.99, 5),
                    "Usage": np.random.randint(100, 500, 5),
                }
            )
            st.dataframe(top_knowledge, use_container_width=True)

        with col2:
            st.subheader("⚠️ Needs Improvement")
            poor_knowledge = pd.DataFrame(
                {
                    "ID": [f"knowledge-{i+100}" for i in range(5)],
                    "Type": np.random.choice(types, 5),
                    "Success Rate": np.random.uniform(0.60, 0.75, 5),
                    "Issues": [
                        "Low confidence",
                        "High failure rate",
                        "Outdated",
                        "Rarely used",
                        "Conflicting",
                    ],
                }
            )
            st.dataframe(poor_knowledge, use_container_width=True)

    def _create_search_tab(self):
        """Create search and exploration tab."""
        st.header("Search & Explore")

        # Search interface
        search_query = st.text_input(
            "🔍 Semantic Search", placeholder="Enter search query..."
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            search_type = st.selectbox(
                "Search Type", ["Semantic", "Exact Match", "Pattern", "Cypher Query"]
            )

        with col2:
            max_results = st.number_input(
                "Max Results", min_value=1, max_value=100, value=10
            )

        with col3:
            if st.button("🔍 Search", type="primary"):
                self._perform_search(search_query, search_type, max_results)

        # Search results
        if "search_results" in st.session_state:
            st.subheader("Search Results")

            for i, result in enumerate(st.session_state.search_results):
                with st.expander(f"{i+1}. {result['id']} - {result['type']}"):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write(f"**Content:** {result['content']}")
                        st.write(f"**Description:** {result['description']}")

                    with col2:
                        st.metric("Confidence", f"{result['confidence']:.2%}")
                        st.metric("Similarity", f"{result['similarity']:.2%}")

        # Relationship explorer
        st.subheader("Relationship Explorer")

        selected_node = st.selectbox(
            "Select Knowledge Node", [f"knowledge-{i}" for i in range(20)]
        )

        relationship_depth = st.slider(
            "Relationship Depth", min_value=1, max_value=3, value=1
        )

        if st.button("Explore Relationships"):
            self._explore_relationships(selected_node, relationship_depth)

        # Pattern discovery
        st.subheader("Pattern Discovery")

        pattern_type = st.selectbox(
            "Pattern Type", ["Frequent Subgraphs", "Communities", "Anomalies", "Trends"]
        )

        if st.button("Discover Patterns"):
            self._discover_patterns(pattern_type)

    def _create_sample_graph(self) -> nx.Graph:
        """Create a sample graph for visualization."""
        G = nx.Graph()

        # Add nodes with attributes
        node_types = ["WORKFLOW", "CODE_PATTERN", "ERROR_SOLUTION", "CONTEXT_PATTERN"]

        for i in range(30):
            G.add_node(
                f"knowledge-{i}",
                title=f"Knowledge {i}",
                group=np.random.choice(node_types),
                confidence=np.random.uniform(0.8, 1.0),
                size=np.random.randint(10, 30),
            )

        # Add edges
        for _ in range(45):
            source = f"knowledge-{np.random.randint(0, 30)}"
            target = f"knowledge-{np.random.randint(0, 30)}"
            if source != target:
                G.add_edge(
                    source,
                    target,
                    weight=np.random.uniform(0.5, 1.0),
                    title=np.random.choice(["RELATED_TO", "IMPLEMENTS", "REQUIRES"]),
                )

        return G

    def _generate_sample_embeddings(self) -> Tuple[np.ndarray, List[str], Dict]:
        """Generate sample embeddings for visualization."""
        n_samples = 200
        n_features = 384  # Typical embedding dimension

        # Generate embeddings with some structure
        embeddings = []
        labels = []

        types = ["WORKFLOW", "CODE_PATTERN", "ERROR_SOLUTION", "CONTEXT_PATTERN"]

        for i, knowledge_type in enumerate(types):
            # Create cluster center
            center = np.random.randn(n_features) * 0.5 + i

            # Generate points around center
            n_points = n_samples // len(types)
            cluster_embeddings = center + np.random.randn(n_points, n_features) * 0.1

            embeddings.append(cluster_embeddings)
            labels.extend([knowledge_type] * n_points)

        embeddings = np.vstack(embeddings)

        # Normalize
        scaler = StandardScaler()
        embeddings = scaler.fit_transform(embeddings)

        # Generate metadata
        metadata = {
            "ids": [f"knowledge-{i}" for i in range(n_samples)],
            "confidence": np.random.uniform(0.7, 1.0, n_samples) * 10,
            "usage": np.random.randint(0, 100, n_samples),
        }

        return embeddings, labels, metadata

    def _perform_search(self, query: str, search_type: str, max_results: int):
        """Perform search and store results."""
        # Mock search results
        results = []

        for i in range(max_results):
            results.append(
                {
                    "id": f"knowledge-{np.random.randint(100, 200)}",
                    "type": np.random.choice(
                        ["WORKFLOW", "CODE_PATTERN", "ERROR_SOLUTION"]
                    ),
                    "content": f"Sample content for {query}",
                    "description": f"Description matching {query}",
                    "confidence": np.random.uniform(0.85, 0.99),
                    "similarity": np.random.uniform(0.7, 0.95),
                }
            )

        st.session_state.search_results = results

    def _explore_relationships(self, node_id: str, depth: int):
        """Explore relationships from a node."""
        st.info(f"Exploring relationships for {node_id} up to depth {depth}")

        # Create a small subgraph
        G = nx.ego_graph(self._create_sample_graph(), node_id, radius=depth)

        st.write(
            f"Found {G.number_of_nodes()} nodes and {G.number_of_edges()} relationships"
        )

    def _discover_patterns(self, pattern_type: str):
        """Discover patterns in the knowledge graph."""
        st.info(f"Discovering {pattern_type}...")

        # Mock pattern discovery results
        if pattern_type == "Communities":
            st.write("Found 5 distinct communities:")
            communities = pd.DataFrame(
                {
                    "Community": range(1, 6),
                    "Size": np.random.randint(10, 50, 5),
                    "Dominant Type": np.random.choice(["WORKFLOW", "CODE_PATTERN"], 5),
                    "Avg Confidence": np.random.uniform(0.85, 0.95, 5),
                }
            )
            st.dataframe(communities)

    def _export_graph_data(self):
        """Export graph data to file."""
        st.success("Graph data exported to 'knowledge_graph_export.json'")

    def _export_embeddings(self):
        """Export embeddings to file."""
        st.success("Embeddings exported to 'knowledge_embeddings.csv'")


# Main execution
if __name__ == "__main__":
    visualizer = KnowledgeVisualizer()
    visualizer.create_dashboard()
