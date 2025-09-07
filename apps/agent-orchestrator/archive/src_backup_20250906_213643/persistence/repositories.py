"""
Data Access Layer - Repository Pattern Implementation
High-performance data access with caching and analytics
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import asyncpg
from sqlalchemy import and_, asc, delete, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .database import DatabaseManager
from .models import (
    Agent,
    AgentModel,
    AgentStatus,
    Artifact,
    ArtifactModel,
    Event,
    EventModel,
    EventType,
    Message,
    MessageModel,
    MessageType,
    Metric,
    MetricModel,
    Session,
    SessionModel,
    Workspace,
    WorkspaceModel,
)

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository with common functionality"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def _cache_key(self, prefix: str, *args) -> str:
        """Generate cache key"""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ":".join(key_parts)

    async def _cache_get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        try:
            async with self.db.get_redis_client() as redis:
                value = await redis.get(key)
                return json.loads(value) if value else None
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
            return None

    async def _cache_set(self, key: str, value: Any, ttl: int = 300):
        """Set value in Redis cache"""
        try:
            async with self.db.get_redis_client() as redis:
                await redis.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")

    async def _cache_delete(self, key: str):
        """Delete value from Redis cache"""
        try:
            async with self.db.get_redis_client() as redis:
                await redis.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete failed: {e}")


class AgentRepository(BaseRepository):
    """Agent data access and management"""

    async def create_agent(self, agent_data: AgentModel) -> str:
        """Create new agent registration"""
        async with self.db.get_async_session() as session:
            agent = Agent(
                agent_id=agent_data.agent_id or str(uuid4()),
                name=agent_data.name,
                agent_type=agent_data.agent_type,
                capabilities=agent_data.capabilities,
                status=agent_data.status,
                metadata=agent_data.metadata,
            )

            session.add(agent)
            await session.flush()  # Get the agent_id

            # Log agent registration event
            await self._log_agent_event(
                session,
                agent.agent_id,
                EventType.AGENT_REGISTERED,
                {
                    "name": agent.name,
                    "agent_type": agent.agent_type,
                    "capabilities": agent.capabilities,
                },
            )

            # Invalidate cache
            await self._cache_delete(await self._cache_key("agent", agent.agent_id))
            await self._cache_delete("agents:active")

            return agent.agent_id

    async def get_agent(self, agent_id: str) -> Optional[AgentModel]:
        """Get agent by ID with caching"""
        cache_key = await self._cache_key("agent", agent_id)
        cached = await self._cache_get(cache_key)

        if cached:
            return AgentModel(**cached)

        async with self.db.get_async_session() as session:
            result = await session.execute(
                select(Agent).where(Agent.agent_id == agent_id)
            )
            agent = result.scalar_one_or_none()

            if agent:
                agent_model = AgentModel(
                    agent_id=agent.agent_id,
                    name=agent.name,
                    agent_type=agent.agent_type,
                    capabilities=agent.capabilities,
                    status=agent.status,
                    metadata=agent.metadata,
                    total_tasks=agent.total_tasks,
                    successful_tasks=agent.successful_tasks,
                    avg_response_time=agent.avg_response_time,
                    last_active=agent.last_active,
                    created_at=agent.created_at,
                    updated_at=agent.updated_at,
                )

                # Cache for 5 minutes
                await self._cache_set(cache_key, agent_model.dict(), ttl=300)
                return agent_model

        return None

    async def update_agent_status(
        self, agent_id: str, status: AgentStatus, metadata: Optional[Dict] = None
    ):
        """Update agent status and metadata"""
        async with self.db.get_async_session() as session:
            agent = await session.get(Agent, agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")

            old_status = agent.status
            agent.status = status
            agent.last_active = datetime.utcnow()

            if metadata:
                agent.metadata.update(metadata)

            # Log status change event
            if old_status != status:
                await self._log_agent_event(
                    session,
                    agent_id,
                    EventType.AGENT_STATUS_CHANGED,
                    {
                        "old_status": old_status,
                        "new_status": status,
                        "metadata": metadata,
                    },
                )

            # Invalidate cache
            await self._cache_delete(await self._cache_key("agent", agent_id))

    async def get_active_agents(
        self, agent_type: Optional[str] = None
    ) -> List[AgentModel]:
        """Get all active agents, optionally filtered by type"""
        cache_key = f"agents:active:{agent_type or 'all'}"
        cached = await self._cache_get(cache_key)

        if cached:
            return [AgentModel(**item) for item in cached]

        async with self.db.get_async_session() as session:
            query = select(Agent).where(
                and_(
                    Agent.status.in_([AgentStatus.IDLE, AgentStatus.ACTIVE]),
                    Agent.last_active > datetime.utcnow() - timedelta(minutes=5),
                )
            )

            if agent_type:
                query = query.where(Agent.agent_type == agent_type)

            result = await session.execute(query.order_by(Agent.last_active.desc()))
            agents = result.scalars().all()

            agent_models = [
                AgentModel(
                    agent_id=a.agent_id,
                    name=a.name,
                    agent_type=a.agent_type,
                    capabilities=a.capabilities,
                    status=a.status,
                    metadata=a.metadata,
                    total_tasks=a.total_tasks,
                    successful_tasks=a.successful_tasks,
                    avg_response_time=a.avg_response_time,
                    last_active=a.last_active,
                    created_at=a.created_at,
                    updated_at=a.updated_at,
                )
                for a in agents
            ]

            # Cache for 30 seconds
            await self._cache_set(cache_key, [a.dict() for a in agent_models], ttl=30)
            return agent_models

    async def update_agent_metrics(
        self, agent_id: str, response_time_ms: int, success: bool
    ):
        """Update agent performance metrics"""
        async with self.db.get_async_session() as session:
            agent = await session.get(Agent, agent_id)
            if not agent:
                return

            # Update counters
            agent.total_tasks += 1
            if success:
                agent.successful_tasks += 1

            # Update average response time (exponential moving average)
            alpha = 0.1
            agent.avg_response_time = (
                alpha * response_time_ms + (1 - alpha) * agent.avg_response_time
            )

            agent.last_active = datetime.utcnow()

            # Invalidate cache
            await self._cache_delete(await self._cache_key("agent", agent_id))

    async def _log_agent_event(
        self, session: AsyncSession, agent_id: str, event_type: EventType, data: Dict
    ):
        """Log agent-related event"""
        event = Event(
            agent_id=agent_id,
            event_type=event_type,
            event_data=data,
            timestamp=datetime.utcnow(),
        )
        session.add(event)


class SessionRepository(BaseRepository):
    """Collaboration session management"""

    async def create_session(self, session_data: SessionModel) -> str:
        """Create new collaboration session"""
        async with self.db.get_async_session() as session_db:
            session_obj = Session(
                session_id=session_data.session_id or str(uuid4()),
                name=session_data.name,
                description=session_data.description,
                session_type=session_data.session_type,
                metadata=session_data.metadata,
                started_at=datetime.utcnow(),
            )

            session_db.add(session_obj)
            await session_db.flush()

            # Log session start event
            event = Event(
                session_id=session_obj.session_id,
                event_type=EventType.COLLABORATION_STARTED,
                event_data={
                    "name": session_obj.name,
                    "session_type": session_obj.session_type,
                    "description": session_obj.description,
                },
                timestamp=datetime.utcnow(),
            )
            session_db.add(event)

            return session_obj.session_id

    async def get_session(self, session_id: str) -> Optional[SessionModel]:
        """Get session with agents"""
        cache_key = await self._cache_key("session", session_id)
        cached = await self._cache_get(cache_key)

        if cached:
            return SessionModel(**cached)

        async with self.db.get_async_session() as session:
            result = await session.execute(
                select(Session)
                .options(selectinload(Session.agents))
                .where(Session.session_id == session_id)
            )
            session_obj = result.scalar_one_or_none()

            if session_obj:
                agents = [
                    AgentModel(
                        agent_id=a.agent_id,
                        name=a.name,
                        agent_type=a.agent_type,
                        capabilities=a.capabilities,
                        status=a.status,
                        metadata=a.metadata,
                        total_tasks=a.total_tasks,
                        successful_tasks=a.successful_tasks,
                        avg_response_time=a.avg_response_time,
                        last_active=a.last_active,
                        created_at=a.created_at,
                        updated_at=a.updated_at,
                    )
                    for a in session_obj.agents
                ]

                session_model = SessionModel(
                    session_id=session_obj.session_id,
                    name=session_obj.name,
                    description=session_obj.description,
                    session_type=session_obj.session_type,
                    status=session_obj.status,
                    metadata=session_obj.metadata,
                    total_messages=session_obj.total_messages,
                    total_tasks=session_obj.total_tasks,
                    success_rate=session_obj.success_rate,
                    avg_response_time=session_obj.avg_response_time,
                    started_at=session_obj.started_at,
                    ended_at=session_obj.ended_at,
                    agents=agents,
                )

                await self._cache_set(cache_key, session_model.dict(), ttl=120)
                return session_model

        return None

    async def add_agent_to_session(self, session_id: str, agent_id: str):
        """Add agent to collaboration session"""
        async with self.db.get_async_session() as session:
            # Get session and agent
            session_obj = await session.get(Session, session_id)
            agent = await session.get(Agent, agent_id)

            if not session_obj or not agent:
                raise ValueError("Session or agent not found")

            # Add agent to session
            if agent not in session_obj.agents:
                session_obj.agents.append(agent)

                # Log event
                event = Event(
                    session_id=session_id,
                    agent_id=agent_id,
                    event_type=EventType.AGENT_REGISTERED,
                    event_data={"joined_session": session_id},
                    timestamp=datetime.utcnow(),
                )
                session.add(event)

            # Invalidate cache
            await self._cache_delete(await self._cache_key("session", session_id))

    async def end_session(self, session_id: str):
        """End collaboration session"""
        async with self.db.get_async_session() as session:
            session_obj = await session.get(Session, session_id)
            if not session_obj:
                return

            session_obj.status = "completed"
            session_obj.ended_at = datetime.utcnow()

            # Log session end event
            event = Event(
                session_id=session_id,
                event_type=EventType.COLLABORATION_ENDED,
                event_data={
                    "duration_seconds": (
                        session_obj.ended_at - session_obj.started_at
                    ).total_seconds()
                },
                timestamp=datetime.utcnow(),
            )
            session.add(event)

            # Invalidate cache
            await self._cache_delete(await self._cache_key("session", session_id))


class MessageRepository(BaseRepository):
    """Message storage and retrieval"""

    async def store_message(self, message_data: MessageModel) -> str:
        """Store inter-agent message"""
        async with self.db.get_async_session() as session:
            message = Message(
                message_id=message_data.message_id or str(uuid4()),
                session_id=message_data.session_id,
                sender_id=message_data.sender_id,
                receiver_id=message_data.receiver_id,
                message_type=message_data.message_type,
                content=message_data.content,
                metadata=message_data.metadata,
                thread_id=message_data.thread_id,
                parent_message_id=message_data.parent_message_id,
                sent_at=datetime.utcnow(),
            )

            session.add(message)
            await session.flush()

            # Update session message counter
            await session.execute(
                update(Session)
                .where(Session.session_id == message_data.session_id)
                .values(total_messages=Session.total_messages + 1)
            )

            # Log message event
            event = Event(
                session_id=message_data.session_id,
                agent_id=message_data.sender_id,
                event_type=EventType.MESSAGE_SENT,
                event_data={
                    "message_id": message.message_id,
                    "receiver_id": message_data.receiver_id,
                    "message_type": message_data.message_type,
                },
                timestamp=datetime.utcnow(),
            )
            session.add(event)

            return message.message_id

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 100,
        before_timestamp: Optional[datetime] = None,
        thread_id: Optional[str] = None,
    ) -> List[MessageModel]:
        """Get conversation history with pagination"""
        cache_key = await self._cache_key(
            "conversation",
            session_id,
            limit,
            before_timestamp or "latest",
            thread_id or "all",
        )
        cached = await self._cache_get(cache_key)

        if cached:
            return [MessageModel(**msg) for msg in cached]

        async with self.db.get_async_session() as session:
            query = select(Message).where(Message.session_id == session_id)

            if before_timestamp:
                query = query.where(Message.sent_at < before_timestamp)

            if thread_id:
                query = query.where(Message.thread_id == thread_id)

            query = query.order_by(desc(Message.sent_at)).limit(limit)

            result = await session.execute(query)
            messages = result.scalars().all()

            message_models = [
                MessageModel(
                    message_id=m.message_id,
                    session_id=m.session_id,
                    sender_id=m.sender_id,
                    receiver_id=m.receiver_id,
                    message_type=m.message_type,
                    content=m.content,
                    metadata=m.metadata,
                    thread_id=m.thread_id,
                    parent_message_id=m.parent_message_id,
                    sent_at=m.sent_at,
                    delivered_at=m.delivered_at,
                    processed_at=m.processed_at,
                    response_time_ms=m.response_time_ms,
                )
                for m in reversed(messages)  # Return in chronological order
            ]

            # Cache for 1 minute
            await self._cache_set(cache_key, [m.dict() for m in message_models], ttl=60)
            return message_models

    async def mark_message_delivered(
        self, message_id: str, response_time_ms: Optional[int] = None
    ):
        """Mark message as delivered/processed"""
        async with self.db.get_async_session() as session:
            await session.execute(
                update(Message)
                .where(Message.message_id == message_id)
                .values(
                    delivered_at=datetime.utcnow(),
                    processed_at=datetime.utcnow(),
                    response_time_ms=response_time_ms,
                )
            )


class WorkspaceRepository(BaseRepository):
    """Workspace and artifact management"""

    async def create_workspace(self, workspace_data: WorkspaceModel) -> str:
        """Create shared workspace"""
        async with self.db.get_async_session() as session:
            workspace = Workspace(
                workspace_id=workspace_data.workspace_id or str(uuid4()),
                session_id=workspace_data.session_id,
                name=workspace_data.name,
                description=workspace_data.description,
                workspace_type=workspace_data.workspace_type,
                permissions=workspace_data.permissions,
                metadata=workspace_data.metadata,
                storage_path=workspace_data.storage_path,
                storage_type=workspace_data.storage_type,
            )

            session.add(workspace)
            await session.flush()

            # Log workspace creation
            event = Event(
                session_id=workspace_data.session_id,
                event_type=EventType.WORKSPACE_CREATED,
                event_data={
                    "workspace_id": workspace.workspace_id,
                    "name": workspace.name,
                    "workspace_type": workspace.workspace_type,
                },
                timestamp=datetime.utcnow(),
            )
            session.add(event)

            return workspace.workspace_id

    async def store_artifact(self, artifact_data: ArtifactModel) -> str:
        """Store shared artifact"""
        async with self.db.get_async_session() as session:
            # Check if artifact with same name exists in workspace
            existing = await session.execute(
                select(Artifact)
                .where(
                    and_(
                        Artifact.workspace_id == artifact_data.workspace_id,
                        Artifact.name == artifact_data.name,
                    )
                )
                .order_by(desc(Artifact.version))
            )

            latest_version = existing.scalar_one_or_none()
            next_version = (latest_version.version + 1) if latest_version else 1

            artifact = Artifact(
                artifact_id=artifact_data.artifact_id or str(uuid4()),
                workspace_id=artifact_data.workspace_id,
                name=artifact_data.name,
                artifact_type=artifact_data.artifact_type,
                content=artifact_data.content,
                storage_path=artifact_data.storage_path,
                size_bytes=artifact_data.size_bytes,
                checksum=artifact_data.checksum,
                version=next_version,
                parent_artifact_id=latest_version.artifact_id
                if latest_version
                else None,
                metadata=artifact_data.metadata,
                tags=artifact_data.tags,
            )

            session.add(artifact)
            await session.flush()

            # Log artifact creation
            event = Event(
                event_type=EventType.FILE_CREATED,
                event_data={
                    "artifact_id": artifact.artifact_id,
                    "workspace_id": artifact_data.workspace_id,
                    "name": artifact.name,
                    "version": next_version,
                },
                timestamp=datetime.utcnow(),
            )
            session.add(event)

            return artifact.artifact_id


class AnalyticsRepository(BaseRepository):
    """Advanced analytics and reporting queries"""

    async def get_collaboration_patterns(self, days_back: int = 30) -> Dict[str, Any]:
        """Analyze collaboration patterns and effectiveness"""
        since = datetime.utcnow() - timedelta(days=days_back)

        async with self.db.get_pg_connection() as conn:
            # Agent collaboration frequency
            agent_pairs = await conn.fetch(
                """
                SELECT
                    m1.sender_id as agent_1,
                    m1.receiver_id as agent_2,
                    COUNT(*) as message_count,
                    AVG(m1.response_time_ms) as avg_response_time
                FROM messages m1
                WHERE m1.sent_at >= $1
                    AND m1.receiver_id IS NOT NULL
                GROUP BY m1.sender_id, m1.receiver_id
                HAVING COUNT(*) >= 5
                ORDER BY message_count DESC
                LIMIT 50
            """,
                since,
            )

            # Session success rates
            session_metrics = await conn.fetch(
                """
                SELECT
                    s.session_type,
                    COUNT(*) as total_sessions,
                    AVG(s.success_rate) as avg_success_rate,
                    AVG(EXTRACT(epoch FROM (s.ended_at - s.started_at))/60) as avg_duration_minutes
                FROM sessions s
                WHERE s.started_at >= $1
                    AND s.ended_at IS NOT NULL
                GROUP BY s.session_type
                ORDER BY total_sessions DESC
            """,
                since,
            )

            # Peak collaboration hours
            hourly_activity = await conn.fetch(
                """
                SELECT
                    EXTRACT(hour FROM sent_at) as hour,
                    COUNT(*) as message_count
                FROM messages
                WHERE sent_at >= $1
                GROUP BY EXTRACT(hour FROM sent_at)
                ORDER BY hour
            """,
                since,
            )

            return {
                "agent_collaborations": [dict(row) for row in agent_pairs],
                "session_metrics": [dict(row) for row in session_metrics],
                "hourly_activity": [dict(row) for row in hourly_activity],
                "analysis_period_days": days_back,
            }

    async def get_agent_performance_metrics(
        self, agent_id: Optional[str] = None, days_back: int = 7
    ) -> Dict[str, Any]:
        """Get detailed agent performance analytics"""
        since = datetime.utcnow() - timedelta(days=days_back)

        async with self.db.get_pg_connection() as conn:
            where_clause = "WHERE m.sent_at >= $1"
            params = [since]

            if agent_id:
                where_clause += " AND m.sender_id = $2"
                params.append(agent_id)

            # Response time trends
            response_times = await conn.fetch(
                f"""
                SELECT
                    DATE_TRUNC('hour', m.sent_at) as time_bucket,
                    m.sender_id,
                    AVG(m.response_time_ms) as avg_response_time,
                    COUNT(*) as message_count
                FROM messages m
                {where_clause}
                    AND m.response_time_ms IS NOT NULL
                GROUP BY DATE_TRUNC('hour', m.sent_at), m.sender_id
                ORDER BY time_bucket, m.sender_id
            """,
                *params,
            )

            # Message type distribution
            message_types = await conn.fetch(
                f"""
                SELECT
                    m.sender_id,
                    m.message_type,
                    COUNT(*) as count
                FROM messages m
                {where_clause}
                GROUP BY m.sender_id, m.message_type
                ORDER BY m.sender_id, count DESC
            """,
                *params,
            )

            return {
                "response_time_trends": [dict(row) for row in response_times],
                "message_type_distribution": [dict(row) for row in message_types],
                "analysis_period_days": days_back,
            }
