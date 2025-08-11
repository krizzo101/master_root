"""
Doc Cleanup Documentation Manager

A unified system for ingesting, embedding, and managing documentation/code artifacts in a knowledge graph (ArangoDB), enabling semantic search, analytics, and doc_cleanup workflows for continuous documentation improvement.

Core modules:
- ingestion: Artifact discovery and loading
- embedding: Embedding generation for semantic search
- graph_manager: ArangoDB storage and relationship management
- agent_workflows: Orchestration of doc_cleanup documentation workflows
- analytics: Knowledge graph analytics and gap detection

Entry points:
- ingestion.ingest_all
- embedding.embed_all
- graph_manager.add_artifact, add_embedding
- agent_workflows.run_workflows
- analytics.run_analytics
"""
