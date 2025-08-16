# AI Capability Implementation Plan

## Current State Analysis

### 🟢 Existing Infrastructure
1. **opsvi-llm** - LLM provider interfaces
   - ✅ OpenAI provider skeleton
   - ✅ Perplexity provider skeleton
   - ✅ Embeddings interface
   - ✅ Batch processing interface
   - ✅ Structured responses interface
   - ⚠️ Requires: `openai>=1.0.0` (NOT installed)

2. **opsvi-agents** - Multi-agent framework
   - ✅ Base component structure
   - ⚠️ Incomplete implementations (syntax errors in `__init__.py`)
   - ⚠️ Template placeholders still present

3. **opsvi-asea** - Advanced cognitive systems
   - ✅ SDLC workflow automation
   - ✅ Orchestrator components
   - ✅ Cognitive enhancement modules
   - ✅ ArangoDB integration

4. **Environment**
   - ✅ API keys configured (OpenAI, Anthropic, Perplexity)
   - ✅ Project intelligence system (`.proj-intel/`)
   - ✅ Gatekeeper context management

### 🔴 Missing Core Dependencies
- ❌ `openai` package
- ❌ `anthropic` package
- ❌ `langchain` framework
- ❌ `chromadb` vector store
- ❌ `qdrant-client` vector store
- ❌ `transformers` for local models

### ⚠️ Critical Issues
1. **Syntax errors** in `libs/opsvi-agents/opsvi_agents/__init__.py`
2. **Missing implementations** for agent coordinators/schedulers
3. **No vector database** configured for RAG
4. **No model registry** or model management

## Implementation Plan

### Phase 1: Foundation (Immediate)
```bash
# 1. Install core AI dependencies
pip install openai anthropic langchain langchain-community chromadb qdrant-client transformers

# 2. Fix syntax errors in opsvi-agents
# - Repair __init__.py imports
# - Complete base agent implementations
# - Remove template placeholders

# 3. Verify LLM provider connections
# - Test OpenAI API connection
# - Test Anthropic API connection
# - Validate embeddings generation
```

### Phase 2: Core Capabilities (Week 1)
1. **LLM Provider Implementation**
   - Complete OpenAI provider with streaming support
   - Implement Anthropic Claude provider
   - Add fallback/retry logic
   - Implement token counting and cost tracking

2. **Agent Framework**
   - Implement base agent class with:
     - Memory management
     - Tool execution
     - State persistence
   - Create agent coordinator for multi-agent workflows
   - Add agent communication protocols

3. **Vector Store Integration**
   - Set up ChromaDB for local development
   - Configure Qdrant for production
   - Implement document chunking strategies
   - Create embedding pipelines

### Phase 3: Advanced Features (Week 2)
1. **RAG System**
   - Document ingestion pipeline
   - Semantic search implementation
   - Context window management
   - Citation tracking

2. **Agent Specializations**
   - Code generation agent
   - Research agent
   - Planning agent
   - QA/Testing agent
   - Documentation agent

3. **Workflow Orchestration**
   - LangGraph integration
   - State machine implementation
   - Checkpoint/resume capabilities
   - Error recovery mechanisms

### Phase 4: Integration (Week 3)
1. **ASEA Integration**
   - Connect cognitive enhancement modules
   - Integrate with ArangoDB knowledge graph
   - Enable autonomous learning loops

2. **Monitoring & Observability**
   - LLM call tracking
   - Cost monitoring
   - Performance metrics
   - Agent decision logging

3. **Testing & Validation**
   - Unit tests for providers
   - Integration tests for agents
   - End-to-end workflow tests
   - Performance benchmarks

## Quick Start Commands

```bash
# Step 1: Install dependencies
pip install -r requirements-ai.txt

# Step 2: Fix critical issues
python scripts/fix_agent_syntax.py

# Step 3: Verify installations
python scripts/verify_ai_setup.py

# Step 4: Run test suite
pytest libs/opsvi-llm/tests/
pytest libs/opsvi-agents/tests/
```

## Configuration Files Needed

1. `requirements-ai.txt` - AI/ML dependencies
2. `config/llm_providers.yaml` - Provider configurations
3. `config/agent_registry.yaml` - Agent definitions
4. `config/vector_stores.yaml` - Vector DB settings

## Success Metrics
- ✅ All AI packages installed and importable
- ✅ LLM providers return valid responses
- ✅ Agents can execute basic tasks
- ✅ Vector store can store/retrieve embeddings
- ✅ Multi-agent workflows complete successfully
- ✅ All tests pass with >80% coverage

## Risk Mitigation
- **API Rate Limits**: Implement exponential backoff
- **Cost Management**: Set spending limits, use caching
- **Model Failures**: Fallback providers, error handling
- **Data Privacy**: Local embeddings option, data sanitization

## Next Immediate Actions
1. Create `requirements-ai.txt` file
2. Fix syntax errors in opsvi-agents
3. Test LLM provider connections
4. Set up vector database
5. Implement base agent class