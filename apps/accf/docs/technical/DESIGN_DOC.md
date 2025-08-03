<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Research Agent Neo4j Migration Design Document","description":"Design document detailing the migration of the ACCF Research Agent from ArangoDB to Neo4j GraphRAG, including architecture, implementation, migration phases, and success criteria.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify logical sections based on the heading hierarchy and content themes. Ensure all line numbers are accurate and non-overlapping. Capture key elements such as code blocks, tables, and important concepts that aid navigation and understanding. Provide clear, descriptive section names and element descriptions to facilitate efficient comprehension and reference.","sections":[{"name":"Document Title and Introduction","description":"Title of the document and initial overview introducing the migration project and its scope.","line_start":7,"line_end":11},{"name":"Current State Analysis","description":"Analysis of the existing Neo4j schema and the current migration status, detailing nodes, relationships, and configuration.","line_start":12,"line_end":25},{"name":"Target Architecture","description":"Description of the target system architecture including Neo4j GraphRAG integration, database schema design with code block, and vector indexes.","line_start":26,"line_end":52},{"name":"Migration Status Overview","description":"Summary of migration phases completed, detailing core infrastructure, data migration, research agent integration, and testing & validation.","line_start":53,"line_end":74},{"name":"Implementation Details","description":"Details on Neo4j GraphRAG components, MCP integration, and research workflow integration outlining key components and processes.","line_start":75,"line_end":96},{"name":"Dependencies","description":"List of software dependencies and external systems required for the migration and operation of the Neo4j-based Research Agent.","line_start":97,"line_end":102},{"name":"Migration Steps","description":"Step-by-step checklist of migration tasks completed to transition to the Neo4j GraphRAG system.","line_start":103,"line_end":112},{"name":"Success Criteria","description":"Defined criteria to evaluate the success of the migration including functionality preservation, performance, and documentation.","line_start":113,"line_end":123}],"key_elements":[{"name":"Existing Neo4j Schema List","description":"Bullet list describing the existing nodes and relationships in the Neo4j schema.","line":14},{"name":"Migration Status: COMPLETED Section","description":"Bullet points listing primary files, dependencies, and configuration related to migration completion.","line":21},{"name":"Database Schema Design Code Block","description":"Code block showing the Neo4j database schema design with node labels, properties, and relationships.","line":36},{"name":"Vector Indexes List","description":"List of vector indexes defined for research content, findings, and questions.","line":48},{"name":"Migration Phases Checklist","description":"Four-phase checklist with completion status for core infrastructure, data migration, research agent integration, and testing.","line":55},{"name":"Neo4j GraphRAG Components List","description":"List of Neo4j GraphRAG components used in the implementation including retrievers and pipeline.","line":77},{"name":"MCP Integration Details","description":"Bullet points describing MCP Neo4j server integration features such as query execution and schema discovery.","line":83},{"name":"Research Workflow Integration Steps","description":"Numbered list outlining the stages of research workflow integration with Neo4j.","line":89},{"name":"Dependencies List","description":"List of required packages and systems for the migration and operation.","line":97},{"name":"Migration Steps Checklist","description":"Numbered list of migration tasks completed to achieve the new system setup.","line":103},{"name":"Success Criteria Checklist","description":"Checklist of criteria to measure migration success including functionality, performance, and documentation.","line":113}]}
-->
<!-- FILE_MAP_END -->

# Research Agent Neo4j Migration Design Document

## Overview
This document outlines the migration of the ACCF Research Agent from ArangoDB to Neo4j GraphRAG, leveraging the existing MCP Neo4j server and current database schema.

## Current State Analysis

### Existing Neo4j Schema
- **Project Nodes**: 2 projects with metadata, requirements, status tracking
- **Run Nodes**: 2 runs with pipeline tracking, cost monitoring, performance metrics
- **Task Nodes**: 3 tasks with decision tracking
- **Decision Nodes**: 3 decisions with confidence scoring and strategy tracking
- **Relationships**: (:Run)-[:OF_PROJECT]→(:Project), (:Task)-[:HAS_DECISION]→(:Decision)

### Migration Status: COMPLETED ✅
- **Primary File**: `capabilities/knowledge_agent.py` - KnowledgeGraph class using Neo4j GraphRAG
- **Dependencies**: `neo4j-graphrag[openai]` in requirements.txt
- **Configuration**: Neo4j environment variables in .cursor/mcp.json

## Target Architecture

### Neo4j GraphRAG Integration
1. **Vector Search Engine**: Neo4j GraphRAG VectorRetriever for semantic search
2. **Knowledge Graph Builder**: SimpleKGPipeline for automated KG construction
3. **Hybrid Retrieval**: Combine vector similarity with graph traversal
4. **Research Workflow**: 11-stage process with Neo4j persistence

### Database Schema Design
```
(:ResearchTopic {id, name, description, created_at})
(:ResearchSource {id, url, title, content, source_type, created_at})
(:ResearchFinding {id, content, confidence, methodology, created_at})
(:ResearchQuestion {id, question, context, status, created_at})

(:ResearchTopic)-[:HAS_QUESTION]->(:ResearchQuestion)
(:ResearchQuestion)-[:HAS_FINDING]->(:ResearchFinding)
(:ResearchFinding)-[:CITED_BY]->(:ResearchSource)
(:ResearchSource)-[:SUPPORTS]->(:ResearchFinding)
(:ResearchFinding)-[:RELATED_TO]->(:ResearchFinding)
```

### Vector Indexes
- **research_content_vector**: For ResearchSource content embeddings
- **research_finding_vector**: For ResearchFinding content embeddings
- **research_question_vector**: For ResearchQuestion embeddings

## Migration Status: COMPLETED ✅

### Phase 1: Core Infrastructure ✅
1. ✅ Replace ArangoDB client with Neo4j GraphRAG components
2. ✅ Implement vector index creation and management
3. ✅ Create Neo4j connection layer with MCP integration

### Phase 2: Data Migration ✅
1. ✅ Preserve existing Project/Run/Task/Decision data
2. ✅ Create new research-specific schema
3. ✅ Implement data validation and integrity checks

### Phase 3: Research Agent Integration ✅
1. ✅ Implement 11-stage research workflow with Neo4j
2. ✅ Add vector search capabilities
3. ✅ Integrate with existing ACCF agent architecture

### Phase 4: Testing & Validation ✅
1. ✅ Unit tests for Neo4j operations
2. ✅ Integration tests for research workflow
3. ✅ Performance validation and optimization

## Implementation Details

### Neo4j GraphRAG Components
- **VectorRetriever**: Native vector similarity search
- **HybridRetriever**: Vector + full-text search
- **VectorCypherRetriever**: Custom Cypher with vector search
- **SimpleKGPipeline**: Automated knowledge graph building

### MCP Integration
- **Existing MCP Neo4j Server**: Already configured and accessible
- **Cypher Query Execution**: Read/write operations via MCP
- **Schema Discovery**: Automatic schema inspection
- **Connection Management**: Secure authentication

### Research Workflow Integration
1. **Query Analysis**: Store research questions in Neo4j
2. **Source Discovery**: Track research sources and metadata
3. **Content Processing**: Vectorize and index research content
4. **Knowledge Extraction**: Build knowledge graph from findings
5. **Quality Assessment**: Confidence scoring and validation
6. **Synthesis**: Combine findings into coherent research output

## Dependencies
- **neo4j-graphrag[openai]**: Core GraphRAG functionality
- **neo4j**: Python driver for database access
- **openai**: Embedding generation
- **Existing MCP Neo4j Server**: Database connectivity

## Migration Steps ✅
1. ✅ Install Neo4j GraphRAG dependencies
2. ✅ Create vector indexes for research content
3. ✅ Implement Neo4j KnowledgeGraph class
4. ✅ Migrate existing knowledge agent functionality
5. ✅ Add research-specific schema and operations
6. ✅ Update configuration and environment variables
7. ✅ Implement comprehensive testing
8. ✅ Update documentation and changelog

## Success Criteria ✅
- ✅ All existing functionality preserved
- ✅ Vector search returns relevant results
- ✅ Research workflow integrates with Neo4j
- ✅ Performance meets or exceeds ArangoDB
- ✅ Comprehensive test coverage
- ✅ Clear documentation and migration notes