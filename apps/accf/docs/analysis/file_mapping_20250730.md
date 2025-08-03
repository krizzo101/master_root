<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"ACCF Research Agent File Mapping","description":"Comprehensive mapping of production, reference, knowledge, and compliance files relevant to the ACCF research agent enhancement project, including priority extraction matrix and detailed file paths.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to understand the hierarchical structure of production, reference, knowledge, and compliance files related to the ACCF research agent. Use the detailed sections and priority matrix to guide file extraction and integration tasks. Pay attention to the comprehensive file paths and their categorization for accurate context during code generation and system enhancement. Ensure navigation through the document is efficient by leveraging the logical divisions and key tables provided.","sections":[{"name":"Document Introduction and Overview","description":"Introduces the document purpose, date, and session ID, and distinguishes between reference and production/development files.","line_start":7,"line_end":15},{"name":"Production and Development Files","description":"Details the core production and development files categorized into Core Research Agent, Shared Infrastructure, Configuration & Dependencies, and Documentation & Analysis.","line_start":16,"line_end":48},{"name":"Reference Files (Comprehensive)","description":"Lists comprehensive reference files grouped into Research Tools (MCP Integration), Research Agent Implementation, MCP Client Implementations, Supporting Infrastructure, and Advanced Research Implementation.","line_start":49,"line_end":91},{"name":"Knowledge and Analysis Files","description":"Contains current knowledge update files and analysis documents relevant to the project status and roadmap.","line_start":92,"line_end":110},{"name":"Cursor Rules","description":"Specifies cursor rule files for OpenAI API compliance and o3 agent usage guidelines.","line_start":111,"line_end":120},{"name":"Extraction Priority Matrix","description":"Defines critical, high, medium priority files for phased extraction and integration, including documentation and architecture references.","line_start":121,"line_end":153},{"name":"Comprehensive File Paths for o3_AGENT","description":"Provides a Python list of absolute file paths covering production, reference, knowledge, and compliance files for the o3_agent context.","line_start":154,"line_end":199},{"name":"Next Action Note","description":"Instruction to use the comprehensive file mapping to provide complete context to o3_agent for code generation.","line_start":200,"line_end":202}],"key_elements":[{"name":"Production/Development Files Tables","description":"Multiple tables listing production files with their types, statuses, and descriptions, aiding understanding of active components and dependencies.","line":18},{"name":"Reference Files Tables","description":"Detailed tables enumerating reference implementation files across various categories, essential for comprehensive codebase understanding.","line":51},{"name":"Knowledge & Analysis Files Tables","description":"Tables listing knowledge update and analysis documents that provide project insights and status updates.","line":94},{"name":"Cursor Rules Table","description":"Table listing compliance and usage guideline files critical for maintaining API standards and agent behavior.","line":113},{"name":"Extraction Priority Matrix Tables","description":"Four tables categorizing files by extraction priority phases with purpose and target integration, guiding phased development and deployment.","line":123},{"name":"Comprehensive File Paths Code Block","description":"Python code block listing all relevant file paths for the o3_agent, facilitating automated context loading and file referencing.","line":155}]}
-->
<!-- FILE_MAP_END -->

# ACCF Research Agent File Mapping
## Reference vs Production/Development Files

**Date**: 2025-07-30
**Purpose**: Map all relevant files for research agent enhancement
**Session ID**: `accf_research_agent_enhancement_20250730`

---

## 1. PRODUCTION/DEVELOPMENT FILES

### 1.1 Core Research Agent
| File                                    | Type           | Status   | Description                           |
| --------------------------------------- | -------------- | -------- | ------------------------------------- |
| `capabilities/research_agent.py`        | **PRODUCTION** | ✅ Active | Current basic research agent (53 LOC) |
| `capabilities/knowledge_agent.py`       | **PRODUCTION** | ✅ Active | Neo4j GraphRAG integration (239 LOC)  |
| `capabilities/neo4j_knowledge_graph.py` | **PRODUCTION** | ✅ Active | GraphRAG implementation (412 LOC)     |

### 1.2 Shared Infrastructure
| File                                              | Type           | Status   | Description                      |
| ------------------------------------------------- | -------------- | -------- | -------------------------------- |
| `shared/openai_interfaces/responses_interface.py` | **PRODUCTION** | ✅ Active | OpenAI Responses API integration |
| `shared/openai_interfaces/base.py`                | **PRODUCTION** | ✅ Active | Base interface class             |
| `shared/mcp/mcp_server_template.py`               | **PRODUCTION** | ✅ Active | MCP server template              |

### 1.3 Configuration & Dependencies
| File                           | Type           | Status      | Description               |
| ------------------------------ | -------------- | ----------- | ------------------------- |
| `requirements.txt`             | **PRODUCTION** | ✅ Active    | Project dependencies      |
| `accf_agents/core/settings.py` | **PRODUCTION** | ⚠️ Needs Fix | Contains gpt-4o violation |
| `.env.example`                 | **PRODUCTION** | ✅ Active    | Environment template      |

### 1.4 Documentation & Analysis
| File                                            | Type           | Status   | Description                  |
| ----------------------------------------------- | -------------- | -------- | ---------------------------- |
| `docs/analysis/phase1_gap_analysis.md`          | **PRODUCTION** | ✅ Active | Phase 1 analysis results     |
| `docs/analysis/current_vs_desired_analysis.md`  | **PRODUCTION** | ✅ Active | Current vs desired state     |
| `docs/analysis/reference_capability_mapping.md` | **PRODUCTION** | ✅ Active | Reference capability mapping |
| `PHASE1_IMPLEMENTATION_PROMPT.md`               | **PRODUCTION** | ✅ Active | o3 agent generated prompt    |

---

## 2. REFERENCE FILES (COMPREHENSIVE)

### 2.1 Research Tools (MCP Integration)
| File                                                   | Type          | Status    | Description                          |
| ------------------------------------------------------ | ------------- | --------- | ------------------------------------ |
| `.reference/research_team/tools/mcp_search_tool.py`    | **REFERENCE** | ✅ Working | Brave search integration (18 LOC)    |
| `.reference/research_team/tools/mcp_firecrawl_tool.py` | **REFERENCE** | ✅ Working | Web scraping integration (15 LOC)    |
| `.reference/research_team/tools/mcp_arxiv_tool.py`     | **REFERENCE** | ✅ Working | Academic papers integration (43 LOC) |
| `.reference/research_team/tools/mcp_context7_tool.py`  | **REFERENCE** | ✅ Working | Tech docs integration                |
| `.reference/research_team/tools/mcp_client.py`         | **REFERENCE** | ✅ Working | ArangoDB database integration        |

### 2.2 Research Agent Implementation
| File                                                 | Type          | Status    | Description                     |
| ---------------------------------------------------- | ------------- | --------- | ------------------------------- |
| `.reference/research_team/agents/research_agent.py`  | **REFERENCE** | ✅ Working | Async MCP orchestration         |
| `.reference/research_team/agents/synthesis_agent.py` | **REFERENCE** | ✅ Working | Multi-source synthesis (47 LOC) |
| `.reference/research_team/research_workflow.py`      | **REFERENCE** | ✅ Working | 11-stage LangGraph workflow     |

### 2.3 MCP Client Implementations
| File                                                   | Type          | Status    | Description         |
| ------------------------------------------------------ | ------------- | --------- | ------------------- |
| `.reference/research_team/mcp/brave_mcp_search.py`     | **REFERENCE** | ✅ Working | Brave search client |
| `.reference/research_team/mcp/firecrawl_mcp_client.py` | **REFERENCE** | ✅ Working | Firecrawl client    |
| `.reference/research_team/mcp/arxiv_mcp_client.py`     | **REFERENCE** | ✅ Working | ArXiv client        |
| `.reference/research_team/mcp/context7_mcp_client.py`  | **REFERENCE** | ✅ Working | Context7 client     |

### 2.4 Supporting Infrastructure
| File                                                  | Type          | Status    | Description          |
| ----------------------------------------------------- | ------------- | --------- | -------------------- |
| `.reference/research_team/logging/research_logger.py` | **REFERENCE** | ✅ Working | Research logging     |
| `.reference/research_team/db/db_writer.py`            | **REFERENCE** | ✅ Working | Database operations  |
| `.reference/research_team/pyproject.toml`             | **REFERENCE** | ✅ Working | Poetry configuration |

### 2.5 Advanced Research Implementation
| File                                            | Type          | Status    | Description                      |
| ----------------------------------------------- | ------------- | --------- | -------------------------------- |
| `.reference/research_team/research_archived.py` | **REFERENCE** | ✅ Working | OAMAT research tools (422 LOC)   |
| `.reference/research_team/research.py`          | **REFERENCE** | ✅ Working | Enhanced research tool (497 LOC) |
| `.reference/research_team/research_workflow.md` | **REFERENCE** | ✅ Working | 11-stage workflow documentation  |
| `.reference/research_team/researcher_agent.md`  | **REFERENCE** | ✅ Working | ResearcherAgent documentation    |

---

## 3. KNOWLEDGE & ANALYSIS FILES

### 3.1 Current Knowledge Files
| File                                                      | Type          | Status   | Description                   |
| --------------------------------------------------------- | ------------- | -------- | ----------------------------- |
| `knowledge_update_accf_research_integration_20250730.md`  | **KNOWLEDGE** | ✅ Active | Project overview and roadmap  |
| `knowledge_update_neo4j_research_agent_20250730.md`       | **KNOWLEDGE** | ✅ Active | Neo4j integration details     |
| `knowledge_update_research_agent_20250730.md`             | **KNOWLEDGE** | ✅ Active | Research agent analysis       |
| `knowledge_update_project_analysis_20250730.md`           | **KNOWLEDGE** | ✅ Active | Project structure analysis    |
| `knowledge_update_research_agent_enhancement_20250730.md` | **KNOWLEDGE** | ✅ Active | Latest tech updates & context |

### 3.2 Analysis Documents
| File                                   | Type         | Status   | Description                 |
| -------------------------------------- | ------------ | -------- | --------------------------- |
| `ACCF_RESEARCH_INTEGRATION_ROADMAP.md` | **ANALYSIS** | ✅ Active | 14-week integration roadmap |
| `PHASE_1_2_COMPLETION_STATUS.md`       | **ANALYSIS** | ✅ Active | Current project status      |

---

## 4. CURSOR RULES

### 4.1 Cursor Rules
| File                                         | Type     | Status   | Description                 |
| -------------------------------------------- | -------- | -------- | --------------------------- |
| `.cursor/rules/953-openai-api-standards.mdc` | **RULE** | ✅ Active | OpenAI API compliance rules |
| `.cursor/rules/o3_agent.mdc`                 | **RULE** | ✅ Active | o3 agent usage guidelines   |

---

## 5. EXTRACTION PRIORITY MATRIX

### 5.1 Critical Files to Extract (Phase 1)
| Priority       | File                                                   | Purpose         | Target Integration               |
| -------------- | ------------------------------------------------------ | --------------- | -------------------------------- |
| 🔴 **Critical** | `.reference/research_team/tools/mcp_search_tool.py`    | Brave search    | `capabilities/research_agent.py` |
| 🔴 **Critical** | `.reference/research_team/tools/mcp_firecrawl_tool.py` | Web scraping    | `capabilities/research_agent.py` |
| 🔴 **Critical** | `.reference/research_team/mcp/brave_mcp_search.py`     | Search client   | `shared/mcp/`                    |
| 🔴 **Critical** | `.reference/research_team/mcp/firecrawl_mcp_client.py` | Scraping client | `shared/mcp/`                    |

### 5.2 High Priority Files (Phase 2)
| Priority   | File                                                 | Purpose                | Target Integration               |
| ---------- | ---------------------------------------------------- | ---------------------- | -------------------------------- |
| 🟡 **High** | `.reference/research_team/agents/research_agent.py`  | Async orchestration    | `capabilities/research_agent.py` |
| 🟡 **High** | `.reference/research_team/agents/synthesis_agent.py` | Multi-source synthesis | `capabilities/research_agent.py` |
| 🟡 **High** | `.reference/research_team/research_archived.py`      | OAMAT research tools   | `capabilities/research_agent.py` |
| 🟡 **High** | `.reference/research_team/research.py`               | Enhanced research tool | `capabilities/research_agent.py` |

### 5.3 Medium Priority Files (Phase 3)
| Priority     | File                                                  | Purpose                | Target Integration               |
| ------------ | ----------------------------------------------------- | ---------------------- | -------------------------------- |
| 🟢 **Medium** | `.reference/research_team/tools/mcp_arxiv_tool.py`    | Academic papers        | `capabilities/research_agent.py` |
| 🟢 **Medium** | `.reference/research_team/research_workflow.py`       | Workflow orchestration | `capabilities/research_agent.py` |
| 🟢 **Medium** | `.reference/research_team/tools/mcp_context7_tool.py` | Tech docs integration  | `capabilities/research_agent.py` |

### 5.4 Documentation & Architecture (Reference)
| Priority     | File                                            | Purpose                | Usage                    |
| ------------ | ----------------------------------------------- | ---------------------- | ------------------------ |
| 🟢 **Medium** | `.reference/research_team/research_workflow.md` | 11-stage workflow docs | Architecture reference   |
| 🟢 **Medium** | `.reference/research_team/researcher_agent.md`  | Agent documentation    | Implementation reference |

---

## 6. COMPREHENSIVE FILE PATHS FOR o3_AGENT

```python
file_paths = [
    # Production files
    "/home/opsvi/ACCF/capabilities/research_agent.py",
    "/home/opsvi/ACCF/capabilities/knowledge_agent.py",
    "/home/opsvi/ACCF/capabilities/neo4j_knowledge_graph.py",
    "/home/opsvi/ACCF/shared/openai_interfaces/responses_interface.py",
    "/home/opsvi/ACCF/shared/openai_interfaces/base.py",
    "/home/opsvi/ACCF/shared/mcp/mcp_server_template.py",
    "/home/opsvi/ACCF/requirements.txt",
    "/home/opsvi/ACCF/accf_agents/core/settings.py",
    "/home/opsvi/ACCF/.env.example",

    # Reference implementation files - TOOLS
    "/home/opsvi/ACCF/.reference/research_team/tools/mcp_search_tool.py",
    "/home/opsvi/ACCF/.reference/research_team/tools/mcp_firecrawl_tool.py",
    "/home/opsvi/ACCF/.reference/research_team/tools/mcp_arxiv_tool.py",
    "/home/opsvi/ACCF/.reference/research_team/tools/mcp_context7_tool.py",
    "/home/opsvi/ACCF/.reference/research_team/tools/mcp_client.py",

    # Reference implementation files - AGENTS
    "/home/opsvi/ACCF/.reference/research_team/agents/research_agent.py",
    "/home/opsvi/ACCF/.reference/research_team/agents/synthesis_agent.py",

    # Reference implementation files - MCP CLIENTS
    "/home/opsvi/ACCF/.reference/research_team/mcp/brave_mcp_search.py",
    "/home/opsvi/ACCF/.reference/research_team/mcp/firecrawl_mcp_client.py",
    "/home/opsvi/ACCF/.reference/research_team/mcp/arxiv_mcp_client.py",
    "/home/opsvi/ACCF/.reference/research_team/mcp/context7_mcp_client.py",

    # Reference implementation files - INFRASTRUCTURE
    "/home/opsvi/ACCF/.reference/research_team/logging/research_logger.py",
    "/home/opsvi/ACCF/.reference/research_team/db/db_writer.py",
    "/home/opsvi/ACCF/.reference/research_team/pyproject.toml",

    # Reference implementation files - ADVANCED RESEARCH
    "/home/opsvi/ACCF/.reference/research_team/research_archived.py",
    "/home/opsvi/ACCF/.reference/research_team/research.py",
    "/home/opsvi/ACCF/.reference/research_team/research_workflow.py",
    "/home/opsvi/ACCF/.reference/research_team/research_workflow.md",
    "/home/opsvi/ACCF/.reference/research_team/researcher_agent.md",

    # Knowledge and analysis files
    "/home/opsvi/ACCF/knowledge_update_accf_research_integration_20250730.md",
    "/home/opsvi/ACCF/knowledge_update_neo4j_research_agent_20250730.md",
    "/home/opsvi/ACCF/knowledge_update_research_agent_20250730.md",
    "/home/opsvi/ACCF/knowledge_update_project_analysis_20250730.md",
    "/home/opsvi/ACCF/knowledge_update_research_agent_enhancement_20250730.md",
    "/home/opsvi/ACCF/docs/analysis/current_vs_desired_analysis.md",
    "/home/opsvi/ACCF/docs/analysis/reference_capability_mapping.md",
    "/home/opsvi/ACCF/ACCF_RESEARCH_INTEGRATION_ROADMAP.md",
    "/home/opsvi/ACCF/PHASE_1_2_COMPLETION_STATUS.md",

    # Compliance files
    "/home/opsvi/ACCF/.cursor/rules/953-openai-api-standards.mdc",
    "/home/opsvi/ACCF/.cursor/rules/o3_agent.mdc",
]
```

---

**Next Action**: Use this comprehensive file mapping to provide complete context to o3_agent for code generation