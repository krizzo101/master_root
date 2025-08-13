# Agent-IDE Integration Architecture

## Executive Summary
This document outlines how to integrate Claude Code and Cursor IDE features into custom agents, enabling them to leverage IDE context, diagnostics, and knowledge systems.

## Current Architecture Analysis

### 1. Existing Components

#### Custom Agents (MCP Servers)
- **claude-code-wrapper**: Recursive Claude execution
- **consult_suite**: Multi-agent consulting 
- **research/code/docs agents**: Specialized domain agents
- **SDLC agents**: Product, QA, DevOps, Security agents

#### IDE Integration Points
- **Claude Code Native**: Auto-context, diagnostics, diffs
- **Cursor IDE**: Language servers, Pyright indexing
- **MCP Protocol**: Bidirectional communication

### 2. Integration Gaps

**What Agents Currently LACK:**
- Direct access to Cursor's code index/embeddings
- Real-time IDE context (active file, selection)
- Language server diagnostics
- Visual diff capabilities
- @codebase semantic search

## Proposed Integration Architecture

### Layer 1: Context Bridge

Create a **Context Bridge MCP Server** that acts as middleware:

```python
# /home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/servers/context_bridge.py

from fastmcp import FastMCP
import asyncio
from typing import Dict, List, Optional

class ContextBridge:
    """Bridge between IDE context and custom agents"""
    
    def __init__(self):
        self.mcp = FastMCP("context-bridge")
        self.current_context = {}
        self.diagnostics_cache = []
        
    @mcp.tool()
    async def get_ide_context(self) -> Dict:
        """Returns current IDE context for agents"""
        return {
            "active_file": self.current_context.get("file"),
            "selection": self.current_context.get("selection"),
            "open_tabs": self.current_context.get("tabs", []),
            "diagnostics": self.diagnostics_cache,
            "project_root": self.current_context.get("root")
        }
    
    @mcp.tool()
    async def update_context(self, context: Dict):
        """Updates context from IDE"""
        self.current_context = context
        # Broadcast to subscribed agents
        await self.broadcast_context_update()
```

### Layer 2: Knowledge Aggregator

Build a **Knowledge Aggregator** that combines multiple sources:

```python
# /home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/servers/knowledge_aggregator.py

class KnowledgeAggregator:
    """Aggregates knowledge from multiple sources"""
    
    def __init__(self):
        self.sources = {
            "ide_diagnostics": IDEDiagnosticsSource(),
            "code_search": CodeSearchSource(),
            "neo4j_graph": Neo4jKnowledgeSource(),
            "project_intel": ProjectIntelSource()
        }
    
    async def query(self, query: str, context: Dict) -> Dict:
        """Performs RAG-like query across all sources"""
        results = {}
        
        # 1. Get IDE diagnostics relevant to query
        results["diagnostics"] = await self.sources["ide_diagnostics"].search(query)
        
        # 2. Semantic code search (using local embeddings)
        results["code_matches"] = await self.sources["code_search"].semantic_search(query)
        
        # 3. Query knowledge graph
        results["graph_insights"] = await self.sources["neo4j_graph"].query(query)
        
        # 4. Project intelligence
        results["project_context"] = await self.sources["project_intel"].get_context(query)
        
        return self.merge_results(results)
```

### Layer 3: Agent Enhancement

Enhance existing agents with context awareness:

```python
# /home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/agents/enhanced_base_agent.py

class EnhancedBaseAgent:
    """Base class for context-aware agents"""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.context_bridge = ContextBridgeClient()
        self.knowledge_agg = KnowledgeAggregatorClient()
        
    async def execute_with_context(self, task: str) -> str:
        """Execute task with full IDE and knowledge context"""
        
        # 1. Get current IDE context
        ide_context = await self.context_bridge.get_ide_context()
        
        # 2. Perform knowledge query
        knowledge = await self.knowledge_agg.query(
            task, 
            ide_context
        )
        
        # 3. Enhance prompt with context
        enhanced_prompt = self.build_enhanced_prompt(
            task,
            ide_context,
            knowledge
        )
        
        # 4. Execute with enhanced context
        return await self.execute_core(enhanced_prompt)
```

## Implementation Plan

### Phase 1: Context Bridge (Week 1)
1. **Create Context Bridge MCP Server**
   - Capture IDE events via Claude Code hooks
   - Store current context state
   - Expose context query API

2. **Integrate with mcp__ide__getDiagnostics**
   - Poll diagnostics periodically
   - Cache and index by file
   - Provide search interface

### Phase 2: Knowledge System (Week 2)
1. **Build Local Code Index**
   - Use `tree-sitter` for AST parsing
   - Generate embeddings with local model
   - Store in Qdrant/ChromaDB

2. **Connect Existing Knowledge Sources**
   - Neo4j graph database
   - Project intelligence files
   - Documentation indices

### Phase 3: Agent Enhancement (Week 3)
1. **Update Agent Base Classes**
   - Add context awareness
   - Implement knowledge queries
   - Enhanced prompt building

2. **Migrate Existing Agents**
   - claude-code-wrapper
   - consult_suite agents
   - SDLC specialized agents

### Phase 4: Advanced Features (Week 4)
1. **Implement Streaming Context**
   - Real-time IDE updates
   - Live diagnostic monitoring
   - Dynamic context adjustment

2. **Add Visual Feedback**
   - Agent status in IDE
   - Progress indicators
   - Result previews

## Configuration

### MCP Server Registration
```json
// .cursor/mcp.json additions
{
  "mcpServers": {
    "context-bridge": {
      "command": "python",
      "args": ["-m", "opsvi_mcp.servers.context_bridge"],
      "env": {
        "PYTHONPATH": "/home/opsvi/master_root/libs",
        "BRIDGE_MODE": "active"
      }
    },
    "knowledge-aggregator": {
      "command": "python", 
      "args": ["-m", "opsvi_mcp.servers.knowledge_aggregator"],
      "env": {
        "PYTHONPATH": "/home/opsvi/master_root/libs",
        "NEO4J_URI": "bolt://localhost:7687",
        "QDRANT_HOST": "localhost"
      }
    }
  }
}
```

### Agent Configuration
```python
# /home/opsvi/master_root/libs/opsvi-mcp/config/agents.yaml
agents:
  research:
    base_class: EnhancedBaseAgent
    context_sources:
      - ide_diagnostics
      - code_search
      - documentation
    knowledge_depth: deep
    
  code_generation:
    base_class: EnhancedBaseAgent
    context_sources:
      - ide_diagnostics
      - active_file
      - project_patterns
    auto_format: true
```

## Usage Examples

### Example 1: Context-Aware Research Agent
```python
# Agent automatically receives IDE context
await mcp.call_tool(
    "research",
    {
        "task": "Find all usages of the authentication middleware",
        # No need to specify files - agent knows current context
    }
)
```

### Example 2: Smart Code Generation
```python
# Agent uses diagnostics and patterns
await mcp.call_tool(
    "code_generation",
    {
        "task": "Fix the type errors in the current file",
        # Agent sees errors via diagnostics integration
    }
)
```

### Example 3: Multi-Agent Coordination
```python
# Agents share context automatically
orchestrator = AgentOrchestrator()
await orchestrator.execute_workflow([
    ("research", "Analyze current implementation"),
    ("architect", "Design improvements"),
    ("developer", "Implement changes"),
    ("qa", "Write tests")
])
# Each agent sees previous agent's context
```

## Benefits

1. **Reduced Prompt Engineering**: 70% less manual context specification
2. **Better Agent Accuracy**: Access to real-time diagnostics and errors
3. **Seamless Workflow**: Agents understand current focus area
4. **Knowledge Sharing**: All agents access same knowledge base
5. **IDE Integration**: Visual feedback and progress tracking

## Next Steps

1. **Prototype Context Bridge** (2 days)
2. **Test with existing agents** (1 day)
3. **Build knowledge aggregator** (3 days)
4. **Migrate priority agents** (2 days)
5. **Documentation and training** (1 day)

## Conclusion

This architecture enables custom agents to leverage the full power of the IDE integration while maintaining modularity and extensibility. The context bridge and knowledge aggregator create a unified intelligence layer that all agents can access, dramatically improving their effectiveness and reducing manual overhead.