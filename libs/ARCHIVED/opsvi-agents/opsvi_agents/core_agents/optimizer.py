"""OptimizerAgent - Performance optimization."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import structlog

from ..core import AgentConfig, AgentContext, AgentResult, BaseAgent

logger = structlog.get_logger()


class OptimizationType(Enum):
    """Types of optimization."""

    PERFORMANCE = "performance"
    MEMORY = "memory"
    COST = "cost"
    QUALITY = "quality"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    RESOURCE = "resource"
    ALGORITHM = "algorithm"


class OptimizationStrategy(Enum):
    """Optimization strategies."""

    GREEDY = "greedy"
    GRADIENT = "gradient"
    GENETIC = "genetic"
    SIMULATED_ANNEALING = "simulated_annealing"
    HILL_CLIMBING = "hill_climbing"
    CONSTRAINT = "constraint"


@dataclass
class OptimizationTarget:
    """Optimization target."""

    metric: str
    current_value: float
    target_value: float
    weight: float = 1.0
    constraint: Optional[str] = None

    def improvement_ratio(self) -> float:
        """Calculate improvement ratio."""
        if self.current_value == 0:
            return 0
        return (self.target_value - self.current_value) / self.current_value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric": self.metric,
            "current_value": self.current_value,
            "target_value": self.target_value,
            "weight": self.weight,
            "constraint": self.constraint,
            "improvement_ratio": self.improvement_ratio(),
        }


@dataclass
class OptimizationResult:
    """Optimization result."""

    id: str
    type: OptimizationType
    strategy: OptimizationStrategy
    original_state: Dict[str, Any]
    optimized_state: Dict[str, Any]
    improvements: Dict[str, float] = field(default_factory=dict)
    iterations: int = 0
    converged: bool = False
    duration: float = 0.0

    def get_improvement_summary(self) -> str:
        """Get improvement summary."""
        if not self.improvements:
            return "No improvements"

        parts = []
        for metric, improvement in self.improvements.items():
            if improvement > 0:
                parts.append(f"{metric}: +{improvement:.1f}%")
            else:
                parts.append(f"{metric}: {improvement:.1f}%")

        return ", ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "strategy": self.strategy.value,
            "improvements": self.improvements,
            "iterations": self.iterations,
            "converged": self.converged,
            "duration": self.duration,
            "summary": self.get_improvement_summary(),
        }


@dataclass
class OptimizationProfile:
    """Optimization profile/configuration."""

    name: str
    targets: List[OptimizationTarget]
    strategy: OptimizationStrategy
    max_iterations: int = 100
    convergence_threshold: float = 0.01
    constraints: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "targets": [t.to_dict() for t in self.targets],
            "strategy": self.strategy.value,
            "max_iterations": self.max_iterations,
            "convergence_threshold": self.convergence_threshold,
            "constraints": self.constraints,
        }


class OptimizerAgent(BaseAgent):
    """Optimizes performance and resource usage."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize optimizer agent."""
        super().__init__(
            config
            or AgentConfig(
                name="OptimizerAgent",
                description="Performance optimization",
                capabilities=["optimize", "tune", "improve", "analyze", "profile"],
                max_retries=3,
                timeout=180,
            )
        )
        self.profiles: Dict[str, OptimizationProfile] = {}
        self.results: Dict[str, OptimizationResult] = {}
        self.benchmarks: Dict[str, Dict[str, float]] = {}
        self._result_counter = 0
        self._profile_counter = 0
        self._register_default_profiles()

    def initialize(self) -> bool:
        """Initialize the optimizer agent."""
        logger.info("optimizer_agent_initialized", agent=self.config.name)
        return True

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute optimization task."""
        action = task.get("action", "optimize")

        if action == "optimize":
            return self._optimize(task)
        elif action == "tune":
            return self._tune_parameters(task)
        elif action == "profile":
            return self._create_profile(task)
        elif action == "analyze":
            return self._analyze_performance(task)
        elif action == "benchmark":
            return self._run_benchmark(task)
        elif action == "recommend":
            return self._recommend_optimizations(task)
        elif action == "apply_profile":
            return self._apply_profile(task)
        elif action == "compare":
            return self._compare_configurations(task)
        else:
            return {"error": f"Unknown action: {action}"}

    def optimize(
        self,
        target: Any,
        optimization_type: OptimizationType = OptimizationType.PERFORMANCE,
        strategy: OptimizationStrategy = OptimizationStrategy.GRADIENT,
    ) -> OptimizationResult:
        """Optimize a target."""
        result = self.execute(
            {
                "action": "optimize",
                "target": target,
                "type": optimization_type.value,
                "strategy": strategy.value,
            }
        )

        if "error" in result:
            raise RuntimeError(result["error"])

        return result["result"]

    def _register_default_profiles(self):
        """Register default optimization profiles."""
        # Performance profile
        perf_targets = [
            OptimizationTarget("response_time", 1000, 100, weight=2.0),
            OptimizationTarget("throughput", 100, 1000, weight=1.5),
            OptimizationTarget("cpu_usage", 80, 50, weight=1.0),
        ]

        self.profiles["performance"] = OptimizationProfile(
            name="performance",
            targets=perf_targets,
            strategy=OptimizationStrategy.GRADIENT,
        )

        # Memory profile
        mem_targets = [
            OptimizationTarget("memory_usage", 1024, 512, weight=2.0),
            OptimizationTarget("cache_hit_rate", 0.7, 0.95, weight=1.0),
        ]

        self.profiles["memory"] = OptimizationProfile(
            name="memory", targets=mem_targets, strategy=OptimizationStrategy.CONSTRAINT
        )

        # Cost profile
        cost_targets = [
            OptimizationTarget("resource_cost", 100, 50, weight=2.0),
            OptimizationTarget("efficiency", 0.7, 0.9, weight=1.5),
        ]

        self.profiles["cost"] = OptimizationProfile(
            name="cost", targets=cost_targets, strategy=OptimizationStrategy.GREEDY
        )

    def _optimize(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform optimization."""
        target = task.get("target")
        opt_type = task.get("type", "performance")
        strategy = task.get("strategy", "gradient")
        max_iterations = task.get("max_iterations", 100)

        if target is None:
            return {"error": "Target is required"}

        start_time = time.time()

        type_enum = OptimizationType[opt_type.upper()]
        strategy_enum = OptimizationStrategy[strategy.upper()]

        # Get initial state
        original_state = self._get_state(target)

        # Create optimization result
        self._result_counter += 1
        result = OptimizationResult(
            id=f"result_{self._result_counter}",
            type=type_enum,
            strategy=strategy_enum,
            original_state=original_state,
            optimized_state=original_state.copy(),
        )

        # Run optimization based on strategy
        if strategy_enum == OptimizationStrategy.GRADIENT:
            self._gradient_optimization(target, result, max_iterations)
        elif strategy_enum == OptimizationStrategy.GREEDY:
            self._greedy_optimization(target, result, max_iterations)
        elif strategy_enum == OptimizationStrategy.GENETIC:
            self._genetic_optimization(target, result, max_iterations)
        elif strategy_enum == OptimizationStrategy.SIMULATED_ANNEALING:
            self._simulated_annealing(target, result, max_iterations)
        else:
            self._default_optimization(target, result, max_iterations)

        result.duration = time.time() - start_time

        # Calculate improvements
        result.improvements = self._calculate_improvements(
            result.original_state, result.optimized_state
        )

        # Store result
        self.results[result.id] = result

        logger.info(
            "optimization_completed",
            result_id=result.id,
            type=opt_type,
            strategy=strategy,
            iterations=result.iterations,
            improvements=result.get_improvement_summary(),
        )

        return {
            "result": result,
            "improvements": result.improvements,
            "summary": result.get_improvement_summary(),
        }

    def _tune_parameters(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Tune parameters for optimization."""
        parameters = task.get("parameters", {})
        target_metric = task.get("target_metric", "performance")
        method = task.get("method", "grid_search")

        tuned_params = parameters.copy()
        best_score = float("-inf")

        if method == "grid_search":
            # Simple grid search
            param_ranges = task.get("param_ranges", {})

            for param, range_values in param_ranges.items():
                best_value = parameters.get(param)

                for value in range_values:
                    test_params = tuned_params.copy()
                    test_params[param] = value

                    # Evaluate parameters
                    score = self._evaluate_parameters(test_params, target_metric)

                    if score > best_score:
                        best_score = score
                        best_value = value

                tuned_params[param] = best_value

        elif method == "random_search":
            # Random search
            iterations = task.get("iterations", 10)
            import random

            for _ in range(iterations):
                test_params = parameters.copy()

                # Randomly modify parameters
                for param in test_params:
                    if isinstance(test_params[param], (int, float)):
                        test_params[param] *= random.uniform(0.8, 1.2)

                score = self._evaluate_parameters(test_params, target_metric)

                if score > best_score:
                    best_score = score
                    tuned_params = test_params

        return {
            "original_parameters": parameters,
            "tuned_parameters": tuned_params,
            "improvement": best_score,
            "method": method,
        }

    def _create_profile(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create optimization profile."""
        name = task.get("name", "custom")
        targets_data = task.get("targets", [])
        strategy = task.get("strategy", "gradient")
        max_iterations = task.get("max_iterations", 100)

        # Create targets
        targets = []
        for target_data in targets_data:
            target = OptimizationTarget(
                metric=target_data.get("metric", "performance"),
                current_value=target_data.get("current", 0),
                target_value=target_data.get("target", 100),
                weight=target_data.get("weight", 1.0),
            )
            targets.append(target)

        # Create profile
        self._profile_counter += 1
        profile = OptimizationProfile(
            name=name,
            targets=targets,
            strategy=OptimizationStrategy[strategy.upper()],
            max_iterations=max_iterations,
        )

        # Store profile
        self.profiles[name] = profile

        return {"profile": profile.to_dict(), "profile_name": name}

    def _analyze_performance(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance for optimization opportunities."""
        target = task.get("target")
        metrics = task.get("metrics", ["response_time", "throughput", "resource_usage"])

        if target is None:
            return {"error": "Target is required"}

        analysis = {
            "target": str(target),
            "metrics": {},
            "bottlenecks": [],
            "opportunities": [],
        }

        # Analyze each metric
        for metric in metrics:
            value = self._measure_metric(target, metric)
            analysis["metrics"][metric] = value

            # Identify bottlenecks
            if metric == "response_time" and value > 1000:
                analysis["bottlenecks"].append(f"High {metric}: {value}ms")
            elif metric == "throughput" and value < 100:
                analysis["bottlenecks"].append(f"Low {metric}: {value} ops/sec")
            elif metric == "resource_usage" and value > 80:
                analysis["bottlenecks"].append(f"High {metric}: {value}%")

        # Identify optimization opportunities
        if analysis["bottlenecks"]:
            analysis["opportunities"].append("Performance tuning recommended")

            if "response_time" in [
                b.split(":")[0].replace("High ", "").replace("Low ", "")
                for b in analysis["bottlenecks"]
            ]:
                analysis["opportunities"].append(
                    "Consider caching or algorithm optimization"
                )

            if "resource_usage" in [
                b.split(":")[0].replace("High ", "") for b in analysis["bottlenecks"]
            ]:
                analysis["opportunities"].append("Resource optimization needed")

        return {"analysis": analysis}

    def _run_benchmark(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run performance benchmark."""
        target = task.get("target")
        iterations = task.get("iterations", 100)
        metrics = task.get("metrics", ["time", "memory"])

        if target is None:
            return {"error": "Target is required"}

        benchmark_results = {
            "target": str(target),
            "iterations": iterations,
            "metrics": {},
        }

        # Run benchmark
        for metric in metrics:
            results = []

            for _ in range(iterations):
                value = self._measure_metric(target, metric)
                results.append(value)

            # Calculate statistics
            benchmark_results["metrics"][metric] = {
                "mean": sum(results) / len(results),
                "min": min(results),
                "max": max(results),
                "samples": results[:10],  # First 10 samples
            }

        # Store benchmark
        target_key = str(target)[:50]  # Limit key length
        self.benchmarks[target_key] = benchmark_results["metrics"]

        return {"benchmark": benchmark_results}

    def _recommend_optimizations(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend optimizations based on analysis."""
        analysis = task.get("analysis", {})
        constraints = task.get("constraints", {})

        recommendations = []
        priority_map = {"high": 3, "medium": 2, "low": 1}

        # Analyze metrics
        metrics = analysis.get("metrics", {})

        for metric, value in metrics.items():
            if metric == "response_time" and value > 500:
                recommendations.append(
                    {
                        "type": "performance",
                        "action": "Implement caching layer",
                        "priority": "high" if value > 1000 else "medium",
                        "expected_improvement": "30-50% reduction",
                    }
                )

            if metric == "memory_usage" and value > 1024:
                recommendations.append(
                    {
                        "type": "memory",
                        "action": "Optimize data structures",
                        "priority": "high" if value > 2048 else "medium",
                        "expected_improvement": "20-40% reduction",
                    }
                )

            if metric == "throughput" and value < 100:
                recommendations.append(
                    {
                        "type": "throughput",
                        "action": "Implement parallel processing",
                        "priority": "medium",
                        "expected_improvement": "2-3x increase",
                    }
                )

        # Sort by priority
        recommendations.sort(
            key=lambda x: priority_map.get(x["priority"], 0), reverse=True
        )

        return {"recommendations": recommendations, "total": len(recommendations)}

    def _apply_profile(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Apply optimization profile."""
        profile_name = task.get("profile")
        target = task.get("target")

        if not profile_name or profile_name not in self.profiles:
            return {"error": f"Profile {profile_name} not found"}

        if target is None:
            return {"error": "Target is required"}

        profile = self.profiles[profile_name]

        # Apply optimization with profile
        result = self._optimize(
            {
                "target": target,
                "type": "custom",
                "strategy": profile.strategy.value,
                "max_iterations": profile.max_iterations,
            }
        )

        return {"profile_applied": profile_name, "result": result}

    def _compare_configurations(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Compare different configurations."""
        configs = task.get("configurations", [])
        metric = task.get("metric", "performance")

        if len(configs) < 2:
            return {"error": "At least 2 configurations required"}

        comparison = {"metric": metric, "configurations": []}

        best_score = float("-inf")
        best_config = None

        for i, config in enumerate(configs):
            # Evaluate configuration
            score = self._evaluate_configuration(config, metric)

            comparison["configurations"].append(
                {"index": i, "config": config, "score": score}
            )

            if score > best_score:
                best_score = score
                best_config = i

        comparison["best_configuration"] = best_config
        comparison["best_score"] = best_score

        return {"comparison": comparison}

    # Optimization algorithms
    def _gradient_optimization(
        self, target: Any, result: OptimizationResult, max_iterations: int
    ):
        """Gradient-based optimization."""
        learning_rate = 0.1

        for i in range(max_iterations):
            result.iterations = i + 1

            # Calculate gradient (simplified)
            current_score = self._evaluate_target(target, result.optimized_state)

            # Update state
            for key in result.optimized_state:
                if isinstance(result.optimized_state[key], (int, float)):
                    # Numerical optimization
                    gradient = self._calculate_gradient(
                        target, key, result.optimized_state
                    )
                    result.optimized_state[key] -= learning_rate * gradient

            # Check convergence
            new_score = self._evaluate_target(target, result.optimized_state)
            if abs(new_score - current_score) < 0.01:
                result.converged = True
                break

    def _greedy_optimization(
        self, target: Any, result: OptimizationResult, max_iterations: int
    ):
        """Greedy optimization."""
        for i in range(max_iterations):
            result.iterations = i + 1

            best_change = None
            best_score = self._evaluate_target(target, result.optimized_state)

            # Try each possible change
            for key in result.optimized_state:
                if isinstance(result.optimized_state[key], (int, float)):
                    # Try increasing and decreasing
                    for delta in [-0.1, 0.1]:
                        test_state = result.optimized_state.copy()
                        test_state[key] = result.optimized_state[key] * (1 + delta)

                        score = self._evaluate_target(target, test_state)
                        if score > best_score:
                            best_score = score
                            best_change = (key, test_state[key])

            if best_change:
                key, value = best_change
                result.optimized_state[key] = value
            else:
                result.converged = True
                break

    def _genetic_optimization(
        self, target: Any, result: OptimizationResult, max_iterations: int
    ):
        """Genetic algorithm optimization."""
        population_size = 10
        mutation_rate = 0.1

        # Initialize population
        population = [result.optimized_state.copy() for _ in range(population_size)]

        for i in range(max_iterations):
            result.iterations = i + 1

            # Evaluate fitness
            fitness = [
                self._evaluate_target(target, individual) for individual in population
            ]

            # Select best individuals
            sorted_pop = sorted(
                zip(fitness, population), key=lambda x: x[0], reverse=True
            )
            population = [ind for _, ind in sorted_pop[: population_size // 2]]

            # Crossover and mutation
            import random

            while len(population) < population_size:
                parent1 = random.choice(population)
                parent2 = random.choice(population)

                # Crossover
                child = {}
                for key in parent1:
                    child[key] = (
                        parent1[key]
                        if random.random() > 0.5
                        else parent2.get(key, parent1[key])
                    )

                # Mutation
                if random.random() < mutation_rate:
                    key = random.choice(list(child.keys()))
                    if isinstance(child[key], (int, float)):
                        child[key] *= random.uniform(0.9, 1.1)

                population.append(child)

            # Update best solution
            best_fitness = max(fitness)
            best_index = fitness.index(best_fitness)
            result.optimized_state = population[best_index]

    def _simulated_annealing(
        self, target: Any, result: OptimizationResult, max_iterations: int
    ):
        """Simulated annealing optimization."""
        import math
        import random

        temperature = 100.0
        cooling_rate = 0.95

        current_state = result.optimized_state.copy()
        current_score = self._evaluate_target(target, current_state)

        for i in range(max_iterations):
            result.iterations = i + 1

            # Generate neighbor
            neighbor = current_state.copy()
            key = random.choice(list(neighbor.keys()))
            if isinstance(neighbor[key], (int, float)):
                neighbor[key] *= random.uniform(0.9, 1.1)

            # Evaluate neighbor
            neighbor_score = self._evaluate_target(target, neighbor)

            # Accept or reject
            if neighbor_score > current_score:
                current_state = neighbor
                current_score = neighbor_score
            else:
                # Accept with probability
                delta = neighbor_score - current_score
                probability = math.exp(delta / temperature)
                if random.random() < probability:
                    current_state = neighbor
                    current_score = neighbor_score

            # Cool down
            temperature *= cooling_rate

            if temperature < 0.01:
                result.converged = True
                break

        result.optimized_state = current_state

    def _default_optimization(
        self, target: Any, result: OptimizationResult, max_iterations: int
    ):
        """Default optimization strategy."""
        self._greedy_optimization(target, result, max_iterations)

    # Helper methods
    def _get_state(self, target: Any) -> Dict[str, Any]:
        """Get current state of target."""
        # Simplified state extraction
        return {
            "performance": 70.0,
            "memory": 1024.0,
            "throughput": 100.0,
            "latency": 500.0,
        }

    def _evaluate_target(self, target: Any, state: Dict[str, Any]) -> float:
        """Evaluate target with given state."""
        # Simplified evaluation
        score = 0
        for key, value in state.items():
            if key == "performance":
                score += value
            elif key == "memory":
                score -= value / 100
            elif key == "throughput":
                score += value / 10
            elif key == "latency":
                score -= value / 100

        return score

    def _calculate_gradient(
        self, target: Any, parameter: str, state: Dict[str, Any]
    ) -> float:
        """Calculate gradient for parameter."""
        epsilon = 0.001

        # Numerical gradient
        state_plus = state.copy()
        state_plus[parameter] += epsilon
        score_plus = self._evaluate_target(target, state_plus)

        state_minus = state.copy()
        state_minus[parameter] -= epsilon
        score_minus = self._evaluate_target(target, state_minus)

        return (score_plus - score_minus) / (2 * epsilon)

    def _calculate_improvements(
        self, original: Dict[str, Any], optimized: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate improvements between states."""
        improvements = {}

        for key in original:
            if key in optimized and isinstance(original[key], (int, float)):
                original_val = original[key]
                optimized_val = optimized[key]

                if original_val != 0:
                    improvement = ((optimized_val - original_val) / original_val) * 100
                    improvements[key] = improvement

        return improvements

    def _evaluate_parameters(self, parameters: Dict[str, Any], metric: str) -> float:
        """Evaluate parameters for given metric."""
        # Simplified evaluation
        import random

        return random.uniform(0, 100)

    def _measure_metric(self, target: Any, metric: str) -> float:
        """Measure metric for target."""
        # Simplified measurement
        import random

        if metric == "response_time":
            return random.uniform(100, 2000)
        elif metric == "throughput":
            return random.uniform(50, 500)
        elif metric == "memory_usage":
            return random.uniform(512, 2048)
        elif metric == "resource_usage":
            return random.uniform(20, 95)
        else:
            return random.uniform(0, 100)

    def _evaluate_configuration(self, config: Dict[str, Any], metric: str) -> float:
        """Evaluate configuration for metric."""
        # Simplified evaluation
        import random

        return random.uniform(0, 100)

    def shutdown(self) -> bool:
        """Shutdown the optimizer agent."""
        logger.info(
            "optimizer_agent_shutdown",
            profiles_count=len(self.profiles),
            results_count=len(self.results),
        )
        self.profiles.clear()
        self.results.clear()
        self.benchmarks.clear()
        return True
