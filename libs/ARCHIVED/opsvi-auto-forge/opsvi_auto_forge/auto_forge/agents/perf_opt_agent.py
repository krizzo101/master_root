"""Performance optimization agent for the autonomous software factory."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from opsvi_auto_forge.agents.base_agent import AgentResponse, BaseAgent
from opsvi_auto_forge.application.orchestrator.task_models import TaskExecution
from opsvi_auto_forge.config.models import AgentRole


@dataclass
class OptimizationSuggestion:
    """A performance optimization suggestion."""

    category: str
    title: str
    description: str
    impact: str  # "high", "medium", "low"
    effort: str  # "low", "medium", "high"
    priority: int  # 1-5, where 1 is highest priority
    code_example: Optional[str] = None
    estimated_improvement: Optional[str] = None


@dataclass
class PerformanceProfile:
    """Performance profile for analysis."""

    bottlenecks: List[str]
    resource_usage: Dict[str, float]
    slow_operations: List[Tuple[str, float]]
    optimization_opportunities: List[str]
    current_metrics: Dict[str, Any]


class PerfOptAgent(BaseAgent):
    """Agent for analyzing performance bottlenecks and suggesting optimizations."""

    def __init__(self, neo4j_client=None, logger=None):
        """Initialize the performance optimization agent."""
        super().__init__(AgentRole.PERF_OPT, neo4j_client, logger)

        # Predefined optimization patterns
        self.optimization_patterns = {
            "database": [
                {
                    "name": "Query Optimization",
                    "description": "Optimize slow database queries",
                    "impact": "high",
                    "effort": "medium",
                },
                {
                    "name": "Connection Pooling",
                    "description": "Implement database connection pooling",
                    "impact": "high",
                    "effort": "low",
                },
                {
                    "name": "Indexing",
                    "description": "Add database indexes for frequently queried columns",
                    "impact": "high",
                    "effort": "low",
                },
            ],
            "caching": [
                {
                    "name": "Redis Caching",
                    "description": "Implement Redis caching for frequently accessed data",
                    "impact": "high",
                    "effort": "medium",
                },
                {
                    "name": "In-Memory Caching",
                    "description": "Add in-memory caching for expensive computations",
                    "impact": "medium",
                    "effort": "low",
                },
            ],
            "async": [
                {
                    "name": "Async Operations",
                    "description": "Convert blocking operations to async",
                    "impact": "high",
                    "effort": "high",
                },
                {
                    "name": "Parallel Processing",
                    "description": "Process independent operations in parallel",
                    "impact": "medium",
                    "effort": "medium",
                },
            ],
            "memory": [
                {
                    "name": "Memory Profiling",
                    "description": "Identify memory leaks and optimize memory usage",
                    "impact": "medium",
                    "effort": "medium",
                },
                {
                    "name": "Garbage Collection",
                    "description": "Optimize garbage collection settings",
                    "impact": "low",
                    "effort": "low",
                },
            ],
            "code": [
                {
                    "name": "Algorithm Optimization",
                    "description": "Replace inefficient algorithms with optimized ones",
                    "impact": "high",
                    "effort": "high",
                },
                {
                    "name": "Data Structure Optimization",
                    "description": "Use more efficient data structures",
                    "impact": "medium",
                    "effort": "medium",
                },
            ],
        }

    async def execute(
        self, task_execution: TaskExecution, inputs: Dict[str, Any]
    ) -> AgentResponse:
        """Execute performance optimization analysis.

        Args:
            task_execution: The task execution context
            inputs: Input parameters including:
                - performance_metrics: Previous performance test results
                - code_analysis: Code analysis results (optional)
                - system_profile: System resource profile (optional)
                - focus_areas: Specific areas to focus on (optional)

        Returns:
            AgentResponse with optimization suggestions
        """
        try:
            # Extract parameters
            performance_metrics = inputs.get("performance_metrics", {})
            code_analysis = inputs.get("code_analysis", {})
            system_profile = inputs.get("system_profile", {})
            focus_areas = inputs.get(
                "focus_areas", ["database", "caching", "async", "memory", "code"]
            )

            self.logger.info("Starting performance optimization analysis")
            self.logger.info(f"Focus areas: {focus_areas}")

            # Analyze performance profile
            profile = await self._analyze_performance_profile(
                performance_metrics, code_analysis, system_profile
            )

            # Generate optimization suggestions
            suggestions = await self._generate_optimization_suggestions(
                profile, focus_areas
            )

            # Prioritize suggestions
            prioritized_suggestions = self._prioritize_suggestions(suggestions, profile)

            # Prepare response
            response_data = {
                "profile": {
                    "bottlenecks": profile.bottlenecks,
                    "resource_usage": profile.resource_usage,
                    "slow_operations": profile.slow_operations,
                    "optimization_opportunities": profile.optimization_opportunities,
                },
                "suggestions": [
                    {
                        "category": s.category,
                        "title": s.title,
                        "description": s.description,
                        "impact": s.impact,
                        "effort": s.effort,
                        "priority": s.priority,
                        "code_example": s.code_example,
                        "estimated_improvement": s.estimated_improvement,
                    }
                    for s in prioritized_suggestions
                ],
                "summary": {
                    "total_suggestions": len(prioritized_suggestions),
                    "high_impact": len(
                        [s for s in prioritized_suggestions if s.impact == "high"]
                    ),
                    "low_effort": len(
                        [s for s in prioritized_suggestions if s.effort == "low"]
                    ),
                    "estimated_total_improvement": self._estimate_total_improvement(
                        prioritized_suggestions
                    ),
                },
            }

            content = self._format_response(response_data)

            self.logger.info(
                f"Performance optimization analysis completed. Generated {len(prioritized_suggestions)} suggestions"
            )

            return AgentResponse(
                success=True,
                content=content,
                metadata={
                    "profile": response_data["profile"],
                    "suggestions": response_data["suggestions"],
                    "summary": response_data["summary"],
                },
            )

        except Exception as e:
            self.logger.error(f"Performance optimization analysis failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Performance optimization analysis failed: {str(e)}",
                metadata={"error": str(e)},
            )

    async def _analyze_performance_profile(
        self,
        performance_metrics: Dict[str, Any],
        code_analysis: Dict[str, Any],
        system_profile: Dict[str, Any],
    ) -> PerformanceProfile:
        """Analyze performance profile from metrics and analysis data."""

        bottlenecks = []
        resource_usage = {}
        slow_operations = []
        optimization_opportunities = []

        # Analyze performance metrics
        if performance_metrics:
            # Check latency bottlenecks
            p95_latency = performance_metrics.get("p95_latency_ms", 0)
            p99_latency = performance_metrics.get("p99_latency_ms", 0)

            if p95_latency > 500:  # More reasonable threshold for testing
                bottlenecks.append("High P95 latency indicates slow response times")
            if p99_latency > 1000:  # More reasonable threshold for testing
                bottlenecks.append(
                    "High P99 latency indicates occasional very slow responses"
                )

            # Check throughput bottlenecks
            throughput = performance_metrics.get("throughput_rps", 0)
            if throughput < 50:  # More reasonable threshold for testing
                bottlenecks.append("Low throughput indicates processing bottlenecks")

            # Check error rate
            error_rate = performance_metrics.get("error_rate", 0)
            if error_rate > 0.05:
                bottlenecks.append("High error rate indicates stability issues")

            # Resource usage analysis
            resource_usage = {
                "memory_mb": performance_metrics.get("memory_usage_mb", 0),
                "cpu_percent": performance_metrics.get("cpu_usage_percent", 0),
            }

            if (
                resource_usage["memory_mb"] > 256
            ):  # More reasonable threshold for testing
                optimization_opportunities.append("Memory usage optimization")
            if (
                resource_usage["cpu_percent"] > 50
            ):  # More reasonable threshold for testing
                optimization_opportunities.append("CPU usage optimization")

        # Analyze code analysis results
        if code_analysis:
            # Check for common performance issues
            if code_analysis.get("n_plus_one_queries", 0) > 0:
                bottlenecks.append("N+1 query pattern detected")
                slow_operations.append(
                    ("N+1 queries", code_analysis["n_plus_one_queries"])
                )

            if code_analysis.get("slow_queries", []):
                for query in code_analysis["slow_queries"]:
                    slow_operations.append(
                        (f"Slow query: {query['name']}", query["duration_ms"])
                    )

            if code_analysis.get("memory_leaks", 0) > 0:
                bottlenecks.append("Potential memory leaks detected")

            if code_analysis.get("blocking_operations", 0) > 0:
                bottlenecks.append("Blocking operations in async context")
                optimization_opportunities.append("Async optimization")

        # Analyze system profile
        if system_profile:
            if system_profile.get("disk_io_bottleneck", False):
                bottlenecks.append("Disk I/O bottleneck detected")
            if system_profile.get("network_bottleneck", False):
                bottlenecks.append("Network bottleneck detected")
            if system_profile.get("cpu_bottleneck", False):
                bottlenecks.append("CPU bottleneck detected")

        return PerformanceProfile(
            bottlenecks=bottlenecks,
            resource_usage=resource_usage,
            slow_operations=slow_operations,
            optimization_opportunities=optimization_opportunities,
            current_metrics=performance_metrics,
        )

    async def _generate_optimization_suggestions(
        self, profile: PerformanceProfile, focus_areas: List[str]
    ) -> List[OptimizationSuggestion]:
        """Generate optimization suggestions based on performance profile."""

        suggestions = []

        # Generate suggestions for each focus area
        for area in focus_areas:
            if area in self.optimization_patterns:
                patterns = self.optimization_patterns[area]

                for pattern in patterns:
                    # Check if this pattern is relevant based on profile
                    if self._is_pattern_relevant(pattern, profile):
                        suggestion = OptimizationSuggestion(
                            category=area,
                            title=pattern["name"],
                            description=pattern["description"],
                            impact=pattern["impact"],
                            effort=pattern["effort"],
                            priority=self._calculate_priority(pattern, profile),
                            code_example=self._generate_code_example(area, pattern),
                            estimated_improvement=self._estimate_improvement(
                                area, pattern
                            ),
                        )
                        suggestions.append(suggestion)

        # Add custom suggestions based on specific bottlenecks
        for bottleneck in profile.bottlenecks:
            if "latency" in bottleneck.lower():
                suggestions.append(
                    OptimizationSuggestion(
                        category="general",
                        title="Response Time Optimization",
                        description="Optimize response times through caching and async processing",
                        impact="high",
                        effort="medium",
                        priority=1,
                        estimated_improvement="20-50% latency reduction",
                    )
                )

            if "throughput" in bottleneck.lower():
                suggestions.append(
                    OptimizationSuggestion(
                        category="general",
                        title="Concurrency Optimization",
                        description="Increase concurrency and parallel processing",
                        impact="high",
                        effort="medium",
                        priority=1,
                        estimated_improvement="30-100% throughput improvement",
                    )
                )

        # Add suggestions based on optimization opportunities
        for opportunity in profile.optimization_opportunities:
            if "memory" in opportunity.lower():
                suggestions.append(
                    OptimizationSuggestion(
                        category="memory",
                        title="Memory Usage Optimization",
                        description="Optimize memory usage through profiling and data structure improvements",
                        impact="medium",
                        effort="medium",
                        priority=2,
                        estimated_improvement="10-30% memory reduction",
                    )
                )
            elif "cpu" in opportunity.lower():
                suggestions.append(
                    OptimizationSuggestion(
                        category="cpu",
                        title="CPU Usage Optimization",
                        description="Optimize CPU usage through algorithm improvements and parallelization",
                        impact="medium",
                        effort="high",
                        priority=2,
                        estimated_improvement="15-40% CPU reduction",
                    )
                )

        # If no suggestions were generated, provide general optimization suggestions
        if not suggestions:
            suggestions.append(
                OptimizationSuggestion(
                    category="general",
                    title="Performance Monitoring",
                    description="Implement comprehensive performance monitoring and profiling",
                    impact="medium",
                    effort="low",
                    priority=3,
                    estimated_improvement="Better visibility into performance bottlenecks",
                )
            )

        return suggestions

    def _is_pattern_relevant(
        self, pattern: Dict[str, Any], profile: PerformanceProfile
    ) -> bool:
        """Check if an optimization pattern is relevant to the current profile."""

        pattern_name = pattern["name"].lower()

        # Check bottlenecks
        for bottleneck in profile.bottlenecks:
            if any(keyword in bottleneck.lower() for keyword in pattern_name.split()):
                return True

        # Check slow operations
        for operation, _ in profile.slow_operations:
            if any(keyword in operation.lower() for keyword in pattern_name.split()):
                return True

        # Check resource usage
        if (
            "memory" in pattern_name
            and profile.resource_usage.get("memory_mb", 0) > 512
        ):
            return True
        if "cpu" in pattern_name and profile.resource_usage.get("cpu_percent", 0) > 80:
            return True

        return False

    def _calculate_priority(
        self, pattern: Dict[str, Any], profile: PerformanceProfile
    ) -> int:
        """Calculate priority for an optimization suggestion."""

        priority = 3  # Default priority

        # Impact-based adjustments
        if pattern["impact"] == "high":
            priority -= 1
        elif pattern["impact"] == "low":
            priority += 1

        # Effort-based adjustments
        if pattern["effort"] == "low":
            priority -= 1
        elif pattern["effort"] == "high":
            priority += 1

        # Bottleneck-based adjustments
        pattern_name = pattern["name"].lower()
        for bottleneck in profile.bottlenecks:
            if any(keyword in bottleneck.lower() for keyword in pattern_name.split()):
                priority -= 1
                break

        return max(1, min(5, priority))  # Ensure priority is between 1-5

    def _generate_code_example(
        self, area: str, pattern: Dict[str, Any]
    ) -> Optional[str]:
        """Generate a code example for the optimization pattern."""

        examples = {
            "database": {
                "Query Optimization": """
# Before: N+1 query problem
for user in users:
    posts = db.query("SELECT * FROM posts WHERE user_id = %s", user.id)

# After: Batch query
user_ids = [user.id for user in users]
posts = db.query("SELECT * FROM posts WHERE user_id IN %s", (user_ids,))
""",
                "Connection Pooling": """
# Before: Direct connection
conn = psycopg2.connect(database_url)

# After: Connection pooling
from psycopg2.pool import SimpleConnectionPool
pool = SimpleConnectionPool(1, 20, database_url)
conn = pool.getconn()
""",
                "Indexing": """
-- Add index for frequently queried column
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_posts_user_id ON posts(user_id);
""",
            },
            "caching": {
                "Redis Caching": """
# Before: Direct database query
user = db.query("SELECT * FROM users WHERE id = %s", user_id)

# After: Redis caching
import redis
r = redis.Redis()

user = r.get(f"user:{user_id}")
if not user:
    user = db.query("SELECT * FROM users WHERE id = %s", user_id)
    r.setex(f"user:{user_id}", 3600, json.dumps(user))
""",
                "In-Memory Caching": """
# Before: Expensive computation
def expensive_function(data):
    return complex_calculation(data)

# After: In-memory caching
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_function(data):
    return complex_calculation(data)
""",
            },
            "async": {
                "Async Operations": """
# Before: Blocking operation
def process_data(data):
    result = blocking_operation(data)
    return result

# After: Async operation
async def process_data(data):
    result = await async_operation(data)
    return result
""",
                "Parallel Processing": """
# Before: Sequential processing
results = []
for item in items:
    result = process_item(item)
    results.append(result)

# After: Parallel processing
import asyncio

async def process_all(items):
    tasks = [process_item(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results
""",
            },
        }

        return examples.get(area, {}).get(pattern["name"], None)

    def _estimate_improvement(
        self, area: str, pattern: Dict[str, Any]
    ) -> Optional[str]:
        """Estimate the improvement from applying an optimization pattern."""

        estimates = {
            "database": {
                "Query Optimization": "50-90% query time reduction",
                "Connection Pooling": "20-40% connection overhead reduction",
                "Indexing": "80-95% query time reduction",
            },
            "caching": {
                "Redis Caching": "70-90% response time reduction for cached data",
                "In-Memory Caching": "50-80% computation time reduction",
            },
            "async": {
                "Async Operations": "30-70% response time improvement",
                "Parallel Processing": "50-300% throughput improvement",
            },
            "memory": {
                "Memory Profiling": "20-50% memory usage reduction",
                "Garbage Collection": "10-30% memory overhead reduction",
            },
            "code": {
                "Algorithm Optimization": "50-90% execution time reduction",
                "Data Structure Optimization": "20-60% memory usage reduction",
            },
        }

        return estimates.get(area, {}).get(pattern["name"], "10-30% improvement")

    def _prioritize_suggestions(
        self, suggestions: List[OptimizationSuggestion], profile: PerformanceProfile
    ) -> List[OptimizationSuggestion]:
        """Prioritize optimization suggestions."""

        # Sort by priority (ascending) and then by impact/effort ratio
        def sort_key(suggestion):
            impact_score = {"high": 3, "medium": 2, "low": 1}[suggestion.impact]
            effort_score = {"low": 3, "medium": 2, "high": 1}[suggestion.effort]
            return (suggestion.priority, -impact_score / effort_score)

        return sorted(suggestions, key=sort_key)

    def _estimate_total_improvement(
        self, suggestions: List[OptimizationSuggestion]
    ) -> str:
        """Estimate total improvement from all suggestions."""

        if not suggestions:
            return "No optimizations suggested"

        high_impact = len([s for s in suggestions if s.impact == "high"])
        low_effort = len([s for s in suggestions if s.effort == "low"])

        if high_impact >= 3:
            return "50-200% overall performance improvement"
        elif high_impact >= 1:
            return "20-100% overall performance improvement"
        elif low_effort >= 3:
            return "10-50% overall performance improvement"
        else:
            return "5-30% overall performance improvement"

    def _format_response(self, response_data: Dict[str, Any]) -> str:
        """Format the response as a readable string."""

        profile = response_data["profile"]
        suggestions = response_data["suggestions"]
        summary = response_data["summary"]

        content = """
# Performance Optimization Analysis

## Performance Profile

### Bottlenecks Identified
"""

        if profile["bottlenecks"]:
            for bottleneck in profile["bottlenecks"]:
                content += f"- {bottleneck}\n"
        else:
            content += "- No major bottlenecks identified\n"

        content += """
### Resource Usage
"""

        for resource, value in profile["resource_usage"].items():
            content += f"- **{resource.replace('_', ' ').title()}**: {value}\n"

        content += """
### Slow Operations
"""

        if profile["slow_operations"]:
            for operation, duration in profile["slow_operations"]:
                content += f"- **{operation}**: {duration}ms\n"
        else:
            content += "- No slow operations identified\n"

        content += f"""
## Optimization Suggestions ({len(suggestions)} total)

### Summary
- **Total Suggestions**: {summary['total_suggestions']}
- **High Impact**: {summary['high_impact']}
- **Low Effort**: {summary['low_effort']}
- **Estimated Total Improvement**: {summary['estimated_total_improvement']}

### Detailed Suggestions
"""

        # Group suggestions by category
        by_category = {}
        for suggestion in suggestions:
            category = suggestion["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(suggestion)

        for category, cat_suggestions in by_category.items():
            content += f"\n#### {category.title()}\n"

            for suggestion in cat_suggestions:
                priority_stars = "⭐" * suggestion["priority"]
                impact_icon = {"high": "🔥", "medium": "⚡", "low": "💡"}[
                    suggestion["impact"]
                ]
                effort_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}[
                    suggestion["effort"]
                ]

                content += f"""
**{suggestion['title']}** {priority_stars} {impact_icon} {effort_icon}

{suggestion['description']}

- **Impact**: {suggestion['impact'].title()}
- **Effort**: {suggestion['effort'].title()}
- **Priority**: {suggestion['priority']}/5
"""

                if suggestion["estimated_improvement"]:
                    content += f"- **Estimated Improvement**: {suggestion['estimated_improvement']}\n"

                if suggestion["code_example"]:
                    content += f"\n**Code Example**:\n```python{suggestion['code_example']}```\n"

        return content
