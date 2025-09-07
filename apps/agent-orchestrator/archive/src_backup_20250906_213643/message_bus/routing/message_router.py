"""
Advanced Message Router with intelligent routing, load balancing, and failover.

Provides sophisticated message routing capabilities including:
- Load balancing across multiple instances
- Geographic routing
- Priority-based routing
- Circuit breaker patterns
- Message transformation and filtering
"""

import asyncio
import hashlib
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from ..core.message_types import Message, MessagePriority, MessageType

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Message routing strategies"""

    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    HASH_BASED = "hash_based"
    PRIORITY_BASED = "priority_based"
    GEOGRAPHIC = "geographic"
    CAPABILITY_BASED = "capability_based"


class CircuitBreakerState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures detected, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class AgentInfo:
    """Information about an agent for routing decisions"""

    agent_id: str
    capabilities: Set[str]
    current_load: int = 0
    max_load: int = 100
    location: Optional[str] = None
    priority_multiplier: float = 1.0
    last_seen: float = 0.0
    failure_count: int = 0
    success_count: int = 0
    response_time_ms: float = 0.0

    @property
    def load_percentage(self) -> float:
        """Get current load as percentage"""
        return (self.current_load / self.max_load) * 100 if self.max_load > 0 else 0

    @property
    def success_rate(self) -> float:
        """Get success rate percentage"""
        total = self.success_count + self.failure_count
        return (self.success_count / total) * 100 if total > 0 else 0

    def is_healthy(self) -> bool:
        """Check if agent is considered healthy"""
        return (
            self.load_percentage < 90
            and self.success_rate > 50
            and time.time() - self.last_seen < 300  # 5 minutes
        )


@dataclass
class RouteConfig:
    """Configuration for a routing rule"""

    name: str
    source_pattern: str = "*"  # sender pattern
    destination_pattern: str = "*"  # recipient pattern
    message_type: Optional[MessageType] = None
    priority: Optional[MessagePriority] = None
    strategy: RoutingStrategy = RoutingStrategy.ROUND_ROBIN
    weight: float = 1.0
    enabled: bool = True
    transformation: Optional[Callable[[Message], Message]] = None
    filter_condition: Optional[Callable[[Message], bool]] = None


@dataclass
class CircuitBreaker:
    """Circuit breaker for agent failure handling"""

    agent_id: str
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: int = 60
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0

    def record_success(self) -> None:
        """Record a successful operation"""
        self.success_count += 1
        self.last_success_time = time.time()

        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.success_count >= self.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker closed for agent: %s", self.agent_id)

    def record_failure(self) -> None:
        """Record a failed operation"""
        self.failure_count += 1
        self.success_count = 0
        self.last_failure_time = time.time()

        if self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning("Circuit breaker opened for agent: %s", self.agent_id)

    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker half-open for agent: %s", self.agent_id)
                return True
            return False
        else:  # HALF_OPEN
            return True


class MessageRouter:
    """Advanced message router with intelligent routing capabilities"""

    def __init__(self):
        # Agent registry
        self.agents: Dict[str, AgentInfo] = {}

        # Routing configuration
        self.routes: List[RouteConfig] = []
        self.default_strategy = RoutingStrategy.ROUND_ROBIN

        # Circuit breakers
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Load balancing state
        self._round_robin_counters: Dict[str, int] = {}  # group/topic -> counter

        # Statistics
        self.routing_stats: Dict[str, int] = {
            "total_routed": 0,
            "failed_routes": 0,
            "circuit_breaker_trips": 0,
            "load_balancer_decisions": 0,
        }

        logger.info("MessageRouter initialized")

    def register_agent(
        self,
        agent_id: str,
        capabilities: Set[str] = None,
        max_load: int = 100,
        location: Optional[str] = None,
        priority_multiplier: float = 1.0,
    ) -> None:
        """Register an agent with the router"""
        self.agents[agent_id] = AgentInfo(
            agent_id=agent_id,
            capabilities=capabilities or set(),
            max_load=max_load,
            location=location,
            priority_multiplier=priority_multiplier,
            last_seen=time.time(),
        )

        # Create circuit breaker
        self.circuit_breakers[agent_id] = CircuitBreaker(agent_id=agent_id)

        logger.debug(
            "Registered agent: %s with capabilities: %s", agent_id, capabilities
        )

    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the router"""
        self.agents.pop(agent_id, None)
        self.circuit_breakers.pop(agent_id, None)
        logger.debug("Unregistered agent: %s", agent_id)

    def add_route(self, route: RouteConfig) -> None:
        """Add a routing rule"""
        self.routes.append(route)
        logger.debug("Added routing rule: %s", route.name)

    def remove_route(self, route_name: str) -> None:
        """Remove a routing rule"""
        self.routes = [r for r in self.routes if r.name != route_name]
        logger.debug("Removed routing rule: %s", route_name)

    def update_agent_load(self, agent_id: str, current_load: int) -> None:
        """Update agent's current load"""
        if agent_id in self.agents:
            self.agents[agent_id].current_load = current_load
            self.agents[agent_id].last_seen = time.time()

    def update_agent_metrics(
        self, agent_id: str, success: bool, response_time_ms: float
    ) -> None:
        """Update agent's performance metrics"""
        if agent_id not in self.agents:
            return

        agent = self.agents[agent_id]
        circuit_breaker = self.circuit_breakers.get(agent_id)

        if success:
            agent.success_count += 1
            agent.response_time_ms = (agent.response_time_ms + response_time_ms) / 2
            if circuit_breaker:
                circuit_breaker.record_success()
        else:
            agent.failure_count += 1
            if circuit_breaker:
                circuit_breaker.record_failure()
                if circuit_breaker.state == CircuitBreakerState.OPEN:
                    self.routing_stats["circuit_breaker_trips"] += 1

        agent.last_seen = time.time()

    def route_message(
        self, message: Message, available_agents: List[str]
    ) -> Optional[List[str]]:
        """
        Route a message to appropriate agents based on routing rules and strategies.
        Returns list of agent IDs that should receive the message.
        """
        try:
            self.routing_stats["total_routed"] += 1

            # Filter available agents by health and circuit breaker status
            healthy_agents = self._filter_healthy_agents(available_agents)

            if not healthy_agents:
                logger.warning("No healthy agents available for routing")
                self.routing_stats["failed_routes"] += 1
                return None

            # Find matching routing rules
            matching_routes = self._find_matching_routes(message)

            # Apply transformations and filters
            filtered_message = self._apply_transformations_and_filters(
                message, matching_routes
            )

            if not filtered_message:
                logger.debug("Message filtered out by routing rules")
                return []

            # Select routing strategy
            strategy = self._select_routing_strategy(filtered_message, matching_routes)

            # Route based on message type
            if message.message_type == MessageType.POINT_TO_POINT:
                # For point-to-point, verify the recipient is healthy
                if message.recipient_id in healthy_agents:
                    return [message.recipient_id]
                else:
                    logger.warning("Recipient %s is not healthy", message.recipient_id)
                    return None

            elif message.message_type in [
                MessageType.BROADCAST,
                MessageType.GROUP,
                MessageType.TOPIC,
            ]:
                # For multi-recipient messages, use routing strategy
                selected_agents = self._apply_routing_strategy(
                    strategy, healthy_agents, filtered_message
                )

                self.routing_stats["load_balancer_decisions"] += 1
                return selected_agents

            else:
                # System messages go to all healthy agents
                return healthy_agents

        except Exception as e:
            logger.error("Error routing message: %s", e)
            self.routing_stats["failed_routes"] += 1
            return None

    def _filter_healthy_agents(self, agent_ids: List[str]) -> List[str]:
        """Filter agents by health status and circuit breaker state"""
        healthy_agents = []

        for agent_id in agent_ids:
            # Check if agent is registered
            if agent_id not in self.agents:
                continue

            agent = self.agents[agent_id]
            circuit_breaker = self.circuit_breakers.get(agent_id)

            # Check agent health
            if not agent.is_healthy():
                continue

            # Check circuit breaker
            if circuit_breaker and not circuit_breaker.can_execute():
                continue

            healthy_agents.append(agent_id)

        return healthy_agents

    def _find_matching_routes(self, message: Message) -> List[RouteConfig]:
        """Find routing rules that match the message"""
        matching_routes = []

        for route in self.routes:
            if not route.enabled:
                continue

            # Check message type
            if route.message_type and route.message_type != message.message_type:
                continue

            # Check priority
            if route.priority and route.priority != message.priority:
                continue

            # Check source pattern
            if not self._match_pattern(route.source_pattern, message.sender_id):
                continue

            # Check destination pattern
            destination = (
                message.recipient_id or message.group_id or message.topic or "*"
            )
            if not self._match_pattern(route.destination_pattern, destination):
                continue

            matching_routes.append(route)

        # Sort by weight (higher weight = higher priority)
        matching_routes.sort(key=lambda r: r.weight, reverse=True)

        return matching_routes

    def _match_pattern(self, pattern: str, value: str) -> bool:
        """Simple pattern matching with wildcards"""
        if pattern == "*":
            return True

        if "*" in pattern:
            # Simple wildcard matching
            parts = pattern.split("*")
            if len(parts) == 2:
                prefix, suffix = parts
                return value.startswith(prefix) and value.endswith(suffix)

        return pattern == value

    def _apply_transformations_and_filters(
        self, message: Message, routes: List[RouteConfig]
    ) -> Optional[Message]:
        """Apply message transformations and filters from routing rules"""
        current_message = message

        for route in routes:
            # Apply filter
            if route.filter_condition and not route.filter_condition(current_message):
                return None  # Message filtered out

            # Apply transformation
            if route.transformation:
                try:
                    current_message = route.transformation(current_message)
                except Exception as e:
                    logger.error(
                        "Error applying transformation in route %s: %s", route.name, e
                    )
                    continue

        return current_message

    def _select_routing_strategy(
        self, message: Message, routes: List[RouteConfig]
    ) -> RoutingStrategy:
        """Select routing strategy based on message and routes"""
        # Use strategy from highest-weight matching route
        if routes:
            return routes[0].strategy

        # Use priority-based routing for high-priority messages
        if message.priority in [MessagePriority.HIGH, MessagePriority.CRITICAL]:
            return RoutingStrategy.PRIORITY_BASED

        return self.default_strategy

    def _apply_routing_strategy(
        self, strategy: RoutingStrategy, available_agents: List[str], message: Message
    ) -> List[str]:
        """Apply routing strategy to select agents"""

        if strategy == RoutingStrategy.ROUND_ROBIN:
            return self._round_robin_routing(available_agents, message)

        elif strategy == RoutingStrategy.RANDOM:
            return self._random_routing(available_agents, message)

        elif strategy == RoutingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_routing(available_agents, message)

        elif strategy == RoutingStrategy.HASH_BASED:
            return self._hash_based_routing(available_agents, message)

        elif strategy == RoutingStrategy.PRIORITY_BASED:
            return self._priority_based_routing(available_agents, message)

        elif strategy == RoutingStrategy.GEOGRAPHIC:
            return self._geographic_routing(available_agents, message)

        elif strategy == RoutingStrategy.CAPABILITY_BASED:
            return self._capability_based_routing(available_agents, message)

        else:
            # Default to all available agents
            return available_agents

    def _round_robin_routing(self, agents: List[str], message: Message) -> List[str]:
        """Round-robin load balancing"""
        if not agents:
            return []

        # Use message context for round-robin key
        key = message.group_id or message.topic or "default"

        if key not in self._round_robin_counters:
            self._round_robin_counters[key] = 0

        selected_index = self._round_robin_counters[key] % len(agents)
        self._round_robin_counters[key] += 1

        return [agents[selected_index]]

    def _random_routing(self, agents: List[str], message: Message) -> List[str]:
        """Random agent selection"""
        if not agents:
            return []

        return [random.choice(agents)]

    def _least_connections_routing(
        self, agents: List[str], message: Message
    ) -> List[str]:
        """Select agent with least current load"""
        if not agents:
            return []

        # Sort agents by current load
        sorted_agents = sorted(
            agents, key=lambda aid: self.agents.get(aid, AgentInfo("")).current_load
        )

        return [sorted_agents[0]]

    def _hash_based_routing(self, agents: List[str], message: Message) -> List[str]:
        """Hash-based consistent routing"""
        if not agents:
            return []

        # Use message ID or sender ID for hash
        hash_input = message.message_id or message.sender_id
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        selected_index = hash_value % len(agents)
        return [agents[selected_index]]

    def _priority_based_routing(self, agents: List[str], message: Message) -> List[str]:
        """Route based on agent priority multipliers"""
        if not agents:
            return []

        # Calculate weighted selection based on priority multipliers
        agent_weights = []
        for agent_id in agents:
            agent = self.agents.get(agent_id)
            if agent:
                # Higher priority multiplier and lower load = higher weight
                weight = agent.priority_multiplier / (1 + agent.load_percentage / 100)
                agent_weights.append((agent_id, weight))

        if not agent_weights:
            return agents[:1]  # Fallback to first agent

        # Select agent with highest weight
        selected_agent = max(agent_weights, key=lambda x: x[1])[0]
        return [selected_agent]

    def _geographic_routing(self, agents: List[str], message: Message) -> List[str]:
        """Route based on geographic location"""
        if not agents:
            return []

        # This is a simplified version - in reality you'd use proper geo-distance calculation
        sender_location = None
        if message.sender_id in self.agents:
            sender_location = self.agents[message.sender_id].location

        if sender_location:
            # Prefer agents in the same location
            same_location_agents = [
                aid
                for aid in agents
                if self.agents.get(aid, AgentInfo("")).location == sender_location
            ]
            if same_location_agents:
                return same_location_agents[:1]

        # Fallback to first available agent
        return agents[:1]

    def _capability_based_routing(
        self, agents: List[str], message: Message
    ) -> List[str]:
        """Route based on agent capabilities"""
        if not agents:
            return []

        # Look for required capabilities in message payload
        required_capabilities = message.payload.get("required_capabilities", [])

        if required_capabilities:
            # Filter agents that have all required capabilities
            capable_agents = []
            for agent_id in agents:
                agent = self.agents.get(agent_id)
                if agent and all(
                    cap in agent.capabilities for cap in required_capabilities
                ):
                    capable_agents.append(agent_id)

            if capable_agents:
                return capable_agents[:1]

        # Fallback to all agents if no specific capabilities required
        return agents[:1]

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            "routing_stats": self.routing_stats.copy(),
            "registered_agents": len(self.agents),
            "active_routes": len([r for r in self.routes if r.enabled]),
            "circuit_breakers": {
                aid: {
                    "state": cb.state.value,
                    "failure_count": cb.failure_count,
                    "success_count": cb.success_count,
                }
                for aid, cb in self.circuit_breakers.items()
            },
            "agent_health": {
                aid: {
                    "load_percentage": agent.load_percentage,
                    "success_rate": agent.success_rate,
                    "is_healthy": agent.is_healthy(),
                }
                for aid, agent in self.agents.items()
            },
        }

    def get_agent_recommendations(self, message: Message) -> Dict[str, Any]:
        """Get agent recommendations for a message"""
        # Simulate getting available agents (this would come from MessageBus)
        available_agents = list(self.agents.keys())

        recommended_agents = self.route_message(message, available_agents)

        return {
            "message_id": message.message_id,
            "message_type": message.message_type.value,
            "available_agents": available_agents,
            "recommended_agents": recommended_agents or [],
            "routing_strategy": "intelligent_selection",
            "confidence_score": 0.85 if recommended_agents else 0.0,
        }
