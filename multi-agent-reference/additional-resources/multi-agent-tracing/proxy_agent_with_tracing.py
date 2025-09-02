"""
Example Proxy Agent with Tracing

This module demonstrates how to use OpenTelemetry tracing with a proxy agent
to monitor and analyze agent operations.
"""

import json
import logging
import random
import time
from typing import Any, Dict, List, Optional

# Import the standalone tracer
from standalone_tracer import AgentTracer, configure_tracing

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure tracing
tracer = configure_tracing(
    service_name="proxy-agent-demo", exporter_type="console", sampling_ratio=1.0
)


class BaseAgent:
    """Simple base agent class."""

    def __init__(self, agent_id: str, name: str, capabilities: List[str]):
        self.id = agent_id
        self.name = name
        self.capabilities = capabilities

    def process_query(
        self, query: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process a query and return a response."""
        # This would be implemented by specialized agents
        raise NotImplementedError("Subclasses must implement process_query")


class SpecializedAgent(BaseAgent):
    """A specialized agent that can handle specific types of queries."""

    def process_query(
        self, query: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process a query with the specialized agent."""
        context = context or {}

        # Use the tracer to create a span for this operation
        with tracer.start_as_current_span(f"{self.id}.process_query") as span:
            span.set_attribute("agent.id", self.id)
            span.set_attribute("agent.name", self.name)
            span.set_attribute("query.length", len(query))

            # Simulate processing time
            processing_time = random.uniform(0.1, 0.5)
            time.sleep(processing_time)

            # Simulate success or failure
            success = random.random() > 0.2  # 80% success rate

            if success:
                response = {
                    "agent_id": self.id,
                    "response": f"Response from {self.name}: I processed '{query}'",
                    "confidence": random.uniform(0.7, 1.0),
                }
                span.set_attribute("processing.success", True)
                span.set_attribute("processing.time", processing_time)
                return response
            else:
                # Simulate an error
                span.set_attribute("processing.success", False)
                span.set_attribute("processing.error", "Failed to process query")
                raise Exception(f"Agent {self.id} failed to process the query")


class ProxyAgent:
    """A proxy agent that routes queries to specialized agents."""

    def __init__(self):
        # Initialize some specialized agents
        self.agents = {
            "general": SpecializedAgent(
                "general", "General Purpose Agent", ["general_query", "information"]
            ),
            "math": SpecializedAgent(
                "math", "Math Agent", ["calculation", "mathematics"]
            ),
            "weather": SpecializedAgent(
                "weather", "Weather Agent", ["weather", "forecast"]
            ),
            "coding": SpecializedAgent(
                "coding", "Coding Agent", ["code", "programming"]
            ),
        }

        # Metrics for tracking agent performance
        self.metrics = {
            agent_id: {"calls": 0, "success": 0, "failure": 0}
            for agent_id in self.agents
        }

    def route_query(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Route a query to the appropriate agent."""
        context = context or {}

        # Create a span for the routing operation
        with tracer.start_as_current_span("proxy.route_query") as span:
            span.set_attribute("query", query)
            span.set_attribute("context_size", len(context))

            # Select an agent
            with tracer.start_as_current_span("agent_selection") as selection_span:
                agent_id = self._select_agent(query)
                selection_span.set_attribute("selected_agent", agent_id)

            # Get the agent
            agent = self.agents.get(agent_id)
            if not agent:
                span.set_attribute("error", f"Agent '{agent_id}' not found")
                raise ValueError(f"Agent '{agent_id}' not found")

            # Update metrics
            self.metrics[agent_id]["calls"] += 1

            # Process the query with the selected agent
            try:
                with tracer.start_as_current_span(
                    "agent_processing"
                ) as processing_span:
                    processing_span.set_attribute("agent.id", agent_id)

                    # Get the start time for performance tracking
                    start_time = time.time()

                    # Process the query
                    result = agent.process_query(query, context)

                    # Record execution time
                    elapsed = time.time() - start_time
                    processing_span.set_attribute("processing_time", elapsed)

                    # Update metrics
                    self.metrics[agent_id]["success"] += 1

                    # Add result attributes to span
                    if isinstance(result, dict):
                        for key, value in result.items():
                            if isinstance(value, (str, int, float, bool)):
                                processing_span.set_attribute(f"result.{key}", value)

                    return result

            except Exception as e:
                # Record the error
                span.record_exception(e)
                span.set_attribute("error", str(e))

                # Update metrics
                self.metrics[agent_id]["failure"] += 1

                # Re-raise the exception
                raise

    def _select_agent(self, query: str) -> str:
        """Select the appropriate agent based on the query."""
        # Simple selection based on keywords
        query_lower = query.lower()

        # Check for math-related keywords
        math_keywords = ["calculate", "math", "sum", "divide", "multiply"]
        for keyword in math_keywords:
            if keyword in query_lower:
                return "math"

        # Check for weather-related keywords
        weather_keywords = ["weather", "forecast", "temperature", "rain"]
        for keyword in weather_keywords:
            if keyword in query_lower:
                return "weather"

        # Check for coding-related keywords
        code_keywords = ["code", "program", "function", "algorithm"]
        for keyword in code_keywords:
            if keyword in query_lower:
                return "coding"

        # Default to general agent
        return "general"

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        with tracer.start_as_current_span("get_metrics") as span:
            span.set_attribute("metrics_count", len(self.metrics))

            # Create metrics summary
            for agent_id, metrics in self.metrics.items():
                calls = metrics["calls"]
                success = metrics["success"]
                success_rate = (success / calls) * 100 if calls > 0 else 0
                span.set_attribute(f"agent.{agent_id}.success_rate", success_rate)

            return self.metrics


# Sample usage
if __name__ == "__main__":
    print("Starting Proxy Agent with Tracing Example")

    # Create proxy agent
    proxy = ProxyAgent()

    # Sample queries
    queries = [
        "What's the weather like today?",
        "Calculate 25 * 17",
        "Tell me a joke",
        "Write a function to calculate Fibonacci numbers",
        "What is the capital of France?",
        "How hot will it be tomorrow?",
        "Explain quantum mechanics",
        "Help me debug my code",
    ]

    # Process each query
    for i, query in enumerate(queries):
        print(f"\nQuery {i+1}: {query}")
        try:
            with tracer.start_as_current_span("process_request") as span:
                span.set_attribute("query_id", i)
                span.set_attribute("query", query)

                # Add some context
                context = {"request_id": f"req-{i+1}", "timestamp": time.time()}

                # Route the query
                result = proxy.route_query(query, context)

                # Print result
                print(f"Result: {json.dumps(result, indent=2)}")
                span.set_attribute("status", "success")
        except Exception as e:
            print(f"Error: {str(e)}")

    # Print metrics
    print("\nAgent Metrics:")
    metrics = proxy.get_metrics()
    for agent_id, agent_metrics in metrics.items():
        calls = agent_metrics["calls"]
        success = agent_metrics["success"]
        failure = agent_metrics["failure"]
        success_rate = (success / calls) * 100 if calls > 0 else 0

        print(f"  {agent_id}: {calls} calls, {success_rate:.1f}% success rate")

    print("\nTracing example completed!")
