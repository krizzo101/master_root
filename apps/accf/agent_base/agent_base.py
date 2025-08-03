"""
ACCF Agent Base Class

Purpose:
    Foundation for all agentic capabilities: initialization, message handling, state management, logging, and extensibility.

References:
    - docs/applications/ACCF/standards/agent_base_class_requirements.md
    - docs/applications/ACCF/architecture/adr/agent_base_class_adrs.md
    - .cursor/templates/implementation/agent_base_class_output_template.yml

Usage:
    from agent_base import AgentBase
    agent = AgentBase(...)
    agent.run()
"""

from abc import ABC, abstractmethod
import logging
import os
import time

import openai


class AgentBase:
    def __init__(self, name: str, config: dict = None):
        """Initialize the agent with a name and optional config."""
        self.name = name
        self.config = config or {}
        self.state = {}
        self.log = []

    def handle_message(self, message: dict) -> dict:
        """Process an incoming message and return a response."""
        # Placeholder for message handling logic
        return {"status": "not_implemented"}

    def update_state(self, key: str, value):
        """Update the agent's internal state."""
        self.state[key] = value

    def get_state(self, key: str):
        """Retrieve a value from the agent's state."""
        return self.state.get(key)

    def log_event(self, event: str):
        """Log an event or action."""
        self.log.append(event)

    def run(self):
        """Persistent, self-generating, autonomous main loop for the agent."""
        self.log_event(
            "[AgentBase] Loading autonomous operation rules and protocols..."
        )
        self.load_rules_and_protocols()
        self.log_event("[AgentBase] Entering persistent autonomous loop.")
        while not self.should_stop():
            try:
                # 1. Check for new work (tasks, files, sessions, logs, optimization opportunities)
                task = self.detect_new_task()
                if task:
                    self.log_event(f"[AgentBase] New task detected: {task}")
                    self.execute_task(task)
                    # Immediately plan and execute the next task
                    continue
                # 2. If no explicit tasks, generate new ones based on system goals, monitoring, self-improvement, maintenance
                generated_task = self.generate_proactive_task()
                if generated_task:
                    self.log_event(
                        f"[AgentBase] Proactively generated new task: {generated_task}"
                    )
                    self.execute_task(generated_task)
                    continue
                # 3. If still idle, perform self-improvement and maintenance
                self.log_event(
                    "[AgentBase] No work found. Performing self-improvement and maintenance."
                )
                self.self_improvement()
                self.maintenance()
                # 4. Log progress and evidence
                self.log_event("[AgentBase] Loop iteration complete. Sleeping briefly.")
                time.sleep(2)  # Sleep to avoid tight loop
            except Exception as e:
                self.log_event(f"[AgentBase] Exception encountered: {e}")
                if self.is_hard_blocker(e):
                    self.log_event(
                        "[AgentBase] Hard blocker encountered. Requesting user input."
                    )
                    self.request_user_input(e)
                else:
                    self.log_event("[AgentBase] Non-fatal error. Continuing loop.")
        self.log_event("[AgentBase] Stop signal received. Exiting persistent loop.")

    def load_rules_and_protocols(self):
        """Load all applicable rules and protocols for autonomous operation (enforce always_applied_workspace_rules, autonomous.md, etc)."""
        # Placeholder: Load rules from disk, environment, or config as needed
        pass

    def detect_new_task(self):
        """Detect new work (tasks, files, sessions, logs, optimization opportunities). Override in subclass."""
        return None

    def generate_proactive_task(self):
        """Proactively generate new tasks if idle (system goals, monitoring, self-improvement, maintenance). Override in subclass."""
        return None

    def execute_task(self, task):
        """Execute a detected or generated task. Override in subclass."""
        pass

    def self_improvement(self):
        """Continuously review past actions, optimize logic, update guardrails, and persist new insights. Override in subclass."""
        pass

    def maintenance(self):
        """Perform maintenance actions (archiving, cleaning, validating data). Override in subclass."""
        pass

    def is_hard_blocker(self, exception):
        """Determine if an exception is a hard blocker requiring user input (override as needed)."""
        return False

    def request_user_input(self, exception):
        """Request user input for a hard blocker (placeholder). Only called if truly blocked."""
        print(f"[AgentBase] User input required: {exception}")

    def should_stop(self):
        """Determine if the agent should stop (override for external stop signals). Default: never stop unless explicitly told."""
        return False


class LLMBaseAgent(AgentBase, ABC):
    """
    Abstract base class for all LLM-backed agents (OpenAI Assistants API).
    Provides OpenAI client and logger setup. Requires 'answer' method.
    """

    def __init__(
        self, name: str, api_key_env: str = "OPENAI_API_KEY", config: dict = None
    ):
        super().__init__(name=name, config=config)
        self.api_key = os.getenv(api_key_env)
        self.client = (
            openai.OpenAI(api_key=self.api_key) if self.api_key else openai.OpenAI()
        )
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

    @abstractmethod
    def answer(self, prompt: str) -> dict:
        """Answer a prompt using the LLM/Assistants API. Must be implemented by subclasses."""
        pass
