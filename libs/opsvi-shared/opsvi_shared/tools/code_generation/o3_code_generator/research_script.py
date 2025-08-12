"""
Research Script using MCP Tools with Agent Intelligence

This module defines ResearchAgent for conducting comprehensive technical research
using web search, Context7, and ArXiv workflows. It leverages shared utilities
for directory management, file generation, input loading, output formatting, and
prompt building. Logging is configured via O3Logger.
"""

import asyncio

from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger

logger = get_logger()


def run_research(topic: str, max_urls: int, methods: list[str]) -> None:
    """Conduct research using MCP tools."""
    try:
        logger.log_info(f"Research: {topic} with methods: {methods}")
        agent = ResearchAgent()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            report = loop.run_until_complete(
                agent.research_topic(topic, max_urls, methods)
            )
            output_file = agent.save_research_report(report)
            logger.log_info(
                f"Research completed successfully. Results saved to: {output_file}"
            )
        finally:
            loop.close()
    except Exception as e:
        logger.log_error(f"Error during research: {e}")
        raise
