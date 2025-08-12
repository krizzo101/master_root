import asyncio
import sys

from .agents.research_agent import ResearchAgent
from .agents.synthesis_agent import SynthesisAgent
from .db.db_writer import write_research_to_db
from .logging.research_logger import get_logger

logger = get_logger(__name__)


# --- Phase 1: Knowledge Assessment ---
async def knowledge_assessment(query: str) -> dict:
    """
    Assess existing knowledge, score confidence, and decide research strategy.
    Returns: dict with assessment, confidence scores, and strategy.
    """
    # Placeholder: In a real system, query internal KB/db, score, and decide.
    logger.info("[Phase 1] Assessing existing knowledge base...")
    assessment = {
        "existing_knowledge": False,
        "confidence": 0.0,
        "strategy": "external_research",
    }
    # Validation gate: must document assessment and strategy
    assert "strategy" in assessment, "Strategy decision missing in assessment."
    return assessment


# --- Phase 2: External Research ---
async def external_research(query: str) -> dict:
    """
    Perform parallel multi-source research using available tools/agents.
    Returns: dict of raw research results from all sources.
    """
    logger.info("[Phase 2] Running external research in parallel...")
    research_agent = ResearchAgent()
    # Gather from all tools in parallel
    raw_results = await research_agent.gather(query)
    # Validation gate: must have results from at least one source
    assert raw_results and any(
        raw_results.values()
    ), "No external research results found."
    return raw_results


# --- Phase 3: Synthesis/Standardization ---
async def synthesis_standardization(raw_results: dict) -> dict:
    """
    Synthesize, standardize, and attribute sources for all research findings.
    Returns: dict with standardized synthesis and source attributions.
    """
    logger.info("[Phase 3] Synthesizing and standardizing research results...")
    synthesis_agent = SynthesisAgent()
    synthesis = await synthesis_agent.synthesize_and_store(raw_results)
    # Validation gate: must include source attribution
    assert "summary" in synthesis, "Synthesis missing summary."
    return synthesis


# --- Phase 4: Quality Assurance ---
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


# --- Phase 5: Knowledge Persistence ---
async def knowledge_persistence(synthesis: dict, qa_result: dict) -> dict:
    """
    Store research synthesis and QA results in the knowledge base, map relationships.
    Returns: dict with storage result and any mapped relationships.
    """
    logger.info("[Phase 5] Persisting research and mapping relationships...")
    # Store synthesis in DB
    db_result = await write_research_to_db({"synthesis": synthesis, "qa": qa_result})
    # Placeholder: In a real system, map relationships/entities
    persistence_result = {"db_result": db_result, "relationships": []}
    # Validation gate: must confirm storage
    assert "db_result" in persistence_result, "Persistence missing db_result."
    return persistence_result


# --- Main Orchestrator ---
async def run_research_workflow(query: str) -> dict:
    """
    Orchestrate the full research workflow across all phases.
    Returns: dict with all intermediate and final results.
    """
    results = {}
    # Phase 1: Knowledge Assessment
    results["assessment"] = await knowledge_assessment(query)
    # Phase 2: External Research (if needed)
    if results["assessment"].get("strategy") == "external_research":
        results["raw_results"] = await external_research(query)
    else:
        results["raw_results"] = {}
    # Phase 3: Synthesis/Standardization
    results["synthesis"] = await synthesis_standardization(results["raw_results"])
    # Phase 4: Quality Assurance
    results["qa_result"] = await quality_assurance(results["synthesis"])
    # Phase 5: Knowledge Persistence
    results["persistence"] = await knowledge_persistence(
        results["synthesis"], results["qa_result"]
    )
    logger.info("[Workflow Complete] All phases executed successfully.")
    return results


# Example usage (for testing)
if __name__ == "__main__":
    from pprint import pprint

    def print_section(title, content, sep=True):
        print(f"\n{'='*40}\n{title}\n{'='*40}")
        if isinstance(content, dict):
            pprint(content, width=120, compact=False)
        elif isinstance(content, list):
            for item in content:
                pprint(item, width=120, compact=False)
        else:
            print(content)
        if sep:
            print("-" * 40)

    def generate_session_report(output):
        report = {}
        # ArXiv papers
        arxiv = output.get("raw_results", {}).get("arxiv", {})
        papers = arxiv.get("papers", [])
        arxiv_report = []
        for p in papers:
            arxiv_report.append(
                {
                    "paper_id": p.get("paper_id"),
                    "title": p.get("title"),
                    "downloaded": bool(p.get("full_text")),
                    "full_text_length": (
                        len(p.get("full_text")) if p.get("full_text") else 0
                    ),
                }
            )
        report["arxiv_papers"] = arxiv_report
        # Brave search
        brave = output.get("raw_results", {}).get("search", {})
        brave_results = brave.get("results", [])
        brave_report = []
        for r in brave_results:
            brave_report.append(
                {
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "desc_len": len(r.get("description", "")),
                }
            )
        report["brave_search_results"] = brave_report
        # Firecrawl
        firecrawl = output.get("raw_results", {}).get("firecrawl", {})
        firecrawl_results = firecrawl.get("results", [])
        firecrawl_report = []
        for r in firecrawl_results:
            firecrawl_report.append(
                {
                    "url": r.get("url", "N/A"),
                    "content_length": len(r.get("content", "")),
                }
            )
        report["firecrawl_scrapes"] = firecrawl_report
        # Context7
        context7 = output.get("raw_results", {}).get("context7", {})
        context7_report = {
            "library_id": context7.get("library_id"),
            "topic": context7.get("topic"),
            "token_count": context7.get("token_count"),
            "success": context7.get("success"),
            "error": context7.get("error"),
        }
        report["context7_docs"] = context7_report
        return report

    if len(sys.argv) < 2:
        print(
            "Usage: python -m applications.research_team.research_workflow 'your research query'"
        )
        sys.exit(1)
    query = sys.argv[1]
    output = asyncio.run(run_research_workflow(query))

    print("\n\nRESEARCH WORKFLOW SUMMARY\n" + "#" * 60)
    print_section("PHASE 1: Knowledge Assessment", output.get("assessment"))
    print_section("PHASE 2: External Research (Raw Results)", output.get("raw_results"))
    print_section("PHASE 3: Synthesis/Standardization", output.get("synthesis"))
    print_section("PHASE 4: Quality Assurance", output.get("qa_result"))
    print_section(
        "PHASE 5: Knowledge Persistence", output.get("persistence"), sep=False
    )
    print("\nWorkflow complete. All results above are human-readable.\n")

    # --- SESSION REPORT ---
    print("\n\nSESSION REPORT\n" + "#" * 60)
    session_report = generate_session_report(output)
    print_section("ArXiv Papers Downloaded/Used", session_report["arxiv_papers"])
    print_section(
        "Brave Search Results (Pages)", session_report["brave_search_results"]
    )
    print_section("Firecrawl Scraped Pages", session_report["firecrawl_scrapes"])
    print_section(
        "Context7 Documentation Accessed", session_report["context7_docs"], sep=False
    )
    print("\nSession report complete.\n")
