from shared.mcp.arxiv_mcp_client import ArXivMCPClient

from ..logging.research_logger import get_logger


class MCPArxivTool:
    def __init__(self):
        self.logger = get_logger(__name__)

    async def run(self, parameters: dict) -> dict:
        self.logger.info(f"Running ArxivMCPClient with: {parameters}")
        client = ArXivMCPClient()
        try:
            papers = await client.search_papers(parameters["query"], max_results=5)
            papers_with_fulltext = []
            for paper in papers:
                paper_dict = {
                    "title": paper.title,
                    "summary": paper.summary,
                    "authors": paper.authors,
                    "links": paper.links,
                    "pdf_url": paper.pdf_url,
                    "paper_id": paper.paper_id,
                }
                try:
                    # Download the paper (if not already downloaded)
                    await client.download_paper(paper.paper_id)
                    # Read the full paper content (markdown)
                    full_text = await client.read_paper(paper.paper_id)
                    paper_dict["full_text"] = full_text
                except Exception as e:
                    self.logger.error(
                        f"Failed to download/read paper {paper.paper_id}: {e}"
                    )
                    paper_dict["full_text"] = None
                papers_with_fulltext.append(paper_dict)
            return {
                "papers": papers_with_fulltext,
                "total_results": len(papers),
            }
        except Exception as e:
            self.logger.error(f"ArXivMCPClient failed: {e}")
            return {"error": str(e), "papers": [], "total_results": 0}
