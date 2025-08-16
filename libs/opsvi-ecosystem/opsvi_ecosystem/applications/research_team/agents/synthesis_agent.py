import logging

from ..db.db_writer import write_research_to_db


class SynthesisAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def synthesize_and_store(self, raw_results: dict) -> dict:
        self.logger.info("Synthesizing research and writing to DB")
        summary = self.synthesize(raw_results)
        db_result = await write_research_to_db({"summary": summary})
        return {"summary": summary, "db_result": db_result}

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
                for i, result in enumerate(search_results[:3], 1):  # Limit to top 3
                    title = result.get("title", "No title")
                    description = result.get("description", "No description")
                    summary_parts.append(f"{i}. **{title}**\n{description}\n")

        # Process Firecrawl results
        if "firecrawl" in raw_results and raw_results["firecrawl"].get("content"):
            firecrawl_content = raw_results["firecrawl"]["content"]
            if firecrawl_content:
                summary_parts.append("## Web Content")
                summary_parts.append(
                    firecrawl_content[:500] + "..."
                    if len(firecrawl_content) > 500
                    else firecrawl_content
                )

        if not summary_parts:
            return "No research data found."

        return "\n\n".join(summary_parts)
