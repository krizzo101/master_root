"""
Advanced Query Engine for Collaboration Analytics
Fast search, pattern analysis, and performance insights
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .cache import CollaborationCacheManager
from .database import DatabaseManager
from .repositories import AnalyticsRepository

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    CONVERSATION_SEARCH = "conversation_search"
    AGENT_PERFORMANCE = "agent_performance"
    COLLABORATION_PATTERNS = "collaboration_patterns"
    SESSION_ANALYTICS = "session_analytics"
    TIME_SERIES = "time_series"
    CUSTOM_SQL = "custom_sql"


@dataclass
class QueryFilter:
    """Query filter parameters"""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    agent_ids: Optional[List[str]] = None
    session_ids: Optional[List[str]] = None
    message_types: Optional[List[str]] = None
    session_types: Optional[List[str]] = None
    agent_types: Optional[List[str]] = None
    limit: int = 100
    offset: int = 0


@dataclass
class QueryResult:
    """Query execution result"""

    query_type: QueryType
    data: List[Dict[str, Any]]
    total_count: int
    execution_time_ms: int
    cached: bool = False
    cache_key: Optional[str] = None


class CollaborationQueryEngine:
    """High-performance query engine for collaboration analytics"""

    def __init__(
        self, db_manager: DatabaseManager, cache_manager: CollaborationCacheManager
    ):
        self.db = db_manager
        self.cache = cache_manager
        self.analytics_repo = AnalyticsRepository(db_manager)

    async def search_conversations(
        self,
        search_text: str,
        filters: Optional[QueryFilter] = None,
        fuzzy: bool = True,
    ) -> QueryResult:
        """Search conversations with full-text search capabilities"""
        start_time = datetime.utcnow()
        filters = filters or QueryFilter()

        # Generate cache key
        cache_key = self._generate_cache_key(
            QueryType.CONVERSATION_SEARCH, search_text, filters.dict(), fuzzy
        )

        # Check cache first
        cached_result = await self.cache.get_cached_analytics(cache_key)
        if cached_result:
            return QueryResult(
                query_type=QueryType.CONVERSATION_SEARCH,
                data=cached_result["data"],
                total_count=cached_result["total_count"],
                execution_time_ms=cached_result["execution_time_ms"],
                cached=True,
                cache_key=cache_key,
            )

        # Execute search query
        async with self.db.get_pg_connection() as conn:
            # Build WHERE clause
            where_conditions = ["TRUE"]
            params = [search_text]
            param_counter = 2

            if filters.start_date:
                where_conditions.append(f"m.sent_at >= ${param_counter}")
                params.append(filters.start_date)
                param_counter += 1

            if filters.end_date:
                where_conditions.append(f"m.sent_at <= ${param_counter}")
                params.append(filters.end_date)
                param_counter += 1

            if filters.session_ids:
                where_conditions.append(f"m.session_id = ANY(${param_counter})")
                params.append(filters.session_ids)
                param_counter += 1

            if filters.agent_ids:
                where_conditions.append(
                    f"(m.sender_id = ANY(${param_counter}) OR m.receiver_id = ANY(${param_counter}))"
                )
                params.append(filters.agent_ids)
                param_counter += 1

            if filters.message_types:
                where_conditions.append(f"m.message_type = ANY(${param_counter})")
                params.append(filters.message_types)
                param_counter += 1

            where_clause = " AND ".join(where_conditions)

            # Full-text search query
            search_operator = "@@" if not fuzzy else "ILIKE"
            search_value = (
                f"plainto_tsquery('english', $1)" if not fuzzy else f"'%{search_text}%'"
            )

            query = f"""
                WITH ranked_messages AS (
                    SELECT
                        m.*,
                        s.name as session_name,
                        s.session_type,
                        sender.name as sender_name,
                        receiver.name as receiver_name,
                        ts_rank(to_tsvector('english', m.content), plainto_tsquery('english', $1)) as rank
                    FROM messages m
                    JOIN sessions s ON m.session_id = s.session_id
                    JOIN agents sender ON m.sender_id = sender.agent_id
                    LEFT JOIN agents receiver ON m.receiver_id = receiver.agent_id
                    WHERE {where_clause}
                        AND (
                            to_tsvector('english', m.content) {search_operator} {search_value}
                            OR m.content ILIKE $1
                        )
                ),
                total_count AS (
                    SELECT COUNT(*) as count FROM ranked_messages
                )
                SELECT
                    rm.*,
                    tc.count as total_count
                FROM ranked_messages rm
                CROSS JOIN total_count tc
                ORDER BY rm.rank DESC, rm.sent_at DESC
                LIMIT {filters.limit} OFFSET {filters.offset}
            """

            results = await conn.fetch(query, *params)

            # Format results
            data = []
            total_count = 0
            for row in results:
                if not total_count:
                    total_count = row["total_count"]

                data.append(
                    {
                        "message_id": row["message_id"],
                        "session_id": row["session_id"],
                        "session_name": row["session_name"],
                        "session_type": row["session_type"],
                        "sender_id": row["sender_id"],
                        "sender_name": row["sender_name"],
                        "receiver_id": row["receiver_id"],
                        "receiver_name": row["receiver_name"],
                        "message_type": row["message_type"],
                        "content": row["content"],
                        "metadata": row["metadata"],
                        "sent_at": row["sent_at"],
                        "relevance_score": float(row["rank"]) if row["rank"] else 0.0,
                    }
                )

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Cache result
        cache_data = {
            "data": data,
            "total_count": total_count,
            "execution_time_ms": execution_time,
        }
        await self.cache.cache_analytics_result(cache_key, cache_data, ttl=600)

        return QueryResult(
            query_type=QueryType.CONVERSATION_SEARCH,
            data=data,
            total_count=total_count,
            execution_time_ms=execution_time,
            cache_key=cache_key,
        )

    async def analyze_agent_performance(
        self, filters: Optional[QueryFilter] = None, metrics: Optional[List[str]] = None
    ) -> QueryResult:
        """Comprehensive agent performance analysis"""
        start_time = datetime.utcnow()
        filters = filters or QueryFilter()
        metrics = metrics or [
            "response_time",
            "message_count",
            "success_rate",
            "collaboration_score",
        ]

        cache_key = self._generate_cache_key(
            QueryType.AGENT_PERFORMANCE, filters.dict(), metrics
        )

        cached_result = await self.cache.get_cached_analytics(cache_key)
        if cached_result:
            return QueryResult(
                query_type=QueryType.AGENT_PERFORMANCE,
                data=cached_result["data"],
                total_count=cached_result["total_count"],
                execution_time_ms=cached_result["execution_time_ms"],
                cached=True,
                cache_key=cache_key,
            )

        async with self.db.get_pg_connection() as conn:
            # Build complex performance query
            date_filter = ""
            params = []

            if filters.start_date:
                date_filter += " AND m.sent_at >= $1"
                params.append(filters.start_date)

            if filters.end_date:
                date_filter += f" AND m.sent_at <= ${len(params) + 1}"
                params.append(filters.end_date)

            agent_filter = ""
            if filters.agent_ids:
                agent_filter = f" AND a.agent_id = ANY(${len(params) + 1})"
                params.append(filters.agent_ids)

            query = f"""
                WITH agent_metrics AS (
                    SELECT
                        a.agent_id,
                        a.name,
                        a.agent_type,
                        a.status,

                        -- Message metrics
                        COUNT(m.message_id) as total_messages,
                        COUNT(CASE WHEN m.receiver_id IS NOT NULL THEN 1 END) as directed_messages,
                        COUNT(CASE WHEN m.receiver_id IS NULL THEN 1 END) as broadcast_messages,

                        -- Response time metrics
                        AVG(m.response_time_ms) as avg_response_time,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY m.response_time_ms) as median_response_time,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY m.response_time_ms) as p95_response_time,

                        -- Collaboration metrics
                        COUNT(DISTINCT m.session_id) as sessions_participated,
                        COUNT(DISTINCT CASE WHEN m.receiver_id IS NOT NULL THEN m.receiver_id END) as unique_collaborators,

                        -- Time-based metrics
                        MIN(m.sent_at) as first_message,
                        MAX(m.sent_at) as last_message,
                        EXTRACT(epoch FROM (MAX(m.sent_at) - MIN(m.sent_at)))/3600 as active_hours

                    FROM agents a
                    LEFT JOIN messages m ON a.agent_id = m.sender_id
                    WHERE TRUE {date_filter} {agent_filter}
                    GROUP BY a.agent_id, a.name, a.agent_type, a.status
                ),
                collaboration_scores AS (
                    SELECT
                        am.agent_id,
                        -- Calculate collaboration score based on interactions
                        CASE
                            WHEN am.total_messages = 0 THEN 0
                            ELSE (
                                (am.unique_collaborators * 10) +
                                (am.sessions_participated * 5) +
                                CASE WHEN am.avg_response_time < 1000 THEN 20 ELSE 0 END +
                                CASE WHEN am.directed_messages::float / NULLIF(am.total_messages, 0) > 0.7 THEN 15 ELSE 0 END
                            )
                        END as collaboration_score
                    FROM agent_metrics am
                )
                SELECT
                    am.*,
                    cs.collaboration_score,
                    CASE
                        WHEN am.total_messages = 0 THEN 0
                        ELSE (am.directed_messages::float / am.total_messages * 100)
                    END as interaction_efficiency,
                    CASE
                        WHEN am.active_hours = 0 THEN 0
                        ELSE (am.total_messages::float / am.active_hours)
                    END as messages_per_hour
                FROM agent_metrics am
                JOIN collaboration_scores cs ON am.agent_id = cs.agent_id
                ORDER BY
                    CASE WHEN 'collaboration_score' = ANY($1) THEN cs.collaboration_score END DESC,
                    CASE WHEN 'response_time' = ANY($1) THEN am.avg_response_time END ASC,
                    CASE WHEN 'message_count' = ANY($1) THEN am.total_messages END DESC
                LIMIT {filters.limit} OFFSET {filters.offset}
            """

            # Add metrics parameter
            params.insert(0, metrics)

            results = await conn.fetch(query, *params)

            data = [dict(row) for row in results]
            total_count = len(data)  # For this query, we return all matching agents

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Cache result
        cache_data = {
            "data": data,
            "total_count": total_count,
            "execution_time_ms": execution_time,
        }
        await self.cache.cache_analytics_result(cache_key, cache_data, ttl=300)

        return QueryResult(
            query_type=QueryType.AGENT_PERFORMANCE,
            data=data,
            total_count=total_count,
            execution_time_ms=execution_time,
            cache_key=cache_key,
        )

    async def get_collaboration_patterns(
        self, filters: Optional[QueryFilter] = None, pattern_type: str = "all"
    ) -> QueryResult:
        """Analyze collaboration patterns and network effects"""
        start_time = datetime.utcnow()
        filters = filters or QueryFilter()

        cache_key = self._generate_cache_key(
            QueryType.COLLABORATION_PATTERNS, filters.dict(), pattern_type
        )

        cached_result = await self.cache.get_cached_analytics(cache_key)
        if cached_result:
            return QueryResult(
                query_type=QueryType.COLLABORATION_PATTERNS,
                data=cached_result["data"],
                total_count=cached_result["total_count"],
                execution_time_ms=cached_result["execution_time_ms"],
                cached=True,
                cache_key=cache_key,
            )

        # Use the analytics repository for complex patterns
        patterns_data = await self.analytics_repo.get_collaboration_patterns(
            days_back=30
            if not filters.start_date
            else (datetime.utcnow() - filters.start_date).days
        )

        # Enhance with real-time metrics
        async with self.db.get_pg_connection() as conn:
            # Add network centrality metrics
            network_query = """
                WITH collaboration_network AS (
                    SELECT
                        m.sender_id,
                        m.receiver_id,
                        COUNT(*) as interaction_count,
                        AVG(m.response_time_ms) as avg_response_time
                    FROM messages m
                    WHERE m.receiver_id IS NOT NULL
                        AND m.sent_at >= $1
                    GROUP BY m.sender_id, m.receiver_id
                ),
                centrality_metrics AS (
                    SELECT
                        agent_id,
                        COUNT(*) as connections,
                        SUM(interaction_count) as total_interactions,
                        AVG(avg_response_time) as network_response_time
                    FROM (
                        SELECT sender_id as agent_id, interaction_count, avg_response_time FROM collaboration_network
                        UNION ALL
                        SELECT receiver_id as agent_id, interaction_count, avg_response_time FROM collaboration_network
                    ) network_agents
                    GROUP BY agent_id
                )
                SELECT
                    cm.*,
                    a.name,
                    a.agent_type
                FROM centrality_metrics cm
                JOIN agents a ON cm.agent_id = a.agent_id
                ORDER BY cm.connections DESC, cm.total_interactions DESC
                LIMIT 20
            """

            start_date = filters.start_date or (datetime.utcnow() - timedelta(days=30))
            network_results = await conn.fetch(network_query, start_date)

            patterns_data["network_centrality"] = [dict(row) for row in network_results]

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Format as standardized result
        data = [patterns_data]
        total_count = 1

        # Cache result
        cache_data = {
            "data": data,
            "total_count": total_count,
            "execution_time_ms": execution_time,
        }
        await self.cache.cache_analytics_result(cache_key, cache_data, ttl=600)

        return QueryResult(
            query_type=QueryType.COLLABORATION_PATTERNS,
            data=data,
            total_count=total_count,
            execution_time_ms=execution_time,
            cache_key=cache_key,
        )

    async def get_time_series_metrics(
        self,
        metric_name: str,
        filters: Optional[QueryFilter] = None,
        granularity: str = "hour",  # hour, day, week
    ) -> QueryResult:
        """Get time-series metrics for dashboard visualization"""
        start_time = datetime.utcnow()
        filters = filters or QueryFilter()

        cache_key = self._generate_cache_key(
            QueryType.TIME_SERIES, metric_name, filters.dict(), granularity
        )

        cached_result = await self.cache.get_cached_analytics(cache_key)
        if cached_result:
            return QueryResult(
                query_type=QueryType.TIME_SERIES,
                data=cached_result["data"],
                total_count=cached_result["total_count"],
                execution_time_ms=cached_result["execution_time_ms"],
                cached=True,
                cache_key=cache_key,
            )

        async with self.db.get_pg_connection() as conn:
            # Build time series query based on metric
            date_trunc = f"DATE_TRUNC('{granularity}', "

            if metric_name == "message_volume":
                query = f"""
                    SELECT
                        {date_trunc}m.sent_at) as time_bucket,
                        COUNT(*) as value,
                        COUNT(DISTINCT m.sender_id) as unique_senders,
                        COUNT(DISTINCT m.session_id) as active_sessions
                    FROM messages m
                    WHERE m.sent_at >= $1 AND m.sent_at <= $2
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """
            elif metric_name == "response_times":
                query = f"""
                    SELECT
                        {date_trunc}m.sent_at) as time_bucket,
                        AVG(m.response_time_ms) as value,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY m.response_time_ms) as median,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY m.response_time_ms) as p95
                    FROM messages m
                    WHERE m.sent_at >= $1 AND m.sent_at <= $2
                        AND m.response_time_ms IS NOT NULL
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """
            elif metric_name == "active_agents":
                query = f"""
                    SELECT
                        {date_trunc}m.sent_at) as time_bucket,
                        COUNT(DISTINCT m.sender_id) as value,
                        COUNT(DISTINCT m.receiver_id) as unique_receivers
                    FROM messages m
                    WHERE m.sent_at >= $1 AND m.sent_at <= $2
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """
            else:
                raise ValueError(f"Unknown metric: {metric_name}")

            start_date = filters.start_date or (datetime.utcnow() - timedelta(days=7))
            end_date = filters.end_date or datetime.utcnow()

            results = await conn.fetch(query, start_date, end_date)
            data = [dict(row) for row in results]

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Cache result
        cache_data = {
            "data": data,
            "total_count": len(data),
            "execution_time_ms": execution_time,
        }
        await self.cache.cache_analytics_result(cache_key, cache_data, ttl=180)

        return QueryResult(
            query_type=QueryType.TIME_SERIES,
            data=data,
            total_count=len(data),
            execution_time_ms=execution_time,
            cache_key=cache_key,
        )

    async def execute_custom_query(
        self, sql_query: str, params: Optional[List[Any]] = None, cache_ttl: int = 300
    ) -> QueryResult:
        """Execute custom SQL query with safety checks"""
        start_time = datetime.utcnow()
        params = params or []

        # Basic safety checks
        sql_lower = sql_query.lower().strip()
        if any(
            keyword in sql_lower
            for keyword in ["drop", "delete", "update", "insert", "alter"]
        ):
            raise ValueError("Only SELECT queries are allowed")

        cache_key = self._generate_cache_key(QueryType.CUSTOM_SQL, sql_query, params)

        cached_result = await self.cache.get_cached_analytics(cache_key)
        if cached_result:
            return QueryResult(
                query_type=QueryType.CUSTOM_SQL,
                data=cached_result["data"],
                total_count=cached_result["total_count"],
                execution_time_ms=cached_result["execution_time_ms"],
                cached=True,
                cache_key=cache_key,
            )

        async with self.db.get_pg_connection() as conn:
            try:
                results = await conn.fetch(sql_query, *params)
                data = [dict(row) for row in results]
            except Exception as e:
                logger.error(f"Custom query failed: {e}")
                raise ValueError(f"Query execution failed: {str(e)}")

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Cache result
        cache_data = {
            "data": data,
            "total_count": len(data),
            "execution_time_ms": execution_time,
        }
        await self.cache.cache_analytics_result(cache_key, cache_data, ttl=cache_ttl)

        return QueryResult(
            query_type=QueryType.CUSTOM_SQL,
            data=data,
            total_count=len(data),
            execution_time_ms=execution_time,
            cache_key=cache_key,
        )

    def _generate_cache_key(self, query_type: QueryType, *args) -> str:
        """Generate consistent cache key for queries"""
        # Create deterministic hash of query parameters
        key_data = f"{query_type.value}:{str(args)}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]

    async def get_query_performance_stats(self) -> Dict[str, Any]:
        """Get query engine performance statistics"""
        cache_health = await self.cache.get_cache_health()

        # Add query-specific metrics
        stats = {
            "cache_health": cache_health,
            "supported_query_types": [qt.value for qt in QueryType],
            "query_safety_enabled": True,
            "default_cache_ttl_seconds": 300,
        }

        return stats
