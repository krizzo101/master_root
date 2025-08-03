<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"PROMPT: Implement Phase 1 \u2013 Discovery & Gap Analysis","description":"This document provides detailed instructions, context, and templates for completing Phase 1 of the ACCF Research Capability Upgrade project, focusing on Discovery & Gap Analysis. It guides the Lead Backend Engineer through objectives, technical context, step-by-step tasks, validation checklists, output templates, and quality criteria to produce a comprehensive analysis report.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to extract a structured file map that reflects its logical organization and content themes. Identify major sections and subsections based on the heading hierarchy and content boundaries. Capture key elements such as code blocks, tables, checklists, and templates that are critical for navigation and understanding. Ensure all line numbers are accurate, sections do not overlap, and descriptions clearly convey each section's purpose. Provide a JSON output with file metadata, AI instructions as a single string, logically divided sections with line ranges and descriptions, and key elements with line references and explanations.","sections":[{"name":"Document Header and Metadata","description":"Introduction to the prompt and metadata specifying target model, token limits, expected output format, and date format conventions.","line_start":7,"line_end":16},{"name":"Role and Situation","description":"Defines the role of the user as Lead Backend Engineer and the immediate mission to complete Phase 1 of the roadmap.","line_start":17,"line_end":23},{"name":"Objective and Scope of Phase 1","description":"Details the goals and boundaries of Phase 1, focusing on discovery and gap analysis without code migration or refactoring.","line_start":24,"line_end":34},{"name":"Essential Technical Context","description":"Provides technical background including current production implementation, reference implementation details, and the approved roadmap snapshot with expectations for Phase 1.","line_start":35,"line_end":61},{"name":"Step-by-Step Instructions","description":"Comprehensive procedural guide outlining environment setup, codebase inventory, functional analysis, architectural delta, risk gathering, stakeholder input, deliverable creation, and internal validation steps.","line_start":62,"line_end":118},{"name":"Completion Validation Checklist","description":"Checklist to confirm all deliverables and quality criteria are met before requesting review and progressing to the next phase.","line_start":119,"line_end":131},{"name":"Output Template for Phase 1 Report","description":"Exact markdown template to be copied verbatim into the analysis report, including sections for executive summary, current and reference states, gap matrix, risks, findings, open questions, and appendices.","line_start":132,"line_end":134},{"name":"Phase 1 \u2013 Discovery & Gap Analysis Report Template","description":"Detailed markdown structure of the final report with nested subsections for code overview and functionality under current and reference states, plus tables for gap matrix and risks.","line_start":135,"line_end":182},{"name":"Quality Criteria","description":"Defines standards for clarity, accuracy, traceability, reproducibility, and token efficiency to ensure high-quality deliverables.","line_start":183,"line_end":192},{"name":"Final Reminders","description":"Important notes emphasizing no production code modification, meaningful commits, and naming conventions for branches and files.","line_start":193,"line_end":202}],"key_elements":[{"name":"Target Model and Token Limit Metadata","description":"Specifies the AI model to be used and the maximum tokens to generate, critical for prompt configuration.","line":11},{"name":"Approved Roadmap Snapshot Table","description":"Table summarizing Phase 1 duration, deliverables, and exit criteria, providing a quick reference for project milestones.","line":55},{"name":"Environment Setup Bash Command","description":"Code block showing Neo4j connectivity verification command, essential for environment validation.","line":76},{"name":"Codebase Inventory Bash Commands","description":"Commands for generating directory tree and lines of code statistics, foundational for analysis artifacts.","line":81},{"name":"Architectural Delta Bash Commands","description":"Commands to generate dependency trees for production and reference implementations, supporting architectural comparison.","line":98},{"name":"Completion Validation Checklist Items","description":"List of specific criteria to confirm completeness and quality of the Phase 1 deliverables before review.","line":120},{"name":"Output Template Markdown Block","description":"Multi-line markdown code block providing the exact template for the Phase 1 report to ensure consistency.","line":133},{"name":"Gap Matrix Table Template","description":"Table format illustrating categories, production vs. reference states, and deltas, central to gap analysis reporting.","line":161},{"name":"Risks & Constraints Table Template","description":"Structured table for documenting identified risks with likelihood, impact, and mitigation strategies.","line":167}]}
-->
<!-- FILE_MAP_END -->

# PROMPT: Implement Phase 1 – Discovery & Gap Analysis
_Artifact Type: LLM Instruction Prompt_

## 0. Metadata
• Target model: `gpt-4o-2025-07` (or any GPT-4-class model ≥32 k context)
• Max tokens to **generate**: 4 000
• Expected assistant output: **Git-style Markdown document** – use the template in §6 exactly.
• Branch / file date format: **YYYYMMDD** (e.g., `20250805`)

---

## 1. Role & Situation
You are **Lead Backend Engineer – ACCF Research Capability Upgrade** working in the `accf` monorepo.
Your immediate mission is to **complete Phase 1 (Discovery & Gap Analysis)** of the 14-week roadmap approved on 2025-08-01.

---

## 2. Objective & Scope (Phase 1 only)
Deliver a comprehensive **Discovery & Gap Analysis Report** that:
1. Compares the _current production_ research stack with the _reference_ advanced implementation.
2. Identifies functional, architectural, and dependency deltas.
3. Enumerates risks, unknowns, and missing assets.
4. Produces an actionable findings list that feeds Phase 2 ADRs.

_Out-of-scope_: Any code migration, refactor, or work beyond analysis & documentation.

---

## 3. Essential Technical Context

### 3.1 Current Production Implementation
Path: `capabilities/research_agent.py` (≈ 54 LOC)
Traits:
• Canned answer logic + fallback LLM call (`OpenAIResponsesInterface`)
• No MCP tool usage, no workflow orchestration
• Public API: `answer_question()` and `answer_question_using_llm()`
• Neo4j GraphRAG persists via separate `KnowledgeAgent`

### 3.2 Reference Implementation (Advanced)
Root: `.reference/research_team/`
Components:
• `agents/research_agent.py` → async MCP orchestration (Brave Search, Firecrawl, etc.)
• `research_workflow.py` → 11-stage LangGraph workflow with QA gates
• Multiple `tools/mcp_*` wrappers
• Persists to graph via `.reference/research_team/db/db_writer.py`

### 3.3 Approved Roadmap Snapshot (Phase 1 expectations)
| Phase | Duration | Deliverable                   | Exit Criterion          |
| ----- | -------- | ----------------------------- | ----------------------- |
| 1     | Week 1   | Delta report, interview notes | PM & Architect sign-off |

Feature-flag architecture (`IResearchEngine`) and Adapter pattern already captured in ADR-001 (draft).

---

## 4. Step-by-Step Instructions

1. Environment Setup
   a. `git pull origin main`
   b. Create branch `feature/phase1-discovery-<YYYYMMDD>`
   c. Ensure Python 3.11, Poetry ≥ 1.7, local Neo4j 5.x instance (bolt://localhost:7687), and `OPENAI_API_KEY` exported.
   d. Verify Neo4j connectivity:
      ```bash
      cypher-shell -u neo4j -p $NEO4J_PASS "MATCH (n) RETURN count(n) LIMIT 1;"
      ```

2. Codebase Inventory
   a. Produce directory tree and LOC stats:
      ```bash
      tree -L 3 capabilities/research_agent.py .reference/research_team | tee artifacts/tree_<YYYYMMDD>.txt
      cloc capabilities/research_agent.py .reference/research_team | tee artifacts/loc_stats_<YYYYMMDD>.txt
      ```
   b. Commit the generated files. Record the exact tool versions (`tree --version`, `cloc --version`) in the report appendix for reproducibility.

3. Functional Analysis
   a. For every public method in production vs. reference, record: signature, side-effects, external calls, and sync/async nature.
   b. Note missing capabilities (e.g., multi-tool gather, synthesis, QA gates, circuit breakers).

4. Architectural Delta
   a. Generate dependency graphs:
      ```bash
      poetry show --tree > artifacts/dep_tree_prod_<YYYYMMDD>.txt
      (cd .reference/research_team && poetry show --tree) > artifacts/dep_tree_ref_<YYYYMMDD>.txt
      ```
   b. Draw data-flow diagrams (ASCII acceptable) showing: question → tool calls → synthesis → KG persist in both versions.
   c. Highlight differences: async vs. sync execution, error handling patterns, logging, telemetry.

5. Risk & Constraint Gathering
   a. Review security hardening notes (all CVEs resolved).
   b. Flag divergent library versions or incompatible licenses.
   c. List potential blockers (e.g., LangGraph compatibility with Python 3.11, Neo4j driver versions).

6. Stakeholder Input
   a. "Simulate interviews" by _reading_ and summarising:
      • `ACCF_RESEARCH_INTEGRATION_ROADMAP.md`
      • ADR-001 draft
      • Issue tracker tickets tagged `research-agent`, `mcp`
   b. Capture stakeholder goals, pain-points, and unanswered questions.

7. Deliverable Creation
   a. Create `docs/analysis/phase1_gap_analysis.md` using the template in §6 **verbatim**.
   b. Populate every section; link each delta to specific file paths or code snippets.
   c. Attach artifacts (LOC stats, dependency trees, diagrams) via relative paths.
   d. Git commit & push; open PR titled "Phase 1 – Discovery & Gap Analysis".

8. Internal Validation (self-check)
   a. Run the checklist in §5; do not request review until all boxes ticked.
   b. Add reviewers: `@tech-architect`, `@project-manager`.
   c. Ensure CI passes: `ruff`, `mypy`, `pytest` (no new tests needed yet).

---

## 5. Completion Validation Checklist

Tick ☑ once satisfied:
☐ `docs/analysis/phase1_gap_analysis.md` exists and follows template.
☐ Sections present: Executive Summary, Current State, Reference State, Gap Matrix, Risks, Open Questions, Recommendations.
☐ At least **5 key deltas** and **3 risks** identified.
☐ Artifacts attached: LOC stats, dependency graphs, data-flow diagrams.
☐ Tool & version metadata documented in Appendix A.
☐ Neo4j connectivity verified with sample query (see §4-1-d) and noted in report.
☐ PR CI green; reviewers assigned; awaiting PM & Architect approval.

---

## 6. Output Template (copy exactly into `docs/analysis/phase1_gap_analysis.md`)

```markdown
# Phase 1 – Discovery & Gap Analysis Report
_Date: YYYY-MM-DD_
_Authors: Lead Backend Engineer, …_

## 1. Executive Summary
<≤150-word overview of findings & next actions>

## 2. Current Production State
### 2.1 Code Overview
- File: `capabilities/research_agent.py` (54 LOC)
- …

### 2.2 Functionality
<bulleted list>

## 3. Reference Implementation State
### 3.1 Code Overview
- Root: `.reference/research_team/`
- …

### 3.2 Functionality
<bulleted list>

## 4. Gap Matrix
| Category           | Production | Reference          | Delta   |
| ------------------ | ---------- | ------------------ | ------- |
| Tool orchestration | ✗          | Brave, Firecrawl ✓ | Missing |
| …                  | …          | …                  | …       |

## 5. Risks & Constraints
| ID  | Description | Likelihood | Impact | Mitigation |
| --- | ----------- | ---------- | ------ | ---------- |
| R1  |             |            |        |

## 6. Findings & Recommendations
1. …

## 7. Open Questions
1. …

## 8. Appendices
A. Tool versions & commands
B. LOC stats (`artifacts/loc_stats_<YYYYMMDD>.txt`)
C. Dependency trees (`artifacts/dep_tree_*`)
D. Data-flow diagrams
```

---

## 7. Quality Criteria
• Clarity: avoid unexplained acronyms; define any new term on first use.
• Accuracy: all stats generated via commands, not estimates.
• Traceability: every delta links to code or artifact.
• Reproducibility: someone else can rerun commands & obtain identical results.
• Token efficiency: avoid redundant prose; use bullets where possible.

---

## 8. Final Reminders
• **Do NOT modify production code** during Phase 1. Analysis only.
• Keep commits small and meaningful (analysis, artifacts, report).
• Branch & file names must contain the **YYYYMMDD** date stamp.

Proceed with the steps above. Once PM & Architect sign off, Phase 2 (Architecture & ADRs) begins.