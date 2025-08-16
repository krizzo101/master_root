import asyncio

from prefect import flow, get_run_logger, task

from scripts.mcp.arxiv_mcp_client import ArxivMCPClient

# Import MCP clients
from scripts.mcp.brave_mcp_search import BraveMCPSearch
from scripts.mcp.context7_mcp_client import Context7MCPClient
from scripts.mcp.firecrawl_mcp_client import FirecrawlMCPClient

# --- Prefect Tasks ---


def run_async(coro):
    """Run an async coroutine in a synchronous context (for Prefect tasks)."""
    return asyncio.get_event_loop().run_until_complete(coro)


@task
def initialize_clients():
    return {
        "brave": BraveMCPSearch(),
        "firecrawl": FirecrawlMCPClient(),
        "context7": Context7MCPClient(),
        "arxiv": ArxivMCPClient(),
    }


@task
def plan_research(topic: str):
    # In a real workflow, this could analyze the topic and set parameters
    return {"search_query": topic, "library": topic, "arxiv_query": topic}


@task
def extract_urls_from_brave_results(brave_results):
    # Extract URLs from Brave search results for Firecrawl
    return [r.url for r in brave_results.results if getattr(r, "url", None)]


@task
def brave_search_task(clients, query: str):
    return run_async(clients["brave"].search(query))


@task
def firecrawl_task(clients, urls):
    # Scrape all URLs in parallel
    if not urls:
        return []
    return run_async(
        asyncio.gather(*(clients["firecrawl"].scrape(url) for url in urls))
    )


@task
def context7_task(clients, library: str):
    # Resolve library ID, then get docs
    libs = run_async(clients["context7"].resolve_library_id(library))
    if not libs:
        return None
    return run_async(clients["context7"].get_library_docs(libs[0].library_id))


@task
def arxiv_task(clients, query: str):
    return run_async(clients["arxiv"].search_papers(query))


@task
def synthesize_results(brave, firecrawl, context7, arxiv):
    # Aggregate and summarize all research
    return {
        "brave": brave,
        "firecrawl": firecrawl,
        "context7": context7,
        "arxiv": arxiv,
    }


# --- Main Prefect Flow ---


@flow
def workflow_generation_flow(topic: str):
    logger = get_run_logger()
    logger.info("Initializing MCP clients...")
    clients = initialize_clients.submit().result()

    logger.info("Planning research...")
    plan = plan_research.submit(topic).result()
    search_query = plan["search_query"]
    library = plan["library"]
    arxiv_query = plan["arxiv_query"]

    logger.info("Running Brave web search...")
    brave_future = brave_search_task.submit(clients, search_query)
    brave_results = brave_future.result()

    logger.info("Extracting URLs for Firecrawl...")
    urls = extract_urls_from_brave_results.submit(brave_results).result()

    logger.info("Launching Firecrawl, Context7, and Arxiv in parallel...")
    firecrawl_future = firecrawl_task.submit(clients, urls)
    context7_future = context7_task.submit(clients, library)
    arxiv_future = arxiv_task.submit(clients, arxiv_query)

    firecrawl_results = firecrawl_future.result()
    context7_results = context7_future.result()
    arxiv_results = arxiv_future.result()

    logger.info("Synthesizing results...")
    synthesis = synthesize_results.submit(
        brave_results, firecrawl_results, context7_results, arxiv_results
    ).result()

    logger.info("Workflow complete.")
    return synthesis


# --- Entrypoint ---

if __name__ == "__main__":
    import sys

    topic = sys.argv[1] if len(sys.argv) > 1 else "prefect workflow orchestration"
    result = workflow_generation_flow(topic)
    print(result)
