"""arxiv_mcp_client.py

Asynchronous client for interacting with ArXiv MCP research tools.
Provides methods to search for papers, download papers, and read paper content,
using the MCP research_papers server interface.
"""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    setup_logger,
)

setup_logger(LogConfig())
import asyncio
import json
import sys
from typing import Any

from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger


class ArxivMCPClient:
    """
    Client for ArXiv MCP operations.

    Attributes:
        logger: O3Logger instance for logging.
    """

    def __init__(self) -> None:
        """
        Initialize the ArxivMCPClient and its logger.
        """
        self.logger = get_logger()

    async def search_papers(
        self, query: str, max_results: int = 5, categories: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Asynchronously search for papers on ArXiv.

        Args:
            query: Search query string.
            max_results: Maximum number of results to return.
            categories: Optional list of category filters.

        Returns:
            A dict containing search results.
        """
        try:
            import mcp_research_papers_search_papers

            result = await mcp_research_papers_search_papers(
                query=query, max_results=max_results, categories=categories
            )
            return result
        except ImportError as e:
            self.logger.log_error(f"Failed to import ArXiv MCP search tool: {e}")
            raise ImportError("Failed to import ArXiv MCP search tool") from e
        except Exception as e:
            self.logger.log_error(f"Failed to search papers: {e}")
            raise RuntimeError("Error searching papers") from e
        else:
            pass
        finally:
            pass

    async def download_paper(
        self, paper_id: str, check_status: bool = False
    ) -> dict[str, Any]:
        """
        Asynchronously download a paper by its ArXiv ID.

        Args:
            paper_id: The ArXiv ID of the paper.
            check_status: If True, only check conversion status.

        Returns:
            A dict containing download status or result.
        """
        try:
            import mcp_research_papers_download_paper

            result = await mcp_research_papers_download_paper(
                paper_id=paper_id, check_status=check_status
            )
            return result
        except ImportError as e:
            self.logger.log_error(f"Failed to import ArXiv MCP download tool: {e}")
            raise ImportError("Failed to import ArXiv MCP download tool") from e
        except Exception as e:
            self.logger.log_error(f"Failed to download paper: {e}")
            raise RuntimeError("Error downloading paper") from e
        else:
            pass
        finally:
            pass

    async def read_paper(self, paper_id: str) -> dict[str, Any]:
        """
        Asynchronously read the content of a paper by its ArXiv ID.

        Args:
            paper_id: The ArXiv ID of the paper.

        Returns:
            A dict containing the paper content.
        """
        try:
            import mcp_research_papers_read_paper

            result = await mcp_research_papers_read_paper(paper_id=paper_id)
            return result
        except ImportError as e:
            self.logger.log_error(f"Failed to import ArXiv MCP read tool: {e}")
            raise ImportError("Failed to import ArXiv MCP read tool") from e
        except Exception as e:
            self.logger.log_error(f"Failed to read paper: {e}")
            raise RuntimeError("Error reading paper") from e
        else:
            pass
        finally:
            pass


async def main() -> None:
    """
    Main asynchronous entry point for command-line invocation.
    """
    logger = get_logger()
    if len(sys.argv) < 2:
        logger.log_error("Usage: python arxiv_mcp_client.py <command> [args...]")
        sys.exit(1)
    else:
        pass
    command = sys.argv[1]
    client = ArxivMCPClient()
    try:
        if command == "search_papers":
            if len(sys.argv) < 3:
                logger.log_error(
                    "Usage: python arxiv_mcp_client.py search_papers <query> [max_results] [categories...]"
                )
                sys.exit(1)
            else:
                pass
            query = sys.argv[2]
            max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            categories = sys.argv[4:] if len(sys.argv) > 4 else None
            result = await client.search_papers(
                query=query, max_results=max_results, categories=categories
            )
        elif command == "download_paper":
            if len(sys.argv) < 3:
                logger.log_error(
                    "Usage: python arxiv_mcp_client.py download_paper <paper_id> [check_status]"
                )
                sys.exit(1)
            else:
                pass
            paper_id = sys.argv[2]
            check_status = (
                sys.argv[3].lower() in ("true", "1", "yes")
                if len(sys.argv) > 3
                else False
            )
            result = await client.download_paper(
                paper_id=paper_id, check_status=check_status
            )
        elif command == "read_paper":
            if len(sys.argv) < 3:
                logger.log_error(
                    "Usage: python arxiv_mcp_client.py read_paper <paper_id>"
                )
                sys.exit(1)
            else:
                pass
            paper_id = sys.argv[2]
            result = await client.read_paper(paper_id=paper_id)
        else:
            logger.log_error(f"Unknown command: {command}")
            sys.exit(1)
        logger.log_info(json.dumps(result))
    except Exception as e:
        logger.log_error(f"Error executing command '{command}': {e}")
        sys.exit(1)
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    asyncio.run(main())
else:
    pass
