#!/usr/bin/env python3
"""
Auto MCP Middleware - Automatic MCP Server Selection for Claude Code
This middleware intercepts all prompts and automatically routes to appropriate MCP servers
"""

import json
import re
import hashlib
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from functools import lru_cache
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/tmp/claude_auto_mcp.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class AutoMCPMiddleware:
    """Middleware for automatic MCP server selection"""

    def __init__(
        self, config_path: str = "/home/opsvi/master_root/.claude/config.json"
    ):
        """Initialize middleware with configuration"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.guidance_cache = {}
        self.decision_cache = {}
        self.metrics = {
            "total_prompts": 0,
            "mcp_engaged": 0,
            "server_usage": {"V1": 0, "V2": 0, "V3": 0},
            "fallbacks": 0,
        }

        # Preload guidance documents if configured
        if self.config["auto_mcp"]["preload_docs"]:
            self._preload_guidance_docs()

    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._default_config()

    def _default_config(self) -> Dict:
        """Return default configuration if file not found"""
        return {
            "auto_mcp": {"enabled": True, "threshold": 2, "default_server": "V1"},
            "complexity_scoring": {
                "keywords": {},
                "thresholds": {"simple": 0, "use_v1": 2, "use_v2": 3, "use_v3": 6},
            },
        }

    def _preload_guidance_docs(self):
        """Preload guidance documents into cache"""
        for doc_name, doc_info in self.config.get("guidance_documents", {}).items():
            if doc_info.get("preload", False):
                try:
                    with open(doc_info["path"], "r") as f:
                        self.guidance_cache[doc_name] = f.read()
                    logger.info(f"Preloaded guidance doc: {doc_name}")
                except Exception as e:
                    logger.error(f"Failed to preload {doc_name}: {e}")

    def analyze_prompt(self, prompt: str) -> Tuple[bool, Optional[str], Dict]:
        """
        Analyze prompt and determine if MCP server should be used

        Returns:
            (should_use_mcp, server_type, metadata)
        """
        self.metrics["total_prompts"] += 1

        # Check if auto MCP is enabled
        if not self.config["auto_mcp"]["enabled"]:
            return (False, None, {})

        # Check cache first
        prompt_hash = hashlib.md5(prompt[:200].encode()).hexdigest()
        if prompt_hash in self.decision_cache:
            cached = self.decision_cache[prompt_hash]
            logger.debug(f"Using cached decision for prompt: {cached}")
            return cached

        # Calculate complexity score
        score, triggers = self._calculate_complexity_score(prompt)

        # Check for instant triggers
        instant_server = self._check_instant_triggers(prompt.lower())
        if instant_server:
            decision = (
                True,
                instant_server,
                {"reason": "instant_trigger", "triggers": triggers},
            )
            self._cache_decision(prompt_hash, decision)
            self.metrics["mcp_engaged"] += 1
            self.metrics["server_usage"][instant_server] += 1
            return decision

        # Determine server based on score
        thresholds = self.config["complexity_scoring"]["thresholds"]

        if score >= thresholds["use_v3"]:
            server = "V3"
        elif score >= thresholds["use_v2"]:
            # Check if task has parallelism opportunity
            if self._has_parallel_opportunity(prompt):
                server = "V2"
            else:
                server = "V1"
        elif score >= thresholds["use_v1"]:
            server = "V1"
        else:
            decision = (False, None, {"reason": "below_threshold", "score": score})
            self._cache_decision(prompt_hash, decision)
            return decision

        decision = (
            True,
            server,
            {"reason": "complexity_score", "score": score, "triggers": triggers},
        )

        self._cache_decision(prompt_hash, decision)
        self.metrics["mcp_engaged"] += 1
        self.metrics["server_usage"][server] += 1

        logger.info(f"Auto-selected {server} for prompt (score: {score})")
        return decision

    def _calculate_complexity_score(self, prompt: str) -> Tuple[int, List[str]]:
        """Calculate complexity score for prompt"""
        score = 0
        triggers = []
        prompt_lower = prompt.lower()

        for keyword, points in self.config["complexity_scoring"]["keywords"].items():
            if keyword in prompt_lower:
                score += points
                triggers.append(keyword)

        return score, triggers

    def _check_instant_triggers(self, prompt_lower: str) -> Optional[str]:
        """Check for keywords that instantly trigger specific servers"""
        # V1 instant triggers
        v1_triggers = self.config["mcp_servers"]["claude_code_v1"][
            "auto_trigger_keywords"
        ]
        if any(trigger in prompt_lower for trigger in v1_triggers):
            return "V1"

        # V2 instant triggers
        v2_triggers = self.config["mcp_servers"]["claude_code_v2"][
            "auto_trigger_keywords"
        ]
        if any(trigger in prompt_lower for trigger in v2_triggers):
            return "V2"

        # V3 instant triggers
        v3_triggers = self.config["mcp_servers"]["claude_code_v3"][
            "auto_trigger_keywords"
        ]
        if any(trigger in prompt_lower for trigger in v3_triggers):
            return "V3"

        return None

    def _has_parallel_opportunity(self, prompt: str) -> bool:
        """Check if prompt suggests parallel processing opportunity"""
        parallel_indicators = ["all", "every", "multiple", "each", "batch"]
        prompt_lower = prompt.lower()
        return any(indicator in prompt_lower for indicator in parallel_indicators)

    def _cache_decision(self, prompt_hash: str, decision: Tuple):
        """Cache decision for future use"""
        # Limit cache size
        if len(self.decision_cache) > 100:
            # Remove oldest entries
            self.decision_cache = dict(list(self.decision_cache.items())[50:])

        self.decision_cache[prompt_hash] = decision

    def get_server_config(self, server: str) -> Dict:
        """Get default configuration for specified server"""
        server_map = {
            "V1": "claude_code_v1",
            "V2": "claude_code_v2",
            "V3": "claude_code_v3",
        }

        server_key = server_map.get(server)
        if server_key and server_key in self.config["mcp_servers"]:
            return self.config["mcp_servers"][server_key].get("default_config", {})

        return {}

    def get_v3_mode(self, prompt: str) -> str:
        """Determine V3 mode based on prompt content"""
        prompt_lower = prompt.lower()
        mode_detection = self.config["mcp_servers"]["claude_code_v3"].get(
            "mode_detection", {}
        )

        for mode, keywords in mode_detection.items():
            if any(keyword in prompt_lower for keyword in keywords):
                return mode

        return "CODE"  # Default mode

    def get_tool_path(self, server: str, tool: str) -> str:
        """Get full tool path for MCP server"""
        server_map = {
            "V1": {
                "sync": "mcp__claude-code-wrapper__claude_run",
                "async": "mcp__claude-code-wrapper__claude_run_async",
                "status": "mcp__claude-code-wrapper__claude_status",
                "result": "mcp__claude-code-wrapper__claude_result",
            },
            "V2": {
                "parallel": "mcp__claude-code-v2__spawn_parallel_agents",
                "spawn": "mcp__claude-code-v2__spawn_agent",
                "collect": "mcp__claude-code-v2__collect_results",
            },
            "V3": {
                "run": "mcp__claude-code-v3__claude_run_v3",
                "status": "mcp__claude-code-v3__get_v3_status",
            },
        }

        return server_map.get(server, {}).get(tool, "")

    def get_fallback_chain(self, server: str) -> List[str]:
        """Get fallback chain for server"""
        return self.config["fallback_chain"].get(server, ["direct"])

    def log_metrics(self):
        """Log current metrics"""
        logger.info(f"Auto MCP Metrics: {json.dumps(self.metrics, indent=2)}")

        # Write to metrics file
        metrics_file = Path("/tmp/claude_mcp_metrics.json")
        with open(metrics_file, "w") as f:
            json.dump(
                {"timestamp": datetime.now().isoformat(), "metrics": self.metrics},
                f,
                indent=2,
            )

    def process_prompt(self, prompt: str) -> Dict:
        """
        Main entry point for processing prompts

        Returns complete routing decision with all metadata
        """
        should_use, server, metadata = self.analyze_prompt(prompt)

        if not should_use:
            return {"use_mcp": False, "route": "direct", "metadata": metadata}

        # Get server configuration
        config = self.get_server_config(server)

        # Special handling for V3
        if server == "V3":
            config["mode"] = self.get_v3_mode(prompt)

        # Build response
        response = {
            "use_mcp": True,
            "server": server,
            "config": config,
            "tools": self._get_server_tools(server),
            "fallback_chain": self.get_fallback_chain(server),
            "metadata": metadata,
        }

        logger.debug(f"Routing decision: {response}")
        return response

    def _get_server_tools(self, server: str) -> Dict[str, str]:
        """Get all available tools for a server"""
        if server == "V1":
            return {
                "sync": self.get_tool_path("V1", "sync"),
                "async": self.get_tool_path("V1", "async"),
                "status": self.get_tool_path("V1", "status"),
                "result": self.get_tool_path("V1", "result"),
            }
        elif server == "V2":
            return {
                "parallel": self.get_tool_path("V2", "parallel"),
                "spawn": self.get_tool_path("V2", "spawn"),
                "collect": self.get_tool_path("V2", "collect"),
            }
        elif server == "V3":
            return {
                "run": self.get_tool_path("V3", "run"),
                "status": self.get_tool_path("V3", "status"),
            }
        return {}


# Global middleware instance
middleware = AutoMCPMiddleware()


def analyze_user_prompt(prompt: str) -> Dict:
    """
    Public API for analyzing user prompts

    This function should be called for every user prompt
    to determine if and how to use MCP servers
    """
    return middleware.process_prompt(prompt)


def get_metrics() -> Dict:
    """Get current metrics"""
    return middleware.metrics


def reset_metrics():
    """Reset metrics"""
    middleware.metrics = {
        "total_prompts": 0,
        "mcp_engaged": 0,
        "server_usage": {"V1": 0, "V2": 0, "V3": 0},
        "fallbacks": 0,
    }


if __name__ == "__main__":
    # Test the middleware
    test_prompts = [
        "Fix the login bug",
        "Analyze all Python files for security issues",
        "Create a production-ready authentication system",
        "What does this function do?",
        "Refactor every module to use async/await",
        "Debug why the API returns 500 errors",
    ]

    for prompt in test_prompts:
        result = analyze_user_prompt(prompt)
        print(f"\nPrompt: {prompt}")
        print(f"Decision: {json.dumps(result, indent=2)}")

    print(f"\nMetrics: {json.dumps(get_metrics(), indent=2)}")
