<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Reference Capability Mapping","description":"Documentation mapping specific working capabilities from reference implementations to the current ResearchAgent class, detailing extraction plans, integration targets, and phased implementation strategy.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to understand the mapping of reference capabilities to the current ResearchAgent implementation. Focus on the structured extraction plans, code integration targets, and phased development strategy. Use the section divisions and key elements such as code blocks, tables, and method descriptions to facilitate navigation and comprehension. Ensure line numbers are precise and sections do not overlap. Highlight important code snippets, tables, and conceptual explanations to aid developers in implementing and integrating these capabilities.","sections":[{"name":"Introduction and Purpose","description":"Overview of the document's purpose, date, and approach to mapping capabilities from reference to current implementation.","line_start":7,"line_end":15},{"name":"External Research Tools","description":"Details on specific external research tools to extract and adapt, including Brave Search, Firecrawl Web Scraping, and ArXiv Research Papers with their reference locations, current implementations, and integration targets.","line_start":16,"line_end":113},{"name":"Multi-source Orchestration","description":"Explanation and code for asynchronous execution of multiple research tools in parallel and query transformation logic to optimize queries for different tools.","line_start":114,"line_end":224},{"name":"Synthesis and Validation","description":"Methods for synthesizing multi-source research results into coherent summaries and quality assurance processes for validating and scoring research results.","line_start":225,"line_end":317},{"name":"Implementation Priority Matrix","description":"Table summarizing the priority, effort, impact, and reference status of various capabilities to guide implementation focus.","line_start":318,"line_end":339},{"name":"Extraction Strategy","description":"Phased plan for extracting and integrating capabilities over weeks, detailing focus areas, tasks, and expected outcomes for each phase.","line_start":340,"line_end":379},{"name":"Integration Guidelines","description":"Guidelines for maintaining API stability, gradual enhancement, and ensuring code quality during capability integration.","line_start":380,"line_end":405},{"name":"Next Action","description":"Final note indicating the immediate next step to begin Phase 1 extraction of Brave Search and Firecrawl capabilities.","line_start":406,"line_end":406}],"key_elements":[{"name":"Brave Search Integration Code Block","description":"Python class MCPSearchTool showing the current implementation of Brave Search integration with async run method.","line":21},{"name":"Firecrawl Web Scraping Code Block","description":"Python class MCPFirecrawlTool illustrating web scraping capability using Firecrawl with async run method.","line":40},{"name":"ArXiv Research Papers Code Block","description":"Python class MCPArxivTool demonstrating academic paper search integration with async run method.","line":67},{"name":"Async Tool Execution Code Block","description":"Async gather method for parallel execution of multiple research tools with error handling and logging.","line":127},{"name":"Query Transformation Code Block","description":"Async _transform_queries_for_tools method implementing intelligent query optimization for different research tools.","line":145},{"name":"Multi-source Synthesis Code Block","description":"synthesize method converting raw research results into a readable summary combining multiple sources.","line":236},{"name":"Quality Assurance Code Block","description":"Async quality_assurance function validating research results with reliability scoring and gap analysis.","line":323},{"name":"Implementation Priority Matrix Table","description":"Table listing capabilities with priority, effort, impact, and reference status to guide implementation order.","line":318},{"name":"Extraction Strategy Phases","description":"Three phased extraction plans detailing focus, tasks, and expected outcomes for capability integration.","line":341},{"name":"Integration Guidelines List","description":"Bullet points outlining best practices for API maintenance, incremental enhancement, and code quality.","line":381}]}
-->
<!-- FILE_MAP_END -->

# Reference Capability Mapping
## Specific Components to Extract and Adapt

**Date**: 2025-07-30
**Purpose**: Map specific working capabilities from reference to current implementation
**Approach**: Extract functional components, not entire architecture

---

## 1. External Research Tools

### 1.1 Brave Search Integration

**Reference Location**: `.reference/research_team/tools/mcp_search_tool.py`
**Status**: ✅ Working
**Lines**: 18 LOC

**Current Implementation**:
```python
class MCPSearchTool:
    def __init__(self):
        self.logger = get_logger(__name__)

    async def run(self, parameters: dict) -> dict:
        self.logger.info(f"Running BraveMCPSearch with: {parameters}")
        searcher = BraveMCPSearch()
        result = await searcher.search(parameters["query"], count=5)
        return {
            "results": [r.__dict__ for r in result.results],
            "total_results": result.total_results,
        }
```

**Extraction Plan**:
1. Copy `BraveMCPSearch` class from reference
2. Adapt for current `ResearchAgent` class
3. Add to existing `answer_question_using_llm()` method
4. Maintain existing response format

**Integration Target**:
```python
# Add to current ResearchAgent class
def _search_web(self, query: str) -> dict:
    """Add web search capability using Brave"""
    # Extract and adapt reference implementation
```

### 1.2 Firecrawl Web Scraping

**Reference Location**: `.reference/research_team/tools/mcp_firecrawl_tool.py`
**Status**: ✅ Working
**Lines**: 15 LOC

**Current Implementation**:
```python
class MCPFirecrawlTool:
    def __init__(self):
        self.logger = get_logger(__name__)

    async def run(self, parameters: dict) -> dict:
        self.logger.info(f"Running FirecrawlMCPClient with: {parameters}")
        client = FirecrawlMCPClient()
        results = await client.search(parameters["query"], limit=5)
        return {"results": [r.__dict__ for r in results]}
```

**Extraction Plan**:
1. Copy `FirecrawlMCPClient` integration
2. Add web content scraping capability
3. Integrate with existing response format
4. Add content extraction and processing

**Integration Target**:
```python
# Add to current ResearchAgent class
def _scrape_web_content(self, query: str) -> dict:
    """Add web scraping capability using Firecrawl"""
    # Extract and adapt reference implementation
```

### 1.3 ArXiv Research Papers

**Reference Location**: `.reference/research_team/tools/mcp_arxiv_tool.py`
**Status**: ✅ Working
**Lines**: 43 LOC

**Current Implementation**:
```python
class MCPArxivTool:
    def __init__(self):
        self.logger = get_logger(__name__)

    async def run(self, parameters: dict) -> dict:
        self.logger.info(f"Running ArxivMCPClient with: {parameters}")
        client = ArxivMCPClient()
        results = await client.search(parameters["query"], limit=5)
        return {"papers": [r.__dict__ for r in results]}
```

**Extraction Plan**:
1. Copy `ArxivMCPClient` integration
2. Add academic paper research capability
3. Extract paper metadata and abstracts
4. Integrate with synthesis process

**Integration Target**:
```python
# Add to current ResearchAgent class
def _search_academic_papers(self, query: str) -> dict:
    """Add academic paper research capability"""
    # Extract and adapt reference implementation
```

---

## 2. Multi-source Orchestration

### 2.1 Async Tool Execution

**Reference Location**: `.reference/research_team/agents/research_agent.py`
**Status**: ✅ Working
**Lines**: 25-35 (gather method)

**Current Implementation**:
```python
async def gather(self, query: str) -> dict:
    self.logger.info(f"Gathering research for: {query}")

    # Transform queries intelligently for each tool
    transformed_queries = await self._transform_queries_for_tools(query)

    tasks = {
        name: tool.run({"query": transformed_queries[name]})
        for name, tool in self.tools.items()
    }
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    output = {}
    for name, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            self.logger.error(f"{name} tool failed: {result}")
            output[name] = {"error": str(result)}
        else:
            output[name] = result
    return output
```

**Extraction Plan**:
1. Extract async orchestration logic
2. Adapt for current `ResearchAgent` class
3. Add parallel execution capability
4. Maintain error handling and logging

**Integration Target**:
```python
# Add to current ResearchAgent class
async def _gather_research_parallel(self, query: str) -> dict:
    """Execute multiple research tools in parallel"""
    # Extract and adapt reference implementation
```

### 2.2 Query Transformation

**Reference Location**: `.reference/research_team/agents/research_agent.py`
**Status**: ✅ Working
**Lines**: 37-75 (_transform_queries_for_tools method)

**Current Implementation**:
```python
async def _transform_queries_for_tools(self, original_query: str) -> dict:
    """Intelligently transform the original query for each research tool."""
    from shared.openai_interfaces.responses_interface import OpenAIResponsesInterface

    interface = OpenAIResponsesInterface()

    system_prompt = """You are an intelligent query transformer for research tools. Transform the user's query to be optimal for each specific tool:

1. **search** (Brave Search): Keep the original query - it's good for general web search
2. **firecrawl** (Web Scraping): Keep the original query - it's good for finding relevant URLs

Return a JSON object with the transformed queries for each tool."""

    user_prompt = f"Transform this query for each research tool: '{original_query}'"

    try:
        result = await interface.create_structured_response(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_format={
                "type": "json_object",
                "properties": {
                    "search": {"type": "string", "description": "Query for Brave Search"},
                    "firecrawl": {"type": "string", "description": "Query for Firecrawl"},
                },
                "required": ["search", "firecrawl"],
            },
        )

        if result and hasattr(result, "content"):
            import json
            transformed = json.loads(result.content)
            return transformed
        else:
            return {"search": original_query, "firecrawl": original_query}

    except Exception as e:
        self.logger.error(f"Query transformation failed: {e}")
        return {"search": original_query, "firecrawl": original_query}
```

**Extraction Plan**:
1. Extract query transformation logic
2. Adapt for current research agent
3. Add intelligent query optimization
4. Maintain fallback to original query

**Integration Target**:
```python
# Add to current ResearchAgent class
def _optimize_query_for_tools(self, query: str) -> dict:
    """Optimize query for different research tools"""
    # Extract and adapt reference implementation
```

---

## 3. Synthesis and Validation

### 3.1 Multi-source Synthesis

**Reference Location**: `.reference/research_team/agents/synthesis_agent.py`
**Status**: ✅ Working
**Lines**: 47 LOC

**Current Implementation**:
```python
def synthesize(self, raw_results: dict) -> str:
    # Convert raw research results to a readable summary
    if not raw_results:
        return ""

    summary_parts = []

    # Process search results
    if "search" in raw_results and raw_results["search"].get("results"):
        search_results = raw_results["search"]["results"]
        if search_results:
            summary_parts.append("## Search Results")
            for i, result in enumerate(search_results[:3], 1):
                title = result.get("title", "No title")
                description = result.get("description", "No description")
                summary_parts.append(f"{i}. **{title}**\n{description}\n")

    # Process Firecrawl results
    if "firecrawl" in raw_results and raw_results["firecrawl"].get("content"):
        firecrawl_content = raw_results["firecrawl"]["content"]
        if firecrawl_content:
            summary_parts.append("## Web Content")
            summary_parts.append(
                firecrawl_content[:500] + "..." if len(firecrawl_content) > 500 else firecrawl_content
            )

    if not summary_parts:
        return "No research data found."

    return "\n\n".join(summary_parts)
```

**Extraction Plan**:
1. Extract synthesis logic
2. Adapt for current response format
3. Add multi-source combination
4. Implement structured output

**Integration Target**:
```python
# Add to current ResearchAgent class
def _synthesize_results(self, raw_results: dict) -> str:
    """Combine results from multiple sources into coherent response"""
    # Extract and adapt reference implementation
```

### 3.2 Quality Assurance

**Reference Location**: `.reference/research_team/research_workflow.py`
**Status**: ✅ Working
**Lines**: 62-75 (quality_assurance function)

**Current Implementation**:
```python
async def quality_assurance(synthesis: dict) -> dict:
    """
    Validate cross-source consistency, reliability, and identify gaps.
    Returns: dict with QA results, reliability scores, and gap analysis.
    """
    logger.info("[Phase 4] Running quality assurance checks...")
    # Placeholder: In a real system, implement cross-source validation, reliability scoring, gap analysis
    qa_result = {"reliability": 1.0, "contradictions": [], "gaps": []}
    # Validation gate: must document reliability and gaps
    assert "reliability" in qa_result, "QA missing reliability score."
    return qa_result
```

**Extraction Plan**:
1. Extract QA framework
2. Add reliability scoring
3. Implement gap analysis
4. Add validation checks

**Integration Target**:
```python
# Add to current ResearchAgent class
def _validate_results(self, results: dict) -> dict:
    """Validate and score research results quality"""
    # Extract and adapt reference implementation
```

---

## 4. Implementation Priority Matrix

| Capability               | Priority   | Effort | Impact | Reference Status |
| ------------------------ | ---------- | ------ | ------ | ---------------- |
| **Brave Search**         | 🔴 Critical | Low    | High   | ✅ Working        |
| **Firecrawl Scraping**   | 🔴 Critical | Low    | High   | ✅ Working        |
| **Async Orchestration**  | 🟡 High     | Medium | High   | ✅ Working        |
| **Query Transformation** | 🟡 High     | Medium | Medium | ✅ Working        |
| **Synthesis**            | 🟢 Medium   | Low    | Medium | ✅ Working        |
| **Quality Assurance**    | 🟢 Medium   | Medium | Low    | ✅ Working        |
| **ArXiv Papers**         | 🟢 Medium   | Low    | Medium | ✅ Working        |

---

## 5. Extraction Strategy

### 5.1 Phase 1: Core Research Tools (Week 1-2)
**Focus**: Brave Search + Firecrawl Scraping

**Extraction Tasks**:
1. Copy `BraveMCPSearch` class from reference
2. Copy `FirecrawlMCPClient` class from reference
3. Adapt for current `ResearchAgent` class
4. Add to existing `answer_question_using_llm()` method
5. Test with existing API

**Expected Outcome**: Enhanced research with web search and content scraping

### 5.2 Phase 2: Parallel Execution (Week 3-4)
**Focus**: Async orchestration + Query transformation

**Extraction Tasks**:
1. Extract async `gather()` method from reference
2. Extract `_transform_queries_for_tools()` method
3. Adapt for current research agent
4. Add parallel execution capability
5. Maintain backward compatibility

**Expected Outcome**: Faster research with intelligent query optimization

### 5.3 Phase 3: Synthesis (Week 5-6)
**Focus**: Multi-source synthesis + Quality assurance

**Extraction Tasks**:
1. Extract `synthesize()` method from reference
2. Extract `quality_assurance()` framework
3. Adapt for current response format
4. Add result validation and scoring
5. Test synthesis quality

**Expected Outcome**: Coherent multi-source research responses

---

## 6. Integration Guidelines

### 6.1 Maintain Current API
- Keep `answer_question()` and `answer_question_using_llm()` methods
- Maintain existing response format
- Preserve error handling patterns
- Keep logging structure

### 6.2 Gradual Enhancement
- Add capabilities incrementally
- Test each addition thoroughly
- Maintain backward compatibility
- Document changes clearly

### 6.3 Code Quality
- Extract clean, reusable components
- Add proper error handling
- Implement comprehensive logging
- Follow existing code patterns

---

**Next Action**: Begin Phase 1 extraction of Brave Search and Firecrawl capabilities