"""
Chat Analytics Module for OPSVI Monitoring

Provides comprehensive analytics for Claude chat logs including:
- Session analysis and summaries
- Response time metrics
- Activity patterns
- Tool usage analysis
- AI-powered insights
"""

from .analysis.response_analyzer import ResponseTimeAnalyzer
from .analysis.response_history import get_response_time_history
from .ingestion.sqlite_ingester import ChatLogParserSQLite

__all__ = [
    "ResponseTimeAnalyzer",
    "get_response_time_history",
    "ChatLogParserSQLite",
]

__version__ = "1.0.0"
