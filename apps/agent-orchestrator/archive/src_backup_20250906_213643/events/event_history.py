"""
Event History System

Persistent storage and querying of collaboration events with advanced
search, analytics, and replay capabilities.
"""

import asyncio
import json
import logging
import sqlite3
import time
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .event_bus import EventBus, get_global_event_bus
from .event_types import BaseEvent, EventType, Priority

logger = logging.getLogger(__name__)


@dataclass
class EventQuery:
    """Query parameters for event history search"""

    event_types: Optional[List[EventType]] = None
    source_agents: Optional[List[str]] = None
    target_agents: Optional[List[str]] = None
    priority_min: Optional[Priority] = None
    priority_max: Optional[Priority] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    keywords: Optional[List[str]] = None
    limit: int = 100
    offset: int = 0
    sort_by: str = "timestamp"  # timestamp, priority, event_type
    sort_desc: bool = True


@dataclass
class EventPattern:
    """Represents a pattern in event data"""

    pattern_id: str
    pattern_type: str
    description: str
    frequency: int
    confidence_score: float
    first_seen: float
    last_seen: float
    related_agents: List[str]
    metadata: Dict[str, Any]


class EventHistory:
    """Persistent event storage and analytics system"""

    def __init__(
        self, db_path: str = "event_history.db", event_bus: Optional[EventBus] = None
    ):
        self.db_path = Path(db_path)
        self.event_bus = event_bus or get_global_event_bus()
        self.connection_pool: List[sqlite3.Connection] = []
        self.pool_lock = asyncio.Lock()
        self.max_connections = 5

        # Initialize database
        self._init_database()

        # Subscribe to all events for storage
        self.event_bus.subscribe(self._store_event)

        logger.info(f"EventHistory initialized with database: {self.db_path}")

    def _init_database(self) -> None:
        """Initialize the SQLite database schema"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            # Create events table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    source_agent_id TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    event_data TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """
            )

            # Create indexes for common queries
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_source ON events(source_agent_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_priority ON events(priority)"
            )

            # Create event patterns table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    frequency INTEGER NOT NULL,
                    confidence_score REAL NOT NULL,
                    first_seen REAL NOT NULL,
                    last_seen REAL NOT NULL,
                    related_agents TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """
            )

            # Create agent activity table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_activity (
                    agent_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    event_count INTEGER NOT NULL,
                    event_types TEXT NOT NULL,
                    PRIMARY KEY (agent_id, date)
                )
            """
            )

            conn.commit()

        finally:
            conn.close()

    @asynccontextmanager
    async def _get_connection(self):
        """Get a database connection from the pool"""
        async with self.pool_lock:
            if self.connection_pool:
                conn = self.connection_pool.pop()
            else:
                conn = sqlite3.connect(str(self.db_path))
                conn.row_factory = sqlite3.Row

        try:
            yield conn
        finally:
            async with self.pool_lock:
                if len(self.connection_pool) < self.max_connections:
                    self.connection_pool.append(conn)
                else:
                    conn.close()

    async def _store_event(self, event: BaseEvent) -> None:
        """Store an event in the database"""
        try:
            async with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO events
                    (event_id, event_type, timestamp, source_agent_id, priority, event_data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        event.event_id,
                        event.event_type.value if event.event_type else "unknown",
                        event.timestamp,
                        event.source_agent_id,
                        event.priority.value,
                        json.dumps(event.to_dict()),
                        time.time(),
                    ),
                )
                conn.commit()

                # Update agent activity
                await self._update_agent_activity(conn, event)

        except Exception as e:
            logger.error(f"Error storing event {event.event_id}: {e}")

    async def _update_agent_activity(
        self, conn: sqlite3.Connection, event: BaseEvent
    ) -> None:
        """Update daily agent activity statistics"""
        try:
            date_str = time.strftime("%Y-%m-%d", time.gmtime(event.timestamp))
            agent_id = event.source_agent_id
            event_type = event.event_type.value if event.event_type else "unknown"

            # Get current activity
            row = conn.execute(
                """
                SELECT event_count, event_types
                FROM agent_activity
                WHERE agent_id = ? AND date = ?
            """,
                (agent_id, date_str),
            ).fetchone()

            if row:
                # Update existing record
                event_count = row["event_count"] + 1
                event_types = json.loads(row["event_types"])
                event_types[event_type] = event_types.get(event_type, 0) + 1

                conn.execute(
                    """
                    UPDATE agent_activity
                    SET event_count = ?, event_types = ?
                    WHERE agent_id = ? AND date = ?
                """,
                    (event_count, json.dumps(event_types), agent_id, date_str),
                )
            else:
                # Create new record
                event_types = {event_type: 1}
                conn.execute(
                    """
                    INSERT INTO agent_activity (agent_id, date, event_count, event_types)
                    VALUES (?, ?, ?, ?)
                """,
                    (agent_id, date_str, 1, json.dumps(event_types)),
                )

            conn.commit()

        except Exception as e:
            logger.error(f"Error updating agent activity: {e}")

    async def query_events(self, query: EventQuery) -> List[BaseEvent]:
        """Query events from history with filtering and sorting"""
        try:
            async with self._get_connection() as conn:
                # Build SQL query
                sql_parts = ["SELECT event_data FROM events WHERE 1=1"]
                params = []

                # Add filters
                if query.event_types:
                    placeholders = ",".join("?" * len(query.event_types))
                    sql_parts.append(f"AND event_type IN ({placeholders})")
                    params.extend([et.value for et in query.event_types])

                if query.source_agents:
                    placeholders = ",".join("?" * len(query.source_agents))
                    sql_parts.append(f"AND source_agent_id IN ({placeholders})")
                    params.extend(query.source_agents)

                if query.priority_min:
                    sql_parts.append("AND priority >= ?")
                    params.append(query.priority_min.value)

                if query.priority_max:
                    sql_parts.append("AND priority <= ?")
                    params.append(query.priority_max.value)

                if query.start_time:
                    sql_parts.append("AND timestamp >= ?")
                    params.append(query.start_time)

                if query.end_time:
                    sql_parts.append("AND timestamp <= ?")
                    params.append(query.end_time)

                # Add keyword search
                if query.keywords:
                    keyword_conditions = []
                    for keyword in query.keywords:
                        keyword_conditions.append("event_data LIKE ?")
                        params.append(f"%{keyword}%")
                    sql_parts.append(f"AND ({' OR '.join(keyword_conditions)})")

                # Add sorting
                sort_direction = "DESC" if query.sort_desc else "ASC"
                sql_parts.append(f"ORDER BY {query.sort_by} {sort_direction}")

                # Add pagination
                sql_parts.append("LIMIT ? OFFSET ?")
                params.extend([query.limit, query.offset])

                # Execute query
                sql = " ".join(sql_parts)
                rows = conn.execute(sql, params).fetchall()

                # Convert back to event objects
                events = []
                for row in rows:
                    try:
                        event_data = json.loads(row["event_data"])
                        # Create a generic BaseEvent (could be enhanced to recreate specific types)
                        event = BaseEvent(
                            event_id=event_data["event_id"],
                            event_type=EventType(event_data["event_type"])
                            if event_data.get("event_type")
                            else None,
                            timestamp=event_data["timestamp"],
                            source_agent_id=event_data["source_agent_id"],
                            priority=Priority(event_data["priority"]),
                            metadata=event_data.get("metadata", {}),
                        )
                        events.append(event)
                    except Exception as e:
                        logger.error(f"Error reconstructing event from data: {e}")
                        continue

                return events

        except Exception as e:
            logger.error(f"Error querying events: {e}")
            return []

    async def get_event_count(self, query: EventQuery) -> int:
        """Get count of events matching query"""
        try:
            async with self._get_connection() as conn:
                # Build count query (similar to query_events but with COUNT)
                sql_parts = ["SELECT COUNT(*) as count FROM events WHERE 1=1"]
                params = []

                # Add same filters as query_events
                if query.event_types:
                    placeholders = ",".join("?" * len(query.event_types))
                    sql_parts.append(f"AND event_type IN ({placeholders})")
                    params.extend([et.value for et in query.event_types])

                if query.source_agents:
                    placeholders = ",".join("?" * len(query.source_agents))
                    sql_parts.append(f"AND source_agent_id IN ({placeholders})")
                    params.extend(query.source_agents)

                if query.priority_min:
                    sql_parts.append("AND priority >= ?")
                    params.append(query.priority_min.value)

                if query.priority_max:
                    sql_parts.append("AND priority <= ?")
                    params.append(query.priority_max.value)

                if query.start_time:
                    sql_parts.append("AND timestamp >= ?")
                    params.append(query.start_time)

                if query.end_time:
                    sql_parts.append("AND timestamp <= ?")
                    params.append(query.end_time)

                if query.keywords:
                    keyword_conditions = []
                    for keyword in query.keywords:
                        keyword_conditions.append("event_data LIKE ?")
                        params.append(f"%{keyword}%")
                    sql_parts.append(f"AND ({' OR '.join(keyword_conditions)})")

                sql = " ".join(sql_parts)
                row = conn.execute(sql, params).fetchone()
                return row["count"] if row else 0

        except Exception as e:
            logger.error(f"Error getting event count: {e}")
            return 0

    async def get_agent_activity(
        self, agent_id: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get agent activity statistics"""
        try:
            async with self._get_connection() as conn:
                start_date = time.strftime(
                    "%Y-%m-%d", time.gmtime(time.time() - (days * 24 * 3600))
                )

                rows = conn.execute(
                    """
                    SELECT date, event_count, event_types
                    FROM agent_activity
                    WHERE agent_id = ? AND date >= ?
                    ORDER BY date DESC
                """,
                    (agent_id, start_date),
                ).fetchall()

                activity = []
                for row in rows:
                    activity.append(
                        {
                            "date": row["date"],
                            "event_count": row["event_count"],
                            "event_types": json.loads(row["event_types"]),
                        }
                    )

                return activity

        except Exception as e:
            logger.error(f"Error getting agent activity: {e}")
            return []

    async def get_collaboration_patterns(
        self, min_frequency: int = 5, days: int = 7
    ) -> List[EventPattern]:
        """Analyze and identify collaboration patterns"""
        try:
            patterns = []

            # Get recent events for pattern analysis
            query = EventQuery(start_time=time.time() - (days * 24 * 3600), limit=10000)
            events = await self.query_events(query)

            # Analyze patterns
            patterns.extend(
                await self._analyze_communication_patterns(events, min_frequency)
            )
            patterns.extend(
                await self._analyze_task_handoff_patterns(events, min_frequency)
            )
            patterns.extend(
                await self._analyze_help_request_patterns(events, min_frequency)
            )

            return patterns

        except Exception as e:
            logger.error(f"Error analyzing collaboration patterns: {e}")
            return []

    async def _analyze_communication_patterns(
        self, events: List[BaseEvent], min_frequency: int
    ) -> List[EventPattern]:
        """Analyze communication patterns between agents"""
        patterns = []

        try:
            # Group events by agent pairs
            agent_pairs = {}
            for event in events:
                if hasattr(event, "target_agent_ids") and event.target_agent_ids:
                    for target in event.target_agent_ids:
                        pair_key = tuple(sorted([event.source_agent_id, target]))
                        if pair_key not in agent_pairs:
                            agent_pairs[pair_key] = []
                        agent_pairs[pair_key].append(event)

            # Find frequent communication patterns
            for pair_key, pair_events in agent_pairs.items():
                if len(pair_events) >= min_frequency:
                    patterns.append(
                        EventPattern(
                            pattern_id=f"comm_{pair_key[0]}_{pair_key[1]}",
                            pattern_type="frequent_communication",
                            description=f"Frequent communication between {pair_key[0]} and {pair_key[1]}",
                            frequency=len(pair_events),
                            confidence_score=min(1.0, len(pair_events) / 50.0),
                            first_seen=min(e.timestamp for e in pair_events),
                            last_seen=max(e.timestamp for e in pair_events),
                            related_agents=list(pair_key),
                            metadata={
                                "event_types": list(
                                    set(
                                        e.event_type.value
                                        for e in pair_events
                                        if e.event_type
                                    )
                                ),
                                "avg_frequency_per_day": len(pair_events) / 7.0,
                            },
                        )
                    )

        except Exception as e:
            logger.error(f"Error analyzing communication patterns: {e}")

        return patterns

    async def _analyze_task_handoff_patterns(
        self, events: List[BaseEvent], min_frequency: int
    ) -> List[EventPattern]:
        """Analyze task handoff patterns"""
        patterns = []

        try:
            handoff_events = [
                e for e in events if e.event_type == EventType.TASK_HANDOFF
            ]

            if len(handoff_events) >= min_frequency:
                # Find common handoff chains
                handoff_chains = {}
                for event in handoff_events:
                    if hasattr(event, "target_agent_ids") and event.target_agent_ids:
                        for target in event.target_agent_ids:
                            chain_key = f"{event.source_agent_id}->{target}"
                            handoff_chains[chain_key] = (
                                handoff_chains.get(chain_key, 0) + 1
                            )

                for chain, count in handoff_chains.items():
                    if count >= min_frequency:
                        source, target = chain.split("->")
                        patterns.append(
                            EventPattern(
                                pattern_id=f"handoff_{chain.replace('->', '_')}",
                                pattern_type="task_handoff_chain",
                                description=f"Frequent task handoffs from {source} to {target}",
                                frequency=count,
                                confidence_score=min(1.0, count / 20.0),
                                first_seen=min(e.timestamp for e in handoff_events),
                                last_seen=max(e.timestamp for e in handoff_events),
                                related_agents=[source, target],
                                metadata={"handoff_direction": chain},
                            )
                        )

        except Exception as e:
            logger.error(f"Error analyzing task handoff patterns: {e}")

        return patterns

    async def _analyze_help_request_patterns(
        self, events: List[BaseEvent], min_frequency: int
    ) -> List[EventPattern]:
        """Analyze help request patterns"""
        patterns = []

        try:
            help_events = [e for e in events if e.event_type == EventType.HELP_REQUEST]

            # Find agents who frequently request help
            help_requests_by_agent = {}
            for event in help_events:
                agent = event.source_agent_id
                help_requests_by_agent[agent] = help_requests_by_agent.get(agent, 0) + 1

            for agent, count in help_requests_by_agent.items():
                if count >= min_frequency:
                    patterns.append(
                        EventPattern(
                            pattern_id=f"help_requester_{agent}",
                            pattern_type="frequent_help_requests",
                            description=f"Agent {agent} frequently requests help",
                            frequency=count,
                            confidence_score=min(1.0, count / 10.0),
                            first_seen=min(
                                e.timestamp
                                for e in help_events
                                if e.source_agent_id == agent
                            ),
                            last_seen=max(
                                e.timestamp
                                for e in help_events
                                if e.source_agent_id == agent
                            ),
                            related_agents=[agent],
                            metadata={"help_request_rate": count / 7.0},
                        )
                    )

        except Exception as e:
            logger.error(f"Error analyzing help request patterns: {e}")

        return patterns

    async def replay_events(
        self,
        query: EventQuery,
        callback: Optional[Callable[[BaseEvent], None]] = None,
        delay_ms: int = 100,
    ) -> None:
        """Replay events from history"""
        events = await self.query_events(query)

        logger.info(f"Replaying {len(events)} events with {delay_ms}ms delay")

        for event in events:
            if callback:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in replay callback: {e}")

            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000.0)

        logger.info("Event replay completed")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get overall event history statistics"""
        try:
            async with self._get_connection() as conn:
                # Total events
                total_events = conn.execute(
                    "SELECT COUNT(*) as count FROM events"
                ).fetchone()["count"]

                # Events by type
                type_stats = conn.execute(
                    """
                    SELECT event_type, COUNT(*) as count
                    FROM events
                    GROUP BY event_type
                    ORDER BY count DESC
                """
                ).fetchall()

                # Active agents
                active_agents = conn.execute(
                    """
                    SELECT COUNT(DISTINCT source_agent_id) as count
                    FROM events
                    WHERE timestamp > ?
                """,
                    (time.time() - 24 * 3600,),
                ).fetchone()["count"]

                # Database size
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

                return {
                    "total_events": total_events,
                    "events_by_type": {
                        row["event_type"]: row["count"] for row in type_stats
                    },
                    "active_agents_24h": active_agents,
                    "database_size_bytes": db_size,
                    "database_path": str(self.db_path),
                }

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    async def cleanup_old_events(self, days_to_keep: int = 90) -> int:
        """Clean up old events to manage database size"""
        try:
            cutoff_time = time.time() - (days_to_keep * 24 * 3600)

            async with self._get_connection() as conn:
                # Count events to be deleted
                count_row = conn.execute(
                    "SELECT COUNT(*) as count FROM events WHERE timestamp < ?",
                    (cutoff_time,),
                ).fetchone()
                deleted_count = count_row["count"] if count_row else 0

                # Delete old events
                conn.execute("DELETE FROM events WHERE timestamp < ?", (cutoff_time,))

                # Delete old activity records
                cutoff_date = time.strftime("%Y-%m-%d", time.gmtime(cutoff_time))
                conn.execute(
                    "DELETE FROM agent_activity WHERE date < ?", (cutoff_date,)
                )

                conn.commit()

                logger.info(
                    f"Cleaned up {deleted_count} events older than {days_to_keep} days"
                )
                return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old events: {e}")
            return 0
