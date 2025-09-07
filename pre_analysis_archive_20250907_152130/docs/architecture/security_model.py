#!/usr/bin/env python3
"""
Agent Collaboration Security Model
Comprehensive security framework for multi-agent collaboration
"""

import asyncio
import hashlib
import hmac
import logging
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import jwt

logger = logging.getLogger(__name__)


class Permission(Enum):
    """Granular permissions for agent operations"""

    # Message permissions
    SEND_MESSAGE = "send_message"
    RECEIVE_MESSAGE = "receive_message"
    BROADCAST_MESSAGE = "broadcast_message"

    # Coordination permissions
    HANDOFF_TASK = "handoff_task"
    RECEIVE_TASK = "receive_task"
    REQUEST_HELP = "request_help"
    PROVIDE_HELP = "provide_help"

    # Workspace permissions
    READ_WORKSPACE = "read_workspace"
    WRITE_WORKSPACE = "write_workspace"
    SHARE_ARTIFACT = "share_artifact"
    MANAGE_WORKSPACE = "manage_workspace"

    # System permissions
    REGISTER_AGENT = "register_agent"
    UPDATE_STATUS = "update_status"
    VIEW_AGENTS = "view_agents"
    SYSTEM_ADMIN = "system_admin"


class SecurityLevel(Enum):
    """Security clearance levels"""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"


@dataclass
class AgentCredentials:
    """Agent authentication credentials"""

    agent_id: str
    api_key: str
    secret_key: str
    jwt_token: Optional[str] = None
    permissions: Set[Permission] = field(default_factory=set)
    security_level: SecurityLevel = SecurityLevel.INTERNAL
    workspace_keys: Dict[str, str] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    is_active: bool = True


@dataclass
class SecurityPolicy:
    """Security policy configuration"""

    # Authentication
    require_api_key: bool = True
    require_jwt_token: bool = False
    api_key_length: int = 32

    # Message security
    enable_message_signing: bool = True
    enable_message_encryption: bool = False
    message_ttl_seconds: int = 3600

    # Rate limiting
    enable_rate_limiting: bool = True
    messages_per_minute: int = 100
    requests_per_minute: int = 1000

    # Workspace security
    workspace_isolation: bool = True
    require_workspace_keys: bool = True

    # Monitoring and auditing
    enable_audit_logging: bool = True
    log_message_content: bool = False
    alert_on_suspicious_activity: bool = True


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, max_tokens: int, refill_rate: float):
        self.max_tokens = max_tokens
        self.tokens = max_tokens
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens, return True if successful"""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_refill

            # Refill tokens based on elapsed time
            self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class MessageSigner:
    """Message signing for integrity verification"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()

    def sign_message(self, message_data: Dict[str, Any]) -> str:
        """Sign message data and return signature"""
        # Create canonical representation
        canonical = self._canonicalize(message_data)

        # Create HMAC signature
        signature = hmac.new(
            self.secret_key, canonical.encode(), hashlib.sha256
        ).hexdigest()

        return signature

    def verify_signature(self, message_data: Dict[str, Any], signature: str) -> bool:
        """Verify message signature"""
        expected_signature = self.sign_message(message_data)
        return hmac.compare_digest(signature, expected_signature)

    def _canonicalize(self, data: Dict[str, Any]) -> str:
        """Create canonical string representation of message data"""
        # Sort keys and create deterministic representation
        import json

        return json.dumps(data, sort_keys=True, separators=(",", ":"))


class JWTManager:
    """JWT token management for agent authentication"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_token(
        self,
        agent_id: str,
        permissions: List[str],
        expires_in: timedelta = timedelta(hours=24),
    ) -> str:
        """Create JWT token for agent"""
        now = datetime.utcnow()
        payload = {
            "agent_id": agent_id,
            "permissions": permissions,
            "iat": now,
            "exp": now + expires_in,
            "iss": "agent_collaboration_system",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
        return None


class SecurityManager:
    """Central security management for agent collaboration"""

    def __init__(self, policy: SecurityPolicy):
        self.policy = policy
        self.credentials: Dict[str, AgentCredentials] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.message_signer = MessageSigner(secrets.token_hex(32))
        self.jwt_manager = JWTManager(secrets.token_hex(32))

        # Audit logging
        self.audit_log: List[Dict[str, Any]] = []

        # Suspicious activity tracking
        self.failed_attempts: Dict[str, List[datetime]] = {}

    async def register_agent(
        self, agent_id: str, agent_type: str, capabilities: List[str]
    ) -> AgentCredentials:
        """Register new agent and generate credentials"""

        # Generate credentials
        api_key = secrets.token_urlsafe(self.policy.api_key_length)
        secret_key = secrets.token_hex(32)

        # Determine permissions based on agent type and capabilities
        permissions = self._determine_permissions(agent_type, capabilities)

        # Create credentials
        credentials = AgentCredentials(
            agent_id=agent_id,
            api_key=api_key,
            secret_key=secret_key,
            permissions=permissions,
            security_level=self._determine_security_level(agent_type),
        )

        # Generate JWT if required
        if self.policy.require_jwt_token:
            credentials.jwt_token = self.jwt_manager.create_token(
                agent_id, [p.value for p in permissions]
            )

        self.credentials[agent_id] = credentials

        # Setup rate limiter
        self.rate_limiters[agent_id] = RateLimiter(
            max_tokens=self.policy.messages_per_minute,
            refill_rate=self.policy.messages_per_minute / 60.0,
        )

        # Log registration
        await self._audit_log(
            {
                "event": "agent_registered",
                "agent_id": agent_id,
                "agent_type": agent_type,
                "permissions": [p.value for p in permissions],
                "timestamp": datetime.now().isoformat(),
            }
        )

        logger.info(f"Agent {agent_id} registered with {len(permissions)} permissions")
        return credentials

    async def authenticate_agent(
        self, agent_id: str, api_key: str
    ) -> Optional[AgentCredentials]:
        """Authenticate agent using API key"""

        if agent_id not in self.credentials:
            await self._log_failed_attempt(agent_id, "unknown_agent")
            return None

        credentials = self.credentials[agent_id]

        if not credentials.is_active:
            await self._log_failed_attempt(agent_id, "inactive_agent")
            return None

        if credentials.expires_at and datetime.now() > credentials.expires_at:
            await self._log_failed_attempt(agent_id, "expired_credentials")
            return None

        if not secrets.compare_digest(credentials.api_key, api_key):
            await self._log_failed_attempt(agent_id, "invalid_api_key")
            return None

        # Update last used
        credentials.last_used = datetime.now()

        await self._audit_log(
            {
                "event": "agent_authenticated",
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return credentials

    async def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        payload = self.jwt_manager.verify_token(token)

        if payload:
            agent_id = payload.get("agent_id")
            if agent_id in self.credentials:
                self.credentials[agent_id].last_used = datetime.now()

        return payload

    async def authorize_operation(self, agent_id: str, permission: Permission) -> bool:
        """Check if agent has permission for operation"""

        if agent_id not in self.credentials:
            return False

        credentials = self.credentials[agent_id]

        if not credentials.is_active:
            return False

        has_permission = permission in credentials.permissions

        if not has_permission:
            await self._audit_log(
                {
                    "event": "permission_denied",
                    "agent_id": agent_id,
                    "permission": permission.value,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return has_permission

    async def check_rate_limit(self, agent_id: str, tokens: int = 1) -> bool:
        """Check if agent is within rate limits"""

        if not self.policy.enable_rate_limiting:
            return True

        if agent_id not in self.rate_limiters:
            return False

        rate_limiter = self.rate_limiters[agent_id]
        allowed = await rate_limiter.acquire(tokens)

        if not allowed:
            await self._audit_log(
                {
                    "event": "rate_limit_exceeded",
                    "agent_id": agent_id,
                    "tokens_requested": tokens,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return allowed

    async def sign_message(
        self, agent_id: str, message_data: Dict[str, Any]
    ) -> Optional[str]:
        """Sign message for agent"""

        if not self.policy.enable_message_signing:
            return None

        if agent_id not in self.credentials:
            return None

        credentials = self.credentials[agent_id]
        signer = MessageSigner(credentials.secret_key)
        return signer.sign_message(message_data)

    async def verify_message_signature(
        self, agent_id: str, message_data: Dict[str, Any], signature: str
    ) -> bool:
        """Verify message signature"""

        if not self.policy.enable_message_signing:
            return True

        if agent_id not in self.credentials:
            return False

        credentials = self.credentials[agent_id]
        signer = MessageSigner(credentials.secret_key)

        is_valid = signer.verify_signature(message_data, signature)

        if not is_valid:
            await self._audit_log(
                {
                    "event": "invalid_message_signature",
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return is_valid

    async def authorize_workspace_access(
        self, agent_id: str, workspace_id: str, operation: str
    ) -> bool:
        """Authorize workspace access"""

        if not self.policy.workspace_isolation:
            return True

        if agent_id not in self.credentials:
            return False

        credentials = self.credentials[agent_id]

        # Check workspace key if required
        if self.policy.require_workspace_keys:
            if workspace_id not in credentials.workspace_keys:
                await self._audit_log(
                    {
                        "event": "workspace_access_denied",
                        "agent_id": agent_id,
                        "workspace_id": workspace_id,
                        "reason": "no_workspace_key",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                return False

        # Check permissions
        required_permission = {
            "read": Permission.READ_WORKSPACE,
            "write": Permission.WRITE_WORKSPACE,
            "manage": Permission.MANAGE_WORKSPACE,
        }.get(operation)

        if required_permission and required_permission not in credentials.permissions:
            return False

        return True

    async def grant_workspace_access(
        self, agent_id: str, workspace_id: str, workspace_key: str
    ):
        """Grant workspace access to agent"""

        if agent_id in self.credentials:
            self.credentials[agent_id].workspace_keys[workspace_id] = workspace_key

            await self._audit_log(
                {
                    "event": "workspace_access_granted",
                    "agent_id": agent_id,
                    "workspace_id": workspace_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )

    async def revoke_agent_access(self, agent_id: str):
        """Revoke all access for an agent"""

        if agent_id in self.credentials:
            self.credentials[agent_id].is_active = False

            await self._audit_log(
                {
                    "event": "agent_access_revoked",
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )

    def _determine_permissions(
        self, agent_type: str, capabilities: List[str]
    ) -> Set[Permission]:
        """Determine permissions based on agent type and capabilities"""

        permissions = set()

        # Base permissions for all agents
        permissions.add(Permission.SEND_MESSAGE)
        permissions.add(Permission.RECEIVE_MESSAGE)
        permissions.add(Permission.UPDATE_STATUS)
        permissions.add(Permission.VIEW_AGENTS)

        # Type-based permissions
        if agent_type in ["coordinator", "orchestrator"]:
            permissions.add(Permission.BROADCAST_MESSAGE)
            permissions.add(Permission.HANDOFF_TASK)
            permissions.add(Permission.MANAGE_WORKSPACE)

        if agent_type in ["specialist", "worker"]:
            permissions.add(Permission.RECEIVE_TASK)
            permissions.add(Permission.REQUEST_HELP)
            permissions.add(Permission.PROVIDE_HELP)

        # Capability-based permissions
        if "workspace_management" in capabilities:
            permissions.add(Permission.WRITE_WORKSPACE)
            permissions.add(Permission.SHARE_ARTIFACT)

        if "system_admin" in capabilities:
            permissions.add(Permission.SYSTEM_ADMIN)

        return permissions

    def _determine_security_level(self, agent_type: str) -> SecurityLevel:
        """Determine security level based on agent type"""

        level_mapping = {
            "public_agent": SecurityLevel.PUBLIC,
            "internal_agent": SecurityLevel.INTERNAL,
            "coordinator": SecurityLevel.CONFIDENTIAL,
            "system_agent": SecurityLevel.SECRET,
        }

        return level_mapping.get(agent_type, SecurityLevel.INTERNAL)

    async def _log_failed_attempt(self, agent_id: str, reason: str):
        """Log failed authentication attempt"""

        now = datetime.now()

        if agent_id not in self.failed_attempts:
            self.failed_attempts[agent_id] = []

        self.failed_attempts[agent_id].append(now)

        # Clean old attempts (older than 1 hour)
        cutoff = now - timedelta(hours=1)
        self.failed_attempts[agent_id] = [
            attempt for attempt in self.failed_attempts[agent_id] if attempt > cutoff
        ]

        # Check for suspicious activity
        if len(self.failed_attempts[agent_id]) > 5:
            await self._alert_suspicious_activity(agent_id, "multiple_failed_attempts")

        await self._audit_log(
            {
                "event": "authentication_failed",
                "agent_id": agent_id,
                "reason": reason,
                "timestamp": now.isoformat(),
            }
        )

    async def _alert_suspicious_activity(self, agent_id: str, activity_type: str):
        """Alert on suspicious activity"""

        if self.policy.alert_on_suspicious_activity:
            logger.warning(
                f"Suspicious activity detected for {agent_id}: {activity_type}"
            )

            # Could integrate with external alerting systems here

    async def _audit_log(self, event_data: Dict[str, Any]):
        """Add event to audit log"""

        if self.policy.enable_audit_logging:
            self.audit_log.append(event_data)

            # Rotate log if it gets too large
            if len(self.audit_log) > 10000:
                self.audit_log = self.audit_log[-5000:]  # Keep last 5000 entries

    def get_audit_log(
        self, agent_id: Optional[str] = None, event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get audit log entries with optional filtering"""

        logs = self.audit_log

        if agent_id:
            logs = [log for log in logs if log.get("agent_id") == agent_id]

        if event_type:
            logs = [log for log in logs if log.get("event") == event_type]

        return logs

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""

        active_agents = sum(1 for cred in self.credentials.values() if cred.is_active)

        return {
            "total_agents": len(self.credentials),
            "active_agents": active_agents,
            "inactive_agents": len(self.credentials) - active_agents,
            "audit_log_entries": len(self.audit_log),
            "failed_attempts_24h": sum(
                len(
                    [
                        attempt
                        for attempt in attempts
                        if attempt > datetime.now() - timedelta(hours=24)
                    ]
                )
                for attempts in self.failed_attempts.values()
            ),
            "policy": {
                "require_api_key": self.policy.require_api_key,
                "enable_message_signing": self.policy.enable_message_signing,
                "enable_rate_limiting": self.policy.enable_rate_limiting,
                "workspace_isolation": self.policy.workspace_isolation,
            },
        }
